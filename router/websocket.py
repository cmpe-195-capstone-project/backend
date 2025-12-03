from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from db import get_db, get_test_db, get_active_db, FireModel, SessionLocal, SessionLocalTest
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation
from utils.geo import get_coordinates
from utils.ws_manager import ConnectionManager
from config import settings
from utils.colors import Color

ws = APIRouter()

manager = ConnectionManager()
cache: dict[str, set[FireSchema]] = {}

@ws.websocket("/alert")
async def alert(websocket: WebSocket):
    await websocket.accept()
    # check id from query parameters
    id = websocket.query_params.get("id")

    try:
        if not id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        # intial connection
        data = await websocket.receive_json()
        print(f"{Color.YELLOW}[INFO] WS: Data recieved: {data}{Color.RESET}")
        location = UserLocation(**data)

        # store the connection
        await manager.add_connection(websocket=websocket, id=id, user_location=location)
        print(f"{Color.YELLOW}[INFO] WS: Connected device [ID] - {id}{Color.RESET}", flush=True)

        # loop over the ongoing messages
        while True:
            data = await websocket.receive_json()

            # client pushes updated location to the server
            if data.get("type") == "update_location":
                print(f"{Color.YELLOW}[INFO] WS: Updated location for device - ID[{id}]{Color.RESET}", flush=True)
                new_location = UserLocation(**data)
                await manager.update_location(id=id, user_location=new_location)

    except WebSocketDisconnect:
        # await manager.disconnect(id=id)
        print(f"{Color.YELLOW}[INFO] WSDisconnect: Disconnect websocket - [ID: {id}]{Color.RESET}", flush=True)
        return
    except (ValueError, TypeError) as e: 
        print(f"{Color.RED}[ERROR]: An error occurred: {e}{Color.RESET}")
        await manager.send_json_message(id, "Invalid location data format")
    except Exception as e:
        print(f"{Color.RED}[ERROR]: Unexpected error occurred with device ID[{id}]: {e}{Color.RESET}", flush=True)
        return
        # await manager.disconnect(id=id)


async def check_fires():
    print(f"{Color.GREEN}[INFO] CheckFires: performing scheduled fire check at {datetime.now()}{Color.RESET}", flush=True)
    db_gen = get_active_db()
    db = next(db_gen)
    id = None
    try:
        # get all active fires  
        active_fires = db.query(FireModel).filter(FireModel.is_active == True).all()
        print(f"{Color.BLUE}[ACTIVE FIRE] there are {(len(active_fires))} active fires{Color.RESET}", flush=True)

        # loop over active connections
        for id, user_data in manager.active_connections.items():
            user_location = user_data["location"]
            print(f"{Color.GREEN}[INFO] CheckFires: Check for client (id={id}) (loc={user_location}) {datetime.now()}{Color.RESET}", flush=True)

            # get the coordinates of a box around the user
            bounding_box = get_coordinates(
                latitude=user_location.latitude, 
                longitude=user_location.longitude, 
                radius=user_location.radius
            )

            # get the cache or create a new cache
            user_cache = cache.setdefault(id, set())

            fire_alerts: list[FireSchema] = [] # used to store alerts that will be sent

            # loop over the active fires 
            if active_fires:   
                for fire in active_fires:
                    # check if there is a fire within the users bounding box
                    if (bounding_box.min_lat <= fire.latitude <= bounding_box.max_lat and
                            bounding_box.min_lon <= fire.longitude <= bounding_box.max_lon):

                        # check if the fire is already in the cache, if not add it to alerts list 
                        fire_schema = FireSchema.model_validate(fire, from_attributes=True) 

                        if fire_schema in user_cache: # if cache hit, skip over it
                            continue
                        else:
                            print(f"{Color.BLUE}[FIRE W/IN BOUNDS] {fire_schema.name} is within bounds. Sending to client... {Color.RESET}", flush=True)
                            fire_alerts.append(fire_schema) # add fire alert to cache

            else: # There are NO active fires
                print(f"{Color.GREEN}[INFO] CheckFires: No active fire incidents available at {datetime.now()}{Color.RESET}", flush=True)
                await manager.send_json_message(id=id, message="There are no fires.")

            # send the fire alerts and store in cache
            if fire_alerts:
                # send the fire and store in cache
                await manager.send_json_of_fires(id=id, fires=fire_alerts)
                user_cache.update(fire_alerts)
                print(f"{Color.GREEN}[INFO] CheckFires: Delivered {len(fire_alerts)} fire alert(s) to device {id}{Color.RESET}", flush=True)
                
       
    except Exception as e:
        print(f"{Color.RED}[ERROR] CheckFires: Error during Task [check_fire()] - Type {type(e).__name__}: {e}{Color.RESET}", flush=True)
    finally:
        db.close()