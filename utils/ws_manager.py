from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from schema.fireschema import FireSchema

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_json_of_fires(self, fires: list[FireSchema], websocket: WebSocket):
        fires_json = [jsonable_encoder(fire) for fire in fires]

        payload = {
            "type" : "fire_alert",
            "num_fires" : len(fires_json),
            "fires" : fires_json 
        }

        await websocket.send_json(payload)
    
    async def send_json_message(self, message: str, websocket: WebSocket):
        payload = {
            "type" : "message",
            "message" : message,
        }

        await websocket.send_json(payload)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)