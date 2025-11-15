// api/generate_kml.js
export default function handler(req, res) {
    try {
        if (req.method !== "POST") {
            res.status(405).send("Only POST allowed");
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

        const coords = [];
        const names = [];

        // WP0: home
        coords.push([homeLon, homeLat, 5.0]);
        names.push("Home");

        // All waypoints: ABSOLUTE from home
        waypoints.forEach((wp, idx) => {
            const horizontal = Math.max(0, Number(wp.horizontal || 0));
            const relBearing = Number(wp.bearing || 0);
            const absBearing = ((baseBearing + relBearing) % 360 + 360) % 360;
            const alt = Math.max(2, Number(wp.vertical || 2));

            const { lat, lon } = destinationPoint(homeLat, homeLon, absBearing, horizontal);
            coords.push([lon, lat, alt]);
            names.push(`WP ${idx + 1}`);
        });

        const coordStr = coords
            .map(([lon, lat, alt]) => `${lon},${lat},${alt}`)
            .join("\n      ");

        let kml = `
  <?xml version="1.0" encoding="UTF-8"?>
  <kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Mission Path</name>
  
    <Style id="pathStyle">
      <LineStyle>
        <color>ff00aaff</color>
        <width>4</width>
      </LineStyle>
    </Style>
  
    <Placemark>
      <name>Flight Path</name>
      <styleUrl>#pathStyle</styleUrl>
      <LineString>
        <tessellate>1</tessellate>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
        ${coordStr}
        </coordinates>
      </LineString>
    </Placemark>
  `;

        coords.forEach(([lon, lat, alt], i) => {
            const nm = names[i] || `WP ${i}`;
            kml += `
    <Placemark>
      <name>${nm}</name>
      <Point>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>${lon},${lat},${alt}</coordinates>
      </Point>
    </Placemark>
  `;
        });

        kml += `
  </Document>
  </kml>
  `.trim();

        res.setHeader("Content-Type", "application/vnd.google-earth.kml+xml");
        res.setHeader(
            "Content-Disposition",
            "attachment; filename=mission_path.kml"
        );
        res.status(200).send(kml);
    } catch (e) {
        console.error(e);
        res.status(500).send("Internal error: " + e);
    }
}
