import asyncio
import json
import websockets


async def receive_messages(name, websocket):
    try:
        async for message in websocket:
            print(f"\n{name} RECEIVED:")
            print(message)
    except websockets.ConnectionClosed:
        print(f"{name} disconnected")


async def send_locations(name, websocket):
    locations = [
        (12.9716, 77.5946),
        (12.9718, 77.5949),
        (12.9721, 77.5952),
        (12.9725, 77.5956),
    ]

    for latitude, longitude in locations:

        data = {
            "latitude": latitude,
            "longitude": longitude
        }

        await websocket.send(json.dumps(data))

        print(f"{name} SENT: {data}")

        await asyncio.sleep(2)


async def main():

    user_id = input("Enter user ID: ")

    uri = f"ws://127.0.0.1:8000/ws/{user_id}"

    async with websockets.connect(uri) as websocket:

        print(f"{user_id} connected")

        await asyncio.gather(
            receive_messages(user_id, websocket),
            send_locations(user_id, websocket)
        )


asyncio.run(main())