from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass(frozen=True)
class GeographicBounds:
    latitude_min: float
    latitude_max: float
    longitude_min: float
    longitude_max: float
    name: str = "Unknown"
    code: Optional[str] = None

    def __post_init__(self):
        if not (-90 <= self.latitude_min <= self.latitude_max <= 90):
            raise ValueError(
                f"Invalid latitude bounds: {self.latitude_min} to {self.latitude_max}"
            )
        if not (-180 <= self.longitude_min <= self.longitude_max <= 180):
            raise ValueError(
                f"Invalid longitude bounds: {self.longitude_min} to {self.longitude_max}"
            )

    def contains(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within bounds"""
        return (
            self.latitude_min <= lat <= self.latitude_max
            and self.longitude_min <= lon <= self.longitude_max
        )

    def get_latitude_bounds(self) -> Tuple[float, float]:
        return (self.latitude_min, self.latitude_max)

    def get_longitude_bounds(self) -> Tuple[float, float]:
        return (self.longitude_min, self.longitude_max)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "latitude_min": self.latitude_min,
            "latitude_max": self.latitude_max,
            "longitude_min": self.longitude_min,
            "longitude_max": self.longitude_max,
        }


@dataclass(frozen=True)
class CustomBounds(GeographicBounds):

    def __init__(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        name: str = "Custom",
        code: Optional[str] = None,
    ):
        super().__init__(
            latitude_min=lat_min,
            latitude_max=lat_max,
            longitude_min=lon_min,
            longitude_max=lon_max,
            name=name,
            code=code,
        )


@dataclass
class ValidationResult:

    is_valid: bool
    message: str
    bounds: GeographicBounds

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "message": self.message,
            "bounds": self.bounds.to_dict(),
        }


@dataclass
class DetectionResult:
    format_type: str  # 'lonlat' or 'latlon'
    confidence: int  # 1-10 confidence score
    reason: str

    def is_confident(self, threshold: int = 5) -> bool:
        return self.confidence >= threshold
