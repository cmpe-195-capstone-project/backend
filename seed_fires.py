from datetime import datetime
from db import FireModel, SessionLocal, Base, engine
from datetime import datetime, timezone

Base.metadata.create_all(bind=engine)
now_utc = lambda: datetime.now(timezone.utc)

dummy_fires = [
    {
        "id": "D1",
        "name": "Test Fire A",
        "location": "Shoreline Park",
        "county": "Santa Clara",
        "is_active": True,
        "final": False,
        "updated_datetime": now_utc(),
        "start_datetime": now_utc(),
        "acres_burned": 120.5,
        "percent_contained": 35.0,
        "latitude": 37.423,
        "longitude": -122.084,
        "fire_type": "Wildfire",
    },
    {
        "id": "D2",
        "name": "Test Fire B",
        "location": "Googleplex",
        "county": "Santa Clara",
        "is_active": True,
        "final": False,
        "updated_datetime": now_utc(),
        "start_datetime": now_utc(),
        "acres_burned": 45.0,
        "percent_contained": 80.0,
        "latitude": 37.422,
        "longitude": -122.086,
        "fire_type": "Brush Fire",
    },
    {
        "id": "D3",
        "name": "Test Fire C",
        "location": "Downtown Mountain View",
        "county": "Santa Clara",
        "is_active": False,
        "final": True,
        "updated_datetime": now_utc(),
        "start_datetime": now_utc(),
        "acres_burned": 10.0,
        "percent_contained": 100.0,
        "latitude": 37.389,
        "longitude": -122.083,
        "fire_type": "Structure Fire",
    },
    {
        "id": "TEST-SJSU-1",
        "name": "Test SJSU Fire",
        "location": "San José State University",
        "county": "Santa Clara",
        "is_active": True,
        "final": False,
        "updated_datetime": now_utc(),
        "start_datetime": now_utc(),
        "acres_burned": 12.3,
        "percent_contained": 10.0,
        "latitude": 37.3352,
        "longitude": -121.8811,
        "fire_type": "Wildfire",
    },
]

def seed():
    db = SessionLocal()
    try:
        for fire in dummy_fires:
            exists = db.query(FireModel).filter(FireModel.id == fire["id"]).first()
            if not exists:
                db.add(FireModel(**fire))
        db.commit()
        print("Dummy fire data inserted.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
