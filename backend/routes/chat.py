from fastapi import APIRouter
from models import ChatRequest, ChatResponse, AdaptiveProfile, AdaptiveThresholds
from services.chat_service import chat_service
from services.adaptive_engine import adaptive_engine
from services.telemetry_service import telemetry_manager
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["AI Chat & Adaptive Engine"])

@router.post("/chat", response_model=ChatResponse, summary="Interactive AI Space Flight Surgeon Chat")
async def chat_with_flight_surgeon(request: ChatRequest) -> ChatResponse:
    """
    Conversational Medical AI endpoint with real-time biometric context injection.
    Supports English & Turkish queries regarding astronaut vitals, medical triage,
    and adaptive psychological countermeasures.
    """
    return await chat_service.chat(request)

@router.get("/adaptive-profile", summary="Get Current Adaptive Baselines & Thresholds")
async def get_adaptive_profile() -> Dict[str, Any]:
    """Returns the current personalized astronaut baseline profile and real-time adaptive thresholds."""
    latest = telemetry_manager.latest_telemetry
    thresholds = adaptive_engine.calculate_adaptive_thresholds(latest)
    return {
        "profile": adaptive_engine.profile.model_dump(),
        "adaptive_thresholds": thresholds.model_dump(),
        "current_telemetry": latest.model_dump() if latest else None
    }

@router.post("/adaptive-profile", response_model=AdaptiveProfile, summary="Update Personalized Baseline / Mission Phase")
async def update_adaptive_profile(profile: AdaptiveProfile) -> AdaptiveProfile:
    """
    Updates the astronaut's operational baseline:
    - mission_phase: 'TRANSIT', 'EVA', 'REST_CYCLE'
    - baseline_resting_hr, baseline_active_hr, baseline_spo2
    Dynamically recalculates safety thresholds and Sanctuary pacing.
    """
    return adaptive_engine.update_profile(profile)

