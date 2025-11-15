import json
import math
import io
import base64
import traceback

# Earth radius
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

    try:
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": "Only POST allowed"
            }

        data = json.loads(request.body or "{}")

        init_lat = float(data["init_lat"])
        init_lon = float(data["init_lon"])
        init_bearing = float(data.get("init_bearing", 0))
        poi_alt = float(data.get("poi_altitude", 1))
        wps = data.get("waypoints", [])

        coords = []
        names = []

        # Home
        coords.append((init_lon, init_lat, poi_alt))
        names.append("Home")

        curr_lat, curr_lon = init_lat, init_lon

        for i, wp in enumerate(wps):
            d = float(wp["horizontal"])
            rel = float(wp["bearing"])
            alt = float(wp["vertical"])
            abs_brg = (init_bearing + rel) % 360

            nlat, nlon = destination_point(curr_lat, curr_lon, abs_brg, d)
            coords.append((nlon, nlat, alt))
            names.append(f"WP {i+1}")

            curr_lat, curr_lon = nlat, nlon

        # Build KML string
        coord_str = "\n".join(
            f"{lon},{lat},{alt}"
            for lon, lat, alt in coords
        )

        kml_text = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Mission Path</name>

  <Style id="pathStyle">
    <LineStyle>
      <color>ff00aaff</color>
      <width>4</width>
    </LineStyle>
  </Style>

  <Placemark>
    <name>Flight Path</name>
    <styleUrl>#pathStyle</styleUrl>
    <LineString>
      <tessellate>1</tessellate>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>
{coord_str}
      </coordinates>
    </LineString>
  </Placemark>

"""

        for (lon, lat, alt), nm in zip(coords, names):
            kml_text += f"""
  <Placemark>
    <name>{nm}</name>
    <Point>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>{lon},{lat},{alt}</coordinates>
    </Point>
  </Placemark>
"""

        kml_text += "</Document></kml>"

        # Vercel requires base64 for binary/string files
        encoded = base64.b64encode(kml_text.encode("utf-8")).decode("utf-8")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/vnd.google-earth.kml+xml",
                "Content-Disposition": "attachment; filename=mission_path.kml"
            },
            "body": encoded,
            "isBase64Encoded": True
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {
            "statusCode": 500,
            "body": tb
        }
