import numpy as np
import pandas as pd

from .utils import cumulative_distances

EARTH_RADIUS_MILES = 3958.8
MAX_DETOUR_MILES = 10.0


def latlon_to_xyz(lat, lon):
    """Convert lat/lon (degrees) to 3D unit sphere coordinates."""
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)

    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)

    return np.column_stack((x, y, z))


def find_nearest_route_segment(route_coords, station_lat, station_lon):
    """
    Find the nearest point on route AND the detour distance.
    Vectorized version - no loops.
    """
    route_array = np.asarray(route_coords, dtype=np.float64)
    lat_diff = np.radians(route_array[:, 0] - station_lat)
    lon_diff = np.radians(route_array[:, 1] - station_lon)

    lat1_rad = np.radians(station_lat)
    lat2_rad = np.radians(route_array[:, 0])

    a = (
        np.sin(lat_diff / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(lon_diff / 2) ** 2
    )
    distances = 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(a))

    idx = np.argmin(distances)
    distance_to_route = distances[idx]
    detour_distance = 2 * distance_to_route

    return idx, distance_to_route, detour_distance


def project_stations_with_detours(route_coords, stations_df, corridor_miles=50):
    """
    Project gas stations onto route with actual detour distances.
    Fully vectorized with numpy operations.
    """

    route_array = np.asarray(route_coords, dtype=np.float64)
    cumd = np.asarray(cumulative_distances(route_coords), dtype=np.float64)

    stations = (
        stations_df.copy()
        .assign(
            Lat=lambda df: pd.to_numeric(df["Lat"], errors="coerce"),
            Lon=lambda df: pd.to_numeric(df["Lon"], errors="coerce"),
        )
        .dropna(subset=["Lat", "Lon"])
    )

    if stations.empty:
        return []

    min_lat, max_lat = route_array[:, 0].min(), route_array[:, 0].max()
    min_lon, max_lon = route_array[:, 1].min(), route_array[:, 1].max()
    degree_buffer = corridor_miles / 69.0

    stations = stations[
        stations["Lat"].between(min_lat - degree_buffer, max_lat + degree_buffer)
        & stations["Lon"].between(min_lon - degree_buffer, max_lon + degree_buffer)
    ]

    if stations.empty:
        return []

    batch_size = 1000
    all_results = []

    station_coords = np.column_stack([stations["Lat"].values, stations["Lon"].values])

    for i in range(0, len(stations), batch_size):
        batch_stations = stations.iloc[i : i + batch_size]
        batch_coords = station_coords[i : i + batch_size]

        n_batch = len(batch_stations)

        route_lats = route_array[:, 0].reshape(1, -1)
        route_lons = route_array[:, 1].reshape(1, -1)
        station_lats = batch_coords[:, 0].reshape(-1, 1)
        station_lons = batch_coords[:, 1].reshape(-1, 1)

        lat_diff = np.radians(route_lats - station_lats)
        lon_diff = np.radians(route_lons - station_lons)
        lat1_rad = np.radians(station_lats)
        lat2_rad = np.radians(route_lats)

        a = (
            np.sin(lat_diff / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(lon_diff / 2) ** 2
        )
        dist_matrix = 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

        min_indices = np.argmin(dist_matrix, axis=1)
        min_distances = dist_matrix[np.arange(n_batch), min_indices]

        for j, idx in enumerate(min_indices):
            row = batch_stations.iloc[j]
            all_results.append(
                {
                    "route_mile": float(cumd[idx]),
                    "price": float(row["Retail Price"]),
                    "name": row.name,
                    "Lat": float(row.Lat),
                    "Lon": float(row.Lon),
                    "detour_miles": float(2 * min_distances[j]),
                    "distance_to_route": float(min_distances[j]),
                    "on_route": bool(min_distances[j] < 0.1),
                }
            )

    result_df = pd.DataFrame(all_results)
    result_df = result_df[result_df["detour_miles"] <= MAX_DETOUR_MILES]

    if result_df.empty:
        return []

    result_df.sort_values("route_mile", inplace=True)

    return result_df.to_dict("records")
