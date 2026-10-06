import asyncio
import json
import websockets


# ==========================================
# RECEIVE MESSAGES
# ==========================================

async def receive_messages(name, websocket):

    try:

        async for message in websocket:

            data = json.loads(message)

            print(
                f"\n{name} RECEIVED:"
            )

            print(data)

    except websockets.ConnectionClosed:

        print(
            f"{name} disconnected"
        )


# ==========================================
# SEND CONTINUOUS LOCATION
# ==========================================

async def send_locations(name, websocket):

    # Starting locations
    locations = {

        "user-2": (
            12.875200,
            77.596300
        ),

        "user-3": (
            12.875400,
            77.594700
        ),

        "user-4": (
            12.873600,
            77.594800
        ),

        "user-5": (
            12.873900,
            77.596100
        ),
    }

    latitude, longitude = locations.get(
        name,
        (
            12.875200,
            77.596300
        )
    )

    while True:

        data = {
            "latitude": latitude,
            "longitude": longitude
        }

        await websocket.send(
            json.dumps(data)
        )

        print(
            f"{name} SENT: {data}"
        )

        # Move approximately 5 meters
        # north every 2 seconds

        latitude += 0.000045

        await asyncio.sleep(2)


# ==========================================
# MAIN
# ==========================================

async def main():

    user_id = input(
        "Enter user ID: "
    ).strip()

    uri = (
        f"ws://127.0.0.1:8000/ws/"
        f"{user_id}"
    )

    async with websockets.connect(
        uri
    ) as websocket:

        print(
            f"{user_id} connected"
        )

        await asyncio.gather(

            receive_messages(
                user_id,
                websocket
            ),

            send_locations(
                user_id,
                websocket
            )

        )


asyncio.run(main())