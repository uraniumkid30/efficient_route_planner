import os
import time

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from applications.fuel_router.router_engine.geocode_stations import geocode


class Command(BaseCommand):
    help = "Geocode fuel station addresses and create/enrich lat/lon data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default="data/fuel-prices-for-be-assessment.csv",
            help="Input CSV file path",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="data/fuel_stations_with_latlon.csv",
            help="Output CSV file path",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force re-geocoding of all records"
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.1,
            help="Delay between geocoding requests in seconds (default: 1.1)",
        )

    def handle(self, *args, **options):
        input_file = options["input"]
        output_file = options["output"]
        force = options["force"]
        delay = options["delay"]

        if not os.path.isabs(input_file):
            input_file = (
                settings.DATA_DIR / input_file or "fuel-prices-for-be-assessment.csv"
            )
        if not os.path.isabs(output_file):
            output_file = (
                settings.DATA_DIR / output_file or "fuel_stations_with_latlon.csv"
            )

        if not os.path.exists(input_file):
            self.stderr.write(self.style.ERROR(f"Input file not found: {input_file}"))
            return

        self.stdout.write(f"Reading input file: {input_file}")
        df_input = pd.read_csv(input_file)
        self.stdout.write(self.style.SUCCESS(f"Input file has {len(df_input)} rows"))

        required_cols = ["Address", "City", "State"]
        missing_cols = [col for col in required_cols if col not in df_input.columns]
        if missing_cols:
            self.stderr.write(
                self.style.ERROR(f"Missing required columns: {missing_cols}")
            )
            return

        if os.path.exists(output_file) and not force:
            self.stdout.write(f"Output file found: {output_file}")
            df_output = pd.read_csv(output_file)
            self.stdout.write(f"Output file has {len(df_output)} rows")

            if len(df_output) >= len(df_input):
                self.stdout.write(
                    self.style.SUCCESS(
                        "Output file is up to date. "
                        "Use --force to re-geocode all records."
                    )
                )
                return

            new_count = len(df_input) - len(df_output)
            self.stdout.write(f"Found {new_count} new rows to geocode")

            new_rows = df_input.iloc[len(df_output) :].copy()
            lats, lons = [], []

            for idx, row in new_rows.iterrows():
                addr = f"{row['Address']}, {row['City']}, {row['State']}, USA"
                self.stdout.write(
                    f"Geocoding {idx + 1}/{len(df_input)}: {addr[:50]}..."
                )

                lat, lon = geocode(addr)
                lats.append(lat)
                lons.append(lon)

                time.sleep(delay)

            new_rows["Lat"] = lats
            new_rows["Lon"] = lons

            df_combined = pd.concat([df_output, new_rows], ignore_index=True)
            df_combined.to_csv(output_file, index=False)

            missing_geocodes = new_rows["Lat"].isna().sum()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added {len(new_rows)} rows. "
                    f"Output file now has {len(df_combined)} rows. "
                    f"Missing geocodes: {missing_geocodes}"
                )
            )

        else:

            if force:
                self.stdout.write(
                    self.style.WARNING("Force mode: re-geocoding all records")
                )
            else:
                self.stdout.write("Output file not found. Creating new file...")

            lats, lons = [], []
            missing_count = 0
            total_rows = len(df_input)

            for idx, row in df_input.iterrows():
                addr = f"{row['Address']}, {row['City']}, {row['State']}, USA"
                self.stdout.write(f"Geocoding {idx + 1}/{total_rows}: {addr[:50]}...")

                lat, lon = geocode(addr)
                lats.append(lat)
                lons.append(lon)

                if lat is None:
                    missing_count += 1
                    self.stdout.write(self.style.WARNING(f"Could not geocode: {addr}"))

                time.sleep(delay)

            df_input["Lat"] = lats
            df_input["Lon"] = lons

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            df_input.to_csv(output_file, index=False)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully geocoded {total_rows - missing_count}/{total_rows} records. "
                    f"Missing geocodes: {missing_count}. "
                    f"Saved to {output_file}"
                )
            )
