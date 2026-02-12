from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers

from applications.fuel_router.router_engine.enums import RouteRequest
from applications.fuel_router.router_engine.processor import (
    RouteProcessorService,
)
from applications.fuel_router.serializers import (
    RouteRequestSerializer,
    RouteResponseSerializer,
)


@extend_schema_view(
    post=extend_schema(
        summary="Plan optimal fuel-efficient route",
        description="""
        Calculates an optimal route between two coordinates and recommends 
        fuel stops to minimize total fuel cost.
        
        The service considers:
        * Current fuel prices at stations along the route
        * Detour distances required to reach stations
        * Vehicle fuel efficiency and tank capacity
        * Geographic region for coordinate validation
        
        Returns a complete route plan with optimized fuel stops and 
        an interactive map visualization.
        """,
        request=RouteRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=RouteResponseSerializer,
                description="Route successfully calculated",
                examples=[
                    OpenApiExample(
                        "Successful Response",
                        value={
                            "start_location": "40.7128,-74.0060",
                            "finish_location": "34.0522,-118.2437",
                            "distance": 2794.3,
                            "total_fuel_cost": 845.67,
                            "stops": [],
                            "map_url": "https://example.com/map/abc123",
                            "summary": {}
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid request parameters",
                response=inline_serializer(
                    'ErrorResponse',
                    fields={
                        'error': serializers.CharField(),
                        'detail': serializers.CharField(required=False),
                        'field_errors': serializers.DictField(
                            child=serializers.ListField(
                                child=serializers.CharField()
                            ),
                            required=False
                        )
                    }
                )
            ),
            500: OpenApiResponse(description="Internal server error")
        },
        tags=["Route Planning"],
        operation_id="plan_route",
    )
)
class RoutePlannerView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = RouteProcessorService()

    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = self.service.execute(
                RouteRequest(
                    start=serializer.validated_data["parsed_coordinates"]["start"],
                    finish=serializer.validated_data["parsed_coordinates"]["finish"],
                )
            )
            response_data = {
                "start_location": request.data["start"],
                "finish_location": request.data["finish"],
                **result,
            }
            response_serializer = RouteResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data)

        except Exception as e:
            return Response(
                {"error": "Failed to plan route", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
