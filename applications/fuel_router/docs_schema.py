from drf_spectacular.utils import OpenApiExample

FUEL_STOP_DOCS = {
    "examples": [
        OpenApiExample(
            "Fuel Stop Example",
            value={
                "route_mile": 150.5,
                "price": 3.45,
                "name": "TA - Petro #123",
                "Lat": 40.7580,
                "Lon": -73.9855,
                "detour_miles": 0.5,
                "distance_to_route": 0.3,
                "on_route": True,
                "gallons": 45.2,
                "cost": 155.94,
                "buy_reason": "Optimal price before mountain region",
            },
        )
    ]
}
ROUTE_RESPONSE_DOCS = {
    "examples": [
        OpenApiExample(
            "Successful Route Response",
            summary="Example of a complete route response",
            description="Full response with fuel stops and summary",
            value={
                "start_location": "40.7128,-74.0060",
                "finish_location": "34.0522,-118.2437",
                "distance": 2794.3,
                "stops": [
                    {
                        "route_mile": 450.2,
                        "price": 3.29,
                        "name": "Pilot #456",
                        "Lat": 36.1627,
                        "Lon": -86.7816,
                        "detour_miles": 1.2,
                        "distance_to_route": 0.8,
                        "on_route": False,
                        "gallons": 120.5,
                        "cost": 396.45,
                        "buy_reason": "Best price in region",
                    }
                ],
                "total_fuel_cost": 396.45,
                "distance_unit": "miles",
                "map_url": "https://maps.example.com/route/abc123",
                "summary": {
                    "total_distance": "2794.3 miles",
                    "total_stops": 1,
                    "total_cost": "$396.45",
                    "average_price_per_gallon": "$3.290",
                    "total_gallons": "120.5",
                    "average_detour": "1.2 miles",
                },
            },
        )
    ]
}

ROUTE_REQUEST_DOCS = {
    "examples": [
        OpenApiExample(
            "Valid Request",
            summary="Example of a valid route request",
            description="Request with auto-detected coordinate format",
            value={
                "start": "40.7128,-74.0060",
                "finish": "34.0522,-118.2437",
                "format": "auto",
                "region": "usa",
                "validation_mode": "strict",
            },
            request_only=True,
        ),
        OpenApiExample(
            "LonLat Format",
            summary="Coordinates in lon,lat format",
            value={
                "start": "-74.0060,40.7128",
                "finish": "-118.2437,34.0522",
                "format": "lonlat",
                "region": "usa",
            },
            request_only=True,
        ),
    ],
}
