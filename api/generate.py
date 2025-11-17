import json
import csv
import io
import traceback


def handler(request):
    try:
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": "❌ Only POST allowed"
            }

        data = json.loads(request.body or "{}")
        waypoints = data.get("waypoints", [])

        if not isinstance(waypoints, list) or len(waypoints) == 0:
            return {
                "statusCode": 400,
                "body": "❌ No valid waypoints array"
            }

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["horizontal", "vertical", "bearing", "hold_time", "speed"])

        for wp in waypoints:
            writer.writerow([
                wp.get("horizontal", 0),
                wp.get("vertical", 0),
                wp.get("bearing", 0),
                wp.get("hold_time", 0),
                wp.get("speed", 0)
            ])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=litchi_waypoints.csv"
            },
            "body": output.getvalue()
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {
            "statusCode": 500,
            "body": tb
        }
