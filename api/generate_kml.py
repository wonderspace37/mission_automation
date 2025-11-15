import json
import math

EARTH_RADIUS = 6378137.0


def destination_point(lat, lon, bearing, distance_m):
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brg = math.radians(bearing)
    d = distance_m / EARTH_RADIUS

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d) +
        math.cos(lat1) * math.sin(d) * math.cos(brg)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2)
    )

    return math.degrees(lat2), math.degrees(lon2)


def handler(request):
    """Serverless KML generator — NO FLASK"""
    try:
        data = json.loads(request.body or "{}")

        init_lat = float(data["init_lat"])
        init_lon = float(data["init_lon"])
        init_bearing = float(data["init_bearing"])
        waypoints = data.get("waypoints", [])

        coords = [(init_lon, init_lat, 5)]  # Home WP0

        for wp in waypoints:
            horiz = float(wp["horizontal"])
            vert = float(wp["vertical"])
            rel_brg = float(wp["bearing"])

            abs_brg = (init_bearing + rel_brg) % 360
            lat2, lon2 = destination_point(init_lat, init_lon, abs_brg, horiz)
            coords.append((lon2, lat2, vert))

        # Build XML — no leading spaces before header
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        xml += '<Document>\n'
        xml += '  <name>Mission Path</name>\n'
        xml += '  <Style id="pathStyle"><LineStyle><color>ff00aaff</color><width>4</width></LineStyle></Style>\n'
        xml += '  <Placemark><name>Flight Path</name><styleUrl>#pathStyle</styleUrl>\n'
        xml += '    <LineString><tessellate>1</tessellate><altitudeMode>absolute</altitudeMode><coordinates>\n'

        for lon, lat, alt in coords:
            xml += f"      {lon},{lat},{alt}\n"

        xml += '    </coordinates></LineString></Placemark>\n'

        for i, (lon, lat, alt) in enumerate(coords):
            name = "Home" if i == 0 else f"WP {i}"
            xml += f'  <Placemark><name>{name}</name><Point><coordinates>{lon},{lat},{alt}</coordinates></Point></Placemark>\n'

        xml += '</Document></kml>'

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/vnd.google-earth.kml+xml",
                "Content-Disposition": "attachment; filename=mission_path.kml"
            },
            "body": xml
        }

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
