"""
Cardiastracont Telemetry Simulator
Simulates continuous Apple Watch biometric streaming with selectable anomaly scenarios.
Optimized for 40 RPM (Requests Per Minute = 1.5s interval) transmission.
"""

import time
import random
import requests
import sys
from datetime import datetime, timezone

SERVER_URL = "http://127.0.0.1:8000/api/telemetry"
EMERGENCY_URL = "http://127.0.0.1:8000/api/emergency-trigger"

# Comprehensive 7 Space Health Scenarios
PROFILES = {
    "1": {
        "name": "🟢 Nominal Deep-Space Cruise",
        "hr_base": 72.0, "hr_var": 3.0,
        "o2_base": 98.5, "o2_var": 0.5,
        "ambient_o2": 20.9, "ppo2": 21.2,
        "stress_base": 22.0, "stress_var": 4.0,
        "co2_base": 420.0, "co2_var": 20.0,
        "ecg_class": "SINUS_RHYTHM",
        "cam_pallor": "NORMAL", "cam_perclos": 0.06, "cam_gaze": "FOCUSED", "cam_expr": "ALERT",
        "sos": False
    },
    "2": {
        "name": "🔴 Critical Hypoxia & Suit Puncture",
        "hr_base": 118.0, "hr_var": 5.0,
        "o2_base": 79.5, "o2_var": 2.0,
        "ambient_o2": 13.8, "ppo2": 12.1,
        "stress_base": 88.0, "stress_var": 4.0,
        "co2_base": 470.0, "co2_var": 25.0,
        "ecg_class": "SINUS_TACHYCARDIA",
        "cam_pallor": "CYANOTIC", "cam_perclos": 0.44, "cam_gaze": "ERRATIC", "cam_expr": "DROWSY",
        "sos": False
    },
    "3": {
        "name": "⚡ Acute Paroxysmal Atrial Fibrillation (AFib)",
        "hr_base": 148.0, "hr_var": 12.0,
        "o2_base": 94.0, "o2_var": 1.5,
        "ambient_o2": 20.8, "ppo2": 21.0,
        "stress_base": 91.0, "stress_var": 3.0,
        "co2_base": 435.0, "co2_var": 15.0,
        "ecg_class": "ATRIAL_FIBRILLATION",
        "cam_pallor": "PALE", "cam_perclos": 0.12, "cam_gaze": "FOCUSED", "cam_expr": "DISTRESSED",
        "sos": False
    },
    "4": {
        "name": "🟣 ECLSS Scrubbing Fail: Hypercapnia (CO2 Buildup)",
        "hr_base": 112.0, "hr_var": 4.0,
        "o2_base": 92.5, "o2_var": 1.5,
        "ambient_o2": 19.4, "ppo2": 19.8,
        "stress_base": 82.0, "stress_var": 4.0,
        "co2_base": 3400.0, "co2_var": 120.0,
        "ecg_class": "SINUS_TACHYCARDIA",
        "cam_pallor": "FLUSHED", "cam_perclos": 0.35, "cam_gaze": "ERRATIC", "cam_expr": "DISTRESSED",
        "sos": False
    },
    "5": {
        "name": "👁️ Cognitive Collapse & Microsleep (Extreme Fatigue)",
        "hr_base": 48.0, "hr_var": 2.5,
        "o2_base": 96.0, "o2_var": 1.0,
        "ambient_o2": 20.9, "ppo2": 21.2,
        "stress_base": 30.0, "stress_var": 5.0,
        "co2_base": 480.0, "co2_var": 20.0,
        "ecg_class": "SINUS_BRADYCARDIA",
        "cam_pallor": "NORMAL", "cam_perclos": 0.82, "cam_gaze": "UNRESPONSIVE", "cam_expr": "UNCONSCIOUS",
        "sos": False
    },
    "6": {
        "name": "🌀 Space Adaptation Syndrome (SAS / Severe Nausea)",
        "hr_base": 102.0, "hr_var": 6.0,
        "o2_base": 98.0, "o2_var": 0.8,
        "ambient_o2": 20.9, "ppo2": 21.2,
        "stress_base": 95.0, "stress_var": 2.5,
        "co2_base": 440.0, "co2_var": 15.0,
        "ecg_class": "SINUS_RHYTHM",
        "cam_pallor": "PALE", "cam_perclos": 0.22, "cam_gaze": "NYSTAGMUS", "cam_expr": "DISTRESSED",
        "sos": False
    },
    "7": {
        "name": "🔥 EVA Suit Thermal Loop Pump Failure (Heat Exhaustion)",
        "hr_base": 168.0, "hr_var": 7.0,
        "o2_base": 95.0, "o2_var": 1.2,
        "ambient_o2": 21.0, "ppo2": 21.3,
        "stress_base": 97.0, "stress_var": 2.0,
        "co2_base": 510.0, "co2_var": 30.0,
        "ecg_class": "SINUS_TACHYCARDIA",
        "cam_pallor": "FLUSHED", "cam_perclos": 0.28, "cam_gaze": "ERRATIC", "cam_expr": "DISTRESSED",
        "sos": True
    }
}

def generate_synthetic_ecg_samples(hr: float, classification: str, num_samples: int = 30) -> list:
    """Generates synthetic Lead I voltage points (mV) matching Apple Watch resolution."""
    samples = []
    cycle_length = max(10, int(60.0 / max(40.0, hr) * 20))
    for i in range(num_samples):
        phase = (i % cycle_length) / float(cycle_length)
        if classification == "ATRIAL_FIBRILLATION":
            # Chaotic baseline with sharp irregular QRS
            val = random.uniform(-0.15, 0.15)
            if 0.45 < phase < 0.55:
                val += random.choice([1.2, 0.9, -0.6])
        else:
            # Normal P-QRS-T complex
            if 0.15 < phase < 0.25:
                val = 0.15  # P wave
            elif 0.45 < phase < 0.48:
                val = -0.2  # Q dip
            elif 0.48 < phase < 0.52:
                val = 1.4   # R spike
            elif 0.52 < phase < 0.55:
                val = -0.35 # S drop
            elif 0.65 < phase < 0.80:
                val = 0.3   # T wave
            else:
                val = random.uniform(-0.03, 0.03)  # isoelectric baseline
        samples.append(round(val, 3))
    return samples

def print_menu():
    print("\n" + "=" * 65)
    print("🛰️  CARDIASTRACONT APPLE WATCH BIOMETRIC STREAM SIMULATOR (40 RPM)")
    print("=" * 65)
    for key, p in PROFILES.items():
        print(f"  [{key}] {p['name']}")
    print("  [q] Quit")
    print("=" * 65)

def run_stream(profile_key="1", stream_rate_rpm=40.0):
    p = PROFILES.get(profile_key, PROFILES["1"])
    interval_seconds = 60.0 / stream_rate_rpm  # 1.5 seconds for 40 RPM
    print(f"\n📡 Active Profile: {p['name']}")
    print(f"🚀 Streaming to {SERVER_URL} at {stream_rate_rpm:.0f} RPM ({interval_seconds:.1f}s interval)...")
    print(f"   (Press Ctrl+C to switch scenario)\n")

    try:
        while True:
            # Generate realistic synthetic biometric data
            hr = round(p["hr_base"] + random.gauss(0, p["hr_var"]), 1)
            o2 = round(min(100.0, max(60.0, p["o2_base"] + random.gauss(0, p["o2_var"]))), 1)
            stress = round(min(100.0, max(0.0, p["stress_base"] + random.gauss(0, p["stress_var"]))), 1)
            co2 = round(max(300.0, p["co2_base"] + random.gauss(0, p["co2_var"])), 0)
            hrv = round(max(10.0, 110.0 - (stress * 0.9) + random.gauss(0, 3)), 1)

            payload = {
                "astronaut_id": "ASTRO-01 (Cmdr. Hayes)",
                "heart_rate": hr,
                "oxygen": o2,
                "stress_level": stress,
                "hrv": hrv,
                "co2_level_ppm": co2,
                "ecg_lead": "LEAD_I_APPLE_WATCH",
                "ecg_classification": p.get("ecg_class", "SINUS_RHYTHM"),
                "ecg_voltage_samples": generate_synthetic_ecg_samples(hr, p.get("ecg_class", "SINUS_RHYTHM")),
                "ambient_o2_percent": p.get("ambient_o2", 20.9),
                "o2_partial_pressure_kpa": p.get("ppo2", 21.2),
                "camera_telemetry": {
                    "facial_pallor": p.get("cam_pallor", "NORMAL"),
                    "eye_perclos": p.get("cam_perclos", 0.08),
                    "pupil_dilation_mm": 3.8 if p.get("cam_expr") != "DISTRESSED" else 6.2,
                    "gaze_stability": p.get("cam_gaze", "FOCUSED"),
                    "expression_state": p.get("cam_expr", "ALERT"),
                    "camera_active": True
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "apple_watch_series_9",
                "is_emergency_triggered": p["sos"]
            }

            try:
                t0 = time.perf_counter()
                res = requests.post(SERVER_URL, json=payload, timeout=2.0)
                latency_ms = (time.perf_counter() - t0) * 1000

                if res.status_code == 200:
                    data = res.json()
                    eval_data = data.get("processed", {}).get("evaluation", {})
                    severity = eval_data.get("severity", "NOMINAL")
                    triage = data.get("processed", {}).get("triage")

                    status_icon = "🟢" if severity == "NOMINAL" else ("🟠" if severity == "WARNING" else "🚨")
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} 40 RPM | "
                        f"HR: {hr:5.1f} | ECG: {p.get('ecg_class', 'SINUS'):<19} | SpO2: {o2:4.1f}% | "
                        f"O2: {p.get('ambient_o2', 20.9):4.1f}% | CAM: {p.get('cam_pallor', 'NORM'):<8} | "
                        f"Status: {severity:<8} | RTT: {latency_ms:4.1f}ms"
                    )

                    if triage:
                        print("\n" + "!" * 65)
                        print(f"🔥 AI MEDICAL TRIAGE ALERT [{triage['source'].upper()}] - {triage['condition_title']}")
                        print(f"   Diagnosis: {triage['diagnosis']}")
                        print(f"   Immediate Actions:")
                        for act in triage.get("immediate_actions", []):
                            print(f"    - {act}")
                        if triage.get("sanctuary_recommended"):
                            print("   🧘 VR Sanctuary Mode: RECOMMENDED ACTIVATION")
                        print("!" * 65 + "\n")

                else:
                    print(f"❌ Server Error {res.status_code}: {res.text}")

            except requests.exceptions.RequestException as e:
                print(f"⚠️  Connection failed to {SERVER_URL}: {e}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nScenario paused.")

def main():
    while True:
        print_menu()
        choice = input("Select scenario (1-5, q to quit) [default 1]: ").strip()
        if choice.lower() == 'q':
            print("Exiting simulator.")
            sys.exit(0)
        if choice not in PROFILES:
            choice = "1"
        run_stream(choice, stream_rate_rpm=40.0)

if __name__ == "__main__":
    main()
