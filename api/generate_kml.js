export default function handler(req, res) {
    try {
        if (req.method !== "POST") {
            res.status(405).send("Only POST allowed");
            return;
        }

        const EARTH_RADIUS = 6378137.0;

        function destinationPoint(lat, lon, bearing, distance) {
            const br = bearing * Math.PI / 180;
            const dR = distance / EARTH_RADIUS;

            const lat1 = lat * Math.PI / 180;
            const lon1 = lon * Math.PI / 180;

            const lat2 = Math.asin(
                Math.sin(lat1) * Math.cos(dR) +
                Math.cos(lat1) * Math.sin(dR) * Math.cos(br)
            );

            const lon2 = lon1 + Math.atan2(
                Math.sin(br) * Math.sin(dR) * Math.cos(lat1),
                Math.cos(dR) - Math.sin(lat1) * Math.sin(lat2)
            );

            return {
                lat: lat2 * 180 / Math.PI,
                lon: lon2 * 180 / Math.PI
            };
        }

        const {
            init_lat,
            init_lon,
            init_bearing,
            poi_altitude,
            waypoints
        } = req.body;

        const coords = [];
        const names = [];

        // home
        coords.push([init_lon, init_lat, poi_altitude]);
        names.push("Home");

        let currLat = init_lat;
        let currLon = init_lon;

        for (let i = 0; i < waypoints.length; i++) {
            const wp = waypoints[i];
            const dist = wp.horizontal;
            const rel = wp.bearing;
            const alt = wp.vertical;

            const absB = (init_bearing + rel) % 360;
            const dest = destinationPoint(currLat, currLon, absB, dist);

            coords.push([dest.lon, dest.lat, alt]);
            names.push(`WP ${i + 1}`);

            currLat = dest.lat;
            currLon = dest.lon;
        }

        const coordString = coords
            .map(([lon, lat, alt]) => `${lon},${lat},${alt}`)
            .join("\n");

        const kml = `
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Mission Path</name>
  <Style id="pathStyle">
    <LineStyle><color>ff00aaff</color><width>4</width></LineStyle>
  </Style>

  <Placemark>
    <name>Flight Path</name>
    <styleUrl>#pathStyle</styleUrl>
    <LineString>
      <tessellate>1</tessellate>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>
${coordString}
      </coordinates>
    </LineString>
  </Placemark>

  ${coords.map((c, i) => `
  <Placemark>
    <name>${names[i]}</name>
    <Point>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>${c[0]},${c[1]},${c[2]}</coordinates>
    </Point>
  </Placemark>
  `).join("")}

</Document>
</kml>
        `.trim();

        res.setHeader("Content-Type", "application/vnd.google-earth.kml+xml");
        res.setHeader("Content-Disposition", "attachment; filename=mission_path.kml");
        res.status(200).send(kml);

    } catch (e) {
        console.error(e);
        res.status(500).send("Internal error: " + e);
    }
}
