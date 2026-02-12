class InvalidCoordinateFormat(Exception):
    def __init__(self, coordinate, field_name):
        message = f"Invalid coordinate format: {coordinate} for {field_name}.Please use Decimal Degrees Format. Example: 40.087659N, 104.980459W, or equivalently 40.087659, -104.980459"
        super().__init__(message)


class CoordinateParsingError(Exception):
    def __init__(self, message, field_name=None, original_string=None):
        self.field_name = field_name
        self.original_string = original_string
        self.message = message
        full_message = message
        if field_name:
            full_message = f"{field_name}: {message}"
        if original_string:
            full_message = f"{full_message} - Original: '{original_string}'"
        super().__init__(full_message)


class InvalidNumberOfCoordinates(CoordinateParsingError):
    """Exception raised when coordinate string doesn't contain exactly two numbers"""

    def __init__(self, field_name, actual_count, original_string=None):
        message = f"Expected exactly 2 coordinates, got {actual_count}"
        super().__init__(message, field_name, original_string)


class CoordinateOrderDetectionError(CoordinateParsingError):
    """Exception raised when coordinate order cannot be auto-detected"""

    def __init__(self, field_name, original_string=None):
        message = "Cannot determine coordinate order (lonlat vs latlon). Please specify format='lonlat' or format='latlon'"
        super().__init__(message, field_name, original_string)


class InvalidLatitudeError(CoordinateParsingError):
    """Exception raised when latitude is outside valid range (-90 to 90)"""

    def __init__(self, latitude, field_name=None, original_string=None):
        message = f"Latitude must be between -90 and 90, got {latitude}"
        super().__init__(message, field_name, original_string)


class InvalidLongitudeError(CoordinateParsingError):
    """Exception raised when longitude is outside valid range (-180 to 180)"""

    def __init__(self, longitude, field_name=None, original_string=None):
        message = f"Longitude must be between -180 and 180, got {longitude}"
        super().__init__(message, field_name, original_string)


class CoordinateRangeError(CoordinateParsingError):
    """Exception raised when coordinates are outside geographic bounds"""

    def __init__(
        self,
        lat,
        lon,
        bounds_name,
        lat_range,
        lon_range,
        field_name=None,
        original_string=None,
    ):
        self.latitude = lat
        self.longitude = lon
        self.bounds_name = bounds_name
        self.latitude_bounds = lat_range
        self.longitude_bounds = lon_range

        message = (
            f"Coordinates ({lat}, {lon}) are outside {bounds_name} bounds. "
            f"Latitude must be between {lat_range[0]} and {lat_range[1]}, "
            f"Longitude between {lon_range[0]} and {lon_range[1]}"
        )
        super().__init__(message, field_name, original_string)


class DMSFormatError(CoordinateParsingError):
    """Exception raised when Degrees-Minutes-Seconds format is invalid"""

    def __init__(self, coordinate_part, field_name=None, original_string=None):
        message = f"Invalid DMS/DM format: '{coordinate_part}'"
        super().__init__(message, field_name, original_string)


class NWSEFormatError(CoordinateParsingError):
    """Exception raised when N/S/E/W directional format is invalid"""

    def __init__(self, coord_string, field_name=None):
        message = f"Invalid NWSE coordinate format: '{coord_string}'"
        super().__init__(message, field_name, coord_string)


class FormatDetectorError(Exception):
    """Base exception for format detector errors"""

    pass


class MissingFormatDetectorError(FormatDetectorError, CoordinateParsingError):
    """Exception raised when auto-detection is requested but no detector is configured"""

    def __init__(self, field_name=None):
        message = "Auto-detection requires a format detector or bounds to be configured"
        super().__init__(message, field_name)


class BoundsValidationError(Exception):
    """Base exception for bounds validation errors"""

    def __init__(self, message, lat=None, lon=None, bounds_name=None):
        self.latitude = lat
        self.longitude = lon
        self.bounds_name = bounds_name
        full_message = message
        if lat is not None and lon is not None:
            full_message = f"({lat}, {lon}): {message}"
        super().__init__(full_message)


class BoundsConfigurationError(BoundsValidationError):
    """Exception raised when bounds validator is misconfigured"""

    def __init__(self, message="Invalid bounds configuration"):
        super().__init__(message)


class UnsupportedBoundsError(BoundsValidationError):
    """Exception raised when requested geographic bounds are not supported"""

    def __init__(self, bounds_name):
        message = f"Unsupported geographic bounds: {bounds_name}"
        super().__init__(message)
