from pydantic import BaseModel

DEFAULT_RADIUS = 10

class UserLocation(BaseModel):
    latitude: float 
    longitude: float
    radius: float = DEFAULT_RADIUS