from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

class CameraTelemetry(BaseModel):
    facial_pallor: str = Field(default="NORMAL", description="Facial skin perfusion: NORMAL, CYANOTIC, PALE, FLUSHED")
    eye_perclos: float = Field(default=0.08, ge=0.0, le=1.0, description="PERCLOS eye closure drowsiness/unconsciousness metric (0.0 - 1.0)")
    pupil_dilation_mm: float = Field(default=3.5, ge=1.0, le=9.0, description="Estimated pupil diameter in mm")
    gaze_stability: str = Field(default="FOCUSED", description="Ocular gaze: FOCUSED, NYSTAGMUS, ERRATIC, UNRESPONSIVE")
    expression_state: str = Field(default="ALERT", description="Observed state: ALERT, DISTRESSED, DROWSY, UNCONSCIOUS")
    camera_active: bool = Field(default=True, description="Whether helmet/cabin visual telemetry is online")
    camera_mode: Optional[str] = Field(default="FACE", description="Active tracking mode: FACE or CABIN_ENVIRONMENT")
    cabin_illuminance_lux: Optional[float] = Field(default=420.0, description="Measured ambient optical lux level")
    cabin_motion_g: Optional[float] = Field(default=0.02, description="Differential frame motion vector in G")
    cabin_stability: Optional[str] = Field(default="STABLE", description="Environmental stability: STABLE, VIBRATION, ANOMALY")

class TelemetryPayload(BaseModel):
    astronaut_id: str = Field(default="ASTRO-01", description="Astronaut callsign or identifier")
    heart_rate: float = Field(..., ge=20.0, le=250.0, description="Heart rate in beats per minute")
    stress_level: float = Field(..., ge=0.0, le=100.0, description="Autonomic stress index (0-100)")
    oxygen: float = Field(..., ge=50.0, le=100.0, description="Blood oxygen saturation SpO2 %")
    hrv: Optional[float] = Field(default=None, description="Heart Rate Variability SDNN in ms")
    co2_level_ppm: Optional[float] = Field(default=420.0, description="Ambient suit / cabin CO2 in PPM")
    
    # Apple Watch Electrical Heart Sensor (ECG Lead I)
    ecg_lead: str = Field(default="LEAD_I_APPLE_WATCH", description="ECG electrode configuration")
    ecg_classification: str = Field(default="SINUS_RHYTHM", description="SINUS_RHYTHM, ATRIAL_FIBRILLATION, SINUS_TACHYCARDIA, SINUS_BRADYCARDIA, INCONCLUSIVE")
    ecg_voltage_samples: Optional[List[float]] = Field(default=None, description="Millivolt P-QRS-T voltage trace samples")
    
    # Environmental & Breathable Oxygen Concentration
    ambient_o2_percent: Optional[float] = Field(default=20.9, ge=5.0, le=100.0, description="Suit/Cabin breathable O2 concentration % (FiO2)")
    o2_partial_pressure_kpa: Optional[float] = Field(default=21.2, ge=5.0, le=40.0, description="O2 partial pressure in kPa (nominal ~21.2 kPa)")
    
    # Computer Vision / Helmet Camera Biomarkers
    camera_telemetry: Optional[CameraTelemetry] = Field(default_factory=CameraTelemetry, description="Visual assessment from helmet/cabin camera")

    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = Field(default="apple_watch", description="Hardware telemetry source")
    is_emergency_triggered: bool = Field(default=False, description="Manual SOS trigger from watch")

class AnomalyEvaluation(BaseModel):
    is_anomaly: bool
    severity: str = "NOMINAL"  # NOMINAL, WARNING, CRITICAL
    anomaly_types: List[str] = []
    triggers: List[str] = []

class TriageResponse(BaseModel):
    anomaly_detected: bool
    severity: str
    condition_title: str
    diagnosis: str
    immediate_actions: List[str]
    countermeasures: List[str]
    sanctuary_recommended: bool
    source: str  # "nvidia_nim" or "offline_protocol"
    model_used: Optional[str] = None
    execution_time_ms: float
    confidence_score: float = 0.95
    margin_of_error_percent: float = 4.2
    ai_disclaimer: str = "AI Autonomous Triage Advisory • Probabilistic Model (Margin of Error: ±4.2%) • Crew confirmation required."
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EmergencyTriggerPayload(BaseModel):
    astronaut_id: str = "ASTRO-01"
    note: Optional[str] = "Manual SOS triggered from Apple Watch"
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VRStreamPacket(BaseModel):
    packet_type: str  # "TELEMETRY_UPDATE" | "AI_TRIAGE_ALERT" | "SANCTUARY_STATE" | "SYSTEM_STATUS" | "CHAT_MESSAGE"
    telemetry: Optional[TelemetryPayload] = None
    triage: Optional[TriageResponse] = None
    system_status: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ========================================================
# AI Chat & Adaptive Personalization Schemas
# ========================================================

class ChatMessage(BaseModel):
    role: str = "user"  # "user", "assistant", "system"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatRequest(BaseModel):
    message: str
    astronaut_id: str = "ASTRO-01"
    conversation_history: List[ChatMessage] = []
    include_telemetry: bool = False  # False by default: AI answers directly without unneeded vitals

class ResearchCitation(BaseModel):
    ref_id: str = Field(..., description="Citation marker e.g. [REF-1]")
    title: str = Field(..., description="Paper / Guideline Title")
    source: str = Field(..., description="Issuing Body e.g. NASA-STD-3001, ESA, PubMed")
    url: str = Field(..., description="Link to publication or standard")
    snippet: str = Field(..., description="Relevant clinical or physiologic extract")

class ChatResponse(BaseModel):
    reply: str
    source: str  # "nvidia_nim" | "gemini_api" | "offline_medical_copilot"
    model_used: str
    latency_ms: float = 0.0
    vitals_inspected: bool = False
    vitals_method_called: str = ""  # e.g., "[REQUEST_VITALS]" when invoked
    telemetry_snapshot: Optional[Dict[str, Any]] = None
    rag_invoked: bool = False
    research_mode: Optional[str] = None  # "SHORT" | "DEEP" | None
    rag_query: Optional[str] = None
    citations: List[ResearchCitation] = []
    deep_research_dossier: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.96
    margin_of_error_percent: float = 3.8
    ai_disclaimer: str = "Cardiastracont Clinical Decision Support • Probabilistic AI (Est. Margin of Error: ±3.8%) • Ground confirmation advised."
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AdaptiveProfile(BaseModel):
    astronaut_id: str = "ASTRO-01"
    baseline_resting_hr: float = 65.0
    baseline_active_hr: float = 120.0
    baseline_spo2: float = 98.2
    stress_sensitivity: float = 1.0  # Multiplier: 0.8 (resilient) to 1.3 (sensitive)
    mission_phase: str = "TRANSIT"   # "LAUNCH", "TRANSIT", "EVA", "REST_CYCLE"
    adaptation_days_in_microgravity: int = 42

class AdaptiveThresholds(BaseModel):
    dynamic_hr_max: float
    dynamic_hr_min: float
    dynamic_o2_min: float
    dynamic_stress_max: float
    recommended_breathing_pattern: str  # e.g., "BOX (4-4-4-4)", "CALM (4-7-8)", "RAPID (3-3-3)"
    recommended_sanctuary_duration_sec: int
    adaptation_status: str

# ========================================================
# Device Ecosystem & Hardware Registration Schemas
# ========================================================

class DeviceRegistrationPayload(BaseModel):
    device_id: str = Field(..., description="Unique device serial or UUID (e.g. AW-SERIES-9-001)")
    device_name: str = Field(..., description="Human-readable device name (e.g. Commander Apple Watch Ultra 2)")
    device_type: str = Field(default="WEARABLE_SMARTWATCH", description="WEARABLE_SMARTWATCH, BIOSENSOR_CHEST_STRAP, CABIN_ECLSS_SENSOR, HELMET_HUD, VR_HEADSET, MEDICAL_MONITOR")
    astronaut_id: str = Field(default="ASTRO-01", description="Assigned astronaut callsign")
    battery_level: Optional[int] = Field(default=100, ge=0, le=100, description="Battery percentage (0-100)")
    firmware_version: Optional[str] = Field(default="1.0.0", description="Device firmware or OS version")
    sensor_capabilities: List[str] = Field(default_factory=lambda: ["HEART_RATE", "SPO2", "STRESS_HRV"], description="List of hardware sensors")

class DeviceHeartbeatPayload(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    battery_level: Optional[int] = Field(default=None, ge=0, le=100)
    status: str = Field(default="ONLINE", description="ONLINE, LOW_POWER, CHARGING, FAULT")

class BatchTelemetryPayload(BaseModel):
    device_id: str = Field(..., description="Source device transmitting offline buffer")
    astronaut_id: str = Field(default="ASTRO-01")
    readings: List[TelemetryPayload] = Field(..., description="Chronological array of buffered telemetry points")
