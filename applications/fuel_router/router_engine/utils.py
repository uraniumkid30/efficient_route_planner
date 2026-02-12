import math
import numpy as np
from typing import List, Tuple

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1, lon1, lat2, lon2):
    phi1, phi2 = map(math.radians, [lat1, lat2])
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return EARTH_RADIUS_MILES * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def cumulative_distances(coords: List[Tuple[float, float]]) -> np.ndarray:
    dists = [0.0]
    for i in range(1, len(coords)):
        dists.append(dists[-1] + haversine_miles(*coords[i - 1], *coords[i]))
    return np.array(dists)
