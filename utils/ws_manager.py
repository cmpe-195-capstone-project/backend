from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict] = {}
    
    async def add_connection(self, websocket: WebSocket, id: str, user_location: UserLocation):
        self.active_connections[id] = {"socket" : websocket, "location" : user_location}

    async def send_message(self, id: str, message: str):
        ws = self.active_connections[id]["socket"]
        await ws.send_text(message)
    
    async def update_location(self, id: str, user_location: UserLocation):
        self.active_connections[id]["location"] = user_location

    async def send_json_of_fires(self, id: str, fires: list[FireSchema]):
        fires_json = [jsonable_encoder(fire) for fire in fires]
        ws = self.active_connections[id]["socket"]

        payload = {
            "type" : "fire_alert",
            "num_fires" : len(fires_json),
            "fires" : fires_json 
        }
        await ws.send_json(payload)
    
    async def send_json_message(self, id: str, message: str):
        ws = self.active_connections[id]["socket"]
        payload = {
            "type" : "message",
            "message" : message,
        }

        await ws.send_json(payload)

    async def disconnect(self, id: str):
        del self.active_connections[id]