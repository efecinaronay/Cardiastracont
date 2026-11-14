import sys
import os
import asyncio

print("START SCRIPT", flush=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import TelemetryPayload, EmergencyTriggerPayload
from routes.telemetry import ingest_telemetry, emergency_trigger, get_history, get_system_status
from routes.analysis import analyze_anomaly
from services.rules_engine import SpaceMedicalRulesEngine

async def run_all_tests():
    print("🛰️  Running Cardiastracont Core Clinical & API Tests...", flush=True)

    # 1. Test Nominal State
    nominal_payload = TelemetryPayload(
        astronaut_id="ASTRO-TEST-01",
        heart_rate=72.0,
        oxygen=98.5,
        stress_level=20.0,
        co2_level_ppm=420.0,
        is_emergency_triggered=False
    )
    print("Testing nominal...", flush=True)
    res_nominal = await ingest_telemetry(nominal_payload)
    assert res_nominal["status"] == "success"
    eval_nominal = res_nominal["processed"]["evaluation"]
    assert eval_nominal["severity"] == "NOMINAL"
    assert eval_nominal["is_anomaly"] is False
    print("  ✓ Nominal telemetry processing validated.", flush=True)

    # 2. Test Hypoxia Anomaly
    hypoxia_payload = TelemetryPayload(
        astronaut_id="ASTRO-TEST-01",
        heart_rate=115.0,
        oxygen=83.5,  # Severe Hypoxia (< 88%)
        stress_level=85.0,
        co2_level_ppm=440.0,
        is_emergency_triggered=False
    )
    print("Testing hypoxia...", flush=True)
    res_hypoxia = await ingest_telemetry(hypoxia_payload)
    eval_hypoxia = res_hypoxia["processed"]["evaluation"]
    assert eval_hypoxia["is_anomaly"] is True
    assert eval_hypoxia["severity"] == "CRITICAL"
    assert "SEVERE_HYPOXIA" in eval_hypoxia["anomaly_types"]
    
    triage = res_hypoxia["processed"]["triage"]
    assert triage is not None
    assert triage["anomaly_detected"] is True
    assert "HYPOXIA" in triage["condition_title"].upper()
    assert len(triage["immediate_actions"]) > 0
    print("  ✓ Hypoxia anomaly detection & flight surgeon triage validated.", flush=True)

    # 3. Test Analyze Anomaly endpoint (Tachycardia & Panic)
    panic_payload = TelemetryPayload(
        astronaut_id="ASTRO-TEST-01",
        heart_rate=165.0,
        oxygen=97.0,
        stress_level=94.0,
        co2_level_ppm=410.0,
        is_emergency_triggered=False
    )
    print("Testing analyze_anomaly...", flush=True)
    triage_panic = await analyze_anomaly(panic_payload)
    assert triage_panic.anomaly_detected is True
    assert triage_panic.severity == "CRITICAL"
    assert triage_panic.sanctuary_recommended is True
    print("  ✓ Analyze-anomaly endpoint & VR Sanctuary recommendation validated.", flush=True)

    # 4. Test Manual SOS Emergency Trigger
    sos_payload = EmergencyTriggerPayload(
        astronaut_id="ASTRO-TEST-01",
        note="Astronaut pressed physical SOS button on Apple Watch"
    )
    print("Testing emergency_trigger...", flush=True)
    res_sos = await emergency_trigger(sos_payload)
    assert res_sos["status"] == "EMERGENCY_DISPATCHED"
    print("  ✓ Manual SOS emergency dispatch validated.", flush=True)

    # 5. Test History & System Status
    history = await get_history()
    assert len(history) >= 2
    status = await get_system_status()
    assert status["server_status"] == "ONLINE"
    print("  ✓ Telemetry history buffer & system status validated.", flush=True)

    print("\n🎉 ALL 5 CLINICAL & API SUITES PASSED FLAWLESSLY!", flush=True)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
