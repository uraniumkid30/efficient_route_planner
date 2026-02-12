from typing import Dict, Tuple
from abc import ABC, abstractmethod

from .enums import GeographicBounds, ValidationResult
from .bounds import USABounds


class BoundsValidator(ABC):

    def __init__(self, bounds: GeographicBounds):
        self.bounds = bounds

    @abstractmethod
    def validate(self, lat: float, lon: float) -> ValidationResult:
        """Validate coordinates are within bounds"""
        pass

    def get_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Get the geographic bounds"""
        return {
            "latitude": self.bounds.get_latitude_bounds(),
            "longitude": self.bounds.get_longitude_bounds(),
        }


class StrictBoundsValidator(BoundsValidator):
    """Strict bounds validator that raises exceptions"""

    def validate(self, lat: float, lon: float) -> ValidationResult:
        if not self.bounds.contains(lat, lon):
            raise ValueError(
                f"Coordinates ({lat}, {lon}) are outside {self.bounds.name} bounds. "
                f"Latitude must be between {self.bounds.latitude_min} and {self.bounds.latitude_max}, "
                f"Longitude between {self.bounds.longitude_min} and {self.bounds.longitude_max}"
            )
        return ValidationResult(
            is_valid=True,
            message=f"Coordinates are within {self.bounds.name} bounds",
            bounds=self.bounds,
        )


class LenientBoundsValidator(BoundsValidator):

    def validate(self, lat: float, lon: float) -> ValidationResult:
        if self.bounds.contains(lat, lon):
            return ValidationResult(
                is_valid=True,
                message=f"Coordinates are within {self.bounds.name} bounds",
                bounds=self.bounds,
            )
        else:
            return ValidationResult(
                is_valid=False,
                message=(
                    f"Coordinates ({lat}, {lon}) are outside {self.bounds.name} bounds. "
                    f"Expected latitude: {self.bounds.latitude_min} to {self.bounds.latitude_max}, "
                    f"longitude: {self.bounds.longitude_min} to {self.bounds.longitude_max}"
                ),
                bounds=self.bounds,
            )


class USAStrictValidator(StrictBoundsValidator):

    def __init__(self):
        super().__init__(bounds=USABounds())


class USALenientValidator(LenientBoundsValidator):
    def __init__(self):
        super().__init__(bounds=USABounds())
