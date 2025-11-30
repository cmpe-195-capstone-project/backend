from fastapi import APIRouter, HTTPException, status, Query, Depends
import httpx, json

from schema.fireschema import FireSchema
from db import get_db, get_active_db, FireModel, EvacPlaceModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import and_, func
from config import settings

from datetime import datetime, date, timedelta
from faker import Faker
import random
fake = Faker()
from schema.resourceplaceschema import ResourcePlaceSchema


# define new router
server_api = APIRouter()

VALID_COUNTY = ["Santa Clara", "Santa Clara County", "County of Santa Clara", "SCC", "SCL"]


# get all fires in Santa Clara County 
@server_api.get("/fires", response_model=list[FireSchema])
async def get_fires(county: str, db: Session = Depends(get_active_db)) -> list[FireSchema]:
    if county.lower() not in map(str.lower, VALID_COUNTY):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid county in query")

    try:
        fires = db.query(FireModel).filter(FireModel.county == county).all()

        if not fires:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fires present.")
        return fires
        
    except OperationalError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to the database.")
    
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error.")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected database error occurred.")
    

# get info for a specific fire based on a fire's id
@server_api.get("/fire-data/{fire_id}", response_model=FireSchema)
async def get_fire_data(fire_id: str, db: Session = Depends(get_active_db)) -> FireSchema:
    if not fire_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fire id provided")
    
    try:
        fire_data = db.query(FireModel).filter(FireModel.id == fire_id).first()

        if not fire_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fire (ID: {fire_id}) does not exist")

        return fire_data
    except OperationalError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to the database.")
    
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error.")

    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected database error occurred.")
    
@server_api.get("/fires/box", response_model=list[FireSchema])
async def get_fires_in_box(
    minLat: float = Query(...),
    minLng: float = Query(...),
    maxLat: float = Query(...),
    maxLng: float = Query(...),
    county: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[FireSchema]:
    if minLat > maxLat:
        minLat, maxLat = maxLat, minLat
    if minLng > maxLng:
        minLng, maxLng = maxLng, minLng

    try:
        q = db.query(FireModel).filter(
            and_(
                FireModel.latitude  >= minLat,
                FireModel.latitude  <= maxLat,
                FireModel.longitude >= minLng,
                FireModel.longitude <= maxLng,
            )
        )
        if county:
            q = q.filter(func.lower(FireModel.county) == county.lower())

        return q.all() 
    except OperationalError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="DB unavailable")
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="DB integrity error")
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected DB error")

#testing endpoint
@server_api.get("/ping")
def ping():
    return {"ok": True}

@server_api.get("/resources", response_model=list[ResourcePlaceSchema])
async def list_resources(db: Session = Depends(get_db)):
    """
    List community resources (shelters, food, services) from evac_places table.
    These are for the Resources page, not used for redirect logic.
    """
    try:
        places = (
            db.query(EvacPlaceModel)
            .filter(EvacPlaceModel.is_active == True)
            .all()
        )
        return places
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the database.",
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected database error occurred.",
        )

from db import EvacZoneModel

@server_api.get("/evac-zones")
async def list_evac_zones(db: Session = Depends(get_db)):
    zones = db.query(EvacZoneModel).all()
    return [
        {"id": z.id, "name": z.name, "county": z.county, "status": z.status}
        for z in zones
    ]


@server_api.post("/seed-sjsu", response_model=FireSchema)
async def seed_sjsu(db: Session = Depends(get_db)):
    row = FireModel(
        id="TEST-SJSU-1",
        name="Test SJSU Fire",
        location="San José State University",
        county="Santa Clara",
        is_active=True,
        final=False,
        updated_datetime=datetime.utcnow(),
        start_datetime=datetime.utcnow(),
        extinguished_datetime=None,
        start_date=date.today(),
        acres_burned=12.3,
        percent_contained=10.0,
        latitude=37.3352,
        longitude=-121.8811,
        fire_type="Wildfire",
        control_statement="Seed for SJSU map test",
        url="https://example.com",
    )
    db.merge(row)  # upsert by primary key
    db.commit()
    return db.query(FireModel).get("TEST-SJSU-1")
