
# Adding New Geographic Region Support For a country

This guide will walk you through adding any country (e.g Germany) as a new geographic region to the Coordinate Parser System. No prior experience with the codebase required! We will use Germany as a case study

## Prerequisites

- Basic Python knowledge
- Understanding of what latitude and longitude are
- A text editor or IDE

## Step 1: Get Germany's Geographic Bounds

First, we need Germany's approximate geographic boundaries:
Latitude: 47.3° N to 55.1° N
Longitude: 5.9° E to 15.2° E

In decimal degrees:

Latitude minimum: 47.3

Latitude maximum: 55.1

Longitude minimum: 5.9

Longitude maximum: 15.2

text

## 📁 Step 2: Create Germany Bounds Class

Open `bounds.py` and add Germany's bounds after the existing country classes. Dont forget that and CountryBounds inherits from GeographicBounds and as such you need to provide details for the following

```

# latitude_min,latitude_max,longitude_min,longitude_max,name,code


@dataclass(frozen=True)
class GermanyBounds(GeographicBounds):
    """Germany geographic bounds"""
    
    def __init__(self):
        super().__init__(
            latitude_min=47.3,
            latitude_max=55.1,
            longitude_min=5.9,
            longitude_max=15.2,
            name="Germany",
            code="DEU",
        )
```
What's happening here? We're creating a new class that inherits from GeographicBounds. The frozen=True makes it immutable (can't be changed after creation).

## Step 3: Register Germany with the Factory
Open factory.py and find the _bounds_registry dictionary. Add Germany to it:

```
class CoordinateParserFactory:
    """Factory for creating coordinate parsers"""

    # Registry of available bounds
    _bounds_registry: Dict[str, Type[GeographicBounds]] = {
        "usa": USABounds,
        "europe": EuropeBounds,
        "canada": CanadaBounds,
        "australia": AustraliaBounds,
        "germany": GermanyBounds,  # ← ADD THIS LINE
    }
```

What's happening here? The factory uses this registry to know which regions exist. By adding "germany": GermanyBounds, we tell it "when someone asks for 'germany', use this class."

## Step 4: Create a Germany Detector (Optional but Recommended)
A detector helps automatically figure out if coordinates are in lon/lat or lat/lon format. Create a new file or open detectors.py and add:

```
class GermanyCoordinateDetector(RangeBasedDetector):
    """Germany-specific coordinate format detector"""
    
    def __init__(self):
        from .bounds import GermanyBounds  # Import here to avoid circular imports
        super().__init__(bounds=GermanyBounds())

Then register it in factory.py:

python
# factory.py - Add to _detector_registry
class CoordinateParserFactory:
    # ... existing code ...
    
    # Registry of available detectors
    _detector_registry: Dict[str, Type[CoordinateFormatDetector]] = {
        "usa": USACoordinateDetector,
        "germany": GermanyCoordinateDetector,  # ← ADD THIS LINE
    }
```

Why do this? Without a detector, the system can still parse coordinates but won't automatically detect whether "52.5, 13.4" is lat,lon or lon,lat. The detector helps figure this out based on geographic ranges.

## Step 5: Create Germany Validators
Validators check if coordinates are actually within Germany. Open validators.py and add:
```
python
# validators.py - Add after USALenientValidator

class GermanyStrictValidator(StrictBoundsValidator):
    """Germany-specific strict validator"""
    
    def __init__(self):
        from .bounds import GermanyBounds
        super().__init__(bounds=GermanyBounds())


class GermanyLenientValidator(LenientBoundsValidator):
    """Germany-specific lenient validator"""
    
    def __init__(self):
        from .bounds import GermanyBounds
        super().__init__(bounds=GermanyBounds())
Then register them in factory.py:

python
# factory.py - Add to _validator_registry
class CoordinateParserFactory:
    # ... existing code ...
    
    # Registry of available validators
    _validator_registry: Dict[str, Type[BoundsValidator]] = {
        "usa_strict": USAStrictValidator,
        "usa_lenient": USALenientValidator,
        "germany_strict": GermanyStrictValidator,   # ← ADD
        "germany_lenient": GermanyLenientValidator, # ← ADD
        "strict": StrictBoundsValidator,
        "lenient": LenientBoundsValidator,
    }
```

What's the difference?

Strict validator throws an error if coordinates are outside Germany

Lenient validator just tells you they're outside without crashing

## Step 6: Test Your Implementation
Create a new test file test_germany.py or add to tests.py:


## Troubleshooting
Problem	Likely Cause	Solution
KeyError: 'germany'	Forgot to register in factory	Add to _bounds_registry in factory.py
ImportError	Circular imports	Use local imports inside methods
Coordinates not validating	Wrong bounds values	Double-check Germany's lat/lon ranges
Auto-detection not working	No detector registered	Add GermanyCoordinateDetector to registry

## What's Next?
Now that you've added Germany, you can:

Add more Countries

## Summary

Remember: The key files you have to modify are:

bounds.py - Add GermanyBounds class

factory.py - Register Germany in registries

detectors.py - Add GermanyCoordinateDetector (optional)

validators.py - Add Germany validators

tests.py - Add comprehensive tests