export default async function handler(req, res) {
    try {
        if (req.method !== "POST") return res.status(405).send("Method not allowed");
        const data = req.body;
        const waypoints = data.waypoints || [];
        if (!waypoints.length) return res.status(400).send("No waypoints provided");

        let csv = "horizontal,vertical,bearing,hold_time,speed\n";
        for (const wp of waypoints) {
            csv += `${wp.horizontal},${wp.vertical},${wp.bearing},${wp.hold_time},${wp.speed}\n`;
        }

        res.setHeader("Content-Type", "text/csv");
        res.setHeader("Content-Disposition", "attachment; filename=litchi_waypoints.csv");
        res.status(200).send(csv);
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal server error: " + err.message);
    }
}
