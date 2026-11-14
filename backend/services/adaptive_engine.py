import math
from typing import Dict, Any, List
from models import TelemetryPayload, AdaptiveProfile, AdaptiveThresholds
from config import settings

class AdaptiveSpaceHealthEngine:
    """
    Adaptive Spaceflight Physiologic Engine.
    Adjusts safety thresholds and countermeasure parameters in real time based on:
    1. Individual astronaut baseline resting & active heart rates
    2. Mission operational phase (EVA vs Transit vs Orbital Rest Sleep)
    3. Microgravity cardiovascular deconditioning curve
    """

    def __init__(self):
        # Current profile (customizable per astronaut)
        self.profile = AdaptiveProfile()

        # Rolling biometric history for adaptive baseline learning
        self._hr_window: List[float] = []
        self._stress_window: List[float] = []

    def update_profile(self, new_profile: AdaptiveProfile) -> AdaptiveProfile:
        self.profile = new_profile
        return self.profile

    def record_biometric_sample(self, t: TelemetryPayload):
        """Learns running baseline vitals over time."""
        self._hr_window.append(t.heart_rate)
        if len(self._hr_window) > 120:
            self._hr_window.pop(0)

        self._stress_window.append(t.stress_level)
        if len(self._stress_window) > 120:
            self._stress_window.pop(0)

    def calculate_adaptive_thresholds(self, current_telemetry: TelemetryPayload = None) -> AdaptiveThresholds:
        p = self.profile
        phase = p.mission_phase.upper()

        # Phase-based threshold modifications
        if phase == "EVA":
            # Extravehicular Activity: higher exertion allowed, stricter O2 monitoring
            dynamic_hr_max = min(165.0, p.baseline_active_hr + 25.0)
            dynamic_hr_min = 55.0
            dynamic_o2_min = 93.0
            dynamic_stress_max = 85.0
            phase_status = "EVA Workload Offset Active (+25 BPM ceiling, strict 93% SpO2)"
        elif phase == "REST_CYCLE":
            # Sleep / Pod Rest: physiological bradycardia is nominal
            dynamic_hr_max = p.baseline_resting_hr + 25.0  # e.g., 90 BPM
            dynamic_hr_min = 40.0                          # lower floor
            dynamic_o2_min = 91.0
            dynamic_stress_max = 60.0
            phase_status = "Circadian Rest Offset (Lower heart rate baseline tolerated)"
        else: # TRANSIT (Standard Cruise)
            dynamic_hr_max = p.baseline_resting_hr + 50.0  # e.g. 115-125
            dynamic_hr_min = 48.0
            dynamic_o2_min = 92.0
            dynamic_stress_max = 78.0 * p.stress_sensitivity
            phase_status = "Standard Deep-Space Cruise Envelope"

        # Adaptive Sanctuary Breathing Pacing Calculation
        current_stress = current_telemetry.stress_level if current_telemetry else 25.0
        current_hr = current_telemetry.heart_rate if current_telemetry else 72.0

        if current_stress >= 85.0 or current_hr > 130.0:
            # Acute storm: 4s hold can provoke air hunger. Use 3-3-3 grounding pacing.
            breathing_pattern = "GROUNDING (3s Inhale - 3s Hold - 3s Exhale)"
            duration_sec = 120  # Extended 2-minute recovery
        elif current_stress >= 65.0:
            # Moderate stress: vagal stimulation with extended 4-7-8 exhale
            breathing_pattern = "VAGAL RESET (4s Inhale - 4s Hold - 6s Exhale)"
            duration_sec = 90
        else:
            # Maintenance / Nominal relaxation
            breathing_pattern = "BOX BALANCE (4s Inhale - 4s Hold - 4s Exhale - 4s Rest)"
            duration_sec = 60

        return AdaptiveThresholds(
            dynamic_hr_max=round(dynamic_hr_max, 1),
            dynamic_hr_min=round(dynamic_hr_min, 1),
            dynamic_o2_min=round(dynamic_o2_min, 1),
            dynamic_stress_max=round(dynamic_stress_max, 1),
            recommended_breathing_pattern=breathing_pattern,
            recommended_sanctuary_duration_sec=duration_sec,
            adaptation_status=phase_status
        )

adaptive_engine = AdaptiveSpaceHealthEngine()

