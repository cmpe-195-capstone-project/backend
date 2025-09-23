from fastapi import FastAPI
from dotenv import load_dotenv

from router.server import server_api
from router.test_api import test
from router.websocket import ws
from db import engine_test, Base

Base.metadata.create_all(bind=engine_test)

# load any .env variables
load_dotenv()

# app init
app = FastAPI()

# include routers
app.include_router(server_api, prefix="/server")
app.include_router(test, prefix="/test")
app.include_router(ws, prefix="/ws")