from typing import Optional, Dict, Any, Type
from .bounds import (
    GeographicBounds,
    USABounds,
    EuropeBounds,
    CanadaBounds,
    AustraliaBounds,
)
from .enums import CustomBounds
from .detectors import (
    CoordinateFormatDetector,
    RangeBasedDetector,
    USACoordinateDetector,
)
from .validators import (
    BoundsValidator,
    StrictBoundsValidator,
    LenientBoundsValidator,
    USAStrictValidator,
    USALenientValidator,
)
from .parsers import CoordinateParser


class CoordinateParserFactory:
    _bounds_registry: Dict[str, Type[GeographicBounds]] = {
        "usa": USABounds,
        "europe": EuropeBounds,
        "canada": CanadaBounds,
        "australia": AustraliaBounds,
    }

    _detector_registry: Dict[str, Type[CoordinateFormatDetector]] = {
        "usa": USACoordinateDetector,
    }

    _validator_registry: Dict[str, Type[BoundsValidator]] = {
        "usa_strict": USAStrictValidator,
        "usa_lenient": USALenientValidator,
        "strict": StrictBoundsValidator,
        "lenient": LenientBoundsValidator,
    }

    @classmethod
    def register_bounds(cls, name: str, bounds_class: Type[GeographicBounds]):
        cls._bounds_registry[name.lower()] = bounds_class

    @classmethod
    def register_detector(
        cls, name: str, detector_class: Type[CoordinateFormatDetector]
    ):
        cls._detector_registry[name.lower()] = detector_class

    @classmethod
    def register_validator(
        cls,
        name: str,
        validator_class: Type[BoundsValidator],
    ):
        cls._validator_registry[name.lower()] = validator_class

    @classmethod
    def create_bounds(
        cls,
        region: str,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        lon_min: Optional[float] = None,
        lon_max: Optional[float] = None,
        name: Optional[str] = None,
        code: Optional[str] = None,
    ) -> GeographicBounds:
        """
        Create geographic bounds.

        Args:
            region: Region name or 'custom' for custom bounds
            lat_min, lat_max, lon_min, lon_max: For custom bounds
            name, code: Optional name and code for custom bounds

        Returns:
            GeographicBounds instance
        """
        region = region.lower()

        if region == "custom":
            if None in (lat_min, lat_max, lon_min, lon_max):
                raise ValueError("Custom bounds require all four bounds values")
            return CustomBounds(
                lat_min, lat_max, lon_min, lon_max, name or "Custom", code
            )

        if region in cls._bounds_registry:
            return cls._bounds_registry[region]()
        return USABounds()

    @classmethod
    def create_parser(
        cls,
        region: str = "usa",
        validation_mode: str = "strict",
        use_auto_detection: bool = True,
        custom_bounds: Optional[GeographicBounds] = None,
        custom_detector: Optional[CoordinateFormatDetector] = None,
        custom_validator: Optional[BoundsValidator] = None,
        logger=None,
    ) -> CoordinateParser:
        """
        Create a configured coordinate parser.

        Args:
            region: Region/country name
            validation_mode: 'strict', 'lenient', or 'none'
            use_auto_detection: Whether to enable auto-detection
            custom_bounds: Custom bounds (overrides region)
            custom_detector: Custom detector
            custom_validator: Custom validator
            logger: Optional logger

        Returns:
            Configured CoordinateParser
        """
        bounds = custom_bounds or cls.create_bounds(region)
        if custom_detector:
            detector = custom_detector
        elif use_auto_detection:
            region_key = region.lower()
            if region_key in cls._detector_registry:
                detector = cls._detector_registry[region_key]()
            else:
                detector = RangeBasedDetector(bounds)
        else:
            detector = None

        if custom_validator:
            validator = custom_validator
        elif validation_mode != "none":
            validator_key = f"{region.lower()}_{validation_mode}"
            if validator_key in cls._validator_registry:
                validator = cls._validator_registry[validator_key]()
            elif validation_mode in cls._validator_registry:
                validator = cls._validator_registry[validation_mode](bounds)
            else:
                validator = StrictBoundsValidator(bounds)
        else:
            validator = None

        return CoordinateParser(
            format_detector=detector,
            bounds_validator=validator,
            bounds=bounds,
            logger=logger,
        )

    @classmethod
    def get_available_regions(cls) -> Dict[str, Dict[str, Any]]:
        regions = {}
        for region, bounds_class in cls._bounds_registry.items():
            bounds = bounds_class()
            regions[region] = {
                "name": bounds.name,
                "code": bounds.code,
                "has_detector": region in cls._detector_registry,
                "has_validator": any(
                    key.startswith(f"{region}_")
                    for key in cls._validator_registry.keys()
                ),
                "bounds": bounds.to_dict(),
            }
        return regions
