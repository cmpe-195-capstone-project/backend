from fastapi import APIRouter, Depends, HTTPException, status
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

@test.post("/fire", response_model=FireSchema)
async def post_fire(db: Session = Depends(get_test_db)) -> FireSchema:
    start_time_ = fake.date_time_this_year()
    final_ = fake.boolean()
    ext_time = None
     
    if final_:
        ext_time = start_time_ + timedelta(days=random.randint(1, 30))
    

    new_fire = FireSchema(
        id=fake.uuid4(),
        name=f"{fake.word()} Fire",
        final=final_,
        updated_datetime=datetime.now(),
        start_datetime=start_time_,
        extinguished_datetime=ext_time, 
        start_date=start_time_.date(),
        county="Santa Clara",
        location=fake.street_address(),
        acres_burned=round(random.uniform(10.5, 50000.0), 2),
        percent_contained=100 if final_ else round(random.uniform(0.0, 99.0), 1),
        control_statement=fake.sentence(nb_words=7),
        latitude=round(random.uniform(36.97, 37.47), 6),
        longitude=round(random.uniform(-122.17, -121.25), 6),
        fire_type=random.choice(['Wildfire', 'Structure', 'Vehicle']),
        is_active=not final_,
        url="https://www.fire.ca.gov/",
        inserted_at=datetime.now()
    )

    db_record = FireModel(**new_fire.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return db_record

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