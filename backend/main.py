from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .database import get_connection

app = FastAPI(title="UrbanSense AI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE / "frontend"), name="static")

@app.get("/")
def home():
    return FileResponse(BASE / "frontend" / "dashboard.html")

class Detection(BaseModel):
    bus_id: str = "BUS-101"
    cars: int = 0
    buses: int = 0
    trucks: int = 0
    motorcycles: int = 0
    bicycles: int = 0
    persons: int = 0
    latitude: float = 11.0168
    longitude: float = 76.9558
    confidence: float = Field(0.0, ge=0, le=1)

class Event(BaseModel):
    bus_id: str = "BUS-101"
    event_type: str
    severity: str = "MEDIUM"
    confidence: float = Field(0.0, ge=0, le=1)
    latitude: float = 11.0168
    longitude: float = 76.9558
    description: str = ""

def level(total):
    if total >= 25:
        return "HIGH"
    if total >= 12:
        return "MEDIUM"
    return "LOW"

@app.get("/api/health")
def health():
    return {"status": "OK", "service": "UrbanSense AI"}

@app.post("/api/detections")
def add_detection(d: Detection):
    total = d.cars + d.buses + d.trucks + d.motorcycles + d.bicycles
    traffic = level(total)
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute(
            """INSERT INTO detections
            (bus_id,cars,buses,trucks,motorcycles,bicycles,persons,total_vehicles,
             traffic_level,latitude,longitude,confidence)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (d.bus_id,d.cars,d.buses,d.trucks,d.motorcycles,d.bicycles,
             d.persons,total,traffic,d.latitude,d.longitude,d.confidence)
        )
        con.commit()
        cur.close()
        con.close()
        return {"message":"Detection stored","total_vehicles":total,"traffic_level":traffic}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/events")
def add_event(e: Event):
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute(
            """INSERT INTO events
            (bus_id,event_type,severity,confidence,latitude,longitude,description)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (e.bus_id,e.event_type,e.severity,e.confidence,e.latitude,
             e.longitude,e.description)
        )
        con.commit()
        event_id = cur.lastrowid
        cur.close()
        con.close()
        return {"message":"Event stored","event_id":event_id}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/stats")
def stats():
    try:
        con = get_connection()
        cur = con.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) c FROM buses WHERE status='ACTIVE'")
        buses = cur.fetchone()["c"]

        cur.execute("SELECT COALESCE(SUM(total_vehicles),0) c FROM detections WHERE detected_at >= NOW()-INTERVAL 1 DAY")
        vehicles = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) c FROM events WHERE detected_at >= NOW()-INTERVAL 1 DAY")
        events = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) c FROM events WHERE event_type='POTHOLE' AND detected_at >= NOW()-INTERVAL 1 DAY")
        potholes = cur.fetchone()["c"]

        cur.execute("""SELECT traffic_level,COUNT(*) c FROM detections
                       WHERE detected_at >= NOW()-INTERVAL 1 DAY
                       GROUP BY traffic_level""")
        traffic = {x["traffic_level"]:x["c"] for x in cur.fetchall()}

        cur.close()
        con.close()
        return {"active_buses":buses,"vehicles_24h":vehicles,
                "events_24h":events,"potholes_24h":potholes,"traffic":traffic}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/detections")
def detections():
    try:
        con = get_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM detections ORDER BY detected_at DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        con.close()
        return rows
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/events")
def events():
    try:
        con = get_connection()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM events ORDER BY detected_at DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        con.close()
        return rows
    except Exception as e:
        raise HTTPException(500, str(e))
