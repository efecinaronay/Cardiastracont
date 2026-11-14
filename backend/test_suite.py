import sys
import os

print("[1] Loading models...", flush=True)
from models import TelemetryPayload, AnomalyEvaluation, TriageResponse, EmergencyTriggerPayload
print("[2] Loading rules engine...", flush=True)
from services.rules_engine import SpaceMedicalRulesEngine
print("[3] Loading nim service...", flush=True)
from services.nim_service import nim_service

def test_nominal():
    t = TelemetryPayload(heart_rate=72.0, stress_level=22.0, oxygen=98.5)
    eval_res = SpaceMedicalRulesEngine.evaluate_telemetry(t)
    assert not eval_res.is_anomaly
    assert eval_res.severity == "NOMINAL"
    triage = SpaceMedicalRulesEngine.generate_offline_triage(t, eval_res)
    assert not triage.anomaly_detected
    print("✓ Test Nominal PASSED", flush=True)

def test_hypoxia():
    t = TelemetryPayload(heart_rate=110.0, stress_level=80.0, oxygen=84.0)
    eval_res = SpaceMedicalRulesEngine.evaluate_telemetry(t)
    assert eval_res.is_anomaly
    assert eval_res.severity == "CRITICAL"
    assert "SEVERE_HYPOXIA" in eval_res.anomaly_types
    triage = SpaceMedicalRulesEngine.generate_offline_triage(t, eval_res)
    assert triage.anomaly_detected
    assert "HYPOXIA" in triage.condition_title
    assert len(triage.immediate_actions) > 0
    print("✓ Test Hypoxia PASSED", flush=True)

def test_tachycardia_panic():
    t = TelemetryPayload(heart_rate=162.0, stress_level=95.0, oxygen=97.0)
    eval_res = SpaceMedicalRulesEngine.evaluate_telemetry(t)
    assert eval_res.is_anomaly
    assert eval_res.severity == "CRITICAL"
    assert "SEVERE_TACHYCARDIA" in eval_res.anomaly_types
    assert "ACUTE_PANIC_STORM" in eval_res.anomaly_types
    triage = SpaceMedicalRulesEngine.generate_offline_triage(t, eval_res)
    assert triage.sanctuary_recommended is True
    print("✓ Test Tachycardia & Panic PASSED", flush=True)

def test_hypercapnia():
    t = TelemetryPayload(heart_rate=105.0, stress_level=75.0, oxygen=94.0, co2_level_ppm=2800.0)
    eval_res = SpaceMedicalRulesEngine.evaluate_telemetry(t)
    assert eval_res.is_anomaly
    assert eval_res.severity == "CRITICAL"
    assert "CRITICAL_HYPERCAPNIA" in eval_res.anomaly_types
    triage = SpaceMedicalRulesEngine.generate_offline_triage(t, eval_res)
    assert any("CDRA" in a or "LiOH" in a for a in triage.immediate_actions)
    print("✓ Test Hypercapnia (CO2) PASSED", flush=True)

def test_manual_sos():
    t = TelemetryPayload(heart_rate=90.0, stress_level=50.0, oxygen=96.0, is_emergency_triggered=True)
    eval_res = SpaceMedicalRulesEngine.evaluate_telemetry(t)
    assert eval_res.is_anomaly
    assert eval_res.severity == "CRITICAL"
    assert "MANUAL_SOS" in eval_res.anomaly_types
    triage = SpaceMedicalRulesEngine.generate_offline_triage(t, eval_res)
    assert "EMERGENCY BEACON" in triage.condition_title
    print("✓ Test Manual SOS PASSED", flush=True)

if __name__ == "__main__":
    print("Running Cardiastracont Space Medical Validation Suite...")
    test_nominal()
    test_hypoxia()
    test_tachycardia_panic()
    test_hypercapnia()
    test_manual_sos()
    print("ALL CLINICAL SCENARIOS PASSED WITH 100% ACCURACY!")

