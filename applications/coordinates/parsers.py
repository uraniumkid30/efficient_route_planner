import re
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any


from .enums import GeographicBounds
from .detectors import CoordinateFormatDetector, RangeBasedDetector
from .validators import BoundsValidator
from applications.coordinates.exceptions import (
    CoordinateOrderDetectionError,
    CoordinateParsingError,
    CoordinateRangeError,
    DMSFormatError,
    InvalidCoordinateFormat,
    InvalidLatitudeError,
    InvalidLongitudeError,
    InvalidNumberOfCoordinates,
    MissingFormatDetectorError,
    NWSEFormatError,
)


@dataclass
class ParsedCoordinates:
    longitude: float
    latitude: float
    detected_format: str
    original_string: str
    validation_result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "lon": self.longitude,
            "lat": self.latitude,
            "format": self.detected_format,
            "original": self.original_string,
        }
        if self.validation_result:
            result["validation"] = self.validation_result.to_dict()
        return result

    def as_tuple(self) -> Tuple[float, float]:
        return (self.longitude, self.latitude)

    def as_reversed_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)


class CoordinateParser:
    def __init__(
        self,
        format_detector: Optional[CoordinateFormatDetector] = None,
        bounds_validator: Optional[BoundsValidator] = None,
        bounds: Optional[GeographicBounds] = None,
        logger=None,
    ):
        """
        Initialize coordinate parser.

        Args:
            format_detector: Strategy for auto-detecting coordinate format
            bounds_validator: Strategy for validating geographic bounds
            bounds: Geographic bounds for detection/validation
            logger: Optional logger for debugging
        """
        self.bounds = bounds

        if format_detector:
            self.format_detector = format_detector
        elif bounds:
            self.format_detector = RangeBasedDetector(bounds)
        else:
            self.format_detector = None

        self.bounds_validator = bounds_validator
        self.logger = logger

    def _validate_coordinate_ranges(
        self,
        lat: float,
        lon: float,
        field_name: str = "coordinate",
        original_string: str = None,
    ) -> None:
        if not (-90 <= lat <= 90):
            raise InvalidLatitudeError(lat, field_name, original_string)
        if not (-180 <= lon <= 180):
            raise InvalidLongitudeError(lon, field_name, original_string)

    def parse(
        self,
        coord_string: str,
        format_type: str = "auto",
        field_name: str = "coordinate",
        validate: bool = True,
    ) -> ParsedCoordinates:
        """
        Args:
            coord_string: The coordinate string to parse
            format_type: 'auto', 'lonlat', or 'latlon'
            field_name: Name of the field for error messages
            validate: Whether to validate against bounds

        Returns:
            ParsedCoordinates object

        Raises:
            InvalidNumberOfCoordinates: When coordinate string doesn't contain exactly two numbers
            CoordinateOrderDetectionError: When auto-detection fails to determine coordinate order
            MissingFormatDetectorError: When auto-detection is requested but no detector is configured
            InvalidLatitudeError: When latitude is outside -90 to 90 range
            InvalidLongitudeError: When longitude is outside -180 to 180 range
            CoordinateRangeError: When coordinates are outside configured bounds
            InvalidCoordinateFormat: When coordinate format is invalid
        """
        numbers = self.extract_numbers(coord_string, field_name)

        if len(numbers) != 2:
            raise InvalidNumberOfCoordinates(
                field_name=field_name,
                actual_count=len(numbers),
                original_string=coord_string,
            )

        num1, num2 = numbers
        validation_result = None

        try:
            if format_type == "lonlat":
                lon, lat = num1, num2
                detected_format = "lonlat"
                detection_reason = "explicitly specified as lonlat"
            elif format_type == "latlon":
                lat, lon = num1, num2
                detected_format = "latlon"
                detection_reason = "explicitly specified as latlon"
            else:
                if self.format_detector:
                    detection_result = self.format_detector.detect(num1, num2)
                    if detection_result:
                        detected_format = detection_result.format_type
                        detection_reason = detection_result.reason
                    else:
                        raise CoordinateOrderDetectionError(
                            field_name=field_name, original_string=coord_string
                        )
                else:
                    raise MissingFormatDetectorError(field_name=field_name)

                if detected_format == "lonlat":
                    lon, lat = num1, num2
                else:
                    lat, lon = num1, num2
        except CoordinateParsingError:
            raise
        except Exception as e:
            raise CoordinateParsingError(
                message=f"Unexpected error during parsing: {str(e)}",
                field_name=field_name,
                original_string=coord_string,
            ) from e

        self._validate_coordinate_ranges(lat, lon, field_name, coord_string)

        if validate and self.bounds_validator:
            try:
                validation_result = self.bounds_validator.validate(lat, lon)
            except ValueError as e:
                raise CoordinateRangeError(
                    lat=lat,
                    lon=lon,
                    bounds_name=getattr(
                        self.bounds_validator.bounds, "name", "configured"
                    ),
                    lat_range=(
                        getattr(
                            self.bounds_validator.bounds,
                            "latitude_min",
                            -90,
                        ),
                        getattr(
                            self.bounds_validator.bounds,
                            "latitude_max",
                            90,
                        ),
                    ),
                    lon_range=(
                        getattr(
                            self.bounds_validator.bounds,
                            "longitude_min",
                            -180,
                        ),
                        getattr(
                            self.bounds_validator.bounds,
                            "longitude_max",
                            180,
                        ),
                    ),
                    field_name=field_name,
                    original_string=coord_string,
                ) from e
            except Exception as e:
                raise CoordinateParsingError(
                    message=f"Validation error: {str(e)}",
                    field_name=field_name,
                    original_string=coord_string,
                ) from e

        return ParsedCoordinates(
            longitude=lon,
            latitude=lat,
            detected_format=detected_format,
            original_string=coord_string,
            validation_result=validation_result,
        )

    def parse_nwse_coordinates(
        self, coord_string: str
    ) -> Optional[Tuple[float, float]]:
        """
        Parse coordinates with N/S/E/W directional suffixes.

        Supported formats:
        - "60.7128 N, 74.0060 W"
        - "N60.7128 W74.0060"
        - "60°42'46.08\"N 74°0'21.6\"W" (DMS format)
        - "60°42.768'N 74°0.36'W" (DM format)

        Returns:
            Tuple[float, float] as (longitude, latitude) or None if not NWSE format

        Raises:
            NWSEFormatError: When NWSE format is detected but invalid
            DMSFormatError: When DMS/DM format is invalid
        """
        coord_string = coord_string.strip()
        if not re.search(r"[NSEW]", coord_string, re.IGNORECASE):
            return None

        try:
            separate_pattern = (
                r"([-+]?\d*\.?\d+)\s*([NSEW])(?:,?\s*)([-+]?\d*\.?\d+)\s*([NSEW])"
            )
            match = re.match(separate_pattern, coord_string, re.IGNORECASE)

            if match:
                lat_value = float(match.group(1))
                lat_dir = match.group(2).upper()
                lon_value = float(match.group(3))
                lon_dir = match.group(4).upper()

                lat = -abs(lat_value) if lat_dir == "S" else abs(lat_value)
                lon = -abs(lon_value) if lon_dir == "W" else abs(lon_value)

                return (lon, lat)

            prefix_pattern = (
                r"([NSEW])\s*([-+]?\d*\.?\d+)(?:,?\s*)([NSEW])\s*([-+]?\d*\.?\d+)"
            )
            match = re.match(prefix_pattern, coord_string, re.IGNORECASE)

            if match:
                lat_dir = match.group(1).upper()
                lat_value = float(match.group(2))
                lon_dir = match.group(3).upper()
                lon_value = float(match.group(4))

                lat = -abs(lat_value) if lat_dir == "S" else abs(lat_value)
                lon = -abs(lon_value) if lon_dir == "W" else abs(lon_value)

                return (lon, lat)

            parts = re.split(r"[,;\s|]+", coord_string)

            lat = None
            lon = None

            i = 0
            while i < len(parts):
                part = parts[i].strip()
                if not part:
                    i += 1
                    continue

                if i + 1 < len(parts):
                    next_part = parts[i + 1].strip()
                    try:

                        value = float(part)

                        if next_part.upper() in ["N", "S", "E", "W"]:
                            direction = next_part.upper()

                            if direction in ["S", "W"]:
                                value = -abs(value)
                            else:
                                value = abs(value)

                            if direction in ["N", "S"]:
                                lat = value
                            else:
                                lon = value

                            i += 2
                            continue
                    except ValueError:
                        pass

                match = re.match(r"^([-+]?\d*\.?\d+)([NSEW])$", part, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    direction = match.group(2).upper()

                    if direction in ["S", "W"]:
                        value = -abs(value)
                    else:
                        value = abs(value)

                    if direction in ["N", "S"]:
                        lat = value
                    else:
                        lon = value

                    i += 1
                    continue

                try:
                    dms_coord = self._parse_dms_coordinate(part)
                    if dms_coord:
                        value, direction = dms_coord
                        if direction.upper() in ["N", "S"]:
                            lat = value
                        else:
                            lon = value
                except DMSFormatError:

                    raise
                except Exception as e:

                    raise NWSEFormatError(coord_string, field_name="coordinate") from e

                i += 1

            if lat is not None and lon is not None:
                return (lon, lat)

            return None

        except (DMSFormatError, NWSEFormatError):
            raise
        except Exception as e:
            raise NWSEFormatError(coord_string, field_name="coordinate") from e

    def extract_numbers(
        self,
        coord_string: str,
        field_name: str,
    ) -> Tuple[float, ...]:
        """Extract numbers from various string formats, including NWSE coordinates

        Raises:
            InvalidCoordinateFormat: When numbers cannot be extracted from the string
            NWSEFormatError: When NWSE format is detected but invalid
            DMSFormatError: When DMS/DM format is invalid
        """

        try:
            nwse_coords = self.parse_nwse_coordinates(coord_string)
            if nwse_coords:

                return nwse_coords
        except (NWSEFormatError, DMSFormatError):

            raise
        except Exception as e:

            pass

        clean_string = re.sub(r"[\[\](){}]", "", coord_string)

        delimiters = r"[,;\s|]+"
        parts = re.split(delimiters, clean_string.strip())

        numbers = []
        for part in parts:
            if part:
                try:
                    numbers.append(float(part))
                except ValueError:

                    try:
                        match = re.match(
                            r"^([-+]?\d*\.?\d+)([NSEW])$", part, re.IGNORECASE
                        )
                        if match:
                            value = float(match.group(1))
                            direction = match.group(2).upper()
                            if direction in ["S", "W"]:
                                value = -value
                            else:
                                value = abs(value)
                            numbers.append(value)
                        else:
                            raise InvalidCoordinateFormat(
                                clean_string.strip(), field_name
                            )
                    except ValueError:
                        raise InvalidCoordinateFormat(clean_string.strip(), field_name)

        return tuple(numbers)

    def _parse_dms_coordinate(
        self,
        coord_str: str,
    ) -> Optional[Tuple[float, str]]:
        """
        Parse DMS (Degrees Minutes Seconds) or DM (Degrees Minutes) format.

        Examples:
        - "60°42'46.08\"N" -> (60.7128, 'N')
        - "74°0'21.6\"W" -> (-74.006, 'W')
        - "60°42.768'N" -> (60.7128, 'N')

        Raises:
            DMSFormatError: When DMS/DM format is invalid
        """

        dms_pattern = r"^(\d+)[°\s]\s*(\d+)[\'\′]\s*(\d+(?:\.\d+)?)[\"\″]?\s*([NSEW])$"
        # DM pattern: DD°MM.mm' [NSEW]
        dm_pattern = r"^(\d+)[°\s]\s*(\d+(?:\.\d+)?)[\'\′]\s*([NSEW])$"

        match = re.match(dms_pattern, coord_str, re.IGNORECASE)
        if match:
            try:
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                direction = match.group(4).upper()

                if minutes >= 60 or seconds >= 60:
                    raise DMSFormatError(coord_str)

                decimal = degrees + minutes / 60 + seconds / 3600

                if direction in ["S", "W"]:
                    decimal = -decimal

                return (decimal, direction)
            except ValueError as e:
                raise DMSFormatError(coord_str) from e

        match = re.match(dm_pattern, coord_str, re.IGNORECASE)
        if match:
            try:
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                direction = match.group(3).upper()

                if minutes >= 60:
                    raise DMSFormatError(coord_str)

                decimal = degrees + minutes / 60

                if direction in ["S", "W"]:
                    decimal = -decimal

                return (decimal, direction)
            except ValueError as e:
                raise DMSFormatError(coord_str) from e

        return None
