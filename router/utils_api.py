from fastapi import APIRouter
from config import settings


# define new router
utils_api = APIRouter()

@utils_api.post("/change-db")
async def change_db():
    if settings.ENV == 'test':
        settings.ENV = 'main'
    else:
        settings.ENV = 'test'
    return {"msg" : f"changed database to {settings.ENV} db"} 
