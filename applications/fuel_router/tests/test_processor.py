from unittest.mock import patch

import pytest
import pandas as pd

from applications.fuel_router.router_engine.processor import (
    RouteProcessorService,
    FuelStationRepository,
    RouteCacheService,
    RoutePlanningError,
)
from applications.fuel_router.router_engine.enums import (
    RouteRequest,
)


@pytest.mark.django_db
class TestFuelStationRepository:

    def test_singleton_pattern(self):

        repo1 = FuelStationRepository()
        repo2 = FuelStationRepository()
        assert repo1 is repo2

    def test_stations_hash(self):

        repo = FuelStationRepository()
        repo._stations_df = pd.DataFrame({"Lat": [40.0], "Lon": [-100.0]})

        hash1 = repo.get_stations_hash()
        assert hash1 != "no_stations"

        hash2 = repo.get_stations_hash()
        assert hash1 == hash2


@pytest.mark.django_db
class TestRouteCacheService:

    def test_cache_key_generation(self):

        start = {"lat": 40.0, "lon": -100.0}
        finish = {"lat": 41.0, "lon": -99.0}
        stations_hash = "abc123"

        key1 = RouteCacheService._generate_key(start, finish, stations_hash)
        key2 = RouteCacheService._generate_key(start, finish, stations_hash)

        assert key1 == key2
        assert key1.startswith(RouteCacheService.CACHE_PREFIX)


@pytest.mark.django_db
class TestRouteProcessorService:

    @pytest.fixture
    def processor(self):

        with patch.object(FuelStationRepository, "get_stations") as mock_get_stations:
            mock_df = pd.DataFrame(
                {
                    "Lat": [40.1, 40.5],
                    "Lon": [-100.1, -99.5],
                    "Retail Price": [3.50, 3.40],
                },
                index=["Station1", "Station2"],
            )
            mock_get_stations.return_value = mock_df

            processor = RouteProcessorService()
            yield processor

    @patch("applications.fuel_router.router_engine.processor.get_route")
    @patch("applications.fuel_router.router_engine.processor.extract_coords")
    @patch(
        "applications.fuel_router.router_engine.processor.project_stations_with_detours"
    )
    @patch("applications.fuel_router.router_engine.processor.cumulative_distances")
    @patch(
        "applications.fuel_router.router_engine.processor.optimize_fuel_stops_with_detours"
    )
    @patch("applications.fuel_router.router_engine.processor.generate_map_with_detours")
    def test_execute_success(
        self,
        mock_generate_map,
        mock_optimize,
        mock_cumulative,
        mock_project,
        mock_extract,
        mock_get_route,
        processor,
    ):

        mock_get_route.return_value = {"route": "data"}
        mock_extract.return_value = [(40.0, -100.0), (41.0, -99.0)]
        mock_cumulative.return_value = [0, 69]
        mock_project.return_value = [{"route_mile": 69, "price": 3.50}]
        mock_optimize.return_value = ([{"name": "Station1"}], 100.50)
        mock_generate_map.return_value = "/maps/route.html"

        request = RouteRequest(
            start={"lat": 40.0, "lon": -100.0},
            finish={"lat": 41.0, "lon": -99.0},
        )

        result = processor.execute(request)

        assert "distance" in result
        assert "stops" in result
        assert "total_fuel_cost" in result
        assert "map_url" in result
        assert result["total_fuel_cost"] == 100.50

    @patch("applications.fuel_router.router_engine.processor.RouteCacheService.get")
    def test_cache_hit(self, mock_cache_get, processor):

        cached_result = {
            "distance": 69,
            "stops": [],
            "total_fuel_cost": 100,
            "map_url": "/cached/map.html",
        }
        mock_cache_get.return_value = cached_result

        request = RouteRequest(
            start={"lat": 40.0, "lon": -100.0},
            finish={"lat": 41.0, "lon": -99.0},
        )

        result = processor.execute(request)

        assert result == cached_result
        mock_cache_get.assert_called_once()

    @patch("applications.fuel_router.router_engine.processor.get_route")
    def test_execute_failure(self, mock_get_route, processor):

        mock_get_route.side_effect = Exception("API Error")

        request = RouteRequest(
            start={"lat": 40.0, "lon": -100.0},
            finish={"lat": 41.0, "lon": -99.0},
        )

        with pytest.raises(RoutePlanningError):
            processor.execute(request)
