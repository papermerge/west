import asyncio
import aioredis
import uuid
import json
from websockets.asyncio.server import serve

from west.config import get_settings


EVENTS = "events"
CONNECTIONS = {}
settings = get_settings()

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


async def cookie_auth(connection, request):
    # extract user ID from "Remote-User" header
    # or from JWT token in Authorization header
    user_id = request.headers.get("Remote-User", None)
    if user_id and isinstance(user_id, str):
        connection.user_id = uuid.UUID(user_id)


async def process_events():
    """Listen to events in Redis and process them."""
    redis = aioredis.from_url(settings.papermerge__redis__url)
    pubsub = redis.pubsub()

    await pubsub.subscribe(EVENTS)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        payload = message["data"].decode()
        # Broadcast event to all users who have permissions to see it.
        event = json.loads(payload)

        for user_id, websocket in CONNECTIONS.items():
            if event["user_id"] == user_id:
               await websocket.send(json.dumps(event))


async def main():
    async with serve(handler, "", 8001, process_request=cookie_auth):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
