let map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",
    center: [-122.0312, 37.332],
    zoom: 14
});

let waypoints = [];

document.getElementById("addPoint").onclick = () => {
    let lat = parseFloat(document.getElementById("lat").value);
    let lon = parseFloat(document.getElementById("lon").value);
    let brg = parseFloat(document.getElementById("bearing").value);
    let dist = parseFloat(document.getElementById("distance").value);

    fetch("/api/generate_kml_status"); // keep backend warm

    fetch("/api/generate_csv_status");

    fetch(`/api/generate_point?lat=${lat}&lon=${lon}&bearing=${brg}&distance=${dist}`)
        .then(r => r.json())
        .then(pt => {
            waypoints.push(pt);

            new maplibregl.Marker({ color: "#4c8ef7" })
                .setLngLat([pt.lon, pt.lat])
                .addTo(map);
        });
};

document.getElementById("generateCSV").onclick = () => {
    fetch("/api/generate_csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ points: waypoints })
    })
        .then(res => res.blob())
        .then(blob => {
            let a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "waypoints.csv";
            a.click();
        });
};

document.getElementById("generateKML").onclick = () => {
    fetch("/api/generate_kml", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ points: waypoints })
    })
        .then(res => res.blob())
        .then(blob => {
            let a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "waypoints.kml";
            a.click();
        });
};
