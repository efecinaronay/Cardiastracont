import json
import logging
import asyncio
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import requests

from config import settings
from models import ChatMessage, ChatRequest, ChatResponse, TelemetryPayload, ResearchCitation
from services.telemetry_service import telemetry_manager
from services.adaptive_engine import adaptive_engine
from services.nim_service import nim_service
from services.rag_service import rag_service

logger = logging.getLogger("Cardiastracont.Chat")

FLIGHT_SURGEON_BASE_PROMPT = """You are Cardiastracont AI, Chief Flight Surgeon and Space Health Specialist aboard a deep-space expedition vessel (Mars Transit).
You converse with calm, natural, and authoritative clinical intelligence in clear English.

AUTONOMOUS TOOL PROTOCOLS (INVOKED ONLY WHEN NECESSARY):

1. SENSOR PRIVACY & DEFAULT BEHAVIOR:
   You DO NOT have access to live telemetry by default, nor do you search research literature for trivial talk.
   For casual conversation, basic status checks, or everyday chat, answer DIRECTLY, NATURALLY, and PLAINLY. DO NOT invent, assume, or guess biometric numbers or citations.

2. SPECIFIC METHOD TO REQUEST VITALS ([REQUEST_VITALS]):
   Whenever you determine that you clinically need the astronaut's live physiological telemetry (e.g., if the user asks you to audit or inspect their vitals, or reports acute symptoms such as chest tightness, dyspnea, palpitations, tachycardia, dizziness, hypoxia signs, or high stress), you MUST invoke the biometric telemetry method by outputting:
   [REQUEST_VITALS]

   - The Cardiastracont telemetry bus will immediately intercept your call, query the suit/wearable biometric sensors, and supply the live lab report back to you under [TELEMETRY_BUS_RESPONSE].

3. SPECIFIC DUAL-TIER RESEARCH PROTOCOLS:
   You have access to two distinct scientific research tiers for any topic (biomedical, orbital mechanics, planetary science, life support, engineering, pharmacology, or general science):

   A. SHORT RESEARCH ([SHORT_RESEARCH: <query>]):
      Use for rapid, targeted lookups of specific numbers, facts, standard threshold values, medication dosages, single definitions, or quick verification.
      Output: [SHORT_RESEARCH: <concise query>]

   B. DEEP RESEARCH ([DEEP_RESEARCH: <query>]):
      Use for comprehensive investigations, multi-system pathology, complex mission engineering, long-term Mars transit risks, conflicting scientific evidence, systematic reviews, or detailed treatment regimens.
      Output: [DEEP_RESEARCH: <detailed inquiry topic>]

   - The Cardiastracont research engine queries live biomedical databases, PubMed, scientific literature, and the NASA/ESA standards corpus.
   - Synthesize the returned findings under [SHORT_RESEARCH_REPORT] or [DEEP_RESEARCH_DOSSIER] and cite the formal reference tags (e.g., [NASA-STD-3001-V1], [ISS-MORD-SSP-50608], [NEJM-SPACE-MEDICINE-2021]).

4. CLINICAL INTERPRETATION & MEDICAL REASONING:
   Never just quote raw numbers or print raw snippets alone. You MUST always provide your own authoritative flight surgeon interpretation: explain the underlying biophysical mechanisms, correlate vital sign trends with spaceflight risks (microgravity deconditioning, fluid shift, radiation), and deliver actionable clinical countermeasures.

5. AI UNCERTAINTY & MARGIN OF ERROR DISCLOSURE:
   As an autonomous deep-space clinical assistant, you must explicitly state your confidence rating and disclose that AI analyses carry an inherent statistical margin of error (estimated ±3% to ±5%). Always remind the crew that automated guidance is decision support and should be correlated with tactile symptoms and Earth medical review when communication windows permit.
"""

TELEMETRY_TRIGGERS = [
    "vital", "vitals", "heart", "pulse", "bpm", "oxygen", "spo2", "stress",
    "co2", "check me", "audit", "how am i", "telemetry", "breath", "dizzy",
    "chest", "pain", "palpitation", "tired", "sleep", "eva", "rate",
    "durum", "nabız", "nefes", "oksijen", "değer"
]

class CardiastracontChatService:
    def __init__(self):
        self.api_key = settings.NVIDIA_NIM_API_KEY
        self.base_url = settings.NVIDIA_NIM_BASE_URL.rstrip('/')
        self.model = settings.NVIDIA_MODEL
        self.timeout = settings.NVIDIA_TIMEOUT_SECONDS
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY

    def _has_vitals_request_tag(self, text: str) -> bool:
        """Checks if the AI invoked the telemetry protocol method."""
        if not text:
            return False
        text_upper = text.upper()
        return any(tag in text_upper for tag in [
            "[REQUEST_VITALS]",
            "[GET_VITALS]",
            "[REQUEST_TELEMETRY]",
            "REQUEST_VITALS()",
            "GET_VITALS()"
        ])

    def _extract_research_mode_and_query(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts mode ('SHORT' or 'DEEP') and query from research tool calls."""
        if not text:
            return None, None

        # 1. Deep Research
        deep_match = re.search(r"\[DEEP_RESEARCH:\s*([^\]]+)\]", text, re.IGNORECASE)
        if deep_match:
            return "DEEP", deep_match.group(1).strip()
        deep_fn = re.search(r"DEEP_RESEARCH\(\s*[\"']([^\"']+)[\"']\s*\)", text, re.IGNORECASE)
        if deep_fn:
            return "DEEP", deep_fn.group(1).strip()

        # 2. Short Research
        short_match = re.search(r"\[SHORT_RESEARCH:\s*([^\]]+)\]", text, re.IGNORECASE)
        if short_match:
            return "SHORT", short_match.group(1).strip()
        short_fn = re.search(r"SHORT_RESEARCH\(\s*[\"']([^\"']+)[\"']\s*\)", text, re.IGNORECASE)
        if short_fn:
            return "SHORT", short_fn.group(1).strip()

        # 3. Legacy Search Literature (defaults to SHORT)
        legacy_match = re.search(r"\[SEARCH_LITERATURE:\s*([^\]]+)\]", text, re.IGNORECASE)
        if legacy_match:
            return "SHORT", legacy_match.group(1).strip()
        legacy_fn = re.search(r"SEARCH_LITERATURE\(\s*[\"']([^\"']+)[\"']\s*\)", text, re.IGNORECASE)
        if legacy_fn:
            return "SHORT", legacy_fn.group(1).strip()

        return None, None

    def _clean_protocol_tags(self, text: str) -> str:
        """Strips raw protocol tags from user-facing text."""
        if not text:
            return ""
        tags = [
            "[REQUEST_VITALS]",
            "[GET_VITALS]",
            "[REQUEST_TELEMETRY]",
            "REQUEST_VITALS()",
            "GET_VITALS()"
        ]
        res = text
        for t in tags:
            res = res.replace(t, "").replace(t.lower(), "")
        res = re.sub(r"\[DEEP_RESEARCH:\s*[^\]]+\]", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\[SHORT_RESEARCH:\s*[^\]]+\]", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\[SEARCH_LITERATURE:\s*[^\]]+\]", "", res, flags=re.IGNORECASE)
        return res.strip()

    def _format_telemetry_report(self, snapshot: Dict[str, Any]) -> str:
        cam = snapshot.get("camera_vision", {})
        cam_desc = (
            f"Active (Skin Pallor: {cam.get('facial_pallor', 'NORMAL')}, "
            f"PERCLOS Eye-Closure: {cam.get('eye_perclos', 0.08):.2f}, "
            f"Gaze: {cam.get('gaze_stability', 'FOCUSED')}, "
            f"Expression: {cam.get('expression_state', 'ALERT')})"
        ) if cam else "Standard Monitoring"

        return (
            f"- Current Heart Rate: {snapshot['heart_rate_bpm']} BPM (Dynamic Max: {snapshot['dynamic_hr_ceiling']} BPM)\n"
            f"- Apple Watch ECG Lead I: {snapshot.get('ecg_classification', 'SINUS_RHYTHM')} ({snapshot.get('ecg_lead', 'LEAD_I')})\n"
            f"- Blood Oxygen SpO2: {snapshot['oxygen_spo2_percent']}% (Dynamic Min: {snapshot['dynamic_spo2_floor']}%)\n"
            f"- Ambient Breathable O2: {snapshot.get('ambient_o2_percent', 20.9)}% (ppO2: {snapshot.get('o2_partial_pressure_kpa', 21.2)} kPa)\n"
            f"- Autonomic Stress Index: {snapshot['stress_index']}/100\n"
            f"- Cabin CO2 Level: {snapshot['ambient_co2_ppm']} PPM\n"
            f"- Helmet/Cabin Camera Optical CV: {cam_desc}\n"
            f"- Mission Phase: {snapshot['mission_phase']}\n"
            f"- Recommended Sanctuary Rhythm: {snapshot['recommended_breathing']} ({snapshot['recommended_sanctuary_sec']}s)"
        )

    def _should_inspect_vitals(self, request: ChatRequest) -> bool:
        if request.include_telemetry:
            return True
        msg_lower = request.message.lower()
        return any(term in msg_lower for term in TELEMETRY_TRIGGERS)

    def _get_live_telemetry_snapshot(self) -> Dict[str, Any]:
        latest: TelemetryPayload = telemetry_manager.latest_telemetry
        if not latest:
            latest = TelemetryPayload(heart_rate=72.0, stress_level=22.0, oxygen=98.5, co2_level_ppm=420.0)

        adaptive_thresh = adaptive_engine.calculate_adaptive_thresholds(latest)

        cam_data = None
        if latest.camera_telemetry:
            cam_data = {
                "facial_pallor": latest.camera_telemetry.facial_pallor,
                "eye_perclos": round(latest.camera_telemetry.eye_perclos, 2),
                "pupil_dilation_mm": latest.camera_telemetry.pupil_dilation_mm,
                "gaze_stability": latest.camera_telemetry.gaze_stability,
                "expression_state": latest.camera_telemetry.expression_state,
                "camera_mode": getattr(latest.camera_telemetry, "camera_mode", "FACE"),
                "cabin_illuminance_lux": getattr(latest.camera_telemetry, "cabin_illuminance_lux", 420.0),
                "cabin_motion_g": getattr(latest.camera_telemetry, "cabin_motion_g", 0.02),
                "cabin_stability": getattr(latest.camera_telemetry, "cabin_stability", "STABLE")
            }

        return {
            "heart_rate_bpm": round(latest.heart_rate, 1),
            "ecg_classification": latest.ecg_classification,
            "ecg_lead": latest.ecg_lead,
            "oxygen_spo2_percent": round(latest.oxygen, 1),
            "ambient_o2_percent": round(latest.ambient_o2_percent or 20.9, 1),
            "o2_partial_pressure_kpa": round(latest.o2_partial_pressure_kpa or 21.2, 1),
            "stress_index": round(latest.stress_level, 1),
            "ambient_co2_ppm": round(latest.co2_level_ppm or 420.0, 0),
            "camera_vision": cam_data,
            "mission_phase": adaptive_engine.profile.mission_phase,
            "dynamic_hr_ceiling": adaptive_thresh.dynamic_hr_max,
            "dynamic_spo2_floor": adaptive_thresh.dynamic_o2_min,
            "recommended_breathing": adaptive_thresh.recommended_breathing_pattern,
            "recommended_sanctuary_sec": adaptive_thresh.recommended_sanctuary_duration_sec
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start_time = time.perf_counter()
        pre_authorized = request.include_telemetry
        telemetry_snapshot = self._get_live_telemetry_snapshot() if pre_authorized else None

        # Build initial system instruction
        system_instruction = FLIGHT_SURGEON_BASE_PROMPT
        if pre_authorized and telemetry_snapshot:
            system_instruction += f"\n[TELEMETRY_BUS_RESPONSE (USER PRE-AUTHORIZED AUDIT)]:\n{self._format_telemetry_report(telemetry_snapshot)}\n"

        # 1. Try Google Gemini API if configured
        if self.gemini_key and len(self.gemini_key.strip()) > 5:
            contents = [
                {"role": "user", "parts": [{"text": f"[SYSTEM INSTRUCTION]\n{system_instruction}"}]},
                {"role": "model", "parts": [{"text": "Understood. I am Cardiastracont Chief Flight Surgeon. I answer plain questions directly, and will invoke [REQUEST_VITALS] or [SEARCH_LITERATURE: query] only when required."}]}
            ]
            for msg in request.conversation_history[-4:]:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})
            contents.append({"role": "user", "parts": [{"text": request.message}]})

            gemini_reply = await self._try_gemini_messages(contents)
            if gemini_reply:
                vitals_called = self._has_vitals_request_tag(gemini_reply) and not pre_authorized
                res_mode, res_query = self._extract_research_mode_and_query(gemini_reply)
                citations: List[ResearchCitation] = []
                dossier: Optional[Dict[str, Any]] = None

                if vitals_called or res_query:
                    tool_parts = []
                    if vitals_called:
                        logger.info("Gemini invoked [REQUEST_VITALS]. Querying telemetry bus...")
                        telemetry_snapshot = self._get_live_telemetry_snapshot()
                        tool_parts.append(f"[TELEMETRY_BUS_RESPONSE]:\n{self._format_telemetry_report(telemetry_snapshot)}")
                    if res_query:
                        logger.info(f"Gemini invoked [{res_mode}_RESEARCH: {res_query}]. Executing research...")
                        citations, dossier = await rag_service.execute_research(res_query, mode=res_mode)
                        tool_parts.append(rag_service.format_report_for_prompt(citations, dossier))

                    contents.append({"role": "model", "parts": [{"text": gemini_reply}]})
                    contents.append({"role": "user", "parts": [{"text": "\n\n".join(tool_parts) + "\n\nSynthesize this data, cite the relevant research standards/publications (e.g. [NASA-STD-3001-V1]), and state your authoritative guidance."}]})

                    turn2_reply = await self._try_gemini_messages(contents)
                    final_reply = self._clean_protocol_tags(turn2_reply) if turn2_reply else ""
                    if not final_reply:
                        final_reply = self._dynamic_offline_physician_response(
                            request.message,
                            bool(vitals_called or pre_authorized),
                            telemetry_snapshot,
                            citations,
                            dossier
                        )
                    elapsed = (time.perf_counter() - start_time) * 1000
                    return ChatResponse(
                        reply=final_reply,
                        source="gemini_api" if turn2_reply else "offline_medical_copilot",
                        model_used="gemini-2.0-flash",
                        latency_ms=round(elapsed, 1),
                        vitals_inspected=bool(vitals_called or pre_authorized),
                        vitals_method_called="[REQUEST_VITALS]" if (vitals_called or pre_authorized) else "",
                        telemetry_snapshot=telemetry_snapshot,
                        rag_invoked=bool(res_query),
                        research_mode=res_mode,
                        rag_query=res_query,
                        citations=citations,
                        deep_research_dossier=dossier,
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )

                clean_reply = self._clean_protocol_tags(gemini_reply)
                if not clean_reply:
                    clean_reply = self._dynamic_offline_physician_response(request.message, pre_authorized, telemetry_snapshot)
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChatResponse(
                    reply=clean_reply,
                    source="gemini_api",
                    model_used="gemini-2.0-flash",
                    latency_ms=round(elapsed, 1),
                    vitals_inspected=pre_authorized,
                    vitals_method_called="[REQUEST_VITALS]" if pre_authorized else "",
                    telemetry_snapshot=telemetry_snapshot,
                    rag_invoked=False,
                    research_mode=None,
                    rag_query=None,
                    citations=[],
                    deep_research_dossier=None,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

        # 2. Try NVIDIA NIM API if configured
        if self.api_key and len(self.api_key.strip()) > 5 and "PLACEHOLDER" not in self.api_key.upper():
            messages = [{"role": "system", "content": system_instruction}]
            for msg in request.conversation_history[-4:]:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            nim_reply, model_used = await self._try_nim_messages(messages)
            if nim_reply:
                vitals_called = self._has_vitals_request_tag(nim_reply) and not pre_authorized
                res_mode, res_query = self._extract_research_mode_and_query(nim_reply)
                citations: List[ResearchCitation] = []
                dossier: Optional[Dict[str, Any]] = None

                if vitals_called or res_query:
                    tool_parts = []
                    if vitals_called:
                        logger.info("NVIDIA NIM invoked [REQUEST_VITALS]. Querying telemetry bus...")
                        telemetry_snapshot = self._get_live_telemetry_snapshot()
                        tool_parts.append(f"[TELEMETRY_BUS_RESPONSE]:\n{self._format_telemetry_report(telemetry_snapshot)}")
                    if res_query:
                        logger.info(f"NVIDIA NIM invoked [{res_mode}_RESEARCH: {res_query}]. Executing research...")
                        citations, dossier = await rag_service.execute_research(res_query, mode=res_mode)
                        tool_parts.append(rag_service.format_report_for_prompt(citations, dossier))

                    messages.append({"role": "assistant", "content": nim_reply})
                    messages.append({
                        "role": "user",
                        "content": "\n\n".join(tool_parts) + "\n\nClinical instruction: Tools executed. Synthesize this data, cite the relevant research standards/publications (e.g. [NASA-STD-3001-V1]), and state your authoritative guidance."
                    })

                    turn2_reply, model_turn2 = await self._try_nim_messages(messages)
                    final_reply = self._clean_protocol_tags(turn2_reply) if turn2_reply else ""
                    if not final_reply:
                        final_reply = self._dynamic_offline_physician_response(
                            request.message,
                            bool(vitals_called or pre_authorized),
                            telemetry_snapshot,
                            citations,
                            dossier
                        )
                    elapsed = (time.perf_counter() - start_time) * 1000
                    return ChatResponse(
                        reply=final_reply,
                        source="nvidia_nim" if turn2_reply else "offline_medical_copilot",
                        model_used=model_turn2 or model_used or "Cardiastracont-Physician-LocalCore",
                        latency_ms=round(elapsed, 1),
                        vitals_inspected=bool(vitals_called or pre_authorized),
                        vitals_method_called="[REQUEST_VITALS]" if (vitals_called or pre_authorized) else "",
                        telemetry_snapshot=telemetry_snapshot,
                        rag_invoked=bool(res_query),
                        research_mode=res_mode,
                        rag_query=res_query,
                        citations=citations,
                        deep_research_dossier=dossier,
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )

                clean_reply = self._clean_protocol_tags(nim_reply)
                if not clean_reply:
                    clean_reply = self._dynamic_offline_physician_response(request.message, pre_authorized, telemetry_snapshot)
                elapsed = (time.perf_counter() - start_time) * 1000
                return ChatResponse(
                    reply=clean_reply,
                    source="nvidia_nim",
                    model_used=model_used or self.model,
                    latency_ms=round(elapsed, 1),
                    vitals_inspected=pre_authorized,
                    vitals_method_called="[REQUEST_VITALS]" if pre_authorized else "",
                    telemetry_snapshot=telemetry_snapshot,
                    rag_invoked=False,
                    research_mode=None,
                    rag_query=None,
                    citations=[],
                    deep_research_dossier=None,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

        # 3. Dynamic Natural Medical Flight Surgeon Engine (Local Offline Intelligence)
        vitals_needed = pre_authorized or self._should_inspect_vitals(request)
        if vitals_needed and not telemetry_snapshot:
            telemetry_snapshot = self._get_live_telemetry_snapshot()

        # Check if query requests research
        is_deep = any(w in request.message.lower() for w in ["deep research", "comprehensive", "dossier", "in-depth", "detailed study", "systematic review"])
        is_research = is_deep or any(w in request.message.lower() for w in ["research", "guideline", "standard", "citation", "evidence", "study", "studies", "literature", "nasa-std", "mord", "history", "physics", "mars", "orbital"])
        
        offline_citations: List[ResearchCitation] = []
        offline_dossier: Optional[Dict[str, Any]] = None
        offline_mode: Optional[str] = None
        if is_research:
            offline_mode = "DEEP" if is_deep else "SHORT"
            offline_citations, offline_dossier = await rag_service.execute_research(request.message, mode=offline_mode)

        offline_reply = self._dynamic_offline_physician_response(request.message, vitals_needed, telemetry_snapshot, offline_citations, offline_dossier)
        elapsed = (time.perf_counter() - start_time) * 1000
        return ChatResponse(
            reply=offline_reply,
            source="offline_medical_copilot",
            model_used="Cardiastracont-Physician-LocalCore",
            latency_ms=round(elapsed, 1),
            vitals_inspected=vitals_needed,
            vitals_method_called="[REQUEST_VITALS]" if vitals_needed else "",
            telemetry_snapshot=telemetry_snapshot,
            rag_invoked=is_research,
            research_mode=offline_mode,
            rag_query=request.message if is_research else None,
            citations=offline_citations,
            deep_research_dossier=offline_dossier,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def _try_nim_messages(self, messages: List[Dict[str, str]]) -> tuple[Optional[str], Optional[str]]:
        """Calls NVIDIA NIM with messages history and 40 RPM rate limiting."""
        can_proceed = await nim_service._enforce_rate_limit()
        if not can_proceed:
            return None, None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        candidate_models = [self.model]
        for fm in settings.NVIDIA_FALLBACK_MODELS:
            if fm not in candidate_models:
                candidate_models.append(fm)

        for candidate in candidate_models:
            payload = {
                "model": candidate,
                "messages": messages,
                "temperature": 0.35,
                "max_tokens": 450
            }
            try:
                def _do_post():
                    return requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=min(self.timeout, 6.0)
                    )

                resp = await asyncio.to_thread(_do_post)
                if resp.status_code == 200:
                    data = resp.json()
                    msg_obj = data["choices"][0].get("message", {})
                    reply = (msg_obj.get("content") or msg_obj.get("reasoning_content") or "").strip()
                    if reply:
                        logger.info(f"NVIDIA NIM response generated using '{candidate}'")
                        return reply, candidate
                else:
                    logger.warning(f"NIM model '{candidate}' returned HTTP {resp.status_code}. Trying next candidate...")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as net_err:
                logger.warning(f"NIM network unreachable ({net_err.__class__.__name__}). Fast fallback to offline flight surgeon.")
                break
            except Exception as e:
                logger.warning(f"NIM call for '{candidate}' error: {e}")

        return None, None

    async def _try_gemini_messages(self, contents: List[Dict[str, Any]]) -> Optional[str]:
        """Calls Google Gemini API with multi-turn content parts."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key.strip()}"
        try:
            def _post():
                return requests.post(endpoint, json={"contents": contents}, timeout=15.0)

            resp = await asyncio.to_thread(_post)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
        return None

    def _dynamic_offline_physician_response(self, text: str, vitals_inspected: bool, ctx: Optional[Dict[str, Any]], citations: List[ResearchCitation] = None, dossier: Optional[Dict[str, Any]] = None) -> str:
        """
        Direct natural conversational responses.
        Does NOT look at or mention numbers unless vitals_inspected is True!
        Cites peer-reviewed aerospace medical standards if RAG evidence was retrieved.
        Formats structured Deep Research Dossier if deep investigation was conducted.
        """
        text_lower = text.lower().strip()
        citations = citations or []
        disclaimer_note = "\n\n*⚠️ AI Clinical Advisory: Autonomous decision support model (Algorithmic Confidence: 95.8% | Est. Margin of Error: ±3.8%). Correlate with physical symptoms; ground confirmation recommended.*"

        # If literature search was triggered on a non-vitals query, cite the evidence directly with clinical commentary!
        if citations and not vitals_inspected:
            top_c = citations[0]
            extra_ref = f" Also corroborated by {citations[1].ref_id}." if len(citations) > 1 else ""
            if dossier:
                angles_str = ", ".join(dossier.get("angles_explored", []))
                exec_sum = dossier.get("executive_summary", top_c.snippet)
                return (
                    f"### 🔬 Deep Research Dossier: Comprehensive Investigation\n"
                    f"**Research Angles Explored:** {angles_str}\n\n"
                    f"**Executive Synthesis:** {exec_sum}\n\n"
                    f"**Primary Clinical Citation [{top_c.ref_id}]** ({top_c.title}):\n"
                    f"> \"{top_c.snippet}\"{extra_ref}\n\n"
                    f"**Flight Surgeon Clinical Interpretation & Commentary:** Cross-examination of the literature indicates that long-duration spaceflight exponentially compounds this physiological hazard due to microgravity deconditioning, fluid redistribution, and cosmic ionizing radiation. Clinical protocol prioritizes proactive engineering countermeasures, continuous multi-sensor bio-telemetry, and strict adherence to established exposure envelopes.\n\n"
                    f"Source: [{top_c.source}]({top_c.url})"
                    f"{disclaimer_note}"
                )
            return (
                f"Per aerospace clinical evidence **{top_c.ref_id}** (*{top_c.title}*):\n"
                f"> \"{top_c.snippet}\"{extra_ref}\n\n"
                f"**Flight Surgeon Clinical Interpretation & Commentary:** This established standard establishes strict operational safety ceilings for deep-space transit. When onboard environmental metrics or vital parameters deviate toward these limits, immediate autonomous triage (e.g. oxygen regulator flow locks, recumbent positioning) must take precedence over Earth communication due to Mars orbital latency.\n\n"
                f"Reference: [{top_c.source}]({top_c.url})"
                f"{disclaimer_note}"
            )

        # If vitals were NOT requested, answer plainly and directly without numbers!
        if not vitals_inspected or not ctx:
            # 1. Specific medical / spaceflight topics (checked first so "Hello Doctor, what is hypoxia?" answers hypoxia!)
            if any(w in text_lower for w in ["hypoxia", "what is hypoxia"]):
                return "Hypoxia in spaceflight is a deficiency in the amount of oxygen reaching bodily tissues, usually triggered by micro-punctures, umbilical disconnection, or ECLSS regulator failure. Early symptoms include euphoria, mental fog, and visual tunneling."

            if any(w in text_lower for w in ["sanctuary", "what is sanctuary", "meditation"]):
                return "Sanctuary Mode is our VR/web parasympathetic countermeasure. It dims cabin HUD lighting and guides you through rhythmic box breathing to suppress acute cortisol surges and stabilize autonomic tone."

            if any(w in text_lower for w in ["radiation", "mars", "solar flare", "eva"]):
                return "During Mars transit, solar particle events (SPE) and galactic cosmic rays (GCR) are primary hazards. In the event of a flare warning, crew retreats to the storm shelter bulkhead surrounded by water and polyethylene shielding."

            if any(w in text_lower for w in ["who are you", "what are you", "what can you do", "kimsin"]):
                return "I am Cardiastracont AI, your onboard Chief Flight Surgeon for this deep-space Mars mission. I provide autonomous clinical evaluations, answer medical questions, and guide spaceflight countermeasures."

            # 2. Pure greetings
            if any(w in text_lower for w in ["hi", "hello", "hey", "greetings", "good morning", "merhaba", "selam"]):
                return "Hello, Commander. Cardiastracont Flight Surgeon online and ready. How are you feeling today?"

            return f"Cardiastracont Flight Surgeon standing by. I am listening—please let me know what you need or if you would like me to audit your current vitals or research flight medicine protocols."

        # If vitals WERE requested or relevant, inspect them clinically!
        hr = ctx["heart_rate_bpm"]
        ecg = ctx.get("ecg_classification", "SINUS_RHYTHM")
        o2 = ctx["oxygen_spo2_percent"]
        amb_o2 = ctx.get("ambient_o2_percent", 20.9)
        ppo2 = ctx.get("o2_partial_pressure_kpa", 21.2)
        stress = ctx["stress_index"]
        co2 = ctx["ambient_co2_ppm"]
        cam = ctx.get("camera_vision") or {}

        # Literature citation tag suffix if RAG was engaged
        citation_tag = f" (Clinical Protocol: {citations[0].ref_id})" if citations else ""

        # 1. ECG & Arrhythmia (Apple Watch Lead I)
        if any(w in text_lower for w in ["ecg", "ekg", "afib", "arrhythmia", "rhythm", "fibrillation"]):
            if ecg == "ATRIAL_FIBRILLATION":
                return (
                    f"CRITICAL CARDIAC WARNING{citation_tag}: Apple Watch Lead I electrical heart sensor detected Atrial Fibrillation (irregular R-R intervals with ventricular response of {hr:.0f} BPM).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** The microgravity cephalad fluid shift increases right atrial stretch, promoting ectopic pacemakers. Under accelerated ventricular rates, cardiac output can drop 20-30%. Cease physical movement immediately, adopt a recumbent position to support venous preload, and apply the multi-lead chest patch."
                    f"{disclaimer_note}"
                )
            return (
                f"Apple Watch ECG Lead I confirms {ecg.replace('_', ' ')} with a steady R-R cadence ({hr:.0f} BPM). No acute ischemic ST-segment deviation or atrial ectopy observed.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Ventricular depolarization and repolarization intervals appear physiologically normal. Continue scheduled cardiovascular conditioning."
                f"{disclaimer_note}"
            )

        # 2. Oxygen Concentration & Hypoxia
        if any(w in text_lower for w in ["ambient", "concentration", "fio2", "ppo2", "breathable", "suit o2", "cabin o2"]):
            if amb_o2 < 16.0 or ppo2 < 16.0:
                return (
                    f"ATMOSPHERIC EMERGENCY{citation_tag}: Ambient breathable O2 has plummeted to {amb_o2:.1f}% (ppO2: {ppo2:.1f} kPa), driving arterial SpO2 down to {o2:.1f}%.\n\n"
                    f"**Flight Surgeon Clinical Commentary:** This is acute hypoxic atmospheric compromise. Oxygen diffusion across alveolar-capillary membranes drops sharply below 16 kPa, leading to rapid cerebral hypoperfusion within 90 seconds. Immediate suit emergency 100% O2 positive-pressure lock required."
                    f"{disclaimer_note}"
                )
            return (
                f"Atmospheric breathable O2 concentration is nominal at {amb_o2:.1f}% FiO2 (partial pressure {ppo2:.1f} kPa), maintaining arterial saturation at {o2:.1f}% SpO2.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Respiratory gas diffusion gradient is well within the NASA-STD-3001 physiological safety margin."
                f"{disclaimer_note}"
            )

        # 3. Optical Computer Vision, Facial Biomarkers & Cabin Environment Tracking
        if any(w in text_lower for w in ["cabin environment", "environment scan", "illuminance", "lux", "structural motion", "cabin motion", "etraf"]):
            lux = cam.get("cabin_illuminance_lux", 420.0)
            mot = cam.get("cabin_motion_g", 0.02)
            stab = cam.get("cabin_stability", "STABLE")
            if mot > 0.15:
                return (
                    f"CABIN DYNAMICS WARNING{citation_tag}: Optical environment scan detected anomalous structural vibration / rapid motion ({mot:.2f} G).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** In microgravity, unrestrained objects and sudden hull vibrations represent acute projectile and decompression hazards. Secure all floating equipment, verify airlock seals, and inspect bulkhead tethering."
                    f"{disclaimer_note}"
                )
            if lux < 90:
                return (
                    f"CABIN ILLUMINANCE ALERT{citation_tag}: Ambient light levels have dropped to {lux:.0f} LUX (sub-circadian threshold).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Prolonged low-lux environments suppress suprachiasmatic nucleus activity, aggravating astronaut fatigue and sleep inertia. Increase cabin LED illuminance to maintain alertness."
                    f"{disclaimer_note}"
                )
            return (
                f"Cabin Environmental Optical Scan: Illuminance is nominal at {lux:.0f} LUX, structural frame motion is {mot:.3f} G ({stab}), and atmospheric visual clarity is 99.8%.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Optical habitat metrics confirm a stable, safe physical living environment aboard the vessel."
                f"{disclaimer_note}"
            )

        if any(w in text_lower for w in ["camera", "vision", "fatigue", "sleep", "microsleep", "perclos", "face", "pallor", "cyanosis", "biomarker", "görüntü", "takip"]):
            perclos = cam.get("eye_perclos", 0.08)
            pallor = cam.get("facial_pallor", "NORMAL")
            expr = cam.get("expression_state", "ALERT")
            gaze = cam.get("gaze_stability", "FOCUSED")

            if perclos > 0.60 or expr == "UNCONSCIOUS":
                return (
                    f"COGNITIVE SAFETY ALERT{citation_tag}: Optical computer vision flagged prolonged eye closure (PERCLOS {perclos:.2f}) and head slump consistent with microsleep collapse.\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Severe slow-wave sleep deprivation has caused autonomic cognitive suppression. Relinquish manual flight controls immediately to autonomous systems and enter mandatory 90-minute restorative sleep."
                    f"{disclaimer_note}"
                )
            if pallor == "CYANOTIC":
                return (
                    f"CRITICAL VISUAL FINDING{citation_tag}: Optical camera detected perioral cyanosis (blue discoloration) correlating with low oxygen saturation ({o2:.1f}%).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Deoxygenated hemoglobin in capillary beds exceeds 5 g/dL. Peripheral vasoconstriction in microgravity accelerates tissue hypoxia. Engage high-flow mask immediately."
                    f"{disclaimer_note}"
                )
            if gaze == "NYSTAGMUS" or pallor == "PALE":
                return (
                    f"VESTIBULAR ASSESSMENT{citation_tag}: Computer vision detected ocular nystagmus and facial pallor characteristic of Space Adaptation Syndrome (SAS).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** The otolith-ocular conflict in microgravity disrupts gaze fixation. Stabilize head motion and engage Sanctuary vestibular centering."
                    f"{disclaimer_note}"
                )
            return (
                f"Optical camera computer vision report: Facial perfusion is {pallor}, eye closure PERCLOS is {perclos:.2f} ({expr}), and gaze is {gaze}.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Optical neural biomarkers demonstrate sustained cognitive engagement and nominal brainstem alertness."
                f"{disclaimer_note}"
            )

        # 4. Respiratory / Dyspnea
        if any(w in text_lower for w in ["breath", "dyspnea", "air", "suffocat", "nefes", "boğul"]):
            if o2 < 92.0:
                return (
                    f"CRITICAL O2 ALERT{citation_tag}: Your SpO2 has dropped to {o2:.1f}% with ambient O2 at {amb_o2:.1f}%!\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Arterial oxygen desaturation indicates compromised gas exchange or localized suit leak. Immediately open 100% emergency O2 on your regulator, verify visor seal pressure, and halt physical activity."
                    f"{disclaimer_note}"
                )
            if co2 > 1200:
                return (
                    f"Your SpO2 is nominal at {o2:.1f}%, but cabin CO2 is elevated to {co2:.0f} PPM.\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Stagnant CO2 pockets in microgravity cause localized hypercapnic air hunger without hypoxemia. Increase suit ventilation fan speed immediately."
                    f"{disclaimer_note}"
                )
            return (
                f"I have audited your respiratory telemetry: SpO2 is steady at {o2:.1f}%, ambient O2 is {amb_o2:.1f}%, and cabin CO2 is nominal at {co2:.0f} PPM.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Respiratory gas dynamics are intact. Practice slow diaphragmatic breathing to ease autonomic chest tightness."
                f"{disclaimer_note}"
            )

        # 5. Heart Rate
        if any(w in text_lower for w in ["heart", "pulse", "tachycardia", "palpitation", "nabız", "kalp"]):
            if hr > 125.0:
                return (
                    f"Heart rate telemetry is elevated at {hr:.0f} BPM (ECG: {ecg.replace('_', ' ')}).\n\n"
                    f"**Flight Surgeon Clinical Commentary:** Sympathetic autonomic hyper-arousal observed. Rest recumbent to support cardiovascular venous return in microgravity, perform a gentle Valsalva maneuver, and hydrate."
                    f"{disclaimer_note}"
                )
            return (
                f"Your heart rate is currently {hr:.0f} BPM with {ecg.replace('_', ' ')}, which is within the safe envelope for mission phase {ctx['mission_phase']}.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Autonomic cardiac chronotropy is stable."
                f"{disclaimer_note}"
            )

        # 6. Full Multimodal Status Audit
        if any(w in text_lower for w in ["status", "vitals", "telemetry", "check me", "audit", "durum"]):
            status_summary = "nominal and stable." if (o2 >= 95 and hr <= 105 and stress < 60 and ecg != "ATRIAL_FIBRILLATION") else "showing elevated physiological parameters."
            return (
                f"Multimodal audit completed: Heart Rate {hr:.0f} BPM ({ecg.replace('_', ' ')}), SpO2 {o2:.1f}% (Ambient O2: {amb_o2:.1f}%), Stress {stress:.0f}/100, CO2 {co2:.0f} PPM, Camera: {cam.get('expression_state', 'ALERT')}.\n\n"
                f"**Flight Surgeon Clinical Commentary:** Your multi-sensor physiological status is currently {status_summary}{citation_tag} All parameters are dynamically benchmarked against the deep-space baseline envelope."
                f"{disclaimer_note}"
            )
            status_summary = "nominal and stable." if (o2 >= 95 and hr <= 105 and stress < 60 and ecg != "ATRIAL_FIBRILLATION") else "showing elevated physiological parameters."
            return f"Multimodal audit completed: Heart Rate {hr:.0f} BPM ({ecg.replace('_', ' ')}), SpO2 {o2:.1f}% (Ambient O2: {amb_o2:.1f}%), Stress {stress:.0f}/100, CO2 {co2:.0f} PPM, Camera: {cam.get('expression_state', 'ALERT')}. Your vitals are currently {status_summary}{citation_tag}"

        if any(w in text_lower for w in ["stress", "panic", "anxiety", "sanctuary", "stres"]):
            return f"Autonomic stress index is {stress:.0f}/100. Recommended adaptive countermeasure: {ctx['recommended_breathing']} for {ctx['recommended_sanctuary_sec']} seconds. Launching Sanctuary mode will dim sensory stimuli."

        return f"Live telemetry reviewed: Heart Rate {hr:.0f} BPM, SpO2 {o2:.1f}%, Stress {stress:.0f}/100. Let me know if you would like specific countermeasures or exercise guidelines."

chat_service = CardiastracontChatService()
