import numpy as np
import json

SENSOR_HEIGHT_CM = 500
PROFILE_LENGTH   = 501       # bins 0 to 500 inclusive
INTENSITY_SIGNAL = 0.9
INTENSITY_NOISE  = 0.01
NOISE_STD        = 0.005


def make_clean_profile(reflection_bin):
    """
    Simulates what XM125 returns for one snapshot.
    Strong peak at reflection_bin, near-zero everywhere else.

    Why three bins (0.4, 0.9, 0.4)?
    Real radar has slight beam spread — not perfectly one bin.
    Signal leaks into adjacent bins. This is realistic.
    """
    profile = np.random.normal(INTENSITY_NOISE, NOISE_STD, PROFILE_LENGTH)
    profile = np.clip(profile, 0, 1)

    profile[reflection_bin] = INTENSITY_SIGNAL

    # Spread to adjacent bins only if within array bounds
    if reflection_bin - 1 >= 0:
        profile[reflection_bin - 1] = 0.4
    if reflection_bin + 1 < PROFILE_LENGTH:
        profile[reflection_bin + 1] = 0.4

    return profile.tolist()


def generate_scenario(name, n_snapshots, water_depth_cm, description):
    """
    water_depth_cm = how deep water is from ground
    reflection_bin = SENSOR_HEIGHT - water_depth
                   = where radar sees the reflection

    Examples:
      water_depth=0  → reflection_bin=500 → dry ground
      water_depth=5  → reflection_bin=495 → 5cm water
      water_depth=12 → reflection_bin=488 → 12cm water
    """
    print(f"  Generating: {description}")
    profiles       = []
    reflection_bin = SENSOR_HEIGHT_CM - int(water_depth_cm)
    reflection_bin = np.clip(reflection_bin, 1, PROFILE_LENGTH - 2)

    for i in range(n_snapshots):

        # ── Standard water/dry scenarios ──────────────────────
        if name in ("normal_dry", "slight_wet", "watch",
                    "warning", "critical"):
            """
            Tiny jitter ±1 bin — simulates natural
            surface variation and sensor measurement noise.
            Weighted so 0 (no jitter) happens most often.
            """
            jitter = int(np.random.choice([-1, 0, 0, 0, 0, 1]))
            bin_   = int(np.clip(reflection_bin + jitter, 1, PROFILE_LENGTH - 2))
            profiles.append(make_clean_profile(bin_))

        # ── Person standing entire 10 seconds ─────────────────
        elif name == "person_standing":
            """
            Person head at 170cm height from ground.
            Distance from sensor = 500 - 170 = 330cm → bin 330.
            bin 330 is BELOW RANGE_GATE_MIN (480).
            So person is completely outside ground zone → ignored.
            Ground water at 2cm → bin 498 → inside range gate → detected.

            This tests that range gate correctly ignores
            objects above ground level.
            """
            profile      = np.random.normal(INTENSITY_NOISE,
                                            NOISE_STD, PROFILE_LENGTH)
            profile      = np.clip(profile, 0, 1)
            profile[330] = 0.9    # person head — outside range gate
            profile[329] = 0.4
            profile[331] = 0.4
            profile[498] = 0.9    # 2cm water — inside range gate
            profile[497] = 0.4
            profile[499] = 0.4
            profiles.append(profile.tolist())

        # ── Vehicle passing snapshot 200 to 250 ───────────────
        elif name == "vehicle_passing":
            """
            Vehicle roof at ~50cm from sensor (very tall vehicle).
            Reflects at bin 50 — far outside range gate (480-500).
            Ground has 2cm water throughout.

            This tests that transient object in beam
            does not corrupt water depth reading.
            """
            profile      = np.random.normal(INTENSITY_NOISE,
                                            NOISE_STD, PROFILE_LENGTH)
            profile      = np.clip(profile, 0, 1)
            if 200 <= i <= 250:
                profile[50]  = 0.9   # vehicle — outside range gate
                profile[49]  = 0.4
                profile[51]  = 0.4
            profile[498] = 0.9       # 2cm water always present
            profile[497] = 0.4
            profile[499] = 0.4
            profiles.append(profile.tolist())

        # ── Rising water ───────────────────────────────────────
        elif name == "rising_water":
            """
            Water rises 1cm across entire 10 second window.
            Tests temporal averaging — final depth should be
            approximately 1.5cm (average of 1cm to 2cm rise).
            """
            rise   = i * (1.0 / n_snapshots)
            bin_   = int(np.clip(reflection_bin - rise, 1, PROFILE_LENGTH - 2))
            profiles.append(make_clean_profile(bin_))

        # ── Sensor submerged ───────────────────────────────────
        elif name == "sensor_submerged":
            """
            Water has reached sensor level.
            Radar sees strong reflection at bins 1-3
            (water surface right at sensor).
            detect_sensor_faults() catches this as SENSOR_SUBMERGED
            which maps to CRITICAL alert.
            """
            profile    = np.random.normal(INTENSITY_NOISE,
                                          NOISE_STD, PROFILE_LENGTH)
            profile    = np.clip(profile, 0, 1)
            profile[1] = 0.95
            profile[2] = 0.95
            profile[3] = 0.90
            profiles.append(profile.tolist())

        # ── Signal loss ────────────────────────────────────────
        elif name == "signal_loss":
            """
            Sensor disconnected or cable fault.
            All bins return near-zero intensity.
            detect_sensor_faults() catches this as SIGNAL_LOSS
            → SENSOR_FAULT alert.
            """
            profile = np.random.normal(0.005, 0.002, PROFILE_LENGTH)
            profile = np.clip(profile, 0, 1)
            profiles.append(profile.tolist())

    return {
        "scenario":          name,
        "description":       description,
        "expected_depth_cm": water_depth_cm,
        "profiles":          profiles
    }


# ── All scenarios ─────────────────────────────────────────────
scenarios = [
    # name               snapshots  depth  description
    ("normal_dry",       500,       0,     "Dry ground no water"),
    ("slight_wet",       500,       2,     "2cm water just wet ground"),
    ("watch",            500,       5,     "5cm water watch level"),
    ("warning",          500,       12,    "12cm water warning level"),
    ("critical",         500,       32,    "32cm water critical level"),
    ("person_standing",  500,       2,     "Person standing entire 10 seconds"),
    ("vehicle_passing",  500,       2,     "Vehicle passes at snapshot 200-250"),
    ("rising_water",     500,       1,     "Water slowly rising"),
    ("sensor_submerged", 500,       0,     "Sensor submerged"),
    ("signal_loss",      500,       0,     "Complete signal loss"),
]

print("\nGenerating clean dummy data...\n")
all_data = []
for s in scenarios:
    result = generate_scenario(*s)
    all_data.append(result)

with open("dummy_data.json", "w") as f:
    json.dump(all_data, f)

print(f"\nSaved to dummy_data.json — {len(all_data)} scenarios ready")