from typing import Optional
from abc import ABC, abstractmethod

from .enums import DetectionResult, GeographicBounds


class CoordinateFormatDetector(ABC):

    def __init__(self, bounds: Optional[GeographicBounds] = None):
        self.bounds = bounds

    @abstractmethod
    def detect(
        self,
        num1: float,
        num2: float,
    ) -> Optional[DetectionResult]:
        """Detect coordinate format"""
        pass

    def _check_absolute_ranges(self, num: float) -> dict:
        """Check if number could be latitude or longitude based on absolute ranges"""
        return {
            "could_be_lat": abs(num) <= 90,
            "could_be_lon": abs(num) <= 180,
            "is_likely_lon": 90
            < abs(num)
            <= 180,  # Between 90-180 can only be longitude
        }
