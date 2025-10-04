from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from router.server import server_api
from router.test_api import test
from router.websocket import ws, check_fires
from db import engine_test, Base

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(check_fires, 'interval', seconds=30)
    scheduler.start()
    yield

Base.metadata.create_all(bind=engine_test)

# load any .env variables
load_dotenv()

# app init
app = FastAPI(lifespan=lifespan)

# include routers
app.include_router(server_api, prefix="/server")
app.include_router(test, prefix="/test")
app.include_router(ws, prefix="/ws")