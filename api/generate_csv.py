from flask import Blueprint, request, send_file, jsonify
import io
import csv
from math import radians, degrees, sin, cos, asin, atan2

generate_csv_bp = Blueprint("generate_csv", __name__)

EARTH_RADIUS = 6378137.0

def destination_point(lat, lon, bearing, distance_m):
    """
    Computes a destination coordinate from (lat, lon) with given
    bearing (deg) and distance (meters) using a spherical earth model.
    """
    lat1 = radians(lat)
    lon1 = radians(lon)
    brg = radians(bearing)
    d_div_r = distance_m / EARTH_RADIUS

    lat2 = asin(
        sin(lat1) * cos(d_div_r)
        + cos(lat1) * sin(d_div_r) * cos(brg)
    )

    lon2 = lon1 + atan2(
        sin(brg) * sin(d_div_r) * cos(lat1),
        cos(d_div_r) - sin(lat1) * sin(lat2)
    )

    return degrees(lat2), degrees(lon2)


@generate_csv_bp.post("/api/generate")
def generate_csv():
    """
    Generates a Litchi-compatible waypoint CSV.
    Waypoints are calculated ABSOLUTELY from HOME.
    """
    try:
        data = request.get_json(force=True)

        init_lat = float(data["init_lat"])
        init_lon = float(data["init_lon"])
        init_bearing = float(data.get("init_bearing", 0))
        poi_altitude = float(data.get("poi_altitude", 1))
        waypoints = data.get("waypoints", [])

        # ===== CONSTANT LITCHI FIELDS =====
        curve_size = 0
        rotationdir = 0
        gimbalmode = 0
        gimbalpitchangle = 0
        altitudemode = 0
        poi_lat = init_lat
        poi_lon = init_lon
        poi_altitudemode = 0
        photo_time = -1
        photo_dist = -1

        # ===== BUILD POINT LIST =====
        points = []

        # WP0 — home only
        points.append({
            "lat": init_lat,
            "lon": init_lon,
            "alt": 5,
            "bearing": init_bearing,
            "speed": 0
        })

        # Skip WP0 from CSV (home row)
        for i, wp in enumerate(waypoints):
            if i == 0:
                continue

            horiz = float(wp.get("horizontal", 0))
            vert  = float(wp.get("vertical", 5))
            rel_brg = float(wp.get("bearing", 0))
            speed   = float(wp.get("speed", 0))

            # Absolute bearing
            abs_brg = (init_bearing + rel_brg) % 360

            # ALWAYS compute from HOME
            lat2, lon2 = destination_point(init_lat, init_lon, abs_brg, horiz)

            points.append({
                "lat": lat2,
                "lon": lon2,
                "alt": vert,
                "bearing": abs_brg,
                "speed": speed
            })

        # ===== WRITE CSV =====
        out = io.StringIO(newline="")
        writer = csv.writer(out)

        writer.writerow([
            "latitude", "longitude", "altitude(m)", "heading(deg)", "curvesize(m)",
            "rotationdir", "gimbalmode", "gimbalpitchangle", "altitudemode",
            "speed(m/s)", "poi_latitude", "poi_longitude", "poi_altitude(m)",
            "poi_altitudemode", "photo_timeinterval", "photo_distinterval"
        ])

        for p in points:
            writer.writerow([
                f"{p['lat']:.8f}",
                f"{p['lon']:.8f}",
                f"{p['alt']:.2f}",
                f"{p['bearing']:.2f}",
                f"{curve_size:.2f}",
                rotationdir,
                gimbalmode,
                gimbalpitchangle,
                altitudemode,
                f"{p['speed']:.2f}",
                f"{poi_lat:.8f}",
                f"{poi_lon:.8f}",
                f"{poi_altitude:.2f}",
                poi_altitudemode,
                photo_time,
                photo_dist
            ])

        mem = io.BytesIO(out.getvalue().encode("utf-8-sig"))
        mem.seek(0)

        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name="litchi_waypoints.csv"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400
