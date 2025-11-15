import json
import csv
import io
from math import radians, degrees, sin, cos, asin, atan2

EARTH_RADIUS = 6378137.0


def destination_point(lat, lon, bearing, distance_m):
    lat1 = radians(lat)
    lon1 = radians(lon)
    brg = radians(bearing)
    d = distance_m / EARTH_RADIUS

    lat2 = asin(
        sin(lat1) * cos(d) +
        cos(lat1) * sin(d) * cos(brg)
    )
    lon2 = lon1 + atan2(
        sin(brg) * sin(d) * cos(lat1),
        cos(d) - sin(lat1) * sin(lat2)
    )

    return degrees(lat2), degrees(lon2)


def handler(request):
    """Serverless CSV generator — NO FLASK"""
    try:
        data = json.loads(request.body or "{}")

        init_lat = float(data["init_lat"])
        init_lon = float(data["init_lon"])
        init_bearing = float(data["init_bearing"])
        waypoints = data.get("waypoints", [])

        # WP0 = home
        points = [(init_lat, init_lon, 5.0, init_bearing, 0.0)]

        # Generate absolute coords from HOME
        for wp in waypoints:
            dist = float(wp["horizontal"])
            alt = float(wp["vertical"])
            rel_brg = float(wp["bearing"])

            abs_brg = (init_bearing + rel_brg) % 360
            new_lat, new_lon = destination_point(init_lat, init_lon, abs_brg, dist)
            speed = float(wp["speed"])

            points.append((new_lat, new_lon, alt, abs_brg, speed))

        # Write CSV
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "latitude", "longitude", "altitude(m)", "heading(deg)",
            "curvesize(m)", "rotationdir", "gimbalmode", "gimbalpitchangle",
            "altitudemode", "speed(m/s)", "poi_latitude", "poi_longitude",
            "poi_altitude(m)", "poi_altitudemode", "photo_timeinterval",
            "photo_distinterval"
        ])

        for lat, lon, alt, bearing, speed in points:
            writer.writerow([
                f"{lat:.8f}",
                f"{lon:.8f}",
                f"{alt:.1f}",
                f"{bearing:.1f}",
                "0", "0", "0", "0",
                "0",
                f"{speed:.1f}",
                f"{init_lat:.8f}",
                f"{init_lon:.8f}",
                "1",
                "0",
                "-1",
                "-1"
            ])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=litchi_waypoints.csv"
            },
            "body": output.getvalue()
        }

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
