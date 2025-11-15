export default function handler(req, res) {
    try {
        if (req.method !== "POST") {
            res.status(405).send("Only POST allowed");
            return;
        }

        const { init_lat, init_lon, init_bearing, waypoints } = req.body || {};

        if (!Array.isArray(waypoints)) {
            res.status(400).send("❌ Missing or invalid waypoints array");
            return;
        }

        const homeLat = Number(init_lat);
        const homeLon = Number(init_lon);
        const baseBearing = Number(init_bearing) || 0;

        const EARTH_RADIUS = 6378137.0;

        function destinationPoint(lat, lon, brDeg, dist) {
            const br = (brDeg * Math.PI) / 180;
            const dR = dist / EARTH_RADIUS;

            const lat1 = (lat * Math.PI) / 180;
            const lon1 = (lon * Math.PI) / 180;

            const sinLat1 = Math.sin(lat1);
            const cosLat1 = Math.cos(lat1);

            const sinLat2 = sinLat1 * Math.cos(dR) + cosLat1 * Math.sin(dR) * Math.cos(br);
            const lat2 = Math.asin(sinLat2);

            const y = Math.sin(br) * Math.sin(dR) * cosLat1;
            const x = Math.cos(dR) - sinLat1 * sinLat2;
            const lon2 = lon1 + Math.atan2(y, x);

            return {
                lat: (lat2 * 180) / Math.PI,
                lon: (lon2 * 180) / Math.PI,
            };
        }

        // clean coords
        const coords = [];

        // Home first
        coords.push([homeLon, homeLat, 5]);

        // Skip waypoint index 0 ALWAYS (home row)
        waypoints.forEach((wp, idx) => {
            if (idx === 0) return; // skip CSV home row

            const horizontal = Number(wp.horizontal) || 0;
            const vertical = Number(wp.vertical) || 5;
            const relBearing = Number(wp.bearing) || 0;

            const absBearing = ((baseBearing + relBearing) % 360 + 360) % 360;

            const { lat, lon } = destinationPoint(homeLat, homeLon, absBearing, horizontal);

            coords.push([lon, lat, vertical]);
        });

        // Build XML manually (NO TEMPLATE WHITESPACE)
        let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
        xml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n';
        xml += '<Document>\n';
        xml += '  <name>Mission Path</name>\n';
        xml += '  <Style id="pathStyle">\n';
        xml += '    <LineStyle><color>ff00aaff</color><width>4</width></LineStyle>\n';
        xml += '  </Style>\n';
        xml += '  <Placemark>\n';
        xml += '    <name>Flight Path</name>\n';
        xml += '    <styleUrl>#pathStyle</styleUrl>\n';
        xml += '    <LineString>\n';
        xml += '      <tessellate>1</tessellate>\n';
        xml += '      <altitudeMode>absolute</altitudeMode>\n';
        xml += '      <coordinates>\n';

        coords.forEach(([lon, lat, alt]) => {
            xml += `        ${lon},${lat},${alt}\n`;
        });

        xml += '      </coordinates>\n';
        xml += '    </LineString>\n';
        xml += '  </Placemark>\n';

        // Individual WPs
        xml += `  <Placemark><name>Home</name><Point><coordinates>${coords[0][0]},${coords[0][1]},${coords[0][2]}</coordinates></Point></Placemark>\n`;

        coords.slice(1).forEach(([lon, lat, alt], i) => {
            xml += `  <Placemark><name>WP ${i + 1}</name><Point><coordinates>${lon},${lat},${alt}</coordinates></Point></Placemark>\n`;
        });

        xml += '</Document>\n';
        xml += '</kml>';

        res.setHeader("Content-Type", "application/vnd.google-earth.kml+xml");
        res.setHeader("Content-Disposition", "attachment; filename=mission_path.kml");
        res.status(200).send(xml);

    } catch (err) {
        res.status(500).json({ error: String(err) });
    }
}
