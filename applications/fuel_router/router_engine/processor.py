import hashlib
import json
import logging
from typing import Dict, Any, Optional

import pandas as pd
from django.conf import settings
from django.core.cache import cache

from applications.fuel_router.router_engine.routing import (
    get_route,
    extract_coords,
)
from applications.fuel_router.router_engine.planner import (
    project_stations_with_detours,
)
from applications.fuel_router.router_engine.fuel_optimizer import (
    optimize_fuel_stops_with_detours,
)
from applications.fuel_router.router_engine.map_view import (
    generate_map_with_detours,
)
from applications.fuel_router.router_engine.enums import (
    Coordinate,
    RouteRequest,
)
from applications.fuel_router.router_engine.utils import cumulative_distances


logger = logging.getLogger(__name__)


class FuelStationRepository:

    _instance = None
    _stations_df = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_stations(self) -> pd.DataFrame:
        if self._stations_df is None:
            file_path = f"{settings.DATA_DIR}/fuel_stations_with_latlon.csv"
            try:
                self._stations_df = pd.read_csv(file_path)
            except FileNotFoundError:
                logger.error(f"Fuel stations CSV not found at {file_path}")
                raise
            except Exception as e:
                logger.error(f"Error loading fuel stations: {str(e)}")
                raise
        return self._stations_df.copy()

    def get_stations_hash(self) -> str:
        """Generate hash of station data for cache invalidation"""
        if self._stations_df is not None:
            return hashlib.md5(
                pd.util.hash_pandas_object(self._stations_df).values
            ).hexdigest()
        return "no_stations"


class RouteCacheService:
    """Service for caching route calculations"""

    CACHE_TIMEOUT = 60 * 60 * 60
    CACHE_PREFIX = "route"

    @classmethod
    def _generate_key(
        cls,
        start: Dict,
        finish: Dict,
        stations_hash: str,
    ) -> str:
        """Generate cache key from request parameters"""
        key_data = {
            "start": start,
            "finish": finish,
            "stations_hash": stations_hash,
            "version": "1",
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"{cls.CACHE_PREFIX}:{hashlib.md5(key_string.encode()).hexdigest()}"

    @classmethod
    def get(
        cls,
        start: Dict,
        finish: Dict,
        stations_hash: str,
    ) -> Optional[Dict]:
        """Get cached route data"""
        cache_key = cls._generate_key(start, finish, stations_hash)
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed: {str(e)}")
            return None

    @classmethod
    def set(
        cls,
        start: Dict,
        finish: Dict,
        stations_hash: str,
        data: Dict,
    ) -> bool:
        """Cache route data"""
        cache_key = cls._generate_key(start, finish, stations_hash)
        try:
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed: {str(e)}")
            return False


class RoutePlanningError(Exception):
    """Custom exception for route planning errors"""

    pass


class RouteProcessorService:
    """Single service to handle all route planning logic"""

    def __init__(self):
        self.station_repo = FuelStationRepository()
        self.cache = RouteCacheService()

    def execute(self, request: RouteRequest) -> Dict[str, Any]:

        try:
            stations_hash = self.station_repo.get_stations_hash()
            start_location = Coordinate(**request.start)
            finish_location = Coordinate(**request.finish)
            print(
                start_location.data,
                finish_location.data,
                stations_hash,
            )
            cached = self.cache.get(
                start_location.data,
                finish_location.data,
                stations_hash,
            )

            if cached:
                logger.info("Returning cached route")
                return cached

            route = get_route(start_location, finish_location)
            coords = extract_coords(route)
            stations = self.station_repo.get_stations()
            projected = project_stations_with_detours(coords, stations)

            total_distance = cumulative_distances(coords)[-1]
            stops, cost = optimize_fuel_stops_with_detours(
                total_distance,
                projected,
            )

            location_key = f"{start_location.lon}_{start_location.lat}_"
            location_key += f"{finish_location.lon}_{finish_location.lat}"
            map_url = generate_map_with_detours(coords, stops, location_key)

            result = {
                "distance": round(total_distance, 1),
                "stops": stops,
                "total_fuel_cost": round(cost, 2),
                "map_url": map_url,
            }

            self.cache.set(
                start_location.data,
                finish_location.data,
                stations_hash,
                result,
            )

            return result
        except Exception as e:
            logger.error(f"Route planning failed: {str(e)}")
            raise RoutePlanningError(f"Failed to plan route: {str(e)}")
