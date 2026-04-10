"""
replay_csv.py

Use this when data transmission team gives you a CSV file.
Reads each row and sends to Flask server as if it were live ESP32 data.

Expected CSV format from data team:
  timestamp,distance_cm
  1234567890,497.2
  1234568190,496.8
  1234568490,495.1
"""

import csv
import json
import urllib.request
import time
import sys

SERVER_URL = "http://127.0.0.1:5001"

def send_distance(distance_cm):
    payload = json.dumps({"distance_cm": distance_cm}).encode()
    req     = urllib.request.Request(
        f"{SERVER_URL}/predict",
        data    = payload,
        headers = {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def replay(csv_file, delay_seconds=0):
    """
    csv_file: path to CSV from data team
    delay_seconds: 0 = replay instantly, 
                   300 = replay at real 5min intervals
    """
    print(f"\nReplaying {csv_file}\n{'-'*50}")

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            distance_cm = float(row["distance_cm"])
            timestamp   = row.get("timestamp", "N/A")

            response    = send_distance(distance_cm)

            print(f"Timestamp : {timestamp}")
            print(f"Distance  : {distance_cm}cm")
            print(f"Depth     : {response.get('water_depth_cm', 'N/A')}cm")
            print(f"Alert     : {response.get('alert', 'N/A')}")
            print(f"Rate      : {response.get('rate_of_rise', 'N/A')} cm/min")
            print(f"Next read : {response.get('next_reading_s', 'N/A')}s")
            reason = response.get('reason', '')
            if reason:
                print(f"Reason    : {reason}")
            print(f"{'-'*50}")

            if delay_seconds > 0:
                time.sleep(delay_seconds)

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "sensor_data.csv"
    replay(csv_file)