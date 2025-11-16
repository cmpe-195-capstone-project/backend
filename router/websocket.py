from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from db import get_db, get_test_db, FireModel, SessionLocal, SessionLocalTest
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation
from utils.geo import get_coordinates
from utils.ws_manager import ConnectionManager

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
        print(f"INFO: Data recieved: {data}")
        location = UserLocation(**data)

        # store the connection
        await manager.add_connection(websocket=websocket, id=id, user_location=location)
        print(f"INFO: Connected device [ID] - {id}", flush=True)

        # loop over the ongoing messages
        while True:
            data = await websocket.receive_json()

            # client pushes updated location to the server
            if data.get("type") == "update_location":
                print(f"ID[{id}] - Updated location", flush=True)
                new_location = UserLocation(**data)
                await manager.update_location(id=id, user_location=new_location)

    except WebSocketDisconnect:
        # await manager.disconnect(id=id)
        print(f"INFO: [WSDisconnect] Disconnect websocket - [ID: {id}]", flush=True)
        return
    except (ValueError, TypeError) as e: 
        print(f"ERROR: An error occurred: {e}")
        await manager.send_json_message(id, "Invalid location data format")
    except Exception as e:
        print(f"Unexpected error occurred with device ID[{id}]: {e}", flush=True)
        return
        # await manager.disconnect(id=id)


async def check_fires():
    print(f"INFO: [CheckingFire] - {datetime.now()}", flush=True)
    db = SessionLocal()
    id = None
    try:
        # get all active fires  
        active_fires = db.query(FireModel).filter(FireModel.is_active == True).all()
        

        # loop over active connections
        for id, user_data in manager.active_connections.items():
            user_location = user_data["location"]

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
                        if fire_schema in user_cache:
                            continue
                        else:
                            fire_alerts.append(fire_schema)
            else:
                # TODO: Remove print message later
                print(f"INFO: [CheckingFire] There are no fires - {datetime.now()}", flush=True)
                await manager.send_json_message(id=id, message="There are no fires.")

            # send the fire alerts and store in cache
            if fire_alerts:
                # send the fire and store in cache
                await manager.send_json_of_fires(id=id, fires=fire_alerts)
                user_cache.update(fire_alerts)
                print(f"INFO: Sent {len(fire_alerts)} alerts to device [{id}]", flush=True)
                
       
    except Exception as e:
        print(f"ERROR: Error during Task [check_fire()] - Type {type(e).__name__}: {e}", flush=True)
    finally:
        db.close()