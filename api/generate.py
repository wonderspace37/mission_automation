import json
import csv
import io
import traceback

def handler(request):
    try:
        # Log everything we receive
        print("=== generate.py invoked ===")
        print("Method:", request.method)
        print("Body raw:", request.body)

        # ---- Handle method ----
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": "❌ Only POST allowed"
            }

        # ---- Parse JSON safely ----
        try:
            data = json.loads(request.body or "{}")
        except Exception as e:
            print("JSON parse error:", str(e))
            return {
                "statusCode": 400,
                "body": f"❌ Invalid JSON: {e}"
            }

        print("Parsed data:", data.keys())

        waypoints = data.get("waypoints", [])
        if not isinstance(waypoints, list) or len(waypoints) == 0:
            return {
                "statusCode": 400,
                "body": "❌ No valid 'waypoints' array found"
            }

        # ---- Generate CSV ----
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

        csv_content = output.getvalue()
        print("✅ CSV generated:")
        print(csv_content)

        # ---- Return CSV ----
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=litchi_waypoints.csv"
            },
            "body": csv_content
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("🔥 CRASH TRACEBACK:")
        print(tb)
        return {
            "statusCode": 500,
            "body": f"❌ Internal Server Error:\n{tb}"
        }
