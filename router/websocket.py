from fastapi import WebSocket, APIRouter, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

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

def _centroid_from_geojson(geometry_json: str | None) -> tuple[float | None, float | None]:
    """
    Compute a simple centroid from a Polygon or MultiPolygon GeoJSON.
    Returns (lat, lon) or (None, None) if it fails.
    """
    if not geometry_json:
        return None, None

    try:
        geom = json.loads(geometry_json)
    except Exception:
        return None, None

    coords = []

    gtype = geom.get("type")
    if gtype == "Polygon":
        for ring in geom.get("coordinates", []):
            coords.extend(ring)
    elif gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []):
            for ring in poly:
                coords.extend(ring)
    else:
        return None, None

    if not coords:
        return None, None

    lon_sum = 0.0
    lat_sum = 0.0
    n = len(coords)
    for lon, lat in coords:
        lon_sum += lon
        lat_sum += lat

    return lat_sum / n, lon_sum / n

def get_nearest_fallback_place(user_lat: float, user_lon: float):
    """
    Pick the closest static fallback location from FALLBACK_SAFE_PLACES.
    Returns (place_dict, lat, lon) or (None, None, None) if none exist.
    """
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

        d_lat = lat - user_lat
        d_lon = lon - user_lon
        dist_sq = d_lat * d_lat + d_lon * d_lon

        if best_dist is None or dist_sq < best_dist:
            best_dist = dist_sq
            best = place
            best_lat = lat
            best_lon = lon

    return best, best_lat, best_lon

# this is to get the nearest evac for the evac route in notif
def get_nearest_evac_zone(db: Session, user_lat: float, user_lon: float):
    zones = db.query(EvacZoneModel).filter(EvacZoneModel.is_active == True).all()
    if not zones:
        return None, None, None  # zone, lat, lon

    best_zone = None
    best_lat = None
    best_lon = None
    best_dist = None

    for zone in zones:
        center_lat, center_lon = _centroid_from_geojson(zone.geometry_geojson)
        if center_lat is None or center_lon is None:
            continue

        d_lat = center_lat - user_lat
        d_lon = center_lon - user_lon
        dist_sq = d_lat * d_lat + d_lon * d_lon

        if best_dist is None or dist_sq < best_dist:
            best_dist = dist_sq
            best_zone = zone
            best_lat = center_lat
            best_lon = center_lon

    return best_zone, best_lat, best_lon


async def check_fires():
    print(f"{Color.GREEN}[INFO] CheckFires: performing scheduled fire check at {datetime.now()}{Color.RESET}", flush=True)
    db = SessionLocalTest() if settings.ENV == "test" else SessionLocal()
    try:
        active_fires = db.query(FireModel).filter(FireModel.is_active == True).all()
        print(f"[CheckFires] active_fires={len(active_fires)}", flush=True)
        print(f"[CheckFires] active_connections={len(manager.active_connections)}", flush=True)

        # loop over active connections
        for id, user_data in manager.active_connections.items():
            user_location = user_data["location"]
            print(f"[CheckFires] user {id} location={user_location}", flush=True)

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

            if active_fires:
                for fire in active_fires:
                    if (
                        bounding_box.min_lat <= fire.latitude <= bounding_box.max_lat
                        and bounding_box.min_lon <= fire.longitude <= bounding_box.max_lon
                    ):
                        user_cache = cache.setdefault(id, set())
                        if fire.id in user_cache:
                            continue

                        fire_alerts.append(fire)
                        user_cache.add(fire.id)
            else:
                print(f"[CheckFires] No active fires in DB", flush=True)

            if fire_alerts:
                print(f"[CheckFires] user {id} has {len(fire_alerts)} overlapping fires", flush=True)
                zone, safe_lat, safe_lon = get_nearest_evac_zone(
                    db=db,
                    user_lat=user_location.latitude,
                    user_lon=user_location.longitude,
                )

                safe_name = None

                # fall back to static list
                if not zone or safe_lat is None or safe_lon is None:
                    fallback_place, fb_lat, fb_lon = get_nearest_fallback_place(
                        user_lat=user_location.latitude,
                        user_lon=user_location.longitude,
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
                        payload["safe_name"] = zone.name or zone.id
                    else:
                        payload["safe_name"] = "Nearest safe location"
                else:
                    # Last-resort test fallback
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