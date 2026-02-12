import requests

from applications.fuel_router.router_engine.enums import Coordinate

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def get_route(start: Coordinate, end: Coordinate):
    url = f"{OSRM_URL}/{start.lon},{start.lat};{end.lon},{end.lat}"
    r = requests.get(url, params={"overview": "full", "geometries": "geojson"})
    r.raise_for_status()
    return r.json()["routes"][0]


def extract_coords(route):
    return [(lat, lon) for lon, lat in route["geometry"]["coordinates"]]
