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

            # 1: look at active fires in db 
            # active_fires = db.query(FireModel).filter(FireModel.final == False, FireModel.is_active == True).all()
            # fire_notifications = []
            # for fire in active_fires:
            #     user_location = (user_lat, user_long)
            #     fire_location = (fire.latitude, fire.longitude)

            #     distance = geodesic(user_location, fire_location)

            #     if distance < float(radius):
            #         fire_notifications.append(fire)
            
            # 2: create a box around users location and query database for fires within that box
            # need to get north point, south point, west point, east point all at a distance of 'radius'
           
             
            
            await manager.send_personal_message(f"list of all fires within {radius} of user's location", websocket)   

            san_jose = (user_lat, user_long) 
            santa_clara=(37.354107, -121.955238)
            distance = geodesic(san_jose, santa_clara).miles 
             
            if distance < float(radius): 
                print("im sending notification")

            
            await manager.send_personal_message(f"distance is: {distance}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_personal_message("Bye", websocket)
    

