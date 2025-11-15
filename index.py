# index.py
from flask import Flask, request, send_file, jsonify
import io
import csv
from math import radians, degrees, sin, cos, asin, atan2

# Import both API blueprints
from api.generate_kml import generate_kml_bp
from api.generate_csv import generate_csv_bp

app = Flask(__name__)

# Register API route blueprints
app.register_blueprint(generate_kml_bp)
app.register_blueprint(generate_csv_bp)

EARTH_RADIUS = 6378137.0


# ===============================
# HELPER: Great-circle destination
# ===============================
def destination_point(lat, lon, bearing, distance_m):
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


# ===============================
#  LITCHI CSV GENERATION
# ===============================
@app.post("/api/generate")
def generate_csv():
    """
    Generates a Litchi-compatible waypoint CSV.
    """
    try:
        payload = request.get_json(force=True)

        init_lat = float(payload["init_lat"])
        init_lon = float(payload["init_lon"])
        init_bearing = float(payload.get("init_bearing", 0.0))
        poi_altitude = float(payload.get("poi_altitude", 1.0))
        rel_wps = payload.get("waypoints", []) or []

        # Static metadata for Litchi
        curve_size = 0
        rotationdir = 0
        gimbalmode = 0
        gimbalpitchangle = 0
        altitudemode = 0
        poi_latitude = init_lat
        poi_longitude = init_lon
        poi_altitudemode = 0
        photo_timeinterval = -1
        photo_distinterval = -1

        # Build waypoint list
        points = []
        curr_lat, curr_lon = init_lat, init_lon

        # WP0 - Home
        points.append({
            "lat": curr_lat,
            "lon": curr_lon,
            "alt": 5.0,
            "bearing": init_bearing,
            "speed": 0.0
        })

        # Generate waypoints relative to HOME (absolute coordinates)
        for seg in rel_wps:
            horiz = max(0.0, float(seg.get("horizontal", 0.0)))
            rel_brg = float(seg.get("bearing", 0.0))
            abs_brg = (init_bearing + rel_brg) % 360

            next_lat, next_lon = destination_point(curr_lat, curr_lon, abs_brg, horiz)
            next_alt = max(2.0, float(seg.get("vertical", 2.0)))
            speed = float(seg.get("speed", 0.0))

            points.append({
                "lat": next_lat,
                "lon": next_lon,
                "alt": next_alt,
                "bearing": abs_brg,
                "speed": speed
            })

            curr_lat, curr_lon = next_lat, next_lon

        # Output CSV
        out = io.StringIO(newline="")
        writer = csv.writer(out)

        writer.writerow([
            "latitude", "longitude", "altitude(m)", "heading(deg)",
            "curvesize(m)", "rotationdir", "gimbalmode", "gimbalpitchangle",
            "altitudemode", "speed(m/s)", "poi_latitude", "poi_longitude",
            "poi_altitude(m)", "poi_altitudemode", "photo_timeinterval", "photo_distinterval"
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
                f"{poi_latitude:.8f}",
                f"{poi_longitude:.8f}",
                f"{poi_altitude:.2f}",
                poi_altitudemode,
                photo_timeinterval,
                photo_distinterval
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


# ===============================
#  LOCAL DEV ENTRY POINT
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
