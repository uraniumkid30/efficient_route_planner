MAX_RANGE = 500.0
MPG = 10.0


def optimize_fuel_stops_with_detours(total_distance, stations):
    """
    Greedy forward-looking fuel optimization WITH DETOUR HANDLING.
    Stations now include 'detour_miles' and 'on_route' fields.
    """
    EPS = 1e-6
    stations = sorted(stations, key=lambda s: s["route_mile"])
    # Add virtual destination
    stations = stations + [
        {
            "route_mile": total_distance,
            "price": 0.0,
            "name": "DESTINATION",
            "detour_miles": 0.0,
            "on_route": True,
        }
    ]

    fuel = MAX_RANGE
    pos = 0.0
    total_cost = 0.0
    stops = []

    i = 0
    while i < len(stations) - 1:
        station = stations[i]

        # Distance to this station's route position
        dist_to_route_pos = station["route_mile"] - pos
        fuel -= dist_to_route_pos
        pos = station["route_mile"]

        if fuel < -EPS:
            raise RuntimeError(f"Out of fuel before reaching {station['name']}")

        fuel = max(0.0, fuel)

        # If station is not on route, we need extra fuel for detour
        detour_needed = (
            station.get("detour_miles", 0) if not station.get("on_route", False) else 0
        )

        gallons = 0.0
        buy_reason = ""

        # Check if we can even make the detour with current fuel
        if detour_needed > fuel + EPS:
            # Can't make the detour - skip this station
            i += 1
            continue

        # Look ahead for cheaper station within reach (including their detours)
        for j, next_station in enumerate(stations[i + 1 :], i + 1):
            # Calculate total distance to reach next station (including its detour)
            distance_to_next_route = next_station["route_mile"] - pos
            next_detour = (
                next_station.get("detour_miles", 0)
                if not next_station.get("on_route", False)
                else 0
            )
            total_distance_to_next = distance_to_next_route + next_detour

            if total_distance_to_next > MAX_RANGE + EPS:
                break  # cannot reach beyond this even with full tank

            if next_station["price"] < station["price"]:
                # Buy just enough to reach cheaper station
                required_miles = distance_to_next_route + next_detour

                # If we're taking a detour now, we need extra fuel for that too
                if detour_needed > 0 and fuel < detour_needed + EPS:
                    # Need to buy enough for current detour AND to reach next
                    required_miles += detour_needed

                required_fuel = required_miles - fuel

                if required_fuel > EPS:
                    gallons = required_fuel / MPG
                    buy_reason = f"to reach cheaper station at {next_station['name']}"
                break
        else:
            max_useful_fuel = MAX_RANGE

            # If we're taking a detour now, we need to save fuel for that
            if detour_needed > 0:
                max_useful_fuel = MAX_RANGE - detour_needed

            required_fuel = max_useful_fuel - fuel
            if required_fuel > EPS:
                gallons = required_fuel / MPG
                buy_reason = "fill tank (no cheaper stations ahead)"

        if gallons > EPS:
            cost = gallons * station["price"]
            if detour_needed > 0:
                fuel -= detour_needed
                pos += detour_needed

            fuel += gallons * MPG
            total_cost += cost

            stop_info = {
                **station,
                "gallons": round(float(gallons), 4),
                "cost": round(float(cost), 2),
                "detour_miles": round(float(detour_needed), 2),
                "buy_reason": buy_reason,
            }
            stops.append(stop_info)

        i += 1

    return stops, round(float(total_cost), 2)
