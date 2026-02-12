from dataclasses import dataclass

from .enums import GeographicBounds


@dataclass(frozen=True)
class USABounds(GeographicBounds):
    """USA geographic bounds"""

    def __init__(self):
        super().__init__(
            latitude_min=24.5,
            latitude_max=49.5,
            longitude_min=-125.0,
            longitude_max=-66.0,
            name="United States of America",
            code="USA",
        )


@dataclass(frozen=True)
class EuropeBounds(GeographicBounds):
    """Europe geographic bounds (approximate)"""

    def __init__(self):
        super().__init__(
            latitude_min=35.0,
            latitude_max=70.0,
            longitude_min=-10.0,
            longitude_max=40.0,
            name="Europe",
            code="EUR",
        )


@dataclass(frozen=True)
class CanadaBounds(GeographicBounds):
    """Canada geographic bounds"""

    def __init__(self):
        super().__init__(
            latitude_min=41.7,
            latitude_max=83.1,
            longitude_min=-141.0,
            longitude_max=-52.6,
            name="Canada",
            code="CAN",
        )


@dataclass(frozen=True)
class AustraliaBounds(GeographicBounds):

    def __init__(self):
        super().__init__(
            latitude_min=-43.6,
            latitude_max=-10.7,
            longitude_min=113.0,
            longitude_max=153.6,
            name="Australia",
            code="AUS",
        )
