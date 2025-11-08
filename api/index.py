@app.post("/api/generate")
def generate_csv():
    """
    Generate CSV with strict Litchi format + constant columns.
    """
    try:
        payload = request.get_json(force=True)

        init_lat = float(payload.get("init_lat"))
        init_lon = float(payload.get("init_lon"))
        init_bearing = float(payload.get("init_bearing", 0.0))
        poi_altitude = float(payload.get("poi_altitude", 1.0))

        rel_wps = payload.get("waypoints", []) or []

        # ---------------- Constants ----------------
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

        # -------------------------------------------

        points = []
        curr_lat, curr_lon = init_lat, init_lon

        # Home waypoint (WP0)
        points.append({
            "lat": curr_lat,
            "lon": curr_lon,
            "alt": 5.0,
            "bearing": init_bearing,
            "speed": 0.0
        })

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

        # Write CSV
        out = io.StringIO(newline="")
        writer = csv.writer(out)
        writer.writerow([
            "latitude","longitude","altitude(m)","heading(deg)","curvesize(m)",
            "rotationdir","gimbalmode","gimbalpitchangle","altitudemode",
            "speed(m/s)","poi_latitude","poi_longitude","poi_altitude(m)",
            "poi_altitudemode","photo_timeinterval","photo_distinterval"
        ])

        for p in points:
            row = [
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
            ]
            writer.writerow(row)

        mem = io.BytesIO(out.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        return send_file(mem, mimetype="text/csv",
                         as_attachment=True,
                         download_name="litchi_waypoints.csv")

    except Exception as e:
        return jsonify({"error": str(e)}), 400
