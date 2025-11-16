from flask import Blueprint, request, Response

generate_kml_bp = Blueprint("generate_kml", __name__)

@generate_kml_bp.post("/api/generate_kml")
def generate_kml():
    pts = request.json["points"]

    kml = ['<?xml version="1.0" encoding="UTF-8"?>']
    kml.append('<kml xmlns="http://www.opengis.net/kml/2.2"><Document>')

    kml.append("<Placemark><LineString><coordinates>")
    for p in pts:
        kml.append(f"{p['lon']},{p['lat']},0 ")
    kml.append("</coordinates></LineString></Placemark>")

    kml.append("</Document></kml>")

    return Response(
        "\n".join(kml),
        mimetype="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": "attachment; filename=waypoints.kml"}
    )

@generate_kml_bp.get("/api/generate_point")
def get_point():
    from utils import destination_point
    lat = float(request.args["lat"])
    lon = float(request.args["lon"])
    bearing = float(request.args["bearing"])
    dist = float(request.args["distance"])
    return destination_point(lat, lon, bearing, dist)

@generate_kml_bp.get("/api/generate_kml_status")
def status():
    return {"status": "KML generator active"}
