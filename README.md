# UrbanSense AI

AI-powered mobile urban sensing prototype for public transport buses.

## Features
- YOLO vehicle detection and counting from webcam/video
- Traffic level estimation
- FastAPI backend
- MySQL storage
- Live dashboard
- Leaflet GIS map
- Road-defect event API ready for a custom pothole model

## Setup

1. Install Python 3.10+ and MySQL 8+.
2. Run `database/urbansense.sql` in MySQL.
3. Create a virtual environment:
   `python -m venv venv`
4. Activate it on Windows:
   `venv\Scripts\activate`
5. Install:
   `pip install -r backend/requirements.txt`
   `pip install -r ai/requirements.txt`
6. Edit `.env.example` and save a copy as `.env`.
7. Start the server:
   `uvicorn backend.main:app --reload`
8. Open http://127.0.0.1:8000
9. In another terminal run:
   `python ai/vehicle_detection.py --source 0`
   or
   `python ai/vehicle_detection.py --source videos/road_video.mp4`

The first YOLO run downloads `yolo11n.pt`.

## Demo road-defect event

The dashboard has a `Demo Pothole Event` button. It inserts a real event into MySQL and displays it on the GIS map.

For real pothole AI, train/export a YOLO model and place it at `ai/models/pothole.pt`, then connect its detections to `/api/events`.

## Architecture

Camera/video -> OpenCV -> YOLO -> vehicle counting -> FastAPI -> MySQL -> dashboard/GIS
