import numpy as np
import json

SENSOR_HEIGHT_CM   = 500
PROFILE_LENGTH     = 501    # bins 0 to 500
INTENSITY_SIGNAL   = 0.9    # strong clean signal
INTENSITY_NOISE    = 0.01   # very low background noise
NOISE_STD          = 0.005  # very tight noise distribution


def make_clean_profile(reflection_bin):
    """
    Clean profile — signal at one bin, everything else near zero.
    Realistic for 60GHz radar on flat water surface.
    """
    # Very low flat noise floor
    profile      = np.random.normal(INTENSITY_NOISE, NOISE_STD, PROFILE_LENGTH)
    profile      = np.clip(profile, 0, 1)

    # Strong clean peak at reflection bin only
    profile[reflection_bin]     = INTENSITY_SIGNAL
    profile[reflection_bin - 1] = 0.4   # slight spread either side
    profile[reflection_bin + 1] = 0.4   # realistic radar response

    return profile.tolist()


def generate_scenario(name, n_snapshots, water_depth_cm, description):
    """
    water_depth_cm → reflection_bin = SENSOR_HEIGHT - water_depth
    """
    print(f"  Generating: {description}")
    profiles          = []
    reflection_bin    = SENSOR_HEIGHT_CM - int(water_depth_cm)  # exact bin

    for i in range(n_snapshots):

        # ── Normal water scenarios ─────────────────────────────
        if name in ("normal_dry", "slight_wet", "watch",
                    "warning", "critical"):
            # Tiny jitter ±1 bin maximum — very clean
            jitter = int(np.random.choice([-1, 0, 0, 0, 1]))
            bin_   = np.clip(reflection_bin + jitter, 480, 500)
            profiles.append(make_clean_profile(bin_))

        # ── Person standing entire 10 seconds ─────────────────
        elif name == "person_standing":
            profile      = np.random.normal(INTENSITY_NOISE,
                                            NOISE_STD, PROFILE_LENGTH)
            profile      = np.clip(profile, 0, 1)
            # Person head at 330cm — outside range gate 480-500
            profile[330] = 0.9
            profile[329] = 0.4
            profile[331] = 0.4
            # Ground water at bin 498 (2cm water) — inside range gate
            profile[498] = INTENSITY_SIGNAL
            profile[497] = 0.4
            profile[499] = 0.4
            profiles.append(profile.tolist())

        # ── Vehicle passing snapshot 200-250 ──────────────────
        elif name == "vehicle_passing":
            profile      = np.random.normal(INTENSITY_NOISE,
                                            NOISE_STD, PROFILE_LENGTH)
            profile      = np.clip(profile, 0, 1)
            if 200 <= i <= 250:
                # Vehicle roof at 50cm from sensor — outside range gate
                profile[50]  = 0.9
                profile[49]  = 0.4
                profile[51]  = 0.4
            # Ground always has 2cm water
            profile[498] = INTENSITY_SIGNAL
            profile[497] = 0.4
            profile[499] = 0.4
            profiles.append(profile.tolist())

        # ── Rising water ───────────────────────────────────────
        elif name == "rising_water":
            # Water rises 1cm over entire 10 second window
            rise   = i * (1.0 / n_snapshots)
            bin_   = int(reflection_bin - rise)
            bin_   = np.clip(bin_, 480, 500)
            profiles.append(make_clean_profile(bin_))

        # ── Sensor submerged ───────────────────────────────────
        elif name == "sensor_submerged":
            profile     = np.random.normal(INTENSITY_NOISE,
                                           NOISE_STD, PROFILE_LENGTH)
            profile     = np.clip(profile, 0, 1)
            profile[2]  = 0.95   # reflection right at sensor
            profile[3]  = 0.90
            profile[1]  = 0.85
            profiles.append(profile.tolist())

        # ── Signal loss ────────────────────────────────────────
        elif name == "signal_loss":
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
    # name               snapshots  depth_cm  description
    ("normal_dry",       500,       0,        "Dry ground no water"),
    ("slight_wet",       500,       2,        "2cm water just wet ground"),
    ("watch",            500,       5,        "5cm water watch level"),
    ("warning",          500,       12,       "12cm water warning level"),
    ("critical",         500,       32,       "32cm water critical level"),
    ("person_standing",  500,       2,        "Person standing entire 10 seconds"),
    ("vehicle_passing",  500,       2,        "Vehicle passes at snapshot 200-250"),
    ("rising_water",     500,       1,        "Water slowly rising"),
    ("sensor_submerged", 500,       0,        "Sensor submerged"),
    ("signal_loss",      500,       0,        "Complete signal loss"),
]

print("\nGenerating clean dummy data...\n")
all_data = []
for s in scenarios:
    result = generate_scenario(*s)
    all_data.append(result)

with open("dummy_data.json", "w") as f:
    json.dump(all_data, f)

print(f"\nSaved dummy_data.json — {len(all_data)} scenarios")