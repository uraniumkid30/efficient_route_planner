from unittest.mock import patch

import pytest
import numpy as np
import pandas as pd

from applications.fuel_router.router_engine.planner import (
    project_stations_with_detours,
    latlon_to_xyz,
)


class TestLatLonToXYZ:

    def test_conversion_basic(self):

        x, y, z = latlon_to_xyz(0, 0)[0]
        assert np.isclose(x, 1.0)
        assert np.isclose(y, 0.0)
        assert np.isclose(z, 0.0)

        x, y, z = latlon_to_xyz(90, 0)[0]
        assert np.isclose(x, 0.0)
        assert np.isclose(y, 0.0)
        assert np.isclose(z, 1.0)

        x, y, z = latlon_to_xyz(-90, 0)[0]
        assert np.isclose(x, 0.0)
        assert np.isclose(y, 0.0)
        assert np.isclose(z, -1.0)

    def test_conversion_vectorized(self):

        lats = [0, 90, -90]
        lons = [0, 0, 0]
        result = latlon_to_xyz(lats, lons)

        assert result.shape == (3, 3)
        assert np.all(np.isclose(np.linalg.norm(result, axis=1), 1.0))


class TestProjectStations:

    @pytest.fixture
    def simple_route(self):

        return [(40.0, -100.0), (41.0, -99.0), (42.0, -98.0)]

    @pytest.fixture
    def sample_stations(self):

        return pd.DataFrame(
            {
                "Lat": [40.1, 40.5, 41.5],
                "Lon": [-100.1, -99.5, -98.5],
                "Retail Price": [3.50, 3.40, 3.30],
            },
            index=["Station A", "Station B", "Station C"],
        )

    def test_empty_stations(self, simple_route):

        empty_df = pd.DataFrame(columns=["Lat", "Lon", "Retail Price"])
        result = project_stations_with_detours(simple_route, empty_df)
        assert result == []

    def test_invalid_coordinates(self, simple_route):

        stations = pd.DataFrame(
            {
                "Lat": [40.1, "invalid", 41.5],
                "Lon": [-100.1, -99.5, "invalid"],
                "Retail Price": [3.50, 3.40, 3.30],
            }
        )
        result = project_stations_with_detours(simple_route, stations)
        assert len(result) == 0

    def test_detour_calculation(self, simple_route):

        on_route_station = pd.DataFrame(
            {
                "Lat": [40.0],
                "Lon": [-100.0],
                "Retail Price": [3.50],
            }
        )

        result = project_stations_with_detours(simple_route, on_route_station)
        assert len(result) == 1
        assert result[0]["detour_miles"] == 0
        assert result[0]["on_route"] is True

    def test_max_detour_filter(self, simple_route):

        far_station = pd.DataFrame(
            {
                "Lat": [40.5],
                "Lon": [-95.0],
                "Retail Price": [3.50],
            }
        )

        with patch(
            "applications.fuel_router.router_engine.planner.MAX_DETOUR_MILES", 1
        ):
            result = project_stations_with_detours(simple_route, far_station)
            assert len(result) == 0


class TestCumulativeDistances:

    def test_cumulative_distances(self):

        from applications.fuel_router.router_engine.utils import cumulative_distances

        coords = [(40.0, -100.0), (41.0, -100.0)]
        distances = cumulative_distances(coords)

        assert len(distances) == 2
        assert distances[0] == 0
        assert np.isclose(distances[1], 69.0, rtol=0.1)

    def test_haversine_miles(self):

        from applications.fuel_router.router_engine.utils import haversine_miles

        dist = haversine_miles(40.0, -100.0, 40.0, -100.0)
        assert dist == 0

        dist = haversine_miles(40.0, -100.0, 41.0, -100.0)
        assert np.isclose(dist, 69.0, rtol=0.1)
