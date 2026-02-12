from typing import Dict, Any

from rest_framework import serializers
from drf_spectacular.utils import (
    extend_schema_serializer,
)
from applications.coordinates.exceptions import InvalidCoordinateFormat
from applications.coordinates.factory import CoordinateParserFactory
from applications.fuel_router.docs_schema import (
    FUEL_STOP_DOCS,
    ROUTE_REQUEST_DOCS,
    ROUTE_RESPONSE_DOCS,
)


@extend_schema_serializer(**ROUTE_REQUEST_DOCS)
class RouteRequestSerializer(serializers.Serializer):

    start = serializers.CharField(
        help_text="Start coordinate in various formats (e.g., '40.7128,-74.0060', '-74.0060 40.7128')"
    )
    finish = serializers.CharField(help_text="Finish coordinate in various formats")
    format = serializers.ChoiceField(
        choices=["auto", "lonlat", "latlon"],
        default="auto",
        required=False,
        help_text="Coordinate format: 'auto' (detect), 'lonlat', or 'latlon'",
    )
    region = serializers.CharField(
        default="usa",
        required=False,
        help_text="Region/country for coordinate validation (e.g., 'usa', 'europe', 'canada')",
    )
    validation_mode = serializers.ChoiceField(
        choices=["strict", "lenient", "none"],
        default="strict",
        required=False,
        help_text="Validation strictness: 'strict' (raises errors), 'lenient' (warnings), 'none'",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = None
        self._cached_regions = None

    def to_internal_value(self, data):
        if "region" not in data:
            data["region"] = "usa"
        if "validation_mode" not in data:
            data["validation_mode"] = "strict"
        if "format" not in data:
            data["format"] = "auto"

        return super().to_internal_value(data)

    def validate_region(self, value):
        available_regions = self.get_available_regions()

        if value.lower() not in available_regions:
            raise serializers.ValidationError(
                f"Region '{value}' is not supported. Available regions: {', '.join(available_regions.keys())}"
            )

        return value.lower()

    def get_available_regions(self) -> Dict[str, Any]:
        if self._cached_regions is None:
            self._cached_regions = CoordinateParserFactory.get_available_regions()
        return self._cached_regions

    def create_parser(self, region: str, validation_mode: str) -> Any:
        try:
            return CoordinateParserFactory.create_parser(
                region=region, validation_mode=validation_mode
            )
        except Exception as e:

            try:
                fallback_parser = CoordinateParserFactory.create_parser("usa")
                if self.context.get("request"):

                    pass
                return fallback_parser
            except Exception:
                raise serializers.ValidationError(
                    f"Failed to create coordinate parser: {str(e)}"
                )

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        region = data.get("region", "usa")
        validation_mode = data.get("validation_mode", "strict")
        format_type = data.get("format", "auto")

        self.parser = self.create_parser(region, validation_mode)
        start_coords = None
        finish_coords = None

        try:

            start_coords = self.parser.parse(
                coord_string=data["start"], format_type=format_type, field_name="start"
            )

            finish_coords = self.parser.parse(
                coord_string=data["finish"],
                format_type=format_type,
                field_name="finish",
            )

        except ValueError as e:
            raise serializers.ValidationError(str(e))
        except InvalidCoordinateFormat as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Failed to parse coordinates: {str(e)}")

        data["parsed_coordinates"] = {
            "start": start_coords.to_dict(),
            "finish": finish_coords.to_dict(),
            "region": region,
            "validation_mode": validation_mode,
            "bounds": self.parser.bounds.to_dict() if self.parser.bounds else None,
        }

        data["coordinate_tuples"] = {
            "start": start_coords.as_tuple(),
            "finish": finish_coords.as_tuple(),
            "start_reversed": start_coords.as_reversed_tuple(),
            "finish_reversed": finish_coords.as_reversed_tuple(),
        }

        return data


@extend_schema_serializer(**FUEL_STOP_DOCS)
class FuelStopSerializer(serializers.Serializer):
    route_mile = serializers.FloatField(help_text="Mile marker on route")
    price = serializers.FloatField(help_text="Price per gallon in USD")
    name = serializers.CharField(help_text="Station identifier/number")
    Lat = serializers.FloatField(help_text="Latitude coordinate")
    Lon = serializers.FloatField(help_text="Longitude coordinate")
    detour_miles = serializers.FloatField(help_text="Detour distance in miles")
    distance_to_route = serializers.FloatField(help_text="Distance from route in miles")
    on_route = serializers.BooleanField(
        help_text="Whether station is directly on route"
    )
    gallons = serializers.FloatField(help_text="Gallons purchased")
    cost = serializers.FloatField(help_text="Cost in USD")
    buy_reason = serializers.CharField(help_text="Reason for buying at this station")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value

    def validate_gallons(self, value):
        if value <= 0:
            raise serializers.ValidationError("Gallons must be positive")
        return value


@extend_schema_serializer(**ROUTE_RESPONSE_DOCS)
class RouteResponseSerializer(serializers.Serializer):
    start_location = serializers.CharField(help_text="Starting location")
    finish_location = serializers.CharField(help_text="Ending location")
    distance = serializers.FloatField(help_text="Total trip distance")
    stops = FuelStopSerializer(many=True, help_text="List of fuel stops")
    total_fuel_cost = serializers.FloatField(help_text="Total fuel cost for trip")
    distance_unit = serializers.CharField(
        default="miles", help_text="Unit of distance measurement"
    )
    map_url = serializers.CharField(default="", help_text="Url of map")

    number_of_stops = serializers.SerializerMethodField()
    average_price = serializers.SerializerMethodField()
    total_gallons = serializers.SerializerMethodField()
    average_detour = serializers.SerializerMethodField()

    def get_number_of_stops(self, obj):
        return len(obj.get("stops", []))

    def get_total_gallons(self, obj):
        return sum(stop.get("gallons", 0) for stop in obj.get("stops", []))

    def get_average_price(self, obj):
        stops = obj.get("stops", [])
        if not stops:
            return 0
        total_cost = sum(stop.get("cost", 0) for stop in stops)
        total_gallons = sum(stop.get("gallons", 0) for stop in stops)
        return round(total_cost / total_gallons, 3) if total_gallons > 0 else 0

    def get_average_detour(self, obj):
        stops = obj.get("stops", [])
        if not stops:
            return 0
        return round(sum(stop.get("detour_miles", 0) for stop in stops) / len(stops), 2)

    def validate_distance(self, value):
        if value <= 0:
            raise serializers.ValidationError("Distance must be positive")
        return value

    def validate_total_fuel_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Total fuel cost cannot be negative")
        return round(value, 2)

    def validate(self, data):
        stops = data.get("stops", [])
        total_cost_from_stops = sum(stop.get("cost", 0) for stop in stops)
        declared_total = data.get("total_fuel_cost", 0)

        if abs(total_cost_from_stops - declared_total) > 0.01:
            raise serializers.ValidationError(
                f"Total fuel cost ({declared_total}) doesn't match sum of stop costs ({total_cost_from_stops})"
            )

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["distance"] = round(data["distance"], 1)
        data["total_fuel_cost"] = round(data["total_fuel_cost"], 2)

        data["summary"] = {
            "total_distance": f"{data['distance']} {data['distance_unit']}",
            "total_stops": data["number_of_stops"],
            "total_cost": f"${data['total_fuel_cost']:,.2f}",
            "average_price_per_gallon": f"${data['average_price']:.3f}",
            "total_gallons": f"{data['total_gallons']:.1f}",
            "average_detour": f"{data['average_detour']} {data['distance_unit']}",
        }

        return data
