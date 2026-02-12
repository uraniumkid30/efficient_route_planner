import folium
from folium import plugins
import numpy as np
from django.conf import settings


def generate_map_with_detours(route_coords, stops, route_data=None) -> str:

    center_idx = len(route_coords) // 2
    m = folium.Map(location=route_coords[center_idx], zoom_start=6)

    folium.PolyLine(
        route_coords, color="blue", weight=4, opacity=0.8, tooltip="Main Route"
    ).add_to(m)

    folium.Marker(
        route_coords[0],
        popup="Start",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)

    total_distance = stops[-1]["route_mile"] if stops else 0
    folium.Marker(
        route_coords[-1],
        popup=f"End<br>Total Distance: {total_distance:.1f} mi",
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
    ).add_to(m)

    for i, stop in enumerate(stops, 1):
        if stop["name"] == "DESTINATION":
            continue

        route_array = np.array(route_coords)
        station_coords = np.array([stop["Lat"], stop["Lon"]])

        distances = np.sqrt(np.sum((route_array - station_coords) ** 2, axis=1))
        closest_idx = np.argmin(distances)
        closest_point = route_coords[closest_idx]

        popup_text = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <b style="font-size: 14px;">🛢️ Stop {i}: {stop.get('name', 'Unknown')}</b><br>
            <hr style="margin: 5px 0;">
            <table style="width: 100%;">
                <tr><td>💰 Price:</td><td><b>${stop['price']:.3f}</b>/gal</td></tr>
                <tr><td>⛽ Gallons:</td><td><b>{stop['gallons']:.2f}</b> gal</td></tr>
                <tr><td>💵 Cost:</td><td><b>${stop['cost']:.2f}</b></td></tr>
                <tr><td>📍 Route mile:</td><td><b>{stop['route_mile']:.1f}</b> mi</td></tr>
        """

        if stop.get("detour_miles", 0) > 0:
            popup_text += f"""
                <tr><td>🔄 Detour:</td><td><b style="color: orange;">{stop['detour_miles']:.1f}</b> mi (round trip)</td></tr>
                <tr><td>📏 Off route:</td><td><b>{stop.get('distance_to_route', 0):.1f}</b> mi</td></tr>
            """

        if stop.get("buy_reason"):
            popup_text += f"""
                <tr><td colspan="2" style="padding-top: 5px;"><i>{stop['buy_reason']}</i></td></tr>
            """

        popup_text += """
            </table>
        </div>
        """

        marker_color = "green" if stop.get("detour_miles", 0) == 0 else "orange"
        marker_icon = "fire" if stop.get("detour_miles", 0) == 0 else "warning"

        folium.Marker(
            [stop["Lat"], stop["Lon"]],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Stop {i}: {stop.get('name', 'Station')} (${stop['price']:.3f}/gal)",
            icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="fa"),
        ).add_to(m)

        if stop.get("detour_miles", 0) > 0 and "distance_to_route" in stop:

            detour_points = [closest_point, [stop["Lat"], stop["Lon"]], closest_point]

            folium.PolyLine(
                detour_points,
                color="orange",
                weight=3,
                opacity=0.7,
                dash_array="5, 8",
                tooltip=f"🔄 Detour: {stop['detour_miles']:.1f} mi round trip",
            ).add_to(m)

            folium.CircleMarker(
                closest_point,
                radius=4,
                color="orange",
                fill=True,
                fillOpacity=0.7,
                popup=f"Detour point for Stop {i}<br>Route mile: {stop['route_mile']:.1f} mi",
                tooltip=f"🔄 Detour point - Stop {i}",
            ).add_to(m)

    plugins.MeasureControl(position="topleft", primary_length_unit="miles").add_to(m)

    plugins.Fullscreen().add_to(m)

    folium.LayerControl().add_to(m)

    output_file = f"{settings.MAP_DIR}/route_map_{route_data}.html"
    m.save(output_file)
    print(f"✅ Map saved as {output_file}")

    return output_file
