from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from router.server import server_api
from router.test_api import test
from router.utils_api import utils_api
from router.websocket import ws, check_fires
from db import engine_test, Base

from fastapi.middleware.cors import CORSMiddleware
from os import getenv
from db import engine, engine_test, Base

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(check_fires, 'interval', seconds=30)
    scheduler.start()

    # make sure main DB tables exist
    Base.metadata.create_all(bind=engine)

    # optional: initialize test DB only when ENV=test
    if getenv("ENV") == "test":
        try:
            Base.metadata.create_all(bind=engine_test)
        except Exception as e:
            print("Test DB init skipped:", e)
    yield

Base.metadata.create_all(bind=engine_test)

# load any .env variables
load_dotenv()

# app init
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(server_api, prefix="/server", tags=["Server API"])
app.include_router(test, prefix="/test", tags=["Test API"])
app.include_router(ws, prefix="/ws", tags=["WebSocket"])
app.include_router(utils_api, prefix="/utils", tags=["Utils API"])