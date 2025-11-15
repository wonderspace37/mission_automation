// api/generate.js
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

        if (!Array.isArray(waypoints)) {
            res.status(400).send("❌ Missing or invalid waypoints array");
            return;
        }

        const EARTH_RADIUS = 6378137.0;

        function destinationPoint(lat, lon, bearingDeg, distanceMeters) {
            const br = (bearingDeg * Math.PI) / 180;
            const dR = distanceMeters / EARTH_RADIUS;

            const lat1 = (lat * Math.PI) / 180;
            const lon1 = (lon * Math.PI) / 180;

            const sinLat1 = Math.sin(lat1);
            const cosLat1 = Math.cos(lat1);

            const sinLat2 =
                sinLat1 * Math.cos(dR) + cosLat1 * Math.sin(dR) * Math.cos(br);
            const lat2 = Math.asin(sinLat2);

            const y = Math.sin(br) * Math.sin(dR) * cosLat1;
            const x = Math.cos(dR) - sinLat1 * sinLat2;
            const lon2 = lon1 + Math.atan2(y, x);

            return {
                lat: (lat2 * 180) / Math.PI,
                lon: (lon2 * 180) / Math.PI,
            };
        }

        const homeLat = Number(init_lat);
        const homeLon = Number(init_lon);
        const baseBearing = Number(init_bearing) || 0;
        const poiAlt = Number(poi_altitude ?? 1);

        if (!Number.isFinite(homeLat) || !Number.isFinite(homeLon)) {
            res.status(400).send("❌ Invalid init_lat or init_lon");
            return;
        }

        // Litchi header
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
            "photo_distinterval",
        ];

        const rows = [];
        const curveSize = 0.0;
        const rotationDir = 0;
        const gimbalMode = 0;
        const gimbalPitchAngle = 0;
        const altitudeMode = 0;
        const poiAltitudeMode = 0;
        const photoTimeInterval = -1;
        const photoDistInterval = -1;

        // ---- WP0: Home (included) ----
        const wp0Speed = 5.0; // fixed speed for WP0 as you requested
        rows.push([
            homeLat.toFixed(8),
            homeLon.toFixed(8),
            (5.0).toFixed(2),                  // altitude for WP0
            baseBearing.toFixed(2),            // heading
            curveSize.toFixed(2),
            rotationDir,
            gimbalMode,
            gimbalPitchAngle,
            altitudeMode,
            wp0Speed.toFixed(2),
            homeLat.toFixed(8),                // poi_latitude
            homeLon.toFixed(8),                // poi_longitude
            poiAlt.toFixed(2),                 // poi_altitude
            poiAltitudeMode,
            photoTimeInterval,
            photoDistInterval,
        ]);

        // ---- Remaining waypoints: ABSOLUTE FROM HOME ----
        for (const wp of waypoints) {
            const horizontal = Math.max(0, Number(wp.horizontal || 0));
            const relBearing = Number(wp.bearing || 0);
            const absBearing = ((baseBearing + relBearing) % 360 + 360) % 360;
            const alt = Math.max(2, Number(wp.vertical || 2));
            const speed = Number(wp.speed || 0);

            const { lat, lon } = destinationPoint(homeLat, homeLon, absBearing, horizontal);

            rows.push([
                lat.toFixed(8),
                lon.toFixed(8),
                alt.toFixed(2),
                absBearing.toFixed(2),
                curveSize.toFixed(2),
                rotationDir,
                gimbalMode,
                gimbalPitchAngle,
                altitudeMode,
                speed.toFixed(2),
                homeLat.toFixed(8),
                homeLon.toFixed(8),
                poiAlt.toFixed(2),
                poiAltitudeMode,
                photoTimeInterval,
                photoDistInterval,
            ]);
        }

        const csv = [header.join(","), ...rows.map((r) => r.join(","))].join("\n");

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
