import numpy as np
from config import (
    SENSOR_HEIGHT_CM, RANGE_GATE_MIN, RANGE_GATE_MAX,
    INTENSITY_THRESHOLD, SNAPSHOT_OUTLIER_CM, MIN_VALID_SNAPSHOTS,
    SATURATION_THRESHOLD, SUBMERSION_ZONE_BINS, SUBMERSION_RATIO
)


def detect_sensor_faults(all_profiles):
    """
    Check for hardware/physical faults before any processing.
    Returns: (fault_detected: bool, reason: str)
    """
    if not all_profiles or len(all_profiles) == 0:
        return True, "EMPTY_PROFILE_LIST"

    total             = len(all_profiles)
    zero_signal_count = 0
    saturated_count   = 0
    submersion_count  = 0

    for profile in all_profiles:
        arr = np.array(profile)

        # Complete signal loss
        if np.max(arr) < INTENSITY_THRESHOLD:
            zero_signal_count += 1

        # Saturated signal
        if np.mean(arr) >= SATURATION_THRESHOLD:
            saturated_count += 1

        # Submersion — strong reflection very close to sensor
        near_slice = arr[0 : SUBMERSION_ZONE_BINS]
        if np.max(near_slice) > INTENSITY_THRESHOLD:
            submersion_count += 1

    if zero_signal_count > total * 0.8:
        return True, "SIGNAL_LOSS — sensor disconnected or obstructed"

    if saturated_count > total * 0.5:
        return True, "SIGNAL_SATURATED — sensor hardware fault"

    if submersion_count > total * SUBMERSION_RATIO:
        return True, "SENSOR_SUBMERGED — water has reached sensor height"

    return False, "OK"


def process_snapshot(profile):
    """
    Single range profile → single depth value.
    Only looks at bins within ground zone (RANGE_GATE_MIN to RANGE_GATE_MAX).
    Anything reflecting outside this zone (person, vehicle, animal)
    is physically above ground level and ignored.
    Returns depth_cm or None if no valid reflection found.
    """
    ground_slice = np.array(profile[RANGE_GATE_MIN : RANGE_GATE_MAX + 1])

    # Filter weak reflections — below threshold = noise
    strong_mask = ground_slice > INTENSITY_THRESHOLD
    if not np.any(strong_mask):
        return None

    # Spatial average of strong bins only
    strong_indices   = np.where(strong_mask)[0]
    strong_distances = strong_indices + RANGE_GATE_MIN
    avg_distance_cm  = float(np.mean(strong_distances))
    water_depth_cm   = SENSOR_HEIGHT_CM - avg_distance_cm

    return round(max(0.0, water_depth_cm), 2)


def filter_outlier_snapshots(depth_values):
    """
    Remove snapshots where depth jumps more than SNAPSHOT_OUTLIER_CM
    compared to previous valid snapshot.
    Water cannot rise 2cm in milliseconds — any such jump = transient
    object passing through beam during 10 second window.
    """
    if not depth_values:
        return []

    filtered = [depth_values[0]]  # first snapshot always kept as reference
    prev     = depth_values[0]

    for depth in depth_values[1:]:
        if abs(depth - prev) <= SNAPSHOT_OUTLIER_CM:
            filtered.append(depth)
            prev = depth
        # else: discard silently — transient object

    return filtered


def process_10_second_window(all_profiles):
    """
    Full pipeline: ~500 range profiles → single water depth reading.

    Step 1: Fault detection
    Step 2: Spatial average per snapshot (ground zone bins only)
    Step 3: Outlier snapshot removal
    Step 4: Temporal average across valid snapshots

    Returns: (depth_cm or None, status_string)
    """

    # Step 1 — Hardware fault detection first
    fault, reason = detect_sensor_faults(all_profiles)
    if fault:
        return None, reason

    # Step 2 — Spatial average per snapshot
    depth_per_snapshot = []
    for profile in all_profiles:
        depth = process_snapshot(profile)
        if depth is not None:
            depth_per_snapshot.append(depth)

    if len(depth_per_snapshot) == 0:
        return None, "NO_VALID_SNAPSHOTS — no ground reflection detected"

    # Step 3 — Remove outlier snapshots
    filtered = filter_outlier_snapshots(depth_per_snapshot)

    if len(filtered) < MIN_VALID_SNAPSHOTS:
        return None, (
            f"TOO_FEW_VALID_SNAPSHOTS "
            f"({len(filtered)}/{MIN_VALID_SNAPSHOTS})"
        )

    # Step 4 — Temporal average
    final_depth = round(float(np.mean(filtered)), 1)
    return final_depth, "OK"