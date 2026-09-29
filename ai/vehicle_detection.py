import cv2
import time
import math
import argparse
import requests
from collections import defaultdict, deque
from ultralytics import YOLO

API_URL = "http://127.0.0.1:8000"
BUS_ID = "BUS-101"

LAT = 11.0168
LON = 76.9558

model = YOLO("yolo11n.pt")

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

ALL_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

positions = defaultdict(lambda: deque(maxlen=8))
pair_history = defaultdict(lambda: deque(maxlen=8))
last_warning = {}
last_api_send = 0

COLLISION_DISTANCE = 0.16
CLOSING_SPEED = 0.012
REQUIRED_FRAMES = 4
WARNING_COOLDOWN = 12


def distance(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2
    )


def send_detection(counts):
    global last_api_send

    now = time.time()

    if now - last_api_send < 2:
        return

    total = sum(counts.values())

    if total >= 25:
        traffic = "HIGH"
    elif total >= 12:
        traffic = "MEDIUM"
    else:
        traffic = "LOW"

    data = {
        "bus_id": BUS_ID,
        "cars": counts.get("car", 0),
        "buses": counts.get("bus", 0),
        "trucks": counts.get("truck", 0),
        "motorcycles": counts.get("motorcycle", 0),
        "bicycles": counts.get("bicycle", 0),
        "persons": counts.get("person", 0),
        "lat": LAT,
        "lon": LON,
        "confidence": 0.90
    }

    try:
        requests.post(
            f"{API_URL}/api/detections",
            json=data,
            timeout=2
        )
        last_api_send = now
    except Exception as e:
        print("Detection API error:", e)


def send_collision_event(confidence):
    data = {
        "bus_id": BUS_ID,
        "event_type": "POTENTIAL_COLLISION",
        "severity": "HIGH",
        "confidence": round(confidence, 2),
        "lat": LAT,
        "lon": LON,
        "description": "Potential collision risk detected from vehicle movement"
    }

    try:
        response = requests.post(
            f"{API_URL}/api/events",
            json=data,
            timeout=2
        )

        if response.status_code < 300:
            print("WARNING SENT: POTENTIAL_COLLISION")
        else:
            print("Event API error:", response.text)

    except Exception as e:
        print("Collision API error:", e)


def check_collision_risk(tracked):
    now = time.time()
    warning = None

    for vehicle_id, info in tracked.items():
        center = info["center"]

        positions[vehicle_id].append(center)

    ids = list(tracked.keys())

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):

            id1 = ids[i]
            id2 = ids[j]

            p1 = tracked[id1]["center"]
            p2 = tracked[id2]["center"]

            current_distance = distance(p1, p2)

            pair = tuple(sorted((id1, id2)))
            history = pair_history[pair]

            history.append(current_distance)

            if len(history) < REQUIRED_FRAMES:
                continue

            previous_distance = history[-REQUIRED_FRAMES]

            closing = previous_distance - current_distance

            normalized_distance = current_distance

            if (
                normalized_distance < COLLISION_DISTANCE
                and closing > CLOSING_SPEED
            ):
                recent = list(history)[-REQUIRED_FRAMES:]

                decreasing = all(
                    recent[k] >= recent[k + 1]
                    for k in range(len(recent) - 1)
                )

                if not decreasing:
                    continue

                last_time = last_warning.get(pair, 0)

                if now - last_time < WARNING_COOLDOWN:
                    continue

                confidence = 0.75

                if normalized_distance < 0.11:
                    confidence = 0.94
                elif normalized_distance < 0.14:
                    confidence = 0.88
                elif normalized_distance < 0.16:
                    confidence = 0.82

                last_warning[pair] = now

                warning = {
                    "id1": id1,
                    "id2": id2,
                    "confidence": confidence
                }

                send_collision_event(confidence)

    return warning


def main(source):
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("ERROR: Could not open video/camera")
        return

    print("UrbanSense Early Collision Detection Started")
    print("Press Q to exit")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Video ended.")
            break

        height, width = frame.shape[:2]

        results = model.track(
            frame,
            persist=True,
            classes=list(ALL_CLASSES.keys()),
            verbose=False
        )

        counts = {
            "car": 0,
            "bus": 0,
            "truck": 0,
            "motorcycle": 0,
            "bicycle": 0,
            "person": 0
        }

        tracked = {}

        result = results[0]

        if result.boxes is not None:

            boxes = result.boxes

            for i in range(len(boxes)):

                cls = int(boxes.cls[i].item())
                confidence = float(boxes.conf[i].item())

                if confidence < 0.40:
                    continue

                if cls not in ALL_CLASSES:
                    continue

                name = ALL_CLASSES[cls]
                counts[name] += 1

                x1, y1, x2, y2 = boxes.xyxy[i].tolist()

                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                track_id = None

                if boxes.id is not None:
                    track_id = int(boxes.id[i].item())

                if track_id is not None and cls in VEHICLE_CLASSES:

                    nx = cx / width
                    ny = cy / height

                    tracked[track_id] = {
                        "center": (nx, ny),
                        "class": name,
                        "confidence": confidence,
                        "box": (int(x1), int(y1), int(x2), int(y2))
                    }

        warning = check_collision_risk(tracked)

        annotated = result.plot()

        cv2.rectangle(
            annotated,
            (10, 10),
            (390, 65),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            annotated,
            "UrbanSense AI - Early Collision Detection",
            (20, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        if warning:

            cv2.rectangle(
                annotated,
                (10, 80),
                (480, 145),
                (0, 0, 255),
                -1
            )

            cv2.putText(
                annotated,
                "WARNING: POTENTIAL COLLISION",
                (25, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )

            cv2.putText(
                annotated,
                f"Confidence: {warning['confidence'] * 100:.0f}%",
                (25, 137),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

        send_detection(counts)

        cv2.imshow("UrbanSense AI - Early Accident Warning", annotated)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        default="0"
    )

    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    main(source)