# FloodSense — Backend API

Real-time flood detection using XM125 60GHz radar + ESP32-S3.

## Setup
pip install -r requirements.txt
python app.py

## Endpoints

### POST /predict

**Option A — Raw profiles (production):**
{ "profiles": [[0.1, 0.2, ..., 0.9], [...], ...] }

**Option B — Pre-processed distance (testing):**
{ "distance_cm": 495.0 }

**Response:**
{
  "timestamp": 1234567890,
  "water_depth_cm": 5.0,
  "rate_of_rise": 0.5,
  "alert": "WATCH",
  "next_reading_s": 300,
  "sensor_height_cm": 500
}

### GET /status
Returns latest depth, alert, rate of rise, and full history.

## Alert Levels
| Alert    | Condition                                    |
|----------|----------------------------------------------|
| NORMAL   | depth < 2cm                                  |
| WATCH    | depth 2-10cm                                 |
| WARNING  | depth 10-30cm or rate > 5cm/min              |
| CRITICAL | depth > 30cm or rate > 10cm/min or submerged |
| SENSOR_FAULT | signal loss, saturation, hardware issue  |

## Processing Pipeline
1. Fault detection (submersion, signal loss, saturation)
2. Spatial average per snapshot — ground zone bins 480-500 only
3. Outlier snapshot removal — transient objects in beam
4. Temporal average — stable final depth value

## Repo Structure
FloodSense/
├── app.py           # Flask server + endpoints
├── processing.py    # Full signal processing pipeline
├── alerts.py        # Alert and sampling interval logic
├── config.py        # All tunable parameters in one place
├── requirements.txt
├── .gitignore
└── README.md

## ESP32 Integration
Read next_reading_s from response → set deep sleep timer.
Normal: 300s. Alert/Fault: 10s.