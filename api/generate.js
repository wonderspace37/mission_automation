export default async function handler(req, res) {
    try {
        if (req.method !== "POST") {
            res.status(405).send("Method not allowed");
            return;
        }

        const { waypoints } = req.body || {};
        if (!waypoints?.length) {
            res.status(400).send("No waypoints provided");
            return;
        }

        // Build CSV
        let csv = "horizontal,vertical,bearing,hold_time,speed\n";
        for (const wp of waypoints) {
            csv += `${wp.horizontal},${wp.vertical},${wp.bearing},${wp.hold_time},${wp.speed}\n`;
        }

        res.setHeader("Content-Type", "text/csv");
        res.setHeader("Content-Disposition", "attachment; filename=litchi_waypoints.csv");
        res.status(200).send(csv);
    } catch (err) {
        console.error("API error:", err);
        res.status(500).send("Internal Server Error: " + err.message);
    }
}
