from flask import Flask, request, send_file, jsonify
import io
import csv
from math import radians, degrees, sin, cos, asin, atan2

app = Flask(__name__)

EARTH_RADIUS = 6378137.0

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

@app.post("/api/generate")
def generate_csv():
    try:
        payload = request.get_json(force=True)

        init_lat = float(payload["init_lat"])
        init_lon = float(payload["init_lon"])
        init_bearing = float(payload["init_bearing"])
        rel_wps = payload["waypoints"]

        points = []
        curr_lat, curr_lon = init_lat, init_lon

        # WP0
        points.append({
            "lat": curr_lat,
            "lon": curr_lon,
            "alt": 5,
            "bearing": init_bearing,
            "speed": 0
        })

        # WP1..N
        for wp in rel_wps:
            horiz = float(wp["horizontal"])
            vert = float(wp["vertical"])
            rel_brg = float(wp["bearing"])
            abs_brg = (init_bearing + rel_brg) % 360

            new_lat, new_lon = destination_point(curr_lat, curr_lon, abs_brg, horiz)
            points.append({
                "lat": new_lat,
                "lon": new_lon,
                "alt": vert,
                "bearing": abs_brg,
                "speed": wp.get("speed", 0)
            })
            curr_lat, curr_lon = new_lat, new_lon

        # Write CSV
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
                p["lat"], p["lon"], p["alt"], p["bearing"],
                0, 0, 0, 0, 0,
                p["speed"],
                init_lat, init_lon, 1, 0, -1, -1
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

# Vercel needs this
def handler(event, context):
    return app(event, context)
