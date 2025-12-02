from db import SessionLocal, EvacZoneModel, Base, engine
from datetime import datetime, timezone
import json

Base.metadata.create_all(bind=engine)
now_utc = lambda: datetime.now(timezone.utc)

evac_zones = [
    {
        "id": "EVAC_MV_1",
        "name": "Mountain View Evacuation Order",
        "county": "Santa Clara",
        "status": "ORDER",
        "notes": "Test evac zone covering Shoreline / Googleplex area.",
        "geometry_geojson": json.dumps({
            "type": "Polygon",
            "coordinates": [
                [
                    [-122.090, 37.430],
                    [-122.070, 37.430],
                    [-122.070, 37.410],
                    [-122.090, 37.410],
                    [-122.090, 37.430]
                ]
            ]
        }),
        "is_active": True,
        "updated_at": now_utc(),
    },
    {
        "id": "EVAC_SJSU_1",
        "name": "SJSU Evacuation Warning",
        "county": "Santa Clara",
        "status": "WARNING",
        "notes": "Test zone around SJSU campus.",
        "geometry_geojson": json.dumps({
            "type": "Polygon",
            "coordinates": [
                [
                    [-121.890, 37.340],
                    [-121.870, 37.340],
                    [-121.870, 37.330],
                    [-121.890, 37.330],
                    [-121.890, 37.340]
                ]
            ]
        }),
        "is_active": True,
        "updated_at": now_utc(),
    },
]

def seed_evac_zones():
    db = SessionLocal()
    try:
        for z in evac_zones:
            exists = db.query(EvacZoneModel).filter(EvacZoneModel.id == z["id"]).first()
            if not exists:
                db.add(EvacZoneModel(**z))
        db.commit()
        print("Dummy evacuation zones inserted.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_evac_zones()
