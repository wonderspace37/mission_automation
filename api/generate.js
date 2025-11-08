export default async function handler(req, res) {
    try {
        console.log("📩 Incoming request:", req.method);
        console.log("Body:", req.body);

        if (req.method !== "POST") {
            res.status(405).send("❌ Only POST allowed");
            return;
        }

        const { waypoints, init_lat, init_lon, init_bearing, poi_altitude } = req.body || {};
        if (!waypoints?.length) {
            res.status(400).send("❌ 'waypoints' missing or empty");
            return;
        }

        let csv = "latitude,longitude,altitude(m),heading(deg),speed(m/s)\n";
        for (const wp of waypoints) {
            csv += `${init_lat || ""},${init_lon || ""},${wp.vertical || 0},${wp.bearing || 0},${wp.speed || 0}\n`;
        }

        res.setHeader("Content-Type", "text/csv");
        res.setHeader("Content-Disposition", "attachment; filename=litchi_waypoints.csv");
        res.status(200).send(csv);
    } catch (err) {
        console.error("🔥 generate.js crashed:", err);
        res.status(500).send("❌ Internal error: " + err.message);
    }
}
