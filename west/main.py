import logging
import typer
import asyncio
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError
import json
import urllib.parse
from http import HTTPStatus
from websockets.asyncio.server import serve

from west.config import get_settings, UserIDParamName
from west import utils


logger = logging.getLogger(__name__)

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
    logger.debug("Received connection")
    try:
        user_id = websocket.user_id
    except AttributeError:
        logger.debug('user_id attribute not in websocket')
        return

    logger.debug(f"user_id={user_id}")
    CONNECTIONS[user_id] = websocket

    try:
        await websocket.wait_closed()
    finally:
        if CONNECTIONS.get(user_id, None):
            del CONNECTIONS[user_id]
        else:
            logger.debug(f"user_id={user_id} not found in CONNECTIONS")


async def process_request(connection, request):
    logger.debug("processing request")
    if request.path == settings.health_check_path:
        logger.debug("Heath check")
        return connection.respond(HTTPStatus.OK, "OK")

    # extract user ID from "remote-user-id" query parameter
    if settings.user_id_param_name == UserIDParamName.remote_user_id:
        # remote-user-id is not validated!
        logger.debug("Checking remote-user-id url param")
        user_id = get_query_param(request.path, "remote-user-id")
        if user_id and isinstance(user_id, str):
            connection.user_id = user_id

    if settings.user_id_param_name == UserIDParamName.token:
        logger.debug("Checking token url param")
        # i.e. jwt token
        token = get_query_param(request.path, "token")

        if not token:
            logger.info("token missing")
            return

        if not utils.token_is_valid(token):
            logger.info(f"Invalid token={token}")
            return

        logger.debug("Valid token found")
        # i.e. valid jwt token
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


async def main(port: int, host: str):
    logger.info(f"Listening on {host}:{port}")

    try:
        async with serve(handler, host, port, process_request=process_request):
            await process_events()  # runs forever
    except ConnectionError as ex:
        logger.critical(f'{ex} Bye.')
    except Exception as ex:
        logger.critical(f'{ex} Bye.')


def entrypoint(port: int = 8001, host: str = "0.0.0.0"):
    asyncio.run(main(port, host))


if __name__ == "__main__":
    typer.run(entrypoint)
