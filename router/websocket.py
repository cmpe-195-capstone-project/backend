from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from db import get_db, FireModel
from geopy.distance import geodesic

ws = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()


@ws.websocket("/notifcation")
async def notification_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            # long. and latt. of San Jose: User sends these points
            # latt: 	37.335480
            # long:     -121.893028
            # radius:   10
            
            # expect data to be JSON with lattitude and longitude data fields
            data = await websocket.receive_json()

            # check the data (i.e. users location) to see if there are fires nearby
            user_lat = data['lattitude']
            user_long = data['longitude']
            radius = data['radius']

            
            # fires = db.query(FireModel).filter(
                
            san_jose = (user_lat, user_long) 
            santa_clara=(37.354107, -121.955238)
            distance = geodesic(san_jose, santa_clara).miles 
             
            if distance < float(radius): 
                print("im sending notification")

            
            await manager.send_personal_message(f"distance is: {distance}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_personal_message("Bye", websocket)
    

