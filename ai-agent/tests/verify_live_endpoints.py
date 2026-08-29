import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from fastapi.testclient import TestClient
from app.main import app

def run_verification():
    client = TestClient(app)
    
    print("\n--- 1. Testing GET /api/v1/automation/detect ---")
    resp = client.get("/api/v1/automation/detect")
    assert resp.status_code == 200, f"Detect failed with {resp.status_code}: {resp.text}"
    detect_data = resp.json()
    print("Detect Status:", detect_data.get("status"))
    print("Summary:", json.dumps(detect_data.get("summary"), indent=2))
    print("Enabled Rules:", detect_data.get("enabled_rule_ids"))
    print("Certificate candidates count:", len(detect_data.get("candidates", {}).get("certificates", [])))
    if detect_data.get("candidates", {}).get("certificates"):
        print("Sample Certificate candidate:", json.dumps(detect_data["candidates"]["certificates"][0], indent=2))
    
    print("\n--- 2. Testing POST /api/v1/automation/trigger ---")
    resp = client.post("/api/v1/automation/trigger")
    assert resp.status_code == 200, f"Trigger failed with {resp.status_code}: {resp.text}"
    trigger_data = resp.json()
    print("Trigger Status:", trigger_data.get("status"))
    print("Planned Events Count:", trigger_data.get("planned_events_count"))
    print("Summary:", json.dumps(trigger_data.get("summary"), indent=2))

    print("\n--- 3. Testing GET /api/v1/notifications ---")
    resp = client.get("/api/v1/notifications?limit=5")
    assert resp.status_code == 200, f"Notifications failed with {resp.status_code}: {resp.text}"
    notif_data = resp.json()
    print("Notifications count returned:", len(notif_data))
    if notif_data:
        print("Sample Notification:", json.dumps(notif_data[0], indent=2, ensure_ascii=True))

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()
