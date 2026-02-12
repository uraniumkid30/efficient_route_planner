from unittest.mock import Mock
from dataclasses import FrozenInstanceError

import pytest

from applications.coordinates.enums import (
    GeographicBounds,
    CustomBounds,
    DetectionResult,
    ValidationResult,
)
from applications.coordinates.bounds import (
    USABounds,
    EuropeBounds,
    CanadaBounds,
    AustraliaBounds,
)
from applications.coordinates.base import CoordinateFormatDetector
from applications.coordinates.detectors import (
    RangeBasedDetector,
    USACoordinateDetector,
)
from applications.coordinates.validators import (
    BoundsValidator,
    StrictBoundsValidator,
    LenientBoundsValidator,
    USAStrictValidator,
    USALenientValidator,
)
from applications.coordinates.parsers import CoordinateParser
from applications.coordinates.factory import CoordinateParserFactory
from applications.coordinates.exceptions import (
    InvalidCoordinateFormat,
    CoordinateOrderDetectionError,
    MissingFormatDetectorError,
    InvalidLatitudeError,
    InvalidLongitudeError,
    CoordinateRangeError,
    InvalidNumberOfCoordinates,
)


@pytest.fixture
def usa_bounds():

    return USABounds()


@pytest.fixture
def europe_bounds():

    return EuropeBounds()


@pytest.fixture
def canada_bounds():

    return CanadaBounds()


@pytest.fixture
def australia_bounds():
    return AustraliaBounds()


@pytest.fixture
def custom_bounds():

    return CustomBounds(35.0, 45.0, -120.0, -100.0, "Western USA", "WUSA")


@pytest.fixture
def usa_detector(usa_bounds):

    return RangeBasedDetector(usa_bounds)


@pytest.fixture
def usa_coordinate_detector():

    return USACoordinateDetector()


@pytest.fixture
def detector_no_bounds():

    return RangeBasedDetector()


@pytest.fixture
def strict_validator(usa_bounds):

    return StrictBoundsValidator(usa_bounds)


@pytest.fixture
def lenient_validator(usa_bounds):

    return LenientBoundsValidator(usa_bounds)


@pytest.fixture
def usa_strict_validator():

    return USAStrictValidator()


@pytest.fixture
def usa_lenient_validator():

    return USALenientValidator()


@pytest.fixture
def usa_parser(usa_bounds, usa_detector, strict_validator):

    return CoordinateParser(
        format_detector=usa_detector,
        bounds_validator=strict_validator,
        bounds=usa_bounds,
    )


@pytest.fixture
def parser_no_detector():

    return CoordinateParser()


@pytest.fixture
def parser_with_bounds_only(usa_bounds):

    return CoordinateParser(bounds=usa_bounds)


@pytest.fixture
def mock_logger():

    return Mock()


@pytest.fixture
def mock_detector():

    detector = Mock(spec=CoordinateFormatDetector)
    detector.detect.return_value = DetectionResult(
        "lonlat",
        10,
        "mock detection",
    )
    return detector


@pytest.fixture
def mock_validator():

    validator = Mock(spec=BoundsValidator)
    validator.validate.return_value = ValidationResult(
        True,
        "valid",
        USABounds(),
    )
    return validator


VALID_COORDINATES_DATA = [
    ("usa", "New York", (40.7128, -74.0060), True),
    ("usa", "Los Angeles", (34.0522, -118.2437), True),
    ("usa", "Chicago", (41.8781, -87.6298), True),
    ("europe", "Paris", (48.8566, 2.3522), True),
    ("europe", "London", (51.5074, -0.1278), True),
    ("europe", "Berlin", (52.5200, 13.4050), True),
    ("canada", "Toronto", (43.6532, -79.3832), True),
    ("canada", "Montreal", (45.5017, -73.5673), True),
    ("canada", "Vancouver", (49.2827, -123.1207), True),
    ("australia", "Sydney", (-33.8688, 151.2093), True),
    ("australia", "Melbourne", (-37.8136, 144.9631), True),
    ("australia", "Brisbane", (-27.4698, 153.0251), True),
]


INVALID_COORDINATES_DATA = [
    ("usa", "Too south", (20.0, -74.0060), False),
    ("usa", "Too west", (40.7128, -130.0), False),
    ("europe", "Too south", (30.0, 2.3522), False),
    ("europe", "Too east", (48.8566, 50.0), False),
    ("canada", "Too south", (40.0, -79.3832), False),
    ("canada", "Too east", (43.6532, -50.0), False),
    ("australia", "Too north", (-10.0, 151.2093), False),
    ("australia", "Too west", (-33.8688, 100.0), False),
]


COORDINATE_STRINGS_DATA = [
    ("lonlat", "-74.0060, 40.7128", -74.0060, 40.7128, "lonlat"),
    ("latlon", "40.7128, -74.0060", -74.0060, 40.7128, "latlon"),
    ("auto", "-74.0060, 40.7128", -74.0060, 40.7128, "lonlat"),
    ("auto", "40.7128, -74.0060", -74.0060, 40.7128, "latlon"),
]


NWSE_FORMATS_DATA = [
    ("40.7128 N, 74.0060 W", -74.0060, 40.7128),
    ("N40.7128 W74.0060", -74.0060, 40.7128),
    ("40.7128N 74.0060W", -74.0060, 40.7128),
    ("60.7128 S, 74.0060 E", 74.0060, -60.7128),
    ("S60.7128 E74.0060", 74.0060, -60.7128),
    ("60.7128S 74.0060E", 74.0060, -60.7128),
]


DMS_DM_FORMATS_DATA = [
    (
        "40°42'46.08\"N 74°0'21.6\"W",
        40.7128,
        -74.006,
    ),
    (
        "40°42.768'N 74°0.36'W",
        40.7128,
        -74.006,
    ),
    (
        "60°30'30\"S 45°30'30\"E",
        -60.5083,
        45.5083,
    ),
]


INVALID_COORDINATE_STRINGS_DATA = [
    ("40.7128", InvalidNumberOfCoordinates, r"Expected exactly 2 coordinates, got 1"),
    (
        "40.7128, -74.0060, 0.0",
        InvalidNumberOfCoordinates,
        r"Expected exactly 2 coordinates, got 3",
    ),
    (
        "40.7128, invalid, -74.0060",
        InvalidCoordinateFormat,
        r"Invalid coordinate format",
    ),
    (
        "100.0, -74.0060",
        InvalidLatitudeError,
        r"Latitude must be between -90 and 90, got 100.0",
    ),
    (
        "-74.0060, 200.0",
        InvalidLongitudeError,
        r"Longitude must be between -180 and 180, got 200.0",
    ),
]


AMBIGUOUS_COORDINATES_DATA = [
    ("40.0, 45.0", CoordinateOrderDetectionError, r"Cannot determine coordinate order"),
    ("30.0, 50.0", CoordinateOrderDetectionError, r"Cannot determine coordinate order"),
]


FACTORY_BOUNDS_DATA = [
    ("usa", USABounds, "United States of America", "USA"),
    ("europe", EuropeBounds, "Europe", "EUR"),
    ("canada", CanadaBounds, "Canada", "CAN"),
    ("australia", AustraliaBounds, "Australia", "AUS"),
]


CUSTOM_BOUNDS_DATA = [
    (35.0, 45.0, -120.0, -100.0, "Western USA", "WUSA"),
    (40.0, 50.0, -80.0, -70.0, "East Coast", "EC"),
    (-45.0, -35.0, 165.0, 175.0, "New Zealand", "NZ"),
]


DETECTOR_CONFIDENCE_DATA = [
    (-74.0060, 40.7128, "lonlat", 5),  # NYC as lon,lat
    (40.7128, -74.0060, "latlon", 5),  # NYC as lat,lon
    (100.0, 40.0, "lonlat", 5),  # num1 can only be lon
    (40.0, 100.0, "latlon", 5),  # num2 can only be lon
]


class TestGeographicBounds:
    @pytest.mark.parametrize(
        "lat_min,lat_max,lon_min,lon_max,name,code",
        [
            (40.0, 50.0, -120.0, -100.0, "Test", "TST"),
            (-90.0, 90.0, -180.0, 180.0, "World", "WLD"),
            (0.0, 0.0, 0.0, 0.0, "Null Island", "NUL"),
        ],
    )
    def test_valid_bounds_creation(
        self, lat_min, lat_max, lon_min, lon_max, name, code
    ):
        bounds = GeographicBounds(
            lat_min,
            lat_max,
            lon_min,
            lon_max,
            name,
            code,
        )
        assert bounds.latitude_min == lat_min
        assert bounds.latitude_max == lat_max
        assert bounds.longitude_min == lon_min
        assert bounds.longitude_max == lon_max
        assert bounds.name == name
        assert bounds.code == code

    @pytest.mark.parametrize(
        "lat_min,lat_max",
        [
            (100.0, 50.0),
            (-100.0, 90.0),
            (0.0, 100.0),
        ],
    )
    def test_invalid_latitude_bounds(self, lat_min, lat_max):
        with pytest.raises(ValueError, match="Invalid latitude bounds"):
            GeographicBounds(lat_min, lat_max, -120.0, -100.0)

    @pytest.mark.parametrize(
        "lon_min,lon_max",
        [
            (200.0, 180.0),
            (-200.0, 180.0),
            (-180.0, 200.0),
        ],
    )
    def test_invalid_longitude_bounds(self, lon_min, lon_max):
        with pytest.raises(ValueError, match="Invalid longitude bounds"):
            GeographicBounds(40.0, 50.0, lon_min, lon_max)

    @pytest.mark.parametrize(
        "bounds_params,test_point,expected",
        [
            ((40.0, 50.0, -120.0, -100.0), (45.0, -110.0), True),
            ((40.0, 50.0, -120.0, -100.0), (55.0, -110.0), False),
            ((40.0, 50.0, -120.0, -100.0), (45.0, -90.0), False),
            ((-90.0, 90.0, -180.0, 180.0), (0.0, 0.0), True),
        ],
    )
    def test_contains(self, bounds_params, test_point, expected):
        bounds = GeographicBounds(*bounds_params)
        assert bounds.contains(*test_point) is expected


class TestPredefinedBounds:
    @pytest.mark.parametrize(
        "bounds_fixture,expected_values",
        [
            (
                "usa_bounds",
                (24.5, 49.5, -125.0, -66.0, "United States of America", "USA"),
            ),
            ("europe_bounds", (35.0, 70.0, -10.0, 40.0, "Europe", "EUR")),
            ("canada_bounds", (41.7, 83.1, -141.0, -52.6, "Canada", "CAN")),
            (
                "australia_bounds",
                (
                    -43.6,
                    -10.7,
                    113.0,
                    153.6,
                    "Australia",
                    "AUS",
                ),
            ),
        ],
    )
    def test_bounds_properties(self, request, bounds_fixture, expected_values):
        bounds = request.getfixturevalue(bounds_fixture)
        lat_min, lat_max, lon_min, lon_max, name, code = expected_values
        assert bounds.latitude_min == lat_min
        assert bounds.latitude_max == lat_max
        assert bounds.longitude_min == lon_min
        assert bounds.longitude_max == lon_max
        assert bounds.name == name
        assert bounds.code == code

    @pytest.mark.parametrize(
        "bounds_fixture,valid_points",
        [
            (
                "usa_bounds",
                [
                    (40.7128, -74.0060),
                    (34.0522, -118.2437),
                    (41.8781, -87.6298),
                ],
            ),
            (
                "europe_bounds",
                [(48.8566, 2.3522), (51.5074, -0.1278), (52.5200, 13.4050)],
            ),
            (
                "canada_bounds",
                [
                    (43.6532, -79.3832),
                    (45.5017, -73.5673),
                    (49.2827, -123.1207),
                ],
            ),
            (
                "australia_bounds",
                [
                    (-33.8688, 151.2093),
                    (-37.8136, 144.9631),
                    (-27.4698, 153.0251),
                ],
            ),
        ],
    )
    def test_valid_coordinates(self, request, bounds_fixture, valid_points):
        bounds = request.getfixturevalue(bounds_fixture)
        for lat, lon in valid_points:
            assert bounds.contains(lat, lon) is True

    @pytest.mark.parametrize(
        "bounds_fixture,invalid_points",
        [
            ("usa_bounds", [(20.0, -74.0060), (40.7128, -130.0)]),
            ("europe_bounds", [(30.0, 2.3522), (48.8566, 50.0)]),
            ("canada_bounds", [(40.0, -79.3832), (43.6532, -50.0)]),
            ("australia_bounds", [(-10.0, 151.2093), (-33.8688, 100.0)]),
        ],
    )
    def test_invalid_coordinates(
        self,
        request,
        bounds_fixture,
        invalid_points,
    ):
        bounds = request.getfixturevalue(bounds_fixture)
        for lat, lon in invalid_points:
            assert bounds.contains(lat, lon) is False


class TestCustomBounds:
    @pytest.mark.parametrize(
        "lat_min,lat_max,lon_min,lon_max,name,code", CUSTOM_BOUNDS_DATA
    )
    def test_custom_bounds_creation(
        self, lat_min, lat_max, lon_min, lon_max, name, code
    ):
        bounds = CustomBounds(lat_min, lat_max, lon_min, lon_max, name, code)
        assert bounds.latitude_min == lat_min
        assert bounds.latitude_max == lat_max
        assert bounds.longitude_min == lon_min
        assert bounds.longitude_max == lon_max
        assert bounds.name == name
        assert bounds.code == code

    def test_custom_bounds_immutable(self, custom_bounds):
        with pytest.raises(FrozenInstanceError):
            custom_bounds.latitude_min = 40.0


class TestDetectionResult:
    @pytest.mark.parametrize(
        "confidence,threshold,expected",
        [
            (7, 5, True),
            (7, 8, False),
            (3, 5, False),
            (10, 10, True),
        ],
    )
    def test_is_confident(self, confidence, threshold, expected):
        result = DetectionResult("lonlat", confidence, "reason")
        assert result.is_confident(threshold) is expected


class TestRangeBasedDetector:
    @pytest.mark.parametrize(
        "num1,num2,expected_format,min_confidence", DETECTOR_CONFIDENCE_DATA
    )
    def test_detection_confidence(
        self, usa_detector, num1, num2, expected_format, min_confidence
    ):
        result = usa_detector.detect(num1, num2)
        assert result is not None
        assert result.format_type == expected_format
        assert result.confidence >= min_confidence

    def test_detection_returns_none_for_ambiguous_coordinates(self, usa_detector):

        result = usa_detector.detect(-0.1278, 51.5074)
        assert result is None

    def test_no_bounds_returns_none(self, detector_no_bounds):
        assert detector_no_bounds.detect(40.7128, -74.0060) is None

    def test_both_numbers_out_of_range(self, usa_detector):
        assert usa_detector.detect(200.0, 200.0) is None


class TestUSACoordinateDetector:
    def test_initialization(self, usa_coordinate_detector, usa_bounds):
        assert usa_coordinate_detector.bounds is not None
        assert isinstance(usa_coordinate_detector.bounds, USABounds)
        assert usa_coordinate_detector.bounds == usa_bounds

    @pytest.mark.parametrize(
        "num1,num2,expected_format",
        [
            (-74.0060, 40.7128, "lonlat"),
            (40.7128, -74.0060, "latlon"),
        ],
    )
    def test_detection(
        self,
        usa_coordinate_detector,
        num1,
        num2,
        expected_format,
    ):
        result = usa_coordinate_detector.detect(num1, num2)
        assert result is not None
        assert result.format_type == expected_format


class TestBoundsValidators:
    @pytest.mark.parametrize(
        "lat,lon",
        [
            (40.7128, -74.0060),
            (34.0522, -118.2437),
            (41.8781, -87.6298),
        ],
    )
    def test_strict_validator_valid(self, strict_validator, lat, lon):
        result = strict_validator.validate(lat, lon)
        assert result.is_valid is True
        assert "within" in result.message.lower()

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (20.0, -74.0060),
            (40.7128, -130.0),
            (55.0, -74.0060),
        ],
    )
    def test_strict_validator_invalid_raises(self, strict_validator, lat, lon):
        with pytest.raises(ValueError, match="outside"):
            strict_validator.validate(lat, lon)

    @pytest.mark.parametrize(
        "lat,lon,expected_valid",
        [
            (40.7128, -74.0060, True),
            (20.0, -74.0060, False),
            (40.7128, -130.0, False),
        ],
    )
    def test_lenient_validator(
        self,
        lenient_validator,
        lat,
        lon,
        expected_valid,
    ):
        result = lenient_validator.validate(lat, lon)
        assert result.is_valid is expected_valid
        if expected_valid:
            assert "within" in result.message.lower()
        else:
            assert "outside" in result.message.lower()

    @pytest.mark.parametrize(
        "validator_fixture,lat,lon,expected_valid",
        [
            ("usa_strict_validator", 40.7128, -74.0060, True),
            ("usa_strict_validator", 20.0, -74.0060, False),
            ("usa_lenient_validator", 40.7128, -74.0060, True),
            ("usa_lenient_validator", 20.0, -74.0060, False),
        ],
    )
    def test_usa_validators(
        self,
        request,
        validator_fixture,
        lat,
        lon,
        expected_valid,
    ):
        validator = request.getfixturevalue(validator_fixture)
        assert isinstance(validator.bounds, USABounds)

        if validator_fixture == "usa_strict_validator" and not expected_valid:
            with pytest.raises(ValueError):
                validator.validate(lat, lon)
        else:
            result = validator.validate(lat, lon)
            assert result.is_valid is expected_valid


class TestCoordinateParser:
    @pytest.mark.parametrize(
        "input_str,expected_lon,expected_lat",
        NWSE_FORMATS_DATA,
    )
    def test_parse_nwse_coordinates(
        self, usa_parser, input_str, expected_lon, expected_lat
    ):
        result = usa_parser.parse_nwse_coordinates(input_str)
        assert result == (expected_lon, expected_lat)

    @pytest.mark.parametrize(
        "format_type,input_str,expected_lon,expected_lat,detected_format",
        COORDINATE_STRINGS_DATA,
    )
    def test_parse_coordinate_strings(
        self,
        usa_parser,
        format_type,
        input_str,
        expected_lon,
        expected_lat,
        detected_format,
    ):
        result = usa_parser.parse(input_str, format_type=format_type)
        assert result.longitude == expected_lon
        assert result.latitude == expected_lat
        assert result.detected_format == detected_format

    @pytest.mark.parametrize(
        "input_str,expected_exception,message_pattern",
        AMBIGUOUS_COORDINATES_DATA,
    )
    def test_auto_detection_failure(
        self, usa_parser, input_str, expected_exception, message_pattern
    ):
        with pytest.raises(expected_exception, match=message_pattern):
            usa_parser.parse(input_str, format_type="auto")

    def test_parser_with_bounds_creates_detector(
        self, parser_with_bounds_only, usa_bounds
    ):
        assert parser_with_bounds_only.format_detector is not None
        assert isinstance(
            parser_with_bounds_only.format_detector,
            RangeBasedDetector,
        )
        assert parser_with_bounds_only.format_detector.bounds == usa_bounds

    def test_parse_auto_without_detector(self, parser_no_detector):
        with pytest.raises(
            MissingFormatDetectorError,
            match="Auto-detection requires",
        ):
            parser_no_detector.parse("40.7128, -74.0060", format_type="auto")

    @pytest.mark.parametrize(
        "validate,expected_validation",
        [
            (True, True),
            (False, None),
        ],
    )
    def test_parse_validation_control(
        self,
        usa_parser,
        validate,
        expected_validation,
    ):
        result = usa_parser.parse(
            "-74.0060, 40.7128", format_type="lonlat", validate=validate
        )
        if expected_validation:
            assert result.validation_result is not None
            assert result.validation_result.is_valid is expected_validation
        else:
            assert result.validation_result is None

    def test_with_logger(self, usa_parser, mock_logger):
        usa_parser.logger = mock_logger
        usa_parser.parse("-74.0060, 40.7128", format_type="lonlat")
        mock_logger.debug.assert_not_called()


class TestCoordinateParserFactory:
    @pytest.mark.parametrize(
        "region,expected_class,expected_name,expected_code",
        FACTORY_BOUNDS_DATA,
    )
    def test_create_bounds_predefined(
        self, region, expected_class, expected_name, expected_code
    ):
        bounds = CoordinateParserFactory.create_bounds(region)
        assert isinstance(bounds, expected_class)
        assert bounds.name == expected_name
        assert bounds.code == expected_code

    @pytest.mark.parametrize(
        "lat_min,lat_max,lon_min,lon_max,name,code", CUSTOM_BOUNDS_DATA
    )
    def test_create_bounds_custom(
        self,
        lat_min,
        lat_max,
        lon_min,
        lon_max,
        name,
        code,
    ):
        bounds = CoordinateParserFactory.create_bounds(
            "custom",
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            name=name,
            code=code,
        )
        assert isinstance(bounds, CustomBounds)
        assert bounds.latitude_min == lat_min
        assert bounds.latitude_max == lat_max
        assert bounds.longitude_min == lon_min
        assert bounds.longitude_max == lon_max
        assert bounds.name == name
        assert bounds.code == code

    def test_create_bounds_custom_missing_params(self):
        with pytest.raises(ValueError, match="require all four bounds"):
            CoordinateParserFactory.create_bounds("custom")

    def test_create_bounds_unknown_region_defaults_to_usa(self):
        bounds = CoordinateParserFactory.create_bounds("mars")
        assert isinstance(bounds, USABounds)

    @pytest.mark.parametrize(
        "validation_mode,has_validator",
        [
            ("strict", True),
            ("lenient", True),
            ("none", False),
        ],
    )
    def test_create_parser_validation_modes(
        self,
        validation_mode,
        has_validator,
    ):
        parser = CoordinateParserFactory.create_parser(
            validation_mode=validation_mode,
        )
        if has_validator:
            assert parser.bounds_validator is not None
        else:
            assert parser.bounds_validator is None

    @pytest.mark.parametrize(
        "use_auto_detection,has_detector",
        [
            (True, True),
            (False, True),
        ],
    )
    def test_create_parser_detection_modes(
        self,
        use_auto_detection,
        has_detector,
    ):
        parser = CoordinateParserFactory.create_parser(
            use_auto_detection=use_auto_detection
        )
        if has_detector:
            assert parser.format_detector is not None
        else:
            assert parser.format_detector is None

    def test_create_parser_without_detector_and_without_bounds(self):

        parser = CoordinateParser()
        assert parser.format_detector is None
        assert parser.bounds is None

    def test_create_parser_with_custom_detector(self, mock_detector):
        parser = CoordinateParserFactory.create_parser(
            custom_detector=mock_detector,
        )
        assert parser.format_detector == mock_detector

    def test_create_parser_with_custom_validator(self, mock_validator):
        parser = CoordinateParserFactory.create_parser(
            custom_validator=mock_validator,
        )
        assert parser.bounds_validator == mock_validator

    def test_register_new_bounds(self):
        class TestBounds(GeographicBounds):
            def __init__(self):
                super().__init__(0, 10, -10, 0, "Test", "TST")

        CoordinateParserFactory.register_bounds("test", TestBounds)
        bounds = CoordinateParserFactory.create_bounds("test")
        assert isinstance(bounds, TestBounds)

        del CoordinateParserFactory._bounds_registry["test"]

    def test_register_new_detector(self):
        class TestDetector(CoordinateFormatDetector):
            def detect(self, num1, num2):
                return DetectionResult("lonlat", 10, "test")

        CoordinateParserFactory.register_detector("test", TestDetector)
        parser = CoordinateParserFactory.create_parser(region="test")
        assert isinstance(parser.format_detector, TestDetector)

        del CoordinateParserFactory._detector_registry["test"]

    def test_get_available_regions(self):
        regions = CoordinateParserFactory.get_available_regions()
        for region in ["usa", "europe", "canada", "australia"]:
            assert region in regions
            assert "name" in regions[region]
            assert "code" in regions[region]
            assert "has_detector" in regions[region]
            assert "bounds" in regions[region]


class TestIntegration:
    @pytest.mark.parametrize(
        "region,lat,lon",
        [
            ("usa", 40.7128, -74.0060),
            ("usa", 34.0522, -118.2437),
            ("europe", 48.8566, 2.3522),
            ("europe", 51.5074, -0.1278),
            ("canada", 43.6532, -79.3832),
            ("australia", -33.8688, 151.2093),
        ],
    )
    def test_parser_with_validation(self, region, lat, lon):
        parser = CoordinateParserFactory.create_parser(
            region=region, validation_mode="strict"
        )

        result = parser.parse(f"{lon}, {lat}", format_type="lonlat")
        assert result.longitude == lon
        assert result.latitude == lat
        assert result.validation_result.is_valid is True

        result = parser.parse(f"{lon}, {lat}", format_type="auto")
        assert result.longitude == lon
        assert result.latitude == lat

    @pytest.mark.parametrize(
        "region,invalid_lat,invalid_lon",
        [
            ("usa", 20.0, -74.0060),
            ("europe", 30.0, 2.3522),
            ("canada", 40.0, -79.3832),
            ("australia", -10.0, 151.2093),
        ],
    )
    def test_parser_with_validation_error(
        self,
        region,
        invalid_lat,
        invalid_lon,
    ):
        parser = CoordinateParserFactory.create_parser(
            region=region, validation_mode="strict"
        )

        with pytest.raises(CoordinateRangeError, match="outside"):
            parser.parse(f"{invalid_lon}, {invalid_lat}", format_type="lonlat")

    @pytest.mark.parametrize(
        "input_str,format_type,expected_lon,expected_lat",
        [
            ("-74.0060, 40.7128", "auto", -74.0060, 40.7128),
            ("40.7128, -74.0060", "auto", -74.0060, 40.7128),
            ("40.7128 N, 74.0060 W", "auto", -74.0060, 40.7128),
            ("N40.7128 W74.0060", "auto", -74.0060, 40.7128),
            ("40.7128N 74.0060W", "auto", -74.0060, 40.7128),
        ],
    )
    def test_multiple_coordinate_formats(
        self, input_str, format_type, expected_lon, expected_lat
    ):
        parser = CoordinateParserFactory.create_parser("usa")
        result = parser.parse(input_str, format_type=format_type)
        assert (result.longitude, result.latitude) == (
            expected_lon,
            expected_lat,
        )

    def test_end_to_end_workflow(self, usa_bounds):
        bounds = USABounds()
        assert bounds.contains(40.7128, -74.0060) is True

        detector = RangeBasedDetector(bounds)
        validator = StrictBoundsValidator(bounds)
        parser = CoordinateParser(
            format_detector=detector, bounds_validator=validator, bounds=bounds
        )

        result = parser.parse("40.7128, -74.0060", format_type="auto")
        assert result.latitude == 40.7128
        assert result.longitude == -74.0060
        assert result.detected_format == "latlon"
        assert result.validation_result.is_valid is True

        assert result.as_tuple() == (-74.0060, 40.7128)
        assert result.as_reversed_tuple() == (40.7128, -74.0060)

        dict_result = result.to_dict()
        assert dict_result["lon"] == -74.0060
        assert dict_result["lat"] == 40.7128
        assert dict_result["format"] == "latlon"
