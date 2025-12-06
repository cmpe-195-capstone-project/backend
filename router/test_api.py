from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import get_test_db, FireModel

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from schema.fireschema import FireSchema 
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

test = APIRouter()

# Min Latitude: 36.97
# Max Latitude: 37.47
# Min Longitude: -122.17
# Max Longitude: -121.25

FIRE_TYPES = [
    'Wildfire', 
    'Structural Fire', 
    'Vehicle Fire', 
    'Forest Fire', 
    'Brush Fire', 
    'Grass Fire',
    'Industrial Fire'
    ]

class FireCoordinatesRequest(BaseModel):
    longitude: float
    latitude: float



def generate_fire_schema(latitude: float, longitude: float) -> FireSchema:
    start_time = fake.date_time_this_year()
    extinguish_time = None

    return FireSchema(
        id=fake.uuid4(),
        name=f"{fake.last_name().capitalize()} Fire",
        final=False,
        updated_datetime=datetime.now(),
        start_datetime=start_time,
        extinguished_datetime=extinguish_time,
        start_date=start_time.date(),
        county="Santa Clara",
        location=fake.street_address(),
        acres_burned=round(random.uniform(10.5, 50000.0), 2),
        percent_contained=round(random.uniform(0.0, 99.0), 1),
        control_statement=fake.sentence(nb_words=7),
        latitude=latitude,
        longitude=longitude,
        fire_type=random.choice(FIRE_TYPES),
        is_active=True,
        url="https://www.fire.ca.gov/",
        inserted_at=datetime.now()
    )


@test.post("/fire-w-coords", response_model=FireSchema)
async def post_fire_w_coords(request: FireCoordinatesRequest, db: Session = Depends(get_test_db)) -> FireSchema:
    new_fire = generate_fire_schema(latitude=request.latitude, longitude=request.longitude)

    db_record = FireModel(**new_fire.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return db_record


@test.post("/fire", response_model=FireSchema)
async def post_fire(db: Session = Depends(get_test_db)) -> FireSchema:
    new_fire = generate_fire_schema(
        latitude=round(random.uniform(36.97, 37.47), 6),
        longitude=round(random.uniform(-122.17, -121.25), 6)
    )
    
    db_record = FireModel(**new_fire.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return db_record

@test.delete("/fire/{fire_id}")
async def delete_fire(fire_id: str, db: Session = Depends(get_test_db)):
    try:
        fire = db.query(FireModel).filter(FireModel.id == fire_id).first()

        if not fire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fire with id '{fire_id}' not found."
            )

        db.delete(fire)
        db.commit()

        return {"message": f"Fire '{fire_id}' successfully deleted."}

    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the database."
        )

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database integrity error."
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected database error occurred."
        )
        
@test.get("/fires", response_model=list[FireSchema])
async def get_all_fires(db: Session = Depends(get_test_db)) -> list[FireSchema]:
    try:
        fires = db.query(FireModel).all()

        if not fires:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fires present.")
        return fires
        
    except OperationalError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to the database.")
    
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error.")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected database error occurred.")
