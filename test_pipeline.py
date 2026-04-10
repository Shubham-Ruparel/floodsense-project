import json
import urllib.request

SERVER_URL = "http://127.0.0.1:5001"

# ── Colours for terminal output ───────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

def color_alert(alert):
    colors = {
        "NORMAL":            GREEN,
        "WATCH":             BLUE,
        "WARNING":           YELLOW,
        "CRITICAL":          RED,
        "SENSOR_FAULT":      RED,
        "OBJECT_ABOVE_GROUND": YELLOW,
    }
    return colors.get(alert, RESET) + alert + RESET

def post_predict(payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{SERVER_URL}/predict",
        data    = data,
        headers = {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_status():
    with urllib.request.urlopen(f"{SERVER_URL}/status") as resp:
        return json.loads(resp.read().decode())

# ── Expected results for each scenario ───────────────────────
EXPECTED = {
    "normal_dry":       "NORMAL",
    "slight_wet":       "WATCH",
    "watch":            "WATCH",
    "warning":          "WARNING",
    "critical":         "CRITICAL",
    "person_standing":  "WATCH",      # person ignored, sees 2cm water
    "vehicle_passing":  "WATCH",      # vehicle ignored, sees 2cm water
    "rising_water":     "WATCH",      # small rise, still low depth
    "sensor_submerged": "CRITICAL",   # submerged = critical
    "signal_loss":      "SENSOR_FAULT"
}

# ── Run tests ─────────────────────────────────────────────────
def run_tests():
    print(f"\n{'='*60}")
    print("  FloodSense Pipeline Tests")
    print(f"{'='*60}\n")

    with open("dummy_data.json", "r") as f:
        all_scenarios = json.load(f)

    passed = 0
    failed = 0

    for scenario in all_scenarios:
        name        = scenario["scenario"]
        description = scenario["description"]
        profiles    = scenario["profiles"]
        expected    = EXPECTED.get(name, "UNKNOWN")

        try:
            response = post_predict({"profiles": profiles})

            alert        = response.get("alert", "UNKNOWN")
            depth        = response.get("water_depth_cm",    
                           response.get("last_known_depth_cm", "N/A"))
            rate         = response.get("rate_of_rise", "N/A")
            next_s       = response.get("next_reading_s", "N/A")
            reason       = response.get("reason", "")
            status_str   = response.get("processing_status", "")

            result = "PASS" if alert == expected else "FAIL"
            if result == "PASS":
                passed += 1
            else:
                failed += 1

            result_color = GREEN if result == "PASS" else RED

            print(f"Scenario   : {name}")
            print(f"Description: {description}")
            print(f"Expected   : {color_alert(expected)}")
            print(f"Got        : {color_alert(alert)}")
            print(f"Depth      : {depth} cm")
            print(f"Rate       : {rate} cm/min")
            print(f"Next read  : {next_s}s")
            if reason:
                print(f"Reason     : {reason}")
            if status_str:
                print(f"Status     : {status_str}")
            print(f"Result     : {result_color}{result}{RESET}")
            print(f"{'-'*60}")

        except Exception as e:
            failed += 1
            print(f"Scenario : {name}")
            print(f"{RED}ERROR: {e}{RESET}")
            print(f"{'-'*60}")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Results: {GREEN}{passed} PASSED{RESET} / {RED}{failed} FAILED{RESET}")
    print(f"{'='*60}\n")

    # ── Final server status ───────────────────────────────────
    print("Server /status after all tests:")
    status = get_status()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    run_tests()