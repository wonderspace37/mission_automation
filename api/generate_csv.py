from flask import Blueprint, request, Response
import csv
import io

generate_csv_bp = Blueprint("generate_csv", __name__)

@generate_csv_bp.post("/api/generate_csv")
def generate_csv():
    data = request.json["points"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["lat", "lon"])

    for p in data:
        writer.writerow([p["lat"], p["lon"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=waypoints.csv"}
    )

@generate_csv_bp.get("/api/generate_csv_status")
def health():
    return {"status": "CSV generator active"}
