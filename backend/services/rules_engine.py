from typing import List
from models import TelemetryPayload, AnomalyEvaluation, TriageResponse
from config import settings
import time
from datetime import datetime, timezone

class SpaceMedicalRulesEngine:
    """
    Offline-First Deterministic Flight Surgeon Clinical Decision Rules.
    Designed for deep space missions (e.g. Mars transit) where light-speed
    communication delays preclude Earth-based real-time doctor support.
    """

    @staticmethod
    def evaluate_telemetry(t: TelemetryPayload) -> AnomalyEvaluation:
        anomaly_types: List[str] = []
        triggers: List[str] = []
        severity = "NOMINAL"

        # 1. Manual SOS
        if t.is_emergency_triggered:
            anomaly_types.append("MANUAL_SOS")
            triggers.append("Astronaut manually triggered emergency SOS beacon.")
            severity = "CRITICAL"

        # 2. Hypoxia check (Oxygen SpO2)
        if t.oxygen < 88.0:
            anomaly_types.append("SEVERE_HYPOXIA")
            triggers.append(f"Critical SpO2 drop: {t.oxygen:.1f}% (< 88%). Risk of acute cognitive impairment.")
            severity = "CRITICAL"
        elif t.oxygen < settings.THRESHOLD_OXYGEN_MIN:
            anomaly_types.append("HYPOXIA_WARNING")
            triggers.append(f"Low SpO2: {t.oxygen:.1f}% (< {settings.THRESHOLD_OXYGEN_MIN}%).")
            if severity != "CRITICAL":
                severity = "WARNING"

        # 3. Heart Rate check
        if t.heart_rate > 150.0:
            anomaly_types.append("SEVERE_TACHYCARDIA")
            triggers.append(f"Dangerous tachyarrhythmia: {t.heart_rate:.0f} BPM (> 150 BPM).")
            severity = "CRITICAL"
        elif t.heart_rate > settings.THRESHOLD_HR_MAX:
            anomaly_types.append("TACHYCARDIA_WARNING")
            triggers.append(f"Elevated Heart Rate: {t.heart_rate:.0f} BPM (> {settings.THRESHOLD_HR_MAX} BPM).")
            if severity != "CRITICAL":
                severity = "WARNING"
        elif t.heart_rate < settings.THRESHOLD_HR_MIN:
            anomaly_types.append("BRADYCARDIA_WARNING")
            triggers.append(f"Abnormally low Heart Rate: {t.heart_rate:.0f} BPM (< {settings.THRESHOLD_HR_MIN} BPM).")
            if severity != "CRITICAL":
                severity = "WARNING"

        # 4. Stress Index / Panic
        if t.stress_level >= 90.0:
            anomaly_types.append("ACUTE_PANIC_STORM")
            triggers.append(f"Critical Autonomic Stress Spike: {t.stress_level:.1f}/100.")
            if severity != "CRITICAL":
                severity = "WARNING"
        elif t.stress_level >= settings.THRESHOLD_STRESS_MAX:
            anomaly_types.append("ELEVATED_STRESS")
            triggers.append(f"Autonomic Stress Elevated: {t.stress_level:.1f}/100.")
            if severity == "NOMINAL":
                severity = "WARNING"

        # 5. CO2 Level
        if t.co2_level_ppm and t.co2_level_ppm > 2500.0:
            anomaly_types.append("CRITICAL_HYPERCAPNIA")
            triggers.append(f"Severe ambient CO2 accumulation: {t.co2_level_ppm:.0f} PPM (> 2500 PPM).")
            severity = "CRITICAL"
        elif t.co2_level_ppm and t.co2_level_ppm > settings.THRESHOLD_CO2_PPM_MAX:
            anomaly_types.append("ELEVATED_CO2")
            triggers.append(f"Elevated ambient CO2: {t.co2_level_ppm:.0f} PPM.")
            if severity == "NOMINAL":
                severity = "WARNING"

        # 6. Apple Watch Electrical Heart Sensor (ECG Lead I)
        if t.ecg_classification == "ATRIAL_FIBRILLATION":
            anomaly_types.append("CARDIAC_AFIB_ARRHYTHMIA")
            triggers.append("Apple Watch ECG sensor detected Atrial Fibrillation (irregular R-R intervals).")
            severity = "CRITICAL"
        elif t.ecg_classification == "VENTRICULAR_ECTOPY":
            anomaly_types.append("VENTRICULAR_ECTOPY")
            triggers.append("Apple Watch ECG waveform shows frequent premature ventricular complexes.")
            severity = "CRITICAL"

        # 7. Environmental Oxygen Concentration & Partial Pressure (FiO2 / ppO2)
        if t.ambient_o2_percent is not None and t.ambient_o2_percent < 16.0:
            anomaly_types.append("AMBIENT_O2_DEPLETION")
            triggers.append(f"Critical ambient/suit O2 concentration drop: {t.ambient_o2_percent:.1f}% (Nominal: 20.9%).")
            severity = "CRITICAL"
        elif t.ambient_o2_percent is not None and t.ambient_o2_percent < 18.5:
            anomaly_types.append("LOW_AMBIENT_O2")
            triggers.append(f"Reduced breathable O2 concentration: {t.ambient_o2_percent:.1f}%.")
            if severity == "NOMINAL":
                severity = "WARNING"

        if t.o2_partial_pressure_kpa is not None and t.o2_partial_pressure_kpa < 16.0:
            anomaly_types.append("LOW_PPO2_HAZARD")
            triggers.append(f"O2 partial pressure below physiologic minimum: {t.o2_partial_pressure_kpa:.1f} kPa (< 16.0 kPa).")
            severity = "CRITICAL"

        # 8. Computer Vision / Helmet Camera Biomarkers
        if t.camera_telemetry and t.camera_telemetry.camera_active:
            cam = t.camera_telemetry
            # Loss of consciousness / severe microsleep via PERCLOS
            if cam.eye_perclos >= 0.70 or cam.expression_state == "UNCONSCIOUS":
                anomaly_types.append("COGNITIVE_MICROSLEEP_COLLAPSE")
                triggers.append(f"Camera detected prolonged eye closure / microsleep collapse (PERCLOS: {cam.eye_perclos:.2f}).")
                severity = "CRITICAL"
            elif cam.eye_perclos >= 0.40:
                anomaly_types.append("DROWSINESS_FATIGUE")
                triggers.append(f"Elevated ocular drowsiness detected (PERCLOS: {cam.eye_perclos:.2f}).")
                if severity == "NOMINAL":
                    severity = "WARNING"

            # Perioral Cyanosis corroborated with SpO2
            if cam.facial_pallor == "CYANOTIC":
                anomaly_types.append("VISUAL_CYANOSIS")
                triggers.append("Helmet camera computer vision flagged facial/perioral cyanosis (blue discoloration).")
                severity = "CRITICAL"

            # Space Motion Sickness / Vestibular Nystagmus
            if cam.gaze_stability == "NYSTAGMUS" or (cam.facial_pallor == "PALE" and t.stress_level > 80):
                anomaly_types.append("VESTIBULAR_SAS_DISTRESS")
                triggers.append("Computer vision detected ocular nystagmus and severe pallor (Space Adaptation Syndrome).")
                if severity != "CRITICAL":
                    severity = "WARNING"

        is_anomaly = len(anomaly_types) > 0
        return AnomalyEvaluation(
            is_anomaly=is_anomaly,
            severity=severity,
            anomaly_types=anomaly_types,
            triggers=triggers
        )

    @classmethod
    def generate_offline_triage(cls, t: TelemetryPayload, eval_res: AnomalyEvaluation) -> TriageResponse:
        start_t = time.perf_counter()

        if not eval_res.is_anomaly:
            return TriageResponse(
                anomaly_detected=False,
                severity="NOMINAL",
                condition_title="All Systems Nominal",
                diagnosis="Vitals are within standard spaceflight physiologic baselines.",
                immediate_actions=["Maintain normal mission operations.", "Continue hydration schedule."],
                countermeasures=["Scheduled orbital rest cycle.", "Standard 2.5hr resistive exercise regimen."],
                sanctuary_recommended=False,
                source="offline_protocol",
                model_used="ISS-FlightSurgeon-Rules-v4",
                execution_time_ms=(time.perf_counter() - start_t) * 1000,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        immediate_actions: List[str] = []
        countermeasures: List[str] = []
        condition_title = "Physiologic Anomaly Detected"
        diagnosis_parts: List[str] = []
        sanctuary_rec = False

        if "MANUAL_SOS" in eval_res.anomaly_types:
            condition_title = "EMERGENCY BEACON TRIGGERED"
            diagnosis_parts.append("Astronaut-initiated manual distress beacon received.")
            immediate_actions.extend([
                "Confirm astronaut conscious state via suit comms / VR HUD.",
                "Initiate automated cabin cabin atmosphere scan (O2, CO2, cabin pressure).",
                "Ready emergency medical pack (MedPack Alpha) at Airlock station."
            ])

        if "SEVERE_HYPOXIA" in eval_res.anomaly_types or "HYPOXIA_WARNING" in eval_res.anomaly_types:
            condition_title = "CRITICAL OXYGEN DESATURATION (HYPOXIA)"
            diagnosis_parts.append(f"SpO2 depleted to {t.oxygen:.1f}%. Risk of cerebral hypoxia and spatial disorientation.")
            immediate_actions.extend([
                "Engage 100% emergency O2 flow on suit regulator / cabin mask.",
                "Inspect suit visor seal and umbilical quick-disconnect valve.",
                "Halt all EVA or heavy physical activity immediately; tether to nearest bulkhead."
            ])
            countermeasures.extend([
                "Administer hyperoxic breathing protocol for 15 minutes.",
                "Monitor for cognitive ataxia via VR HUD response prompts.",
                "Check ECLSS primary oxygen line pressure telemetry."
            ])

        if "CRITICAL_HYPERCAPNIA" in eval_res.anomaly_types or "ELEVATED_CO2" in eval_res.anomaly_types:
            diagnosis_parts.append(f"CO2 buildup detected at {t.co2_level_ppm:.0f} PPM.")
            immediate_actions.extend([
                "Cycle ECLSS Carbon Dioxide Removal Assembly (CDRA) valves.",
                "Verify suit ventilation fan RPM > 90% to clear facial pocket CO2 dead zones.",
                "Replace secondary LiOH (lithium hydroxide) absorption canister if in EVA."
            ])

        if "SEVERE_TACHYCARDIA" in eval_res.anomaly_types or "TACHYCARDIA_WARNING" in eval_res.anomaly_types:
            diagnosis_parts.append(f"Heart rate elevated to {t.heart_rate:.0f} BPM.")
            immediate_actions.extend([
                "Assume recumbent posture to maximize cardiovascular venous return in microgravity.",
                "Perform modified Valsalva maneuver (bear down gently for 10-15s).",
                "Check core temperature to differentiate cardiac event from heat exhaustion."
            ])
            countermeasures.extend([
                "Drink 500mL electrolyte replenishment solution.",
                "Prepare 12-lead ECG electrode patch array for telemetry review."
            ])

        if "ACUTE_PANIC_STORM" in eval_res.anomaly_types or "ELEVATED_STRESS" in eval_res.anomaly_types:
            sanctuary_rec = True
            diagnosis_parts.append(f"Sympathetic autonomic nervous system overdrive (Stress: {t.stress_level:.0f}/100).")
            immediate_actions.extend([
                "Activate VR Sanctuary Mode immediately: dim HUD lighting and engage spatial audio.",
                "Begin guided 4-7-8 parasympathetic box breathing sequence.",
                "Verbal grounding: confirm coordinates, pressure seal, and communication status."
            ])
            countermeasures.extend([
                "Administer sensory reduction protocol in sleep pod / VR sanctuary for 10 mins.",
                "Verify no environmental toxic release triggering claustrophobia or panic."
            ])

        if "CARDIAC_AFIB_ARRHYTHMIA" in eval_res.anomaly_types or "VENTRICULAR_ECTOPY" in eval_res.anomaly_types:
            condition_title = "ACUTE CARDIAC ARRHYTHMIA (AFIB)"
            diagnosis_parts.append(f"Apple Watch Lead I ECG flagged Atrial Fibrillation with irregular ventricular response ({t.heart_rate:.0f} BPM).")
            immediate_actions.extend([
                "Halt all physical exertion immediately; sit recumbent to assist venous return.",
                "Apply multi-lead telemetry patch from medical pack to corroborate Lead I reading.",
                "Verify coronary perfusion and check for acute chest tightness or radiation down left arm."
            ])
            countermeasures.extend([
                "Initiate autonomous telemetry recording for ground flight surgeon packet uplink.",
                "Prepare oral beta-blocker/antiarrhythmic dose per spacecraft medical protocol Alpha.",
                "Monitor for microgravity fluid redistribution induced atrial stretch."
            ])

        if "AMBIENT_O2_DEPLETION" in eval_res.anomaly_types or "VISUAL_CYANOSIS" in eval_res.anomaly_types:
            condition_title = "ATMOSPHERIC O2 LOSS & HYPOXIC CRISIS"
            o2_conc = f"{t.ambient_o2_percent:.1f}%" if t.ambient_o2_percent is not None else "CRITICAL"
            diagnosis_parts.append(f"Cabin/Suit O2 dropped to {o2_conc} corroborated by camera cyanosis and SpO2 {t.oxygen:.1f}%.")
            immediate_actions.extend([
                "Lock suit emergency oxygen bypass valve to deliver 100% positive pressure O2.",
                "Verify helmet visor seal clamp integrity and umbilical lock collar.",
                "Check ECLSS cabin partial pressure gauge (ppO2) for hull micro-breach."
            ])
            countermeasures.extend([
                "Isolate compromised cabin module via bulkhead emergency hatch seal.",
                "Run hyperbaric oxygen re-saturation protocol.",
                "Perform neuro-cognitive ataxia verification test on VR HUD."
            ])

        if "COGNITIVE_MICROSLEEP_COLLAPSE" in eval_res.anomaly_types or "DROWSINESS_FATIGUE" in eval_res.anomaly_types:
            condition_title = "COGNITIVE COLLAPSE / SEVERE MICROSLEEP"
            perclos_val = t.camera_telemetry.eye_perclos if t.camera_telemetry else 0.8
            diagnosis_parts.append(f"Computer vision camera flagged critical eye closure (PERCLOS: {perclos_val:.2f}) and head slump.")
            immediate_actions.extend([
                "Trigger high-intensity auditory arousal chime and haptic suit pulse.",
                "Hand over flight controls/EVA critical ops to automated station copilot.",
                "Verify cabin atmosphere is free of odorless nitrogen or CO2 asphyxiant pocket."
            ])
            countermeasures.extend([
                "Mandate immediate 90-minute circadian restorative sleep cycle in crew quarters.",
                "Administer 100mg modafinil or caffeine countermeasure per flight rules.",
                "Schedule rest-activity rhythm realignment."
            ])

        if "VESTIBULAR_SAS_DISTRESS" in eval_res.anomaly_types:
            condition_title = "SPACE ADAPTATION SYNDROME (SAS)"
            diagnosis_parts.append("Visual telemetry detected ocular nystagmus and profound pallor from otolith-visual conflict.")
            immediate_actions.extend([
                "Fix visual gaze on stationary reference point inside spacecraft cabin.",
                "Restrict sudden head movements across pitch and roll axes.",
                "Ready emesis containment bag and suction line."
            ])
            countermeasures.extend([
                "Administer intramuscular or oral promethazine countermeasure.",
                "Sanctuary relaxation protocol with head stabilization harness.",
                "Gradual adaptation re-exposure over 24-48 hours."
            ])

        # Deduplicate and format
        diagnosis = " | ".join(diagnosis_parts) if diagnosis_parts else "Spaceflight physiological boundary deviation."

        return TriageResponse(
            anomaly_detected=True,
            severity=eval_res.severity,
            condition_title=condition_title,
            diagnosis=diagnosis,
            immediate_actions=list(dict.fromkeys(immediate_actions))[:4],
            countermeasures=list(dict.fromkeys(countermeasures))[:3],
            sanctuary_recommended=sanctuary_rec or eval_res.severity == "CRITICAL",
            source="offline_protocol",
            model_used="Offline-SpaceSurgeon-Protocol",
            execution_time_ms=(time.perf_counter() - start_t) * 1000,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

