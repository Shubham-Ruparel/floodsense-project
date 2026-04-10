from flask import Flask, request, jsonify
from collections import deque
import time

from config import (
    SENSOR_HEIGHT_CM, RANGE_GATE_MIN, HISTORY_WINDOW
)
from processing import process_10_second_window
from alerts import get_alert, get_next_interval

app = Flask(__name__)

# ── STATE ─────────────────────────────────────────────────────
depth_history        = deque(maxlen=HISTORY_WINDOW)
time_history         = deque(maxlen=HISTORY_WINDOW)
last_confirmed_depth = None   # None = no reading yet since server start


# ── HELPERS ───────────────────────────────────────────────────
def compute_rate_of_rise():
    if len(depth_history) < 2:
        return 0.0
    delta_depth = depth_history[-1] - depth_history[0]
    delta_time  = (time_history[-1] - time_history[0]) / 60
    if delta_time == 0:
        return 0.0
    return round(delta_depth / delta_time, 2)


# ── ENDPOINTS ─────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "FloodSense server running"})


@app.route('/predict', methods=['POST'])
def predict():
    """
    Accepts either:

    A) Raw profiles from ESP32:
       { "profiles": [[...], [...], ...] }

    B) Pre-processed distance for testing:
       { "distance_cm": 495.0 }
    """
    global last_confirmed_depth

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    now = time.time()

    # ── MODE A: Raw profiles ───────────────────────────────────
    if "profiles" in data:
        profiles = data["profiles"]

        if not isinstance(profiles, list) or len(profiles) == 0:
            return jsonify({"error": "profiles must be a non-empty list"}), 400

        depth_cm, status = process_10_second_window(profiles)

        # Processing failed — fault or insufficient data
        if depth_cm is None:

            # Submersion = implicit CRITICAL regardless of last depth
            if "SUBMERGED" in status:
                return jsonify({
                    "alert":               "CRITICAL",
                    "reason":              status,
                    "last_known_depth_cm": last_confirmed_depth,
                    "next_reading_s":      get_next_interval("SENSOR_FAULT"),
                    "action":              "SENSOR SUBMERGED — flood at sensor height"
                }), 200

            # All other faults
            return jsonify({
                "alert":               "SENSOR_FAULT",
                "reason":              status,
                "last_known_depth_cm": last_confirmed_depth,
                "next_reading_s":      get_next_interval("SENSOR_FAULT"),
                "action":              "Check sensor hardware"
            }), 200

    # ── MODE B: Pre-processed distance (testing) ───────────────
    elif "distance_cm" in data:
        distance_cm = float(data["distance_cm"])

        # Sensor submerged
        if distance_cm < 0:
            return jsonify({
                "alert":               "CRITICAL",
                "reason":              "SENSOR_SUBMERGED — negative distance",
                "last_known_depth_cm": last_confirmed_depth,
                "next_reading_s":      get_next_interval("SENSOR_FAULT"),
                "action":              "SENSOR SUBMERGED — flood at sensor height"
            }), 200

        # Sensor disconnected or miscalibrated
        if distance_cm > SENSOR_HEIGHT_CM + 20:
            return jsonify({
                "alert":               "SENSOR_FAULT",
                "reason":              f"Distance {distance_cm}cm exceeds pole height",
                "last_known_depth_cm": last_confirmed_depth,
                "next_reading_s":      get_next_interval("SENSOR_FAULT")
            }), 200

        # Object above ground — not water
        if distance_cm < RANGE_GATE_MIN:
            return jsonify({
                "alert":               "OBJECT_ABOVE_GROUND",
                "reason":              f"Reflection at {distance_cm}cm — object detected, not water",
                "last_known_depth_cm": last_confirmed_depth,
                "next_reading_s":      get_next_interval("NORMAL")
            }), 200

        depth_cm = max(0.0, round(SENSOR_HEIGHT_CM - distance_cm, 1))
        status   = "OK"

    else:
        return jsonify({"error": "Send either profiles or distance_cm"}), 400

    # ── UPDATE STATE ───────────────────────────────────────────
    last_confirmed_depth = depth_cm
    depth_history.append(depth_cm)
    time_history.append(now)

    rate          = compute_rate_of_rise()
    alert         = get_alert(depth_cm, rate)
    next_interval = get_next_interval(alert)

    return jsonify({
        "timestamp":         int(now),
        "water_depth_cm":    depth_cm,
        "rate_of_rise":      rate,
        "alert":             alert,
        "next_reading_s":    next_interval,
        "processing_status": status,
        "sensor_height_cm":  SENSOR_HEIGHT_CM
    })


@app.route('/status', methods=['GET'])
def status():
    """Dashboard polling endpoint"""
    if last_confirmed_depth is None:
        return jsonify({
            "message": "No readings received since server start",
            "alert":   "UNKNOWN"
        })

    rate  = compute_rate_of_rise()
    alert = get_alert(last_confirmed_depth, rate)

    return jsonify({
        "water_depth_cm":      last_confirmed_depth,
        "rate_of_rise":        rate,
        "alert":               alert,
        "readings_stored":     len(depth_history),
        "history_cm":          list(depth_history),
        "history_timestamps":  [int(t) for t in time_history]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)