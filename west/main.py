import asyncio
import uuid
from websockets.asyncio.server import serve


async def handler(websocket):
    try:
        user_id = websocket.user_id
    except AttributeError:
        return

    print(user_id)

    async for message in websocket:
        print(message)


async def cookie_auth(connection, request):
    user_id = request.headers.get("Remote-User", None)
    if user_id and isinstance(user_id, str):
        connection.user_id = uuid.UUID(user_id)


async def main():
    async with serve(handler, "", 8001, process_request=cookie_auth):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
