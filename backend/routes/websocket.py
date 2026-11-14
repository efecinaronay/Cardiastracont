import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.telemetry_service import telemetry_manager
import json

logger = logging.getLogger("Cardiastracont.WebSocket")

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/vr-stream")
async def vr_stream_endpoint(websocket: WebSocket):
    """
    Real-time high-speed bidirectional WebSocket stream for Meta Quest 3 VR headsets.
    Broadcasts:
    1. Real-time Apple Watch biometrics (heart rate, SpO2, stress)
    2. NVIDIA NIM / Offline AI Triage alerts and emergency procedures
    3. Bidirectional state sync (e.g. VR Sanctuary Mode activation)
    """
    await telemetry_manager.connect(websocket)
    try:
        while True:
            # Listen for inbound commands from VR headset (e.g., Sanctuary Mode toggled, Ping)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                
                if msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG", "timestamp": msg.get("timestamp")}))
                elif msg_type == "SANCTUARY_STATE_CHANGE":
                    logger.info(f"VR Headset toggled Sanctuary Mode: {msg.get('is_active')}")
                    # Broadcast state to any other attached telemetry stations
                    # (No-op or relay)
                else:
                    logger.debug(f"Received from VR client: {data}")
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        telemetry_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        telemetry_manager.disconnect(websocket)

