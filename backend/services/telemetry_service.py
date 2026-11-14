import logging
import time
from typing import List, Dict, Optional, Set, Any
from collections import deque
from fastapi import WebSocket

from config import settings
from models import TelemetryPayload, AnomalyEvaluation, TriageResponse, VRStreamPacket
from services.rules_engine import SpaceMedicalRulesEngine
from services.nim_service import nim_service

logger = logging.getLogger("Cardiastracont.Telemetry")

class TelemetryManager:
    def __init__(self):
        # Active WebSocket connections (Meta Quest 3 VR headsets, HUDs)
        self.active_connections: Set[WebSocket] = set()
        
        # Telemetry history buffer (last 120 points for graphs)
        self.history: deque[TelemetryPayload] = deque(maxlen=120)
        
        # Latest states
        self.latest_telemetry: Optional[TelemetryPayload] = None
        self.latest_triage: Optional[TriageResponse] = None
        
        # Cooldown management for AI triage requests
        self.last_alert_time: float = 0.0
        self.last_severity: str = "NOMINAL"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"VR Client connected. Total active connections: {len(self.active_connections)}")
        
        # Immediately send current state packet to newly connected VR headset
        initial_packet = VRStreamPacket(
            packet_type="SYSTEM_STATUS",
            telemetry=self.latest_telemetry,
            triage=self.latest_triage,
            system_status={
                "status": "ONLINE",
                "connected_clients": len(self.active_connections),
                "ai_engine": "NVIDIA NIM / Llama-3.1 + Offline Rules Fallback"
            }
        )
        await websocket.send_text(initial_packet.model_dump_json())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"VR Client disconnected. Total active connections: {len(self.active_connections)}")

    async def broadcast_packet(self, packet: VRStreamPacket):
        if not self.active_connections:
            return
            
        json_data = packet.model_dump_json()
        dead_connections = set()
        
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json_data)
            except Exception as e:
                logger.warning(f"Error broadcasting to VR client: {e}")
                dead_connections.add(connection)
                
        for dead in dead_connections:
            self.disconnect(dead)

    async def process_telemetry(self, telemetry: TelemetryPayload) -> Dict[str, Any]:
        """
        Ingests incoming Apple Watch telemetry, evaluates safe space boundaries,
        dispatches live updates to VR, and triggers autonomous AI triage if anomalous.
        """
        self.latest_telemetry = telemetry
        self.history.append(telemetry)

        # 1. First, immediately stream the live telemetry to the VR HUD for low latency
        stream_packet = VRStreamPacket(
            packet_type="TELEMETRY_UPDATE",
            telemetry=telemetry
        )
        await self.broadcast_packet(stream_packet)

        # 2. Evaluate for space health anomalies
        eval_result: AnomalyEvaluation = SpaceMedicalRulesEngine.evaluate_telemetry(telemetry)
        
        triage_result: Optional[TriageResponse] = None
        now = time.time()
        cooldown_elapsed = (now - self.last_alert_time) > settings.ALERT_COOLDOWN_SECONDS
        escalation = eval_result.severity == "CRITICAL" and self.last_severity != "CRITICAL"

        # If anomaly detected and (cooldown passed or urgent escalation)
        if eval_result.is_anomaly and (cooldown_elapsed or escalation or telemetry.is_emergency_triggered):
            self.last_alert_time = now
            self.last_severity = eval_result.severity
            
            logger.warning(f"Medical Anomaly Detected! Severity: {eval_result.severity}. Triggers: {eval_result.triggers}")
            
            # Request AI triage (NVIDIA NIM or offline fallback)
            triage_result = await nim_service.triage_anomaly(telemetry, eval_result)
            self.latest_triage = triage_result

            # Broadcast AI emergency alert to VR headset
            alert_packet = VRStreamPacket(
                packet_type="AI_TRIAGE_ALERT",
                telemetry=telemetry,
                triage=triage_result
            )
            await self.broadcast_packet(alert_packet)

        return {
            "status": "PROCESSED",
            "evaluation": eval_result.model_dump(),
            "triage": triage_result.model_dump() if triage_result else None
        }

telemetry_manager = TelemetryManager()
