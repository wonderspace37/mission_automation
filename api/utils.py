import math

EARTH_RADIUS = 6378137.0

def destination_point(lat, lon, bearing, distance_m):
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brg = math.radians(bearing)
    d = distance_m / EARTH_RADIUS

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d)
        + math.cos(lat1) * math.sin(d) * math.cos(brg)
    )

    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2)
    )

    return {
        "lat": math.degrees(lat2),
        "lon": math.degrees(lon2)
    }
