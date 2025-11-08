import io
import csv
import math
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

EARTH_RADIUS = 6378137.0  # WGS84, meters


def destination_point(lat, lon, bearing_deg, distance_m):
    """Project from (lat, lon) by distance_m along bearing_deg (0=N, clockwise)."""
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brg = math.radians(bearing_deg % 360)
    d_r = distance_m / EARTH_RADIUS

    sin_lat2 = math.sin(lat1) * math.cos(d_r) + math.cos(lat1) * math.sin(d_r) * math.cos(brg)
    lat2 = math.asin(sin_lat2)

    y = math.sin(brg) * math.sin(d_r) * math.cos(lat1)
    x = math.cos(d_r) - math.sin(lat1) * sin_lat2
    lon2 = lon1 + math.atan2(y, x)

    return (math.degrees(lat2), (math.degrees(lon2) + 540) % 360 - 180)  # normalize lon


def clamp(v, lo, hi):
    try:
        v = float(v)
    except Exception:
        v = lo
    return max(lo, min(hi, v))


@app.post("/api/generate")
def generate_csv():
    """
    Expects JSON:
    {
      init_lat, init_lon, init_bearing,
      poi_altitude, speed_start, curve_size, gimbal_pitch, photo_interval,
      waypoints: [{horizontal, vertical, bearing, hold_time}, ...]  // relative to init_bearing
    }
    Returns: downloadable CSV for Litchi.
    """
    try:
        payload = request.get_json(force=True)

        init_lat = float(payload.get("init_lat"))
        init_lon = float(payload.get("init_lon"))
        init_bearing = float(payload.get("init_bearing", 0.0))

        poi_altitude = float(payload.get("poi_altitude", 1.0))
        speed_start = float(payload.get("speed_start", 0.0))
        curve_size = float(payload.get("curve_size", 0.0))
        gimbal_pitch = float(payload.get("gimbal_pitch", 0.0))
        photo_interval = float(payload.get("photo_interval", 1.0))

        rel_wps = payload.get("waypoints", []) or []

        # Build absolute track from the relative spec
        points = []
        # WP0 (home) fixed at 5 m altitude, hold 0
        curr_lat, curr_lon = init_lat, init_lon
        curr_alt = 5.0
        points.append(
            dict(lat=curr_lat, lon=curr_lon, alt=curr_alt, hold=0.0, abs_bearing=init_bearing % 360)
        )

        for seg in rel_wps:
            horiz = max(0.0, float(seg.get("horizontal", 0.0)))
            rel_brg = float(seg.get("bearing", 0.0))
            abs_brg = (init_bearing + rel_brg) % 360
            next_lat, next_lon = destination_point(curr_lat, curr_lon, abs_brg, horiz)
            next_alt = max(2.0, float(seg.get("vertical", 2.0)))
            hold = max(0.0, float(seg.get("hold_time", 0.0)))
            points.append(dict(lat=next_lat, lon=next_lon, alt=next_alt, hold=hold, abs_bearing=abs_brg))
            curr_lat, curr_lon, curr_alt = next_lat, next_lon, next_alt

        # Litchi CSV skeleton (commonly-used subset & order)
        # latitude, longitude, altitude(m), heading(deg), curvesize(m), rotationdir,
        # gimbalmode, gimbalpitchangle, actiontype1, actionparam1, altitudemode, speed(m/s),
        # poi_latitude, poi_longitude, poi_altitude(m), poi_altitudemode, photo_timeinterval, photo_distinterval
        out = io.StringIO(newline="")
        writer = csv.writer(out)

        # (Optional) header row for humans (Litchi ignores unknown headers, but we’ll skip to be safe)
        # writer.writerow([...])

        # Some fixed/defaults that work well:
        rotationdir = 0
        gimbalmode = 1              # 1 = gimbal pitch angle (set)
        actiontype1 = 0             # 0 = none
        actionparam1 = 0
        altitudemode = 1            # 1 = AGL
        poi_altitudemode = 1        # 1 = AGL
        photo_distinterval = 0

        # For POI columns, we’ll leave lat/lon empty (0) unless you want to bind a real POI.
        poi_latitude = 0
        poi_longitude = 0

        for i, p in enumerate(points):
            heading = float(p["abs_bearing"])
            alt = float(p["alt"])
            # Litchi treats "hold" as an action if desired; we’ll keep it simple (no hold action here)
            row = [
                f"{p['lat']:.8f}",
                f"{p['lon']:.8f}",
                f"{alt:.2f}",
                f"{heading:.2f}",
                f"{curve_size:.2f}",
                rotationdir,
                gimbalmode,
                f"{gimbal_pitch:.2f}",
                actiontype1,
                actionparam1,
                altitudemode,
                f"{speed_start:.2f}",
                f"{poi_latitude:.8f}",
                f"{poi_longitude:.8f}",
                f"{poi_altitude:.2f}",
                poi_altitudemode,
                f"{photo_interval:.2f}",
                photo_distinterval,
            ]
            writer.writerow(row)

        mem = io.BytesIO()
        mem.write(out.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name="litchi_waypoints.csv",
        )

    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# Vercel discovers `app` in this file and serves /api/* endpoints accordingly.
# No `if __name__ == "__main__":` needed.
