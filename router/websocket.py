from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import timedelta

from db import get_db, get_test_db, FireModel
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation
from utils.geo import get_coordinates
from utils.ws_manager import ConnectionManager

ws = APIRouter()

manager = ConnectionManager()
cache: dict[str, FireSchema] = {}
DEFAULT_RADIUS = 10.0

@ws.websocket("/alert")
async def alert(websocket: WebSocket, db: Session = Depends(get_test_db)):
    await manager.connect(websocket)
    try:
        while True:
            # long. and latt. of San Jose: 
            # User sends these points (example)
            # latt: 	37.335480
            # long:     -121.893028
            # radius:   10
            
            # expect data to be JSON with lattitude and longitude data fields
            data = await websocket.receive_json()
            loc = UserLocation(**data)


            # create bouding box around users location 
            bounding_box = get_coordinates(latitude=loc.latitude, longitude=loc.longitude, radius=loc.radius)

            # select all fires in the box
            fires = db.query(FireModel).filter(
                FireModel.is_active == True,                 
                FireModel.longitude.between(bounding_box.min_lon, bounding_box.max_lon),
                FireModel.latitude.between(bounding_box.min_lat, bounding_box.max_lat)
            ).all()

            # list of alerts (in schema format)
            fires_schemas = []
            for fire in fires:
                cache_key = fire.id
                
                # fire is not cached, means we can send alert 
                if cache_key not in cache:
                    fires_schemas.append(fire)
                    cache[cache_key] = fire

                # if it is in the cache, check if the fire has been updated
                else:
                    # check if it has been updated
                    time_delta = fire.updated_datetime - cache[cache_key].updated_datetime
                    if time_delta > timedelta(seconds=0) and cache[cache_key].is_active:
                        # add the new fire to alert list and cache
                        fires_schemas.append(fire)
                        cache[cache_key] = fire
        
            if fires_schemas:
                fires_schemas = [FireSchema.model_validate(fire, from_attributes=True) for fire in fires_schemas]
                
            # send the fires
            if fires:
                await manager.send_json_of_fires(fires=fires_schemas, websocket=websocket)
            else:
                await manager.send_json_message(message="No fires detected.", websocket=websocket)

    except WebSocketDisconnect:
        await manager.send_message("Bye", websocket)
        manager.disconnect(websocket)
    except (ValueError, TypeError):
        await manager.send_json_message({"error": "Invalid location data format"}, websocket)