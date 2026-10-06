from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
import json

import os
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

app = FastAPI()
#for local setup 
'''
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)'''


ONLINE_USERS_KEY = "online_users"


class ConnectionManager:

    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        user_id: str,
        websocket: WebSocket
    ):

        await websocket.accept()

        self.connections[user_id] = websocket

        # Add user to Redis online set
        await redis_client.sadd(
            ONLINE_USERS_KEY,
            user_id
        )

        # Send existing users' locations
        online_users = await redis_client.smembers(
            ONLINE_USERS_KEY
        )

        for existing_user_id in online_users:

            # Don't send the new user's own location
            if existing_user_id == user_id:
                continue

            location = await redis_client.get(
                f"user:{existing_user_id}:location"
            )

            if location:

                await websocket.send_json({
                    "type": "user_location",
                    "data": json.loads(location)
                })

    async def disconnect(
        self,
        user_id: str
    ):

        self.connections.pop(user_id, None)

        # Remove from online users
        await redis_client.srem(
            ONLINE_USERS_KEY,
            user_id
        )

        # Remove latest location
        await redis_client.delete(
            f"user:{user_id}:location"
        )

    async def broadcast(
        self,
        message: dict,
        exclude_user: str | None = None
    ):

        dead_users = []

        for user_id, websocket in self.connections.items():

            if user_id == exclude_user:
                continue

            try:

                await websocket.send_json(message)

            except Exception:

                dead_users.append(user_id)

        for user_id in dead_users:

            await self.disconnect(user_id)


manager = ConnectionManager()


@app.get("/")
async def root():

    return {
        "status": "Live location server running"
    }


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):

    await manager.connect(
        user_id,
        websocket
    )

    print(f"User {user_id} connected")

    # Tell other users that this user is online
    await manager.broadcast(
        {
            "type": "user_online",
            "user_id": user_id
        },
        exclude_user=user_id
    )

    try:

        while True:

            data = await websocket.receive_json()

            latitude = data["latitude"]
            longitude = data["longitude"]
            display_name = data.get( "displayName", f"User {user_id[:6]}" )

            location = { "user_id": user_id, "displayName": display_name, "latitude": latitude, "longitude": longitude }

            # Store latest location
            await redis_client.set( f"user:{user_id}:location", json.dumps(location) )
            await manager.broadcast( { "type": "user_location", "data": location }, exclude_user=user_id )

    except WebSocketDisconnect:

        await manager.disconnect(user_id)

        # Tell remaining users
        await manager.broadcast(
            {
                "type": "user_offline",
                "user_id": user_id
            }
        )

        print(f"User {user_id} disconnected")