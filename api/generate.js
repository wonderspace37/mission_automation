export default async function handler(req, res) {
    try {
        console.log("📩 /api/generate called");

        if (req.method !== "POST") {
            res.status(405).send("❌ Only POST allowed");
            return;
        }

        const {
            init_lat,
            init_lon,
            init_bearing,
            poi_altitude,
            waypoints
        } = req.body || {};

        if (!Array.isArray(waypoints) || waypoints.length === 0) {
            res.status(400).send("❌ Missing or invalid waypoints array");
            return;
        }

        // Build CSV header (exact order required by Litchi)
        const header = [
            "latitude",
            "longitude",
            "altitude(m)",
            "heading(deg)",
            "curvesize(m)",
            "rotationdir",
            "gimbalmode",
            "gimbalpitchangle",
            "altitudemode",
            "speed(m/s)",
            "poi_latitude",
            "poi_longitude",
            "poi_altitude(m)",
            "poi_altitudemode",
            "photo_timeinterval",
            "photo_distinterval"
        ];

        // ---- Build rows ----
        const rows = [];

        // WP0 (home)
        rows.push([
            init_lat,
            init_lon,
            5, // altitude rule for WP0
            init_bearing || 0,
            0, // curvesize
            0, // rotationdir
            0, // gimbalmode
            0, // gimbalpitchangle
            0, // altitudemode
            waypoints[0]?.speed || 0, // speed
            init_lat, // poi_latitude
            init_lon, // poi_longitude
            poi_altitude || 1, // poi_altitude
            0, // poi_altitudemode
            -1, // photo_timeinterval
            -1  // photo_distinterval
        ]);

        // Remaining waypoints
        for (const wp of waypoints) {
            rows.push([
                init_lat,
                init_lon,
                Math.max(2, wp.vertical || 2),
                (init_bearing + (wp.bearing || 0)) % 360,
                0, // curvesize
                0, // rotationdir
                0, // gimbalmode
                0, // gimbalpitchangle
                0, // altitudemode
                wp.speed || 0,
                init_lat,
                init_lon,
                poi_altitude || 1,
                0,
                -1,
                -1
            ]);
        }

        // ---- Convert to CSV string ----
        const csv = [header.join(","), ...rows.map(r => r.join(","))].join("\n");

        // ---- Send response ----
        res.setHeader("Content-Type", "text/csv");
        res.setHeader(
            "Content-Disposition",
            "attachment; filename=litchi_waypoints.csv"
        );
        res.status(200).send(csv);

    } catch (err) {
        console.error("🔥 generate.js crashed:", err);
        res.status(500).send("❌ Internal error: " + err.message);
    }
}
