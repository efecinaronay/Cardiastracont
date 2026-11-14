import json
import logging
import time
import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Optional
import requests

from config import settings
from models import TelemetryPayload, AnomalyEvaluation, TriageResponse
from services.rules_engine import SpaceMedicalRulesEngine

logger = logging.getLogger("Cardiastracont.NIM")

SPACE_MEDICINE_SYSTEM_PROMPT = """You are Cardiastracont AI, an autonomous Chief Flight Surgeon and Space Health Expert aboard a deep-space exploration vessel (Mars transit).
Communication latency with Earth Mission Control is between 4 to 22 minutes. You must provide immediate, high-fidelity clinical triage and countermeasures for astronaut telemetry anomalies.

Analyze the biometric data, identify the physiological hazard (e.g., hypoxia, space motion sickness, autonomic hyper-arousal, hypercapnia, cardiac arrhythmia), and deliver concise, actionable protocols.

You MUST respond strictly with a valid JSON object matching this exact schema:
{
  "condition_title": "Short descriptive title (e.g. ACUTE HYPOXIC EVENT)",
  "severity": "CRITICAL" | "WARNING" | "NOMINAL",
  "diagnosis": "Concise medical assessment explaining the physiological risk under microgravity/space conditions (2-3 sentences)",
  "immediate_actions": [
    "Step 1: Immediate tactile or equipment action",
    "Step 2: Emergency life-support adjustment",
    "Step 3: Verification check"
  ],
  "countermeasures": [
    "Longer-term pharmacological, ECLSS, or operational countermeasure 1",
    "Countermeasure 2"
  ],
  "sanctuary_recommended": true | false
}
Do not include any conversational filler, markdown formatting backticks (```json), or text outside the JSON object.
"""

class NvidiaNimService:
    def __init__(self):
        self.api_key = settings.NVIDIA_NIM_API_KEY
        self.base_url = settings.NVIDIA_NIM_BASE_URL.rstrip('/')
        self.model = settings.NVIDIA_MODEL
        self.timeout = settings.NVIDIA_TIMEOUT_SECONDS
        
        # 40 RPM Rate Limiter State (Sliding 60-second window)
        self.max_rpm = settings.NVIDIA_MAX_RPM  # 40 requests per minute
        self.request_timestamps = deque()
        self._min_interval = 60.0 / float(self.max_rpm)  # 1.5s per request
        self._last_request_time = 0.0

    def _sync_nim_call(self, endpoint: str, headers: dict, payload: dict) -> dict:
        """Synchronous HTTP call executed in thread pool for async compatibility."""
        response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
        if not response.ok:
            error_detail = response.text
            try:
                err_json = response.json()
                error_detail = err_json.get("detail", err_json.get("message", response.text))
            except Exception:
                pass
            raise requests.exceptions.HTTPError(
                f"HTTP {response.status_code} ({response.reason}): {error_detail}",
                response=response
            )
        return response.json()

    async def _enforce_rate_limit(self) -> bool:
        """
        Enforces 40 RPM (Requests Per Minute) rate limit.
        Returns True if request can proceed, or False if quota exceeded (triggering offline fallback).
        """
        now = time.time()
        
        # 1. Prune timestamps older than 60 seconds
        while self.request_timestamps and (now - self.request_timestamps[0]) > 60.0:
            self.request_timestamps.popleft()

        # 2. Check 40 RPM cap
        if len(self.request_timestamps) >= self.max_rpm:
            oldest = self.request_timestamps[0]
            wait_time = 60.0 - (now - oldest)
            if wait_time > 2.0:
                logger.warning(f"40 RPM limit reached ({len(self.request_timestamps)} reqs in last 60s). Fast fallback to offline rules.")
                return False
            else:
                await asyncio.sleep(wait_time)
                now = time.time()

        # 3. Spacing guard: ensure at least 1.5s between rapid-fire calls
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_interval:
            await asyncio.sleep(self._min_interval - time_since_last)
            now = time.time()

        self.request_timestamps.append(now)
        self._last_request_time = now
        return True

    async def triage_anomaly(self, telemetry: TelemetryPayload, evaluation: AnomalyEvaluation) -> TriageResponse:
        """
        Attempts to call the NVIDIA NIM API for autonomous AI triage capped at 40 RPM.
        If rate limit is reached, API key is missing, or network fails,
        seamlessly falls back to the deterministic offline space medical rules engine.
        """
        start_time = time.perf_counter()

        # Check for valid API key
        is_key_configured = bool(self.api_key and self.api_key.strip() and "PLACEHOLDER" not in self.api_key.upper())

        if not is_key_configured:
            logger.info("NVIDIA NIM API key not configured. Using deterministic Space Medical Rules Engine.")
            return SpaceMedicalRulesEngine.generate_offline_triage(telemetry, evaluation)

        # Enforce 40 RPM limit
        can_proceed = await self._enforce_rate_limit()
        if not can_proceed:
            offline_res = SpaceMedicalRulesEngine.generate_offline_triage(telemetry, evaluation)
            offline_res.diagnosis += " [Note: 40 RPM rate limit reached. Instant offline flight surgeon protocol engaged.]"
            offline_res.execution_time_ms = (time.perf_counter() - start_time) * 1000
            return offline_res

        cam = telemetry.camera_telemetry
        cam_info = (
            f"Active (Pallor: {cam.facial_pallor}, PERCLOS: {cam.eye_perclos:.2f}, "
            f"Gaze: {cam.gaze_stability}, Expression: {cam.expression_state}, Pupils: {cam.pupil_dilation_mm}mm)"
            if cam and cam.camera_active else "Offline / Not Available"
        )

        prompt = f"""MULTIMODAL ASTRONAUT TELEMETRY SNAPSHOT:
- Astronaut ID: {telemetry.astronaut_id}
- Heart Rate: {telemetry.heart_rate:.1f} BPM (Nominal: {settings.THRESHOLD_HR_MIN}-{settings.THRESHOLD_HR_MAX})
- Apple Watch Lead I ECG: {telemetry.ecg_classification} ({telemetry.ecg_lead})
- SpO2 Blood Oxygen Saturation: {telemetry.oxygen:.1f}% (Safe min: {settings.THRESHOLD_OXYGEN_MIN}%)
- Breathable Ambient O2 Concentration: {telemetry.ambient_o2_percent or 20.9:.1f}% (FiO2) | ppO2: {telemetry.o2_partial_pressure_kpa or 21.2:.1f} kPa
- Autonomic Stress Index: {telemetry.stress_level:.1f} / 100 (Threshold: <={settings.THRESHOLD_STRESS_MAX})
- Ambient Cabin/Suit CO2: {telemetry.co2_level_ppm or 420:.0f} PPM (Max Safe: {settings.THRESHOLD_CO2_PPM_MAX})
- Heart Rate Variability (SDNN): {telemetry.hrv or 'N/A'} ms
- Helmet / Cabin Optical Camera CV: {cam_info}
- Manual SOS Activated: {telemetry.is_emergency_triggered}

FLAGGED ANOMALIES & MULTISENSOR CORRELATIONS:
{json.dumps(evaluation.triggers, indent=2)}

Provide immediate flight surgeon triage protocol in strict JSON format."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SPACE_MEDICINE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 600,
            "top_p": 0.95
        }

        endpoint = f"{self.base_url}/chat/completions"

        try:
            # Execute HTTP POST in an async worker thread to prevent blocking event loop
            data = await asyncio.to_thread(self._sync_nim_call, endpoint, headers, payload)

            msg_obj = data["choices"][0].get("message", {})
            raw_content = msg_obj.get("content") or msg_obj.get("reasoning_content") or ""
            raw_content = raw_content.strip()

            if not raw_content:
                raise ValueError("NVIDIA NIM model returned empty message content")

            # Clean markdown backticks if present
            if raw_content.startswith("```"):
                lines = raw_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_content = "\n".join(lines).strip()

            parsed = json.loads(raw_content)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"NVIDIA NIM triage generated in {elapsed_ms:.1f}ms using {self.model} (40 RPM compliant)")

            return TriageResponse(
                anomaly_detected=True,
                severity=parsed.get("severity", evaluation.severity),
                condition_title=parsed.get("condition_title", "Space Medical Alert"),
                diagnosis=parsed.get("diagnosis", "Autonomous AI assessment completed."),
                immediate_actions=parsed.get("immediate_actions", []),
                countermeasures=parsed.get("countermeasures", []),
                sanctuary_recommended=bool(parsed.get("sanctuary_recommended", False)),
                source="nvidia_nim",
                model_used=self.model,
                execution_time_ms=elapsed_ms,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        except Exception as e:
            err_msg = str(e)
            logger.warning(
                f"NVIDIA NIM API call failed ({type(e).__name__}: {err_msg}). "
                f"Falling back to Deep Space Offline Medical Protocol."
            )
            offline_res = SpaceMedicalRulesEngine.generate_offline_triage(telemetry, evaluation)
            offline_res.diagnosis += f" [Note: Offline fallback activated due to NIM API unavailability: {err_msg}]"
            offline_res.execution_time_ms = (time.perf_counter() - start_time) * 1000
            return offline_res

nim_service = NvidiaNimService()
