from typing import Optional

from .base import CoordinateFormatDetector
from .bounds import USABounds
from .enums import DetectionResult


class RangeBasedDetector(CoordinateFormatDetector):
    """This class is just Detector based on geographic ranges"""

    def detect(self, num1: float, num2: float) -> Optional[DetectionResult]:
        if not self.bounds:
            return None

        num1_range = self._check_absolute_ranges(num1)
        num2_range = self._check_absolute_ranges(num2)

        # Check if numbers are within bounds
        num1_in_bounds = self.bounds.contains(num1, num2)
        num2_in_bounds = self.bounds.contains(num2, num1)

        scenario1_confidence = 0
        scenario1_reasons = []

        if (
            self.bounds.longitude_min <= num1 <= self.bounds.longitude_max
            or num1_range["is_likely_lon"]
        ):
            scenario1_confidence += 3
            scenario1_reasons.append("num1 matches longitude range")

        if (
            self.bounds.latitude_min <= num2 <= self.bounds.latitude_max
            or num2_range["could_be_lat"]
        ):
            scenario1_confidence += 3
            scenario1_reasons.append("num2 matches latitude range")

        if num1_in_bounds:
            scenario1_confidence += 2
            scenario1_reasons.append("coordinates are within bounds as lon,lat")

        scenario2_confidence = 0
        scenario2_reasons = []

        if (
            self.bounds.latitude_min <= num1 <= self.bounds.latitude_max
            or num1_range["could_be_lat"]
        ):
            scenario2_confidence += 3
            scenario2_reasons.append("num1 matches latitude range")

        if (
            self.bounds.longitude_min <= num2 <= self.bounds.longitude_max
            or num2_range["is_likely_lon"]
        ):
            scenario2_confidence += 3
            scenario2_reasons.append("num2 matches longitude range")

        if num2_in_bounds:
            scenario2_confidence += 2
            scenario2_reasons.append("coordinates are within bounds as lat,lon")

        if scenario1_confidence == 0 and scenario2_confidence == 0:
            return None

        if scenario1_confidence > scenario2_confidence:
            return DetectionResult(
                format_type="lonlat",
                confidence=min(scenario1_confidence, 10),
                reason="; ".join(scenario1_reasons),
            )
        elif scenario2_confidence > scenario1_confidence:
            return DetectionResult(
                format_type="latlon",
                confidence=min(scenario2_confidence, 10),
                reason="; ".join(scenario2_reasons),
            )
        else:
            # Tie - choose based on absolute ranges
            if num1_range["is_likely_lon"] and not num2_range["is_likely_lon"]:
                return DetectionResult(
                    format_type="lonlat",
                    confidence=5,
                    reason="num1 can only be longitude (abs > 90)",
                )
            elif num2_range["is_likely_lon"] and not num1_range["is_likely_lon"]:
                return DetectionResult(
                    format_type="latlon",
                    confidence=5,
                    reason="num2 can only be longitude (abs > 90)",
                )

        return None


class USACoordinateDetector(RangeBasedDetector):
    """USA-specific coordinate format detector using dataclass bounds"""

    def __init__(self):
        super().__init__(bounds=USABounds())
