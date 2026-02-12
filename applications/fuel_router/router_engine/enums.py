from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float
    data: Optional[str]

    def __init__(self, lat: float, lon: float, **kwargs):
        object.__setattr__(self, "lat", lat)
        object.__setattr__(self, "lon", lon)
        object.__setattr__(self, "data", f"{lat},{lon}")


@dataclass
class RouteRequest:
    start: Dict[str, float]
    finish: Dict[str, float]
