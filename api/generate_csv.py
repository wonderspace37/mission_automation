from flask import Blueprint, jsonify

generate_csv_bp = Blueprint("generate_csv", __name__)

# This blueprint does NOT override /api/generate
# It only serves as a health-check so index.py import does not break.

@generate_csv_bp.get("/api/generate_csv_status")
def csv_status():
    return jsonify({"status": "csv generator active (handled in index.py)"}), 200