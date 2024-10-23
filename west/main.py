import asyncio
from redis import asyncio as aioredis
import uuid
import json
import urllib.parse
from websockets.asyncio.server import serve

from west.config import get_settings


CHANNEL = "notifications"
CONNECTIONS = {}
settings = get_settings()


def get_query_param(path, key):
    query = urllib.parse.urlparse(path).query
    params = urllib.parse.parse_qs(query)
    values = params.get(key, [])
    if len(values) == 1:
        return values[0]

async def handler(websocket):
    try:
        user_id = websocket.user_id
    except AttributeError:
        return

    CONNECTIONS[user_id] = websocket

    try:
        await websocket.wait_closed()
    finally:
        del CONNECTIONS[user_id]


async def remove_user_auth(connection, request):
    # extract user ID from "Remote-User" header
    # or from JWT token in Authorization header
    user_id = get_query_param(request.path, "remote-user-id")
    if user_id and isinstance(user_id, str):
        connection.user_id = uuid.UUID(user_id)


async def process_events():
    """Listen to events in Redis and process them."""
    redis = aioredis.from_url(settings.papermerge__redis__url)
    pubsub = redis.pubsub()

    await pubsub.subscribe(CHANNEL)
    print(f"Subscribing to {settings.papermerge__redis__url} channel: {CHANNEL}")
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        payload = message["data"].decode()
        event = json.loads(payload)
        for user_id, websocket in CONNECTIONS.items():
            if event['payload']["user_id"] == str(user_id):
                data = json.dumps(event)
                print(data)
                await websocket.send(data)


async def main():
    print("Starting on port 8001")
    async with serve(handler, "", 8001, process_request=remove_user_auth):
        await process_events()  # runs forever

if __name__ == "__main__":
    asyncio.run(main())
