import logging
import typer
import asyncio
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError
import json
import urllib.parse
from websockets.asyncio.server import serve

from west.config import get_settings
from west import utils


logger = logging.getLogger(__name__)
app = typer.Typer()

CHANNEL = "notifications"
CONNECTIONS = {}
settings = get_settings()

if settings.papermerge__main__logging_cfg:
    utils.setup_logging(settings.papermerge__main__logging_cfg)


def get_query_param(path, key) -> str | None:
    query = urllib.parse.urlparse(path).query
    params = urllib.parse.parse_qs(query)
    values = params.get(key, [])
    if len(values) == 1:
        return values[0]

    return None


async def handler(websocket):
    try:
        user_id = websocket.user_id
    except AttributeError:
        logger.debug('user_id attribute not in websocket')
        return

    CONNECTIONS[user_id] = websocket

    try:
        await websocket.wait_closed()
    finally:
        if CONNECTIONS.get(user_id, None):
            del CONNECTIONS[user_id]
        else:
            logger.debug(f"user_id={user_id} not found in CONNECTIONS")


async def extract_user_id(connection, request):
    """Extract user_id either from `remote-user-id` or from `token` param"""

    # extract user ID from "remote-user-id" query parameter
    user_id = get_query_param(request.path, "remote-user-id")
    if user_id and isinstance(user_id, str):
        connection.user_id = user_id

    # i.e. jwt token
    token = get_query_param(request.path, "token")
    if '.' in token:
        _, payload, _ = token.split('.')
        data = utils.decode(payload)
        user_id: str = data.get("sub")
        if user_id and isinstance(user_id, str):
            connection.user_id = user_id


async def process_events():
    """Listen to events in Redis and process them."""
    redis = aioredis.from_url(settings.papermerge__redis__url)
    pubsub = redis.pubsub()

    await pubsub.subscribe(CHANNEL)
    logger.info(f"Subscribing to {settings.papermerge__redis__url} channel: {CHANNEL}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        payload = message["data"].decode()
        event = json.loads(payload)

        for user_id, websocket in CONNECTIONS.items():
            if event['payload']["user_id"] == user_id:
                data = json.dumps(event)
                logger.debug(f"Sending data to client {data}")
                await websocket.send(data)


async def main(port: int):
    logger.info(f"Listening on local port {port}")

    try:
        async with serve(handler, "", port, process_request=extract_user_id):
            await process_events()  # runs forever
    except ConnectionError as ex:
        logger.critical(f'{ex} Bye.')


@app.command()
def entrypoint(port: int = 8001):
    asyncio.run(main(port))


if __name__ == "__main__":
    entrypoint()
