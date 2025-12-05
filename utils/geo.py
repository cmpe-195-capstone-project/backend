from geopy.point import Point
from geopy.distance import geodesic, Distance

class MinCoordinates:
    def __init__(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float):
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
    
def get_coordinates(latitude: float, longitude: float, radius: float) -> MinCoordinates:
    # create the center point
    center_pt = Point(latitude, longitude)
    
    # distance object
    distance = geodesic(meters=radius)
    
    # calculate the four points from the center along N, E, S, W (0=N, 90=E, 180=S, 270=W).
    north = distance.destination(point=center_pt, bearing=0)
    east = distance.destination(point=center_pt, bearing=90)
    south = distance.destination(point=center_pt, bearing=180)
    west = distance.destination(point=center_pt, bearing=270)

    min_lat = south.latitude
    max_lat = north.latitude
    min_lon = west.longitude
    max_lon = east.longitude

    return MinCoordinates(min_lat, max_lat, min_lon, max_lon)