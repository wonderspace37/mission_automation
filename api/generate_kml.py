from flask import Blueprint, request, Response, jsonify
import math

generate_kml_bp = Blueprint("generate_kml", __name__)

EARTH_RADIUS = 6378137.0

def destination_point(lat, lon, bearing, distance_m):
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brg = math.radians(bearing)
    d_div_r = distance_m / EARTH_RADIUS

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d_div_r)
        + math.cos(lat1) * math.sin(d_div_r) * math.cos(brg)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d_div_r) * math.cos(lat1),
        math.cos(d_div_r) - math.sin(lat1) * math.sin(lat2)
    )

    return (math.degrees(lat2), math.degrees(lon2))


@generate_kml_bp.post("/api/generate_kml")
def generate_kml():
    try:
        data = request.get_json(force=True)

        init_lat = float(data["init_lat"])
        init_lon = float(data["init_lon"])
        init_bearing = float(data.get("init_bearing", 0))
        waypoints = data.get("waypoints", [])

        # ----- ABSOLUTE COORDINATES FROM HOME -----
        coords = []

        # Only ONE home coordinate used (NO duplication)
        coords.append((init_lon, init_lat, 5))  

        for wp in waypoints:
            horiz = float(wp["horizontal"])
            vert = float(wp["vertical"])
            rel_brg = float(wp["bearing"])

            abs_brg = (init_bearing + rel_brg) % 360
            nlat, nlon = destination_point(init_lat, init_lon, abs_brg, horiz)

            coords.append((nlon, nlat, vert))

        # ----- BUILD CLEAN KML WITH ZERO LEADING WHITESPACE -----
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            '<Document>',
            '  <name>Mission Path</name>',
            '  <Style id="pathStyle">',
            '    <LineStyle>',
            '      <color>ff00aaff</color>',
            '      <width>4</width>',
            '    </LineStyle>',
            '  </Style>',
            '  <Placemark>',
            '    <name>Flight Path</name>',
            '    <styleUrl>#pathStyle</styleUrl>',
            '    <LineString>',
            '      <tessellate>1</tessellate>',
            '      <altitudeMode>absolute</altitudeMode>',
            '      <coordinates>'
        ]

        for lon, lat, alt in coords:
            lines.append(f"        {lon},{lat},{alt}")

        lines += [
            '      </coordinates>',
            '    </LineString>',
            '  </Placemark>',
        ]

        # Add waypoint markers
        lines.append(f'  <Placemark><name>Home</name><Point><coordinates>{coords[0][0]},{coords[0][1]},{coords[0][2]}</coordinates></Point></Placemark>')

        for idx, (lon, lat, alt) in enumerate(coords[1:], start=1):
            lines.append(
                f'  <Placemark><name>WP {idx}</name><Point><coordinates>{lon},{lat},{alt}</coordinates></Point></Placemark>'
            )

        lines += [
            '</Document>',
            '</kml>'
        ]

        xml_text = "\n".join(lines)

        return Response(xml_text, mimetype="application/vnd.google-earth.kml+xml")

    except Exception as e:
        return jsonify({"error": str(e)}), 400
