from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from shapely.geometry import shape, Point
from shapely.ops import nearest_points
import math
from typing import Sequence

from db import get_db, get_test_db, get_active_db, FireModel, SessionLocal, SessionLocalTest, EvacZoneModel
from schema.fireschema import FireSchema
from schema.userlocation import UserLocation
from utils.geo import get_coordinates
from utils.ws_manager import ConnectionManager
from config import settings
from utils.colors import Color
import json

ws = APIRouter()

manager = ConnectionManager()
cache: dict[str, set[str]] = {}

FALLBACK_SAFE_PLACES = [
    {
        "id": "SAFE_SJSU_STUDENT_UNION",
        "name": "SJSU Student Union",
        "lat": 37.3352,
        "lon": -121.8811,
    },
    {
        "id": "SAFE_MLK_LIBRARY",
        "name": "Dr. Martin Luther King Jr. Library",
        "lat": 37.3359,
        "lon": -121.8853,
    },
    {
        "id": "SAFE_EVGREEN_COMMUNITY_CENTER",
        "name": "Evergreen Community Center",
        "lat": 37.3324,
        "lon": -121.7922,
    },
    {
        "id": "SAFE_CAMBELL_COMMUNITY_CENTER",
        "name": "Campbell Community Center",
        "lat": 37.2872,
        "lon": -121.9445,
    },
    {
        "id": "SAFE_SANTA_CLARA_COMMUNITY_CENTER",
        "name": "Santa Clara Community Recreation Center",
        "lat": 37.3533,
        "lon": -121.9617,
    },
    {
        "id": "SAFE_MORGAN_HILL_COMMUNITY_CENTER",
        "name": "Morgan Hill Community & Cultural Center",
        "lat": 37.1305,
        "lon": -121.6544,
    },
    {
        "id": "SAFE_SUNNYVALE_COMMUNITY_CENTER",
        "name": "Sunnyvale Community Center",
        "lat": 37.3705,
        "lon": -122.0374,
    },
    {
        "id": "SAFE_MOUNTAIN_VIEW_COMMUNITY_CENTER",
        "name": "Mountain View Community Center",
        "lat": 37.3905,
        "lon": -122.0713,
    },
    {
        "id": "SAFE_PALO_ALTO_MITCHELL_PARK",
        "name": "Mitchell Park Community Center (Palo Alto)",
        "lat": 37.4263,
        "lon": -122.1087,
    },
    {
        "id": "SAFE_GILROY_SENIOR_CENTER",
        "name": "Gilroy Senior Center (Emergency Facility)",
        "lat": 37.0058,
        "lon": -121.5683,
    },
]

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



def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_nearest_fallback_place(
    user_lat: float,
    user_lon: float,
    active_fires: Sequence[FireModel] | None = None,
    fire_exclusion_km: float = 2.0,
):
    if not FALLBACK_SAFE_PLACES:
        return None, None, None

    best = None
    best_lat = None
    best_lon = None
    best_dist = None

    for place in FALLBACK_SAFE_PLACES:
        lat = place.get("lat")
        lon = place.get("lon")
        if lat is None or lon is None:
            continue

        # ignore fallback places that are too close to a fire (waht we have is approx 2km radius)
        if active_fires:
            too_close_to_fire = False
            for fire in active_fires:
                if not fire.is_active:
                    continue
                fire_dist_km = _haversine_km(lat, lon, fire.latitude, fire.longitude)
                if fire_dist_km <= fire_exclusion_km:
                    too_close_to_fire = True
                    break
            if too_close_to_fire:
                continue
        dist_km = _haversine_km(user_lat, user_lon, lat, lon)
        if best_dist is None or dist_km < best_dist:
            best_dist = dist_km
            best = place
            best_lat = lat
            best_lon = lon
    if best is None:
        return None, None, None
    return best, best_lat, best_lon



def get_nearest_exit_from_evac_zone(db: Session, user_lat: float, user_lon: float):
    user_point = Point(user_lon, user_lat)
    zones = db.query(EvacZoneModel).filter(EvacZoneModel.is_active == True).all()
    if not zones:
        return None, None, None

    best_zone = None
    best_exit_lat = None
    best_exit_lon = None
    best_dist = None

    for zone in zones:
        geom_json = zone.geometry_geojson
        if not geom_json:
            continue

        try:
            geom_dict = json.loads(geom_json)
            zone_geom = shape(geom_dict)   # use polygon
        except Exception:
            continue

        # find zones that contain the user loc
        if not zone_geom.is_valid or not zone_geom.contains(user_point):
            continue

        # nearest point on the boundary of this polygon to user
        boundary = zone_geom.boundary
        _, nearest_on_boundary = nearest_points(user_point, boundary)

        dist = user_point.distance(nearest_on_boundary)

        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_zone = zone
            best_exit_lon = float(nearest_on_boundary.x)
            best_exit_lat = float(nearest_on_boundary.y)

    if best_zone is None:
        return None, None, None

    return best_zone, best_exit_lat, best_exit_lon



async def check_fires():
    print(f"{Color.GREEN}[INFO] CheckFires: performing scheduled fire check at {datetime.now()}{Color.RESET}", flush=True)
    db_gen = get_active_db()
    db = next(db_gen)
    id = None
    try:
        active_fires = db.query(FireModel).filter(FireModel.is_active == True).all()
        print(f"[CheckFires] active_fires={len(active_fires)}", flush=True)
        print(f"[CheckFires] active_connections={len(manager.active_connections)}", flush=True)

        # loop over active connections
        for id, user_data in manager.active_connections.items():
            user_location = user_data["location"]
            print(f"{Color.GREEN}[INFO] CheckFires: Check for client (id={id}) (loc={user_location}) {datetime.now()}{Color.RESET}", flush=True)

            bounding_box = get_coordinates(
                latitude=user_location.latitude,
                longitude=user_location.longitude,
                radius=user_location.radius
            )

            #temp debug stuff
            print(f"[CheckFires] BBOX: "
            f"minLat={bounding_box.min_lat}, maxLat={bounding_box.max_lat}, "
            f"minLon={bounding_box.min_lon}, maxLon={bounding_box.max_lon}", flush=True)


            user_cache = cache.setdefault(id, set())
            fire_alerts: list[FireSchema] = []

            # loop over the active fires 
            if active_fires:   
                for fire in active_fires:
                    # check if there is a fire within the users bounding box
                    if (
                        bounding_box.min_lat <= fire.latitude <= bounding_box.max_lat
                        and bounding_box.min_lon <= fire.longitude <= bounding_box.max_lon
                    ):

                        # check if the fire is already in the cache, if not add it to alerts list 
                        fire_schema = FireSchema.model_validate(fire, from_attributes=True) 

                        if fire_schema in user_cache: # if cache hit, skip over it
                            continue
                        else:
                            print(f"{Color.BLUE}[FIRE W/IN BOUNDS] {fire_schema.name} is within bounds. Sending to client... {Color.RESET}", flush=True)
                            fire_alerts.append(fire_schema) # add fire alert to cache

            else: # There are NO active fires
                print(f"{Color.GREEN}[INFO] CheckFires: No active fire incidents available in DB (time={datetime.now()}){Color.RESET}", flush=True)

            if fire_alerts:
                print(f"[CheckFires] user {id} has {len(fire_alerts)} overlapping fires", flush=True)

                safe_name = None
                # get nearest exit from any evac zone the user is inside
                zone, safe_lat, safe_lon = get_nearest_exit_from_evac_zone(
                    db=db,
                    user_lat=user_location.latitude,
                    user_lon=user_location.longitude,
                )

                # user is not inside any evac zone fall back to nearest static safe place
                if safe_lat is None or safe_lon is None:
                    fallback_place, fb_lat, fb_lon = get_nearest_fallback_place(
                        user_lat=user_location.latitude,
                        user_lon=user_location.longitude,
                        active_fires=active_fires,
                    )
                    if fallback_place and fb_lat is not None and fb_lon is not None:
                        safe_lat = fb_lat
                        safe_lon = fb_lon
                        safe_name = fallback_place.get("name") or "Nearest safe location"

                payload = {
                    "type": "fire_alert",
                    "fires": [
                        FireSchema.model_validate(fire, from_attributes=True).model_dump(mode="json")
                        for fire in fire_alerts
                    ],
                }
                if safe_lat is not None and safe_lon is not None:
                    payload["safe_latitude"] = safe_lat
                    payload["safe_longitude"] = safe_lon
                    if safe_name:
                        payload["safe_name"] = safe_name
                    elif zone:
                        payload["safe_name"] = f"Nearest exit from evac zone: {zone.name or zone.id}"
                    else:
                        payload["safe_name"] = "Nearest safe location"
                else:
                    # google HQ fallback
                    payload["safe_latitude"] = 37.4220
                    payload["safe_longitude"] = -122.0841
                    payload["safe_name"] = "Google HQ (test fallback)"

                await manager.active_connections[id]["socket"].send_json(payload)
                user_cache.update(fire_alerts)
                print(
                    f"{Color.GREEN}[INFO] CheckFires: Delivered {len(fire_alerts)} fire alert(s) to device {id}{Color.RESET}",
                    flush=True
                )
    except Exception as e:
        print(f"{Color.RED}[ERROR] CheckFires: Error during Task [check_fire()] - Type {type(e).__name__}: {e}{Color.RESET}", flush=True)
    finally:
        db.close()