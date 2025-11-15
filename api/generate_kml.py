from flask import Response

def generate_kml_file(init_lat, init_lon, init_bearing, waypoints):
    from math import sin, cos, atan2, asin, radians, degrees

    R = 6378137.0

    def dest_point(lat, lon, bearing, dist):
        lat1 = radians(lat)
        lon1 = radians(lon)
        brg = radians(bearing)
        dr = dist / R

        lat2 = asin(
            sin(lat1) * cos(dr) +
            cos(lat1) * sin(dr) * cos(brg)
        )
        lon2 = lon1 + atan2(
            sin(brg) * sin(dr) * cos(lat1),
            cos(dr) - sin(lat1) * sin(lat2)
        )
        return degrees(lat2), degrees(lon2)

    # ---- Compute absolute GPS coords ----
    coords = []
    for wp in waypoints:
        abs_bearing = (init_bearing + wp["bearing"]) % 360
        lat, lon = dest_point(init_lat, init_lon, abs_bearing, wp["horizontal"])
        coords.append((lon, lat, wp["vertical"]))

    # --------- BUILD CLEAN XML (NO prefix whitespace) ---------
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '  <name>Mission Path</name>',
        '  <Style id="lineStyle">',
        '    <LineStyle>',
        '      <color>ff00ffff</color>',
        '      <width>3</width>',
        '    </LineStyle>',
        '  </Style>',
        '  <Placemark>',
        '    <name>Flight Path</name>',
        '    <styleUrl>#lineStyle</styleUrl>',
        '    <LineString>',
        '      <extrude>true</extrude>',
        '      <tessellate>true</tessellate>',
        '      <altitudeMode>absolute</altitudeMode>',
        '      <coordinates>'
    ]

    for lon, lat, alt in coords:
        lines.append(f"        {lon},{lat},{alt}")

    lines += [
        '      </coordinates>',
        '    </LineString>',
        '  </Placemark>',
        '</Document>',
        '</kml>'
    ]

    # Join WITHOUT a leading newline
    xml_text = "\n".join(lines)

    # Return as raw bytes without BOM
    return Response(xml_text.encode("utf-8"), mimetype="application/vnd.google-earth.kml+xml")
