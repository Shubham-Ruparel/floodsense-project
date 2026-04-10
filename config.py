# ── SENSOR PHYSICAL SPECS ─────────────────────────────────────
SENSOR_HEIGHT_CM             = 500   # 5 meter pole
MAX_FLOOD_DEPTH_CM           = 20    # max water depth we measure
RANGE_GATE_MIN               = SENSOR_HEIGHT_CM - MAX_FLOOD_DEPTH_CM  # 480
RANGE_GATE_MAX               = SENSOR_HEIGHT_CM                        # 500

# ── SAMPLING ──────────────────────────────────────────────────
SAMPLE_INTERVAL_NORMAL_S     = 300   # 5 minutes
SAMPLE_INTERVAL_ALERT_S      = 10    # 10 seconds when WARNING/CRITICAL
SNAPSHOTS_PER_WINDOW         = 500   # ~500 snapshots in 10 seconds

# ── SIGNAL QUALITY ────────────────────────────────────────────
INTENSITY_THRESHOLD          = 0.3   # ignore weak reflections
SNAPSHOT_OUTLIER_CM          = 2.0   # max depth change between consecutive snapshots
MIN_VALID_SNAPSHOTS          = 10    # need at least 10 valid snapshots per window
SATURATION_THRESHOLD         = 0.99  # at or above this = saturated signal
SUBMERSION_ZONE_BINS         = 10    # bins 0-10 = sensor submerging
SUBMERSION_RATIO             = 0.5   # 50% snapshots show submersion = fault

# ── ALERT THRESHOLDS ──────────────────────────────────────────
WATCH_DEPTH_CM               = 2.0
WARNING_DEPTH_CM             = 10.0
CRITICAL_DEPTH_CM            = 30.0
WARNING_RATE_CM_PER_MIN      = 5.0
CRITICAL_RATE_CM_PER_MIN     = 10.0

# ── HISTORY ───────────────────────────────────────────────────
HISTORY_WINDOW               = 12    # last 12 readings