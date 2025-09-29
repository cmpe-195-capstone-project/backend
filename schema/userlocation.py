from pydantic import BaseModel

DEFAULT_RADIUS = 10

class UserLocation(BaseModel):
    longitude: float
    latitude: float 
    radius: float = DEFAULT_RADIUS