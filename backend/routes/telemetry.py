from fastapi import APIRouter, HTTPException, BackgroundTasks
from models import (
    TelemetryPayload, EmergencyTriggerPayload, AnomalyEvaluation,
    DeviceRegistrationPayload, DeviceHeartbeatPayload, BatchTelemetryPayload
)
from services.telemetry_service import telemetry_manager
from typing import Dict, Any, List
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["Telemetry & Devices"])

# In-memory Device Registry for hardware wearables, biosensors, and ECLSS microcontrollers
DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "APPLE-WATCH-ULTRA-01": {
        "device_id": "APPLE-WATCH-ULTRA-01",
        "device_name": "Commander Apple Watch Ultra 2",
        "device_type": "WEARABLE_SMARTWATCH",
        "astronaut_id": "ASTRO-01",
        "battery_level": 92,
        "firmware_version": "watchOS 11.2",
        "sensor_capabilities": ["ECG_LEAD_I", "OPTICAL_PPG_HR", "SPO2", "SKIN_TEMP", "ACCELEROMETER"],
        "status": "ONLINE",
        "registered_at": "2026-11-14T10:00:00Z",
        "last_seen": datetime.now(timezone.utc).isoformat()
    }
}

@router.post("/telemetry", summary="Ingest Real-time Device Biometrics")
async def ingest_telemetry(payload: TelemetryPayload) -> Dict[str, Any]:
    """
    Receives real-time biometric metrics from Apple Watch, WearOS, Garmin, or biosensors:
    - heart_rate (BPM)
    - stress_level (0-100 index derived from HRV)
    - oxygen (SpO2 percentage)
    - ecg_lead & classification
    - suit/cabin co2 & ambient o2
    - camera computer vision state
    
    Streams data immediately to Meta Quest 3 VR headsets and Web HUD via WebSocket,
    and executes AI triage & physiological countermeasure evaluation.
    """
    result = await telemetry_manager.process_telemetry(payload)
    return {
        "status": "success",
        "astronaut_id": payload.astronaut_id,
        "processed": result
    }

@router.post("/telemetry/batch", summary="Ingest Buffered Offline Telemetry from Devices")
async def ingest_telemetry_batch(batch: BatchTelemetryPayload) -> Dict[str, Any]:
    """
    Ingests multiple historical/buffered biometric readings when a wearable or sensor
    reconnects after an EVA communication blackout or network dropout.
    """
    processed_count = 0
    last_result = None
    for item in batch.readings:
        item.astronaut_id = item.astronaut_id or batch.astronaut_id
        last_result = await telemetry_manager.process_telemetry(item)
        processed_count += 1

    # Update device last seen
    if batch.device_id in DEVICE_REGISTRY:
        DEVICE_REGISTRY[batch.device_id]["last_seen"] = datetime.now(timezone.utc).isoformat()

    return {
        "status": "batch_success",
        "device_id": batch.device_id,
        "readings_ingested": processed_count,
        "latest_evaluation": last_result
    }

@router.get("/telemetry/latest", summary="Get Single Latest Telemetry Snapshot")
async def get_latest_telemetry() -> Dict[str, Any]:
    """Returns the most recent physiological telemetry packet recorded on the station."""
    latest = telemetry_manager.latest_telemetry
    if not latest:
        raise HTTPException(status_code=404, detail="No telemetry available yet.")
    return {
        "status": "online",
        "telemetry": latest,
        "active_triage": telemetry_manager.latest_triage
    }

# ========================================================
# Device Registration & Heartbeat Subsystem
# ========================================================

@router.post("/devices/register", summary="Register Hardware Sensor / Wearable Device")
async def register_device(payload: DeviceRegistrationPayload) -> Dict[str, Any]:
    """
    Registers a new physical sensor, Apple Watch, Garmin smartwatch, ESP32 biosensor,
    or ECLSS cabin atmospheric telemetry module.
    """
    now = datetime.now(timezone.utc).isoformat()
    DEVICE_REGISTRY[payload.device_id] = {
        "device_id": payload.device_id,
        "device_name": payload.device_name,
        "device_type": payload.device_type,
        "astronaut_id": payload.astronaut_id,
        "battery_level": payload.battery_level,
        "firmware_version": payload.firmware_version,
        "sensor_capabilities": payload.sensor_capabilities,
        "status": "ONLINE",
        "registered_at": now,
        "last_seen": now
    }
    return {
        "status": "DEVICE_REGISTERED",
        "device": DEVICE_REGISTRY[payload.device_id]
    }

@router.get("/devices", summary="List All Connected Hardware Devices")
async def list_devices() -> Dict[str, Any]:
    """Returns list of all active connected sensors, smartwatches, and habitat hardware."""
    return {
        "total_devices": len(DEVICE_REGISTRY),
        "devices": list(DEVICE_REGISTRY.values())
    }

@router.post("/devices/heartbeat", summary="Device Keepalive & Battery Telemetry")
async def device_heartbeat(payload: DeviceHeartbeatPayload) -> Dict[str, Any]:
    """Keepalive ping sent periodically (e.g. every 30s) by smartwatches and wireless sensors."""
    now = datetime.now(timezone.utc).isoformat()
    if payload.device_id in DEVICE_REGISTRY:
        DEVICE_REGISTRY[payload.device_id]["last_seen"] = now
        DEVICE_REGISTRY[payload.device_id]["status"] = payload.status
        if payload.battery_level is not None:
            DEVICE_REGISTRY[payload.device_id]["battery_level"] = payload.battery_level
        return {"status": "ACK", "device_id": payload.device_id}
    else:
        # Auto-register minimal entry
        DEVICE_REGISTRY[payload.device_id] = {
            "device_id": payload.device_id,
            "device_name": f"Generic Device ({payload.device_id})",
            "device_type": "UNKNOWN_BIOSENSOR",
            "astronaut_id": "ASTRO-01",
            "battery_level": payload.battery_level or 100,
            "status": payload.status,
            "registered_at": now,
            "last_seen": now
        }
        return {"status": "AUTO_REGISTERED", "device_id": payload.device_id}

@router.post("/devices/alarm-test", summary="Trigger Station & Wearable Master Alarm Test")
async def test_master_alarm() -> Dict[str, Any]:
    """
    Dispatches a high-priority caution & warning acoustic klaxon test packet
    to all active Web, VR, and wearable clients.
    """
    test_telemetry = TelemetryPayload(
        astronaut_id="ASTRO-TEST",
        heart_rate=145.0,
        stress_level=85.0,
        oxygen=88.5,
        source="MASTER_ALARM_TEST"
    )
    result = await telemetry_manager.process_telemetry(test_telemetry)
    return {
        "status": "ALARM_BROADCAST_TEST_DISPATCHED",
        "evaluation": result
    }

@router.post("/emergency-trigger", summary="Manual Astronaut SOS Panic Trigger")
async def emergency_trigger(payload: EmergencyTriggerPayload) -> Dict[str, Any]:
    """
    Emergency endpoint invoked when an astronaut hits the physical/watch SOS panic button.
    Forces immediate high-priority triage and alert broadcast.
    """
    current_hr = telemetry_manager.latest_telemetry.heart_rate if telemetry_manager.latest_telemetry else 115.0
    current_o2 = telemetry_manager.latest_telemetry.oxygen if telemetry_manager.latest_telemetry else 94.0
    
    sos_telemetry = TelemetryPayload(
        astronaut_id=payload.astronaut_id,
        heart_rate=current_hr,
        stress_level=98.0,
        oxygen=current_o2,
        is_emergency_triggered=True,
        source="apple_watch_emergency_button"
    )
    result = await telemetry_manager.process_telemetry(sos_telemetry)
    return {
        "status": "EMERGENCY_DISPATCHED",
        "details": result
    }

@router.get("/history", summary="Get Recent Telemetry History (for VR Graphs)")
async def get_history() -> List[TelemetryPayload]:
    """Returns the last 120 telemetry entries for rendering trends in the VR HUD."""
    return list(telemetry_manager.history)

@router.get("/status", summary="Server & Telemetry Subsystem Status")
async def get_system_status() -> Dict[str, Any]:
    return {
        "server_status": "ONLINE",
        "connected_vr_clients": len(telemetry_manager.active_connections),
        "buffered_points": len(telemetry_manager.history),
        "registered_devices": len(DEVICE_REGISTRY),
        "latest_telemetry": telemetry_manager.latest_telemetry,
        "latest_triage": telemetry_manager.latest_triage
    }

