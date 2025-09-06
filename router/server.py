from fastapi import APIRouter, HTTPException, status, Depends
import httpx, json

from schema.fireschema import FireSchema
from db import get_db, FireModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

# define new router
server_api = APIRouter()

VALID_COUNTY = ["Santa Clara", "Santa Clara County", "County of Santa Clara", "SCC", "SCL"]


# get all fires in Santa Clara County 
@server_api.get("/fires", response_model=list[FireSchema])
async def get_fires(county: str, db: Session = Depends(get_db)) -> list[FireSchema]:
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
async def get_fire_data(fire_id: str, db: Session = Depends(get_db)) -> FireSchema:
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