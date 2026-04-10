# ── SENSOR PHYSICAL SPECS ─────────────────────────────────────
SENSOR_HEIGHT_CM             = 500
MAX_FLOOD_DEPTH_CM           = 35   # must be >= CRITICAL_DEPTH_CM (30)
RANGE_GATE_MIN               = SENSOR_HEIGHT_CM - MAX_FLOOD_DEPTH_CM  # 465
RANGE_GATE_MAX               = SENSOR_HEIGHT_CM                        # 500

# ── SAMPLING ──────────────────────────────────────────────────
SAMPLE_INTERVAL_NORMAL_S     = 300
SAMPLE_INTERVAL_ALERT_S      = 10
SNAPSHOTS_PER_WINDOW         = 500

# ── SIGNAL QUALITY ────────────────────────────────────────────
INTENSITY_THRESHOLD          = 0.35
SNAPSHOT_OUTLIER_CM          = 2.0
MIN_VALID_SNAPSHOTS          = 10
SATURATION_THRESHOLD         = 0.99
SUBMERSION_ZONE_BINS         = 10
SUBMERSION_RATIO             = 0.5

# ── ALERT THRESHOLDS ──────────────────────────────────────────
WATCH_DEPTH_CM               = 2.0
WARNING_DEPTH_CM             = 10.0
CRITICAL_DEPTH_CM            = 30.0
WARNING_RATE_CM_PER_MIN      = 5.0
CRITICAL_RATE_CM_PER_MIN     = 10.0

# ── HISTORY ───────────────────────────────────────────────────
HISTORY_WINDOW               = 12