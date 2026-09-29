# Pothole model integration template.
# Train/export a YOLO road-defect model and save it as:
# ai/models/pothole.pt
#
# When a pothole is detected, POST:
#
# {
#   "bus_id":"BUS-101",
#   "event_type":"POTHOLE",
#   "severity":"HIGH",
#   "confidence":0.92,
#   "latitude":11.0168,
#   "longitude":76.9558,
#   "description":"Pothole detected by onboard camera"
# }
#
# Endpoint:
# POST http://127.0.0.1:8000/api/events
