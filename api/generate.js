export default async function handler(req, res) {
    try {
        console.log("Incoming request method:", req.method);
        console.log("Request body raw:", req.body);

        // 1️⃣ Method check
        if (req.method !== "POST") {
            return res.status(405).send("❌ Only POST allowed");
        }

        // 2️⃣ Validate body
        if (!req.body) {
            return res.status(400).send("❌ Empty body received");
        }

        const { waypoints, init_lat, init_lon, init_bearing, poi_altitude } = req.body;
        if (!waypoints || !Array.isArray(waypoints) || waypoints.length === 0) {
            return res.status(400).send("❌ 'waypoints' missing or empty");
        }

        console.log(`Processing ${waypoints.length} waypoints...`);
        console.log("Extra fields:", { init_lat, init_lon, init_bearing, poi_altitude });

        // 3️⃣ Generate CSV header + rows
        let csv = "latitude,longitude,altitude(m),heading(deg),speed(m/s)\n";
        for (const [i, wp] of waypoints.entries()) {
            csv += `${init_lat || ""},${init_lon || ""},${wp.vertical || 0},${wp.bearing || 0},${wp.speed || 0}\n`;
        }

        console.log("CSV generated successfully:\n", csv);

        // 4️⃣ Send file response
        res.setHeader("Content-Type", "text/csv");
        res.setHeader("Content-Disposition", "attachment; filename=litchi_waypoints.csv");
        res.status(200).send(csv);
    } catch (err) {
        console.error("🔥 API generate.js crashed:", err);
        res
            .status(500)
            .send("❌ Server crashed: " + (err.stack || err.message || "Unknown error"));
    }
}
