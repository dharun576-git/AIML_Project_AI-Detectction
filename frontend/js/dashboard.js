let map;
let eventMarkers = [];

const MAP_LAT = 11.0168;
const MAP_LON = 76.9558;


/* ==========================================
   INITIALIZE MAP
========================================== */

function initializeMap() {

    map = L.map("map").setView(
        [MAP_LAT, MAP_LON],
        12
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    L.marker([MAP_LAT, MAP_LON])
        .addTo(map)
        .bindPopup("UrbanSense AI - BUS-101")
        .openPopup();
}


/* ==========================================
   LOAD DASHBOARD STATISTICS
========================================== */

async function loadStats() {

    try {

        const response =
            await fetch("/api/stats");

        if (!response.ok) {
            throw new Error("Stats API failed");
        }

        const data =
            await response.json();

        document.getElementById("activeBuses").textContent =
            data.active_buses ?? 0;

        document.getElementById("vehicles24h").textContent =
            data.vehicles_24h ?? 0;

        document.getElementById("roadEvents").textContent =
            data.events_24h ?? 0;

        document.getElementById("potholes").textContent =
            data.potholes_24h ?? 0;

        document.getElementById("lowTraffic").textContent =
            data.traffic?.LOW ?? 0;

        document.getElementById("mediumTraffic").textContent =
            data.traffic?.MEDIUM ?? 0;

        document.getElementById("highTraffic").textContent =
            data.traffic?.HIGH ?? 0;

    } catch (error) {

        console.error(
            "Statistics loading error:",
            error
        );
    }
}


/* ==========================================
   FORMAT TIME
========================================== */

function formatTime(value) {

    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


/* ==========================================
   FORMAT DETECTION TIME
========================================== */

function formatDetectionTime(value) {

    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleTimeString();
}


/* ==========================================
   LOAD AI DETECTIONS
========================================== */

async function loadDetections() {

    try {

        const response =
            await fetch("/api/detections");

        if (!response.ok) {
            throw new Error("Detection API failed");
        }

        const detections =
            await response.json();

        const tbody =
            document.getElementById(
                "detectionTableBody"
            );

        if (!tbody) {
            console.error(
                "detectionTableBody not found"
            );
            return;
        }

        if (
            !detections ||
            detections.length === 0
        ) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="10">
                        No AI detections available
                    </td>
                </tr>
            `;

            return;
        }


        tbody.innerHTML =
            detections.map(detection => {

                const cars =
                    Number(detection.cars || 0);

                const buses =
                    Number(detection.buses || 0);

                const trucks =
                    Number(detection.trucks || 0);

                const motorcycles =
                    Number(detection.motorcycles || 0);

                const bicycles =
                    Number(detection.bicycles || 0);

                const persons =
                    Number(detection.persons || 0);

                const total =
                    Number(
                        detection.total_vehicles ||
                        (
                            cars +
                            buses +
                            trucks +
                            motorcycles +
                            bicycles
                        )
                    );

                const traffic =
                    detection.traffic_level ||
                    "LOW";

                const trafficClass =
                    traffic.toLowerCase();


                return `
                    <tr>

                        <td>
                            ${escapeHTML(
                                detection.bus_id ||
                                "BUS-101"
                            )}
                        </td>

                        <td>
                            ${cars}
                        </td>

                        <td>
                            ${buses}
                        </td>

                        <td>
                            ${trucks}
                        </td>

                        <td>
                            ${motorcycles}
                        </td>

                        <td>
                            ${bicycles}
                        </td>

                        <td>
                            ${persons}
                        </td>

                        <td>
                            <strong>
                                ${total}
                            </strong>
                        </td>

                        <td>
                            <span class="traffic-${trafficClass}">
                                ${escapeHTML(traffic)}
                            </span>
                        </td>

                        <td>
                            ${formatDetectionTime(
                                detection.detected_at
                            )}
                        </td>

                    </tr>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "Detection loading error:",
            error
        );
    }
}


/* ==========================================
   LOAD ROAD EVENTS
========================================== */

async function loadEvents() {

    try {

        const response =
            await fetch("/api/events");

        if (!response.ok) {
            throw new Error("Events API failed");
        }

        const events =
            await response.json();

        const tbody =
            document.getElementById(
                "eventTableBody"
            );

        if (!tbody) {
            return;
        }

        if (
            !events ||
            events.length === 0
        ) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="6">
                        No road events detected
                    </td>
                </tr>
            `;

            return;
        }


        tbody.innerHTML =
            events.map(event => {

                const eventType =
                    event.event_type || "-";

                let eventClass = "";

                if (
                    eventType ===
                    "POTENTIAL_COLLISION"
                ) {
                    eventClass =
                        "event-potential";
                }

                if (
                    eventType === "POTHOLE"
                ) {
                    eventClass =
                        "event-pothole";
                }


                const confidence =
                    event.confidence != null
                        ? Math.round(
                            event.confidence * 100
                        ) + "%"
                        : "-";


                const location =
                    event.latitude != null &&
                    event.longitude != null
                        ? `${Number(event.latitude).toFixed(4)}, ${Number(event.longitude).toFixed(4)}`
                        : "-";


                return `
                    <tr>

                        <td>
                            <span class="${eventClass}">
                                ${escapeHTML(eventType)}
                            </span>
                        </td>

                        <td>
                            ${escapeHTML(
                                event.bus_id ||
                                "BUS-101"
                            )}
                        </td>

                        <td>
                            ${escapeHTML(
                                event.severity ||
                                "-"
                            )}
                        </td>

                        <td>
                            ${confidence}
                        </td>

                        <td>
                            ${location}
                        </td>

                        <td>
                            ${formatTime(
                                event.detected_at
                            )}
                        </td>

                    </tr>
                `;

            }).join("");


        updateCollisionAlert(events);

        updateEventMarkers(events);

    } catch (error) {

        console.error(
            "Event loading error:",
            error
        );
    }
}


/* ==========================================
   COLLISION ALERT
========================================== */

function updateCollisionAlert(events) {

    const alert =
        document.getElementById(
            "collisionAlert"
        );

    const text =
        document.getElementById(
            "collisionText"
        );

    if (!alert || !text) {
        return;
    }


    const collision =
        events.find(
            event =>
                event.event_type ===
                "POTENTIAL_COLLISION"
        );


    if (collision) {

        alert.classList.remove(
            "hidden"
        );

        const confidence =
            collision.confidence != null
                ? Math.round(
                    collision.confidence * 100
                )
                : 0;

        text.textContent =
            `Potential collision risk detected. ` +
            `Confidence: ${confidence}%. ` +
            `Sensing bus: ${collision.bus_id || "BUS-101"}.`;

    } else {

        alert.classList.add(
            "hidden"
        );
    }
}


/* ==========================================
   MAP EVENT MARKERS
========================================== */

function updateEventMarkers(events) {

    if (!map) {
        return;
    }


    eventMarkers.forEach(marker => {

        map.removeLayer(marker);

    });

    eventMarkers = [];


    events.forEach(event => {

        if (
            event.latitude == null ||
            event.longitude == null
        ) {
            return;
        }


        let markerText =
            event.event_type || "EVENT";


        if (
            event.event_type ===
            "POTENTIAL_COLLISION"
        ) {

            markerText =
                "POTENTIAL COLLISION";

        }


        const marker =
            L.marker([
                Number(event.latitude),
                Number(event.longitude)
            ])
            .addTo(map)
            .bindPopup(
                `<strong>${escapeHTML(markerText)}</strong><br>` +
                `Bus: ${escapeHTML(event.bus_id || "BUS-101")}<br>` +
                `Severity: ${escapeHTML(event.severity || "-")}`
            );


        eventMarkers.push(marker);

    });
}


/* ==========================================
   DEMO POTHOLE EVENT
========================================== */

async function createDemoPothole() {

    const button =
        document.getElementById(
            "demoPotholeButton"
        );

    if (button) {
        button.disabled = true;
        button.textContent =
            "Sending...";
    }


    const event = {

        bus_id: "BUS-101",

        event_type: "POTHOLE",

        severity: "HIGH",

        confidence: 0.92,

        lat: 11.0168,

        lon: 76.9558,

        description:
            "Demo pothole detected"

    };


    try {

        const response =
            await fetch(
                "/api/events",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(event)
                }
            );


        if (!response.ok) {

            const error =
                await response.text();

            throw new Error(error);
        }


        await loadStats();

        await loadEvents();

    } catch (error) {

        console.error(
            "Demo event error:",
            error
        );

        alert(
            "Could not create demo event."
        );

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Demo Pothole Event";
        }
    }
}


/* ==========================================
   HTML SECURITY
========================================== */

function escapeHTML(value) {

    if (value === null ||
        value === undefined) {

        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* ==========================================
   INITIALIZE
========================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeMap();

        loadStats();

        loadEvents();

        loadDetections();


        const button =
            document.getElementById(
                "demoPotholeButton"
            );

        if (button) {

            button.addEventListener(
                "click",
                createDemoPothole
            );
        }


        setInterval(
            loadStats,
            3000
        );

        setInterval(
            loadEvents,
            3000
        );

        setInterval(
            loadDetections,
            3000
        );

    }
);