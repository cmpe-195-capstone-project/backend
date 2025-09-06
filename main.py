from fastapi import FastAPI
from dotenv import load_dotenv

from router.server import server_api

# load any .env variables
load_dotenv()

# app init
app = FastAPI()

# include routers
app.include_router(server_api, prefix="/server")