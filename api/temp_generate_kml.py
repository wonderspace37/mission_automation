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

        # ----- ABSOLUTE COORDINATES (ALWAYS FROM HOME) -----
        coords = []

        # ONLY ONE home coordinate added
        coords.append((init_lon, init_lat, 5))

        for wp in waypoints:
            horiz = float(wp["horizontal"])
            vert = float(wp["vertical"])
            rel_brg = float(wp["bearing"])

            abs_brg = (init_bearing + rel_brg) % 360
            new_lat, new_lon = destination_point(init_lat, init_lon, abs_brg, horiz)
            coords.append((new_lon, new_lat, vert))

        # ----- CLEAN XML (NO LEADING NEWLINES, NO SPACES) -----
        xml_lines = [
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
            xml_lines.append(f'        {lon},{lat},{alt}')

        xml_lines += [
            '      </coordinates>',
            '    </LineString>',
            '  </Placemark>',
            f'  <Placemark><name>Home</name><Point><coordinates>{coords[0][0]},{coords[0][1]},{coords[0][2]}</coordinates></Point></Placemark>'
        ]

        # Add individual marked WPs
        for i, (lon, lat, alt) in enumerate(coords[1:], start=1):
            xml_lines.append(
                f'  <Placemark><name>WP {i}</name><Point><coordinates>{lon},{lat},{alt}</coordinates></Point></Placemark>'
            )

        xml_lines += [
            '</Document>',
            '</kml>'
        ]

        xml_text = "\n".join(xml_lines)

        return Response(xml_text, mimetype="application/vnd.google-earth.kml+xml")

    except Exception as e:
        return jsonify({"error": str(e)}), 400
