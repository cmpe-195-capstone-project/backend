from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict] = {}

    async def add_connection(self, websocket: WebSocket, id: str, user_location: UserLocation):
        self.active_connections[id] = {"socket": websocket, "location": user_location}

    async def send_message(self, id: str, message: str):
        conn = self.active_connections.get(id)
        if not conn:
            print(f"[WS] Tried to send message to missing ID: {id}")
            return
        await conn["socket"].send_text(message)

    async def update_location(self, id: str, user_location: UserLocation):
        conn = self.active_connections.get(id)
        if not conn:
            print(f"[WS] Tried to update location for missing ID: {id}")
            return
        conn["location"] = user_location

    async def send_json_of_fires(self, id: str, fires: list[FireSchema]):
        conn = self.active_connections.get(id)
        if not conn:
            print(f"[WS] Tried to send fires JSON to missing ID: {id}")
            return

        fires_json = [jsonable_encoder(fire) for fire in fires]
        payload = {
            "type": "fire_alert",
            "num_fires": len(fires_json),
            "fires": fires_json
        }

        await conn["socket"].send_json(payload)

    async def send_json_message(self, id: str, message: str):
        conn = self.active_connections.get(id)
        if not conn:
            print(f"[WS] Tried to send JSON message to missing ID: {id}")
            return
        
        payload = {
            "type": "message",
            "message": message,
        }
        await conn["socket"].send_json(payload)

    async def disconnect(self, id: str):
        if id in self.active_connections:
            del self.active_connections[id]
            print(f"[WS] Disconnected: {id}")
        else:
            print(f"[WS] Tried to disconnect missing ID: {id}")
