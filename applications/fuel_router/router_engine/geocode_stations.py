import time
import requests
import pandas as pd

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "fuel-route-planner"}


def geocode(addr: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            r = requests.get(
                NOMINATIM_URL,
                params={"q": addr, "format": "json", "limit": 1},
                headers=HEADERS,
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            return None, None
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to geocode '{addr}' after {max_retries} attempts: {e}")
                return None, None
            time.sleep(2 ** attempt) 
    return None, None


def enrich_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    lats, lons = [], []

    for _, row in df.iterrows():
        print(_)
        addr = f"{row['Address']}, {row['City']}, {row['State']}, USA"
        lat, lon = geocode(addr)
        lats.append(lat)
        lons.append(lon)
        time.sleep(1.1)

    df["Lat"] = lats
    df["Lon"] = lons
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    enrich_csv(
        "data/fuel-prices-for-be-assessment.csv", "data/fuel_stations_with_latlon.csv"
    )
