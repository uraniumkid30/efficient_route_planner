import pytest
import numpy as np

from applications.fuel_router.router_engine.fuel_optimizer import (
    optimize_fuel_stops_with_detours,
    MAX_RANGE,
    MPG,
)


class TestFuelOptimizer:

    @pytest.fixture
    def simple_route_stations(self):

        return [
            {
                "route_mile": 200,
                "price": 3.50,
                "name": "Station A",
                "detour_miles": 0,
                "on_route": True,
                "Lat": 40.0,
                "Lon": -100.0,
            },
            {
                "route_mile": 400,
                "price": 3.40,
                "name": "Station B",
                "detour_miles": 5,
                "on_route": False,
                "Lat": 40.5,
                "Lon": -99.5,
            },
            {
                "route_mile": 600,
                "price": 3.60,
                "name": "Station C",
                "detour_miles": 0,
                "on_route": True,
                "Lat": 41.0,
                "Lon": -99.0,
            },
            {
                "route_mile": 800,
                "price": 3.30,
                "name": "Station D",
                "detour_miles": 3,
                "on_route": False,
                "Lat": 41.5,
                "Lon": -98.5,
            },
        ]

    def test_basic_optimization(self, simple_route_stations):

        total_distance = 1000
        stops, cost = optimize_fuel_stops_with_detours(
            total_distance, simple_route_stations
        )

        assert len(stops) > 0
        assert cost > 0
        assert all("gallons" in stop for stop in stops)
        assert all("cost" in stop for stop in stops)

    def test_fill_tank_no_cheaper_ahead(self):

        stations = [
            {
                "route_mile": 200,
                "price": 3.50,
                "name": "Only Station",
                "detour_miles": 0,
                "on_route": True,
                "Lat": 40.0,
                "Lon": -100.0,
            },
            {
                "route_mile": 1000,
                "price": 0,
                "name": "DESTINATION",
                "detour_miles": 0,
                "on_route": True,
            },
        ]

        total_distance = 1000
        with pytest.raises(
            RuntimeError, match="Out of fuel before reaching DESTINATION"
        ):
            stops, cost = optimize_fuel_stops_with_detours(total_distance, stations)

            stop = stops[0]
            expected_gallons = (MAX_RANGE - (200 - 0)) / MPG
            assert np.isclose(stop["gallons"], expected_gallons, rtol=0.01)

    def test_detour_fuel_consumption(self):

        stations = [
            {
                "route_mile": 250,
                "price": 3.50,
                "name": "With Detour",
                "detour_miles": 10,
                "on_route": False,
                "Lat": 40.0,
                "Lon": -100.0,
            },
            {
                "route_mile": 500,
                "price": 0,
                "name": "DESTINATION",
                "detour_miles": 0,
                "on_route": True,
            },
        ]

        total_distance = 500
        stops, cost = optimize_fuel_stops_with_detours(total_distance, stations)

        assert len(stops) == 1

        assert stops[0]["detour_miles"] == 0

    def test_multiple_stations_optimization(self):

        stations = [
            {
                "route_mile": 150,
                "price": 3.60,
                "name": "A",
                "detour_miles": 0,
                "on_route": True,
            },
            {
                "route_mile": 300,
                "price": 3.40,
                "name": "B",
                "detour_miles": 2,
                "on_route": False,
            },
            {
                "route_mile": 450,
                "price": 3.55,
                "name": "C",
                "detour_miles": 0,
                "on_route": True,
            },
            {
                "route_mile": 600,
                "price": 3.30,
                "name": "D",
                "detour_miles": 5,
                "on_route": False,
            },
            {
                "route_mile": 750,
                "price": 3.45,
                "name": "E",
                "detour_miles": 0,
                "on_route": True,
            },
            {
                "route_mile": 1000,
                "price": 0,
                "name": "DESTINATION",
                "detour_miles": 0,
                "on_route": True,
            },
        ]

        total_distance = 1000
        stops, cost = optimize_fuel_stops_with_detours(total_distance, stations)

        stop_names = [s["name"] for s in stops]
        assert "B" in stop_names or "D" in stop_names
        assert cost > 0
