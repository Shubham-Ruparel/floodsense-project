import numpy as np
import json

SENSOR_HEIGHT_CM  = 500
PROFILE_LENGTH    = 501   # bins 0 to 500
INTENSITY_SIGNAL  = 0.8   # strong reflection intensity
INTENSITY_NOISE   = 0.05  # background noise level


def make_profile(reflection_bin, noise_std=0.5):
    """
    Create one range profile with peak at reflection_bin.
    Everything else is low noise.
    """
    profile = np.random.normal(INTENSITY_NOISE, 0.02, PROFILE_LENGTH)
    profile = np.clip(profile, 0, 1)

    # Add strong reflection at target bin
    profile[reflection_bin] = INTENSITY_SIGNAL + np.random.normal(0, noise_std * 0.01)
    profile[reflection_bin] = np.clip(profile[reflection_bin], 0, 1)

    return profile.tolist()


def generate_scenario(name, n_snapshots, base_distance_cm,
                      noise_std, description, **kwargs):
    print(f"\nGenerating: {description}")
    profiles = []

    for i in range(n_snapshots):

        # ── Normal / water scenarios ───────────────────────────
        if name in ("normal_dry", "slight_wet", "watch",
                    "warning", "critical"):
            reflection_bin = int(base_distance_cm +
                                 np.random.normal(0, noise_std))
            reflection_bin = np.clip(reflection_bin, 0, PROFILE_LENGTH - 1)
            profiles.append(make_profile(reflection_bin, noise_std))

        # ── Person standing entire 10 seconds ─────────────────
        elif name == "person_standing":
            # Person head at 330cm — outside range gate 480-500
            # Ground water at 498cm — inside range gate
            profile = np.random.normal(INTENSITY_NOISE, 0.02, PROFILE_LENGTH)
            profile = np.clip(profile, 0, 1)
            profile[330] = 0.7   # person head — will be ignored by range gate
            profile[498] = 0.8   # ground — 2cm water
            profiles.append(profile.tolist())

        # ── Vehicle passing snapshot 200-250 ──────────────────
        elif name == "vehicle_passing":
            profile = np.random.normal(INTENSITY_NOISE, 0.02, PROFILE_LENGTH)
            profile = np.clip(profile, 0, 1)
            if 200 <= i <= 250:
                profile[50] = 0.9    # vehicle roof very close — outside range gate
            profile[498] = 0.8       # ground — 2cm water always present
            profiles.append(profile.tolist())

        # ── Rising water — each snapshot slightly deeper ───────
        elif name == "rising_water":
            # Water rises 1cm across entire 10 second window
            rise = i * (1.0 / n_snapshots)
            reflection_bin = int(base_distance_cm - rise +
                                 np.random.normal(0, noise_std))
            reflection_bin = np.clip(reflection_bin, 480, 500)
            profiles.append(make_profile(reflection_bin, noise_std))

        # ── Sensor submerged ───────────────────────────────────
        elif name == "sensor_submerged":
            profile = np.random.normal(INTENSITY_NOISE, 0.02, PROFILE_LENGTH)
            profile = np.clip(profile, 0, 1)
            profile[2] = 0.95    # strong reflection right at sensor
            profile[3] = 0.90
            profiles.append(profile.tolist())

        # ── Signal loss ────────────────────────────────────────
        elif name == "signal_loss":
            profile = np.random.normal(0.01, 0.005, PROFILE_LENGTH)
            profile = np.clip(profile, 0, 1)
            profiles.append(profile.tolist())

    return {"scenario": name, "description": description,
            "profiles": profiles}


# ── Generate all scenarios ────────────────────────────────────
scenarios = [
    ("normal_dry",       500, 500, 0.5, "Dry ground no water"),
    ("slight_wet",       500, 498, 0.5, "2cm water just wet ground"),
    ("watch",            500, 495, 0.5, "5cm water watch level"),
    ("warning",          500, 488, 0.5, "12cm water warning level"),
    ("critical",         500, 468, 0.5, "32cm water critical level"),
    ("person_standing",  500, 500, 0.5, "Person standing entire 10 seconds"),
    ("vehicle_passing",  500, 500, 0.5, "Vehicle passes at snapshot 200-250"),
    ("rising_water",     500, 499, 0.3, "Water slowly rising"),
    ("sensor_submerged", 500, 500, 0.5, "Sensor submerged"),
    ("signal_loss",      500, 500, 0.5, "Complete signal loss"),
]

all_data = []
for s in scenarios:
    result = generate_scenario(*s)
    all_data.append(result)

with open("dummy_data.json", "w") as f:
    json.dump(all_data, f)

print("\nDummy data saved to dummy_data.json")
print(f"Total scenarios: {len(all_data)}")