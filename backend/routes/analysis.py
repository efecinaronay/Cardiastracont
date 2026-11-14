from fastapi import APIRouter
from models import TelemetryPayload, TriageResponse
from services.rules_engine import SpaceMedicalRulesEngine
from services.nim_service import nim_service

router = APIRouter(prefix="/api", tags=["Analysis"])

@router.post("/analyze-anomaly", response_model=TriageResponse, summary="Analyze Telemetry & Generate AI Triage")
async def analyze_anomaly(telemetry: TelemetryPayload) -> TriageResponse:
    """
    Checks if telemetry breaches safe space thresholds.
    If an anomaly is detected, calls the NVIDIA NIM API (or deep space offline protocol)
    with a specialized space-medicine prompt to generate actionable medical triage steps.
    """
    evaluation = SpaceMedicalRulesEngine.evaluate_telemetry(telemetry)
    triage = await nim_service.triage_anomaly(telemetry, evaluation)
    return triage

