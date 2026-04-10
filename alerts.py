from config import (
    WATCH_DEPTH_CM, WARNING_DEPTH_CM, CRITICAL_DEPTH_CM,
    WARNING_RATE_CM_PER_MIN, CRITICAL_RATE_CM_PER_MIN,
    SAMPLE_INTERVAL_NORMAL_S, SAMPLE_INTERVAL_ALERT_S
)


def get_alert(depth_cm, rate_cm_per_min):
    """
    SENSOR_SUBMERGED is handled in app.py before this is called.
    This only handles normal depth/rate based alerting.
    """
    if (depth_cm  >= CRITICAL_DEPTH_CM or
            rate_cm_per_min >= CRITICAL_RATE_CM_PER_MIN):
        return "CRITICAL"

    elif (depth_cm  >= WARNING_DEPTH_CM or
              rate_cm_per_min >= WARNING_RATE_CM_PER_MIN):
        return "WARNING"

    elif depth_cm >= WATCH_DEPTH_CM:
        return "WATCH"

    else:
        return "NORMAL"


def get_next_interval(alert):
    """
    Tell ESP32 how long to sleep before next reading.
    CRITICAL/WARNING → 10 seconds (rapid sampling)
    WATCH/NORMAL     → 5 minutes  (duty cycle)
    SENSOR_FAULT     → 10 seconds (keep checking if fault clears)
    """
    if alert in ("CRITICAL", "WARNING", "SENSOR_FAULT"):
        return SAMPLE_INTERVAL_ALERT_S
    return SAMPLE_INTERVAL_NORMAL_S