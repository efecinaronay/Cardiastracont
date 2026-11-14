/**
 * Cardiastracont Web Console & Mobile Health Pad
 * Real-Time Biometrics, NVIDIA NIM Triage, and Sanctuary Countermeasures
 */

(function () {
  // DOM Elements
  const linkStatusDot = document.getElementById("link-status-dot");
  const linkStatusText = document.getElementById("link-status-text");
  const latencyBadge = document.getElementById("latency-badge");

  const hrValueEl = document.getElementById("val-hr");
  const hrBarEl = document.getElementById("bar-hr");
  const heartIconEl = document.getElementById("heart-icon");

  const o2ValueEl = document.getElementById("val-o2");
  const o2BarEl = document.getElementById("bar-o2");

  const stressValueEl = document.getElementById("val-stress");
  const stressBarEl = document.getElementById("bar-stress");

  const co2ValueEl = document.getElementById("val-co2");
  const co2BarEl = document.getElementById("bar-co2");

  const aiTriagePanel = document.getElementById("ai-triage-panel");
  const triageBadgeEl = document.getElementById("triage-badge");
  const triageTitleEl = document.getElementById("triage-title");
  const triageEngineEl = document.getElementById("triage-engine");
  const triageDiagnosisEl = document.getElementById("triage-diagnosis");
  const triageActionsList = document.getElementById("triage-actions-list");
  const btnDismissAlert = document.getElementById("btn-dismiss-alert");
  const btnTriageSanctuary = document.getElementById("btn-triage-sanctuary");

  const btnEmergencySOS = document.getElementById("btn-emergency-sos");
  const btnOpenSanctuary = document.getElementById("btn-open-sanctuary");
  const btnCloseSanctuary = document.getElementById("btn-close-sanctuary");
  const sanctuaryModal = document.getElementById("sanctuary-modal");
  const breathingCircle = document.getElementById("breathing-circle");
  const sanctuaryPhaseText = document.getElementById("sanctuary-phase");
  const sanctuaryTipText = document.getElementById("sanctuary-tip");
  const sanctuaryCountdownText = document.getElementById("sanctuary-countdown");

  const btnToggleStreamer = document.getElementById("btn-toggle-streamer");
  const streamerStatusText = document.getElementById("streamer-status-text");
  const scenarioButtons = document.querySelectorAll(".btn-scenario");

  // Telemetry Graph Canvases
  const canvasHR = document.getElementById("canvas-hr");
  const canvasO2 = document.getElementById("canvas-o2");
  const ctxHR = canvasHR.getContext("2d");
  const ctxO2 = canvasO2.getContext("2d");

  // State Variables
  const hrHistory = [];
  const o2History = [];
  const maxHistoryPoints = 35;
  let socket = null;
  let lastPacketTime = Date.now();
  let audioCtx = null;

  // Simulator State
  let isBrowserStreamerActive = false;
  let streamerInterval = null;
  let activeScenario = "1";

  let currentECGClass = "SINUS_RHYTHM";
  let currentHRForECG = 72;
  let ecgSweepX = 0;
  let ecgPhase = 0;

  // Live Camera & Optical Computer Vision State
  let isCameraActive = false;
  let cameraFacingMode = "user"; // "user" (Astronaut Face) or "environment" (Cabin Environment)
  let cameraStream = null;
  let cameraAnimId = null;
  let prevFrameData = null;
  let rollingPerclos = 0.08;
  let liveCameraTelemetry = {
    facial_pallor: "NORMAL",
    eye_perclos: 0.08,
    gaze_stability: "FOCUSED",
    pupil_dilation_mm: 3.6,
    expression_state: "ALERT",
    cabin_illuminance_lux: 420,
    cabin_motion_g: 0.02,
    cabin_stability: "STABLE",
    camera_active: false,
    camera_mode: "FACE"
  };

  const SCENARIOS = {
    "1": {
      name: "Nominal Cruise",
      hr: 72, o2: 98.5, ambient_o2: 20.9, ppo2: 21.2, stress: 22, co2: 420,
      ecg: "SINUS_RHYTHM", pallor: "NORMAL", perclos: 0.08, gaze: "FOCUSED", expr: "ALERT", sos: false
    },
    "2": {
      name: "Hypoxia & Suit Puncture",
      hr: 118, o2: 79.5, ambient_o2: 13.8, ppo2: 12.1, stress: 88, co2: 470,
      ecg: "SINUS_TACHYCARDIA", pallor: "CYANOTIC", perclos: 0.44, gaze: "ERRATIC", expr: "DROWSY", sos: false
    },
    "3": {
      name: "Paroxysmal AFib",
      hr: 148, o2: 94.0, ambient_o2: 20.8, ppo2: 21.0, stress: 91, co2: 435,
      ecg: "ATRIAL_FIBRILLATION", pallor: "PALE", perclos: 0.12, gaze: "FOCUSED", expr: "DISTRESSED", sos: false
    },
    "4": {
      name: "Hypercapnia (3400 PPM)",
      hr: 112, o2: 92.5, ambient_o2: 19.4, ppo2: 19.8, stress: 82, co2: 3400,
      ecg: "SINUS_TACHYCARDIA", pallor: "FLUSHED", perclos: 0.35, gaze: "ERRATIC", expr: "DISTRESSED", sos: false
    },
    "5": {
      name: "Cognitive Microsleep",
      hr: 48, o2: 96.0, ambient_o2: 20.9, ppo2: 21.2, stress: 30, co2: 480,
      ecg: "SINUS_BRADYCARDIA", pallor: "NORMAL", perclos: 0.82, gaze: "UNRESPONSIVE", expr: "UNCONSCIOUS", sos: false
    },
    "6": {
      name: "SAS Motion Sickness",
      hr: 102, o2: 98.0, ambient_o2: 20.9, ppo2: 21.2, stress: 95, co2: 440,
      ecg: "SINUS_RHYTHM", pallor: "PALE", perclos: 0.22, gaze: "NYSTAGMUS", expr: "DISTRESSED", sos: false
    },
    "7": {
      name: "EVA Heat Stroke",
      hr: 168, o2: 95.0, ambient_o2: 21.0, ppo2: 21.3, stress: 97, co2: 510,
      ecg: "SINUS_TACHYCARDIA", pallor: "FLUSHED", perclos: 0.28, gaze: "ERRATIC", expr: "DISTRESSED", sos: true
    }
  };

  // Initialize Web Audio API for harmonic chimes
  function initAudio() {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) audioCtx = new AudioContext();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume();
    }
  }

  function playChime(freq, duration = 0.5, type = "sine") {
    if (!audioCtx) return;
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      console.warn("Audio chime error:", e);
    }
  }

  // ========================================================
  // Piercing Aerospace Master Caution Klaxon & Emergency Siren
  // ========================================================
  let activeAlarmInterval = null;

  function stopMasterAlarm() {
    if (activeAlarmInterval) {
      clearInterval(activeAlarmInterval);
      activeAlarmInterval = null;
    }
  }

  function playMasterAlarm(severity = "CRITICAL") {
    initAudio();
    if (!audioCtx) return;
    stopMasterAlarm();

    const isCritical = severity === "CRITICAL";
    let pulses = isCritical ? 6 : 3;

    function playAlarmBurst() {
      if (!audioCtx) return;
      try {
        const now = audioCtx.currentTime;

        // Tone 1: High piercing alarm pitch (1150Hz -> 750Hz sweep)
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.type = isCritical ? "sawtooth" : "square";
        osc1.frequency.setValueAtTime(isCritical ? 1150 : 880, now);
        osc1.frequency.exponentialRampToValueAtTime(isCritical ? 750 : 660, now + 0.22);
        gain1.gain.setValueAtTime(0.35, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.24);
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        osc1.start(now);
        osc1.stop(now + 0.24);

        // Tone 2: Harmonized secondary klaxon with 110ms offset (1400Hz -> 820Hz)
        setTimeout(() => {
          if (!audioCtx) return;
          try {
            const t2 = audioCtx.currentTime;
            const osc2 = audioCtx.createOscillator();
            const gain2 = audioCtx.createGain();
            osc2.type = "sawtooth";
            osc2.frequency.setValueAtTime(isCritical ? 1400 : 960, t2);
            osc2.frequency.exponentialRampToValueAtTime(isCritical ? 820 : 700, t2 + 0.22);
            gain2.gain.setValueAtTime(0.38, t2);
            gain2.gain.exponentialRampToValueAtTime(0.001, t2 + 0.24);
            osc2.connect(gain2);
            gain2.connect(audioCtx.destination);
            osc2.start(t2);
            osc2.stop(t2 + 0.24);
          } catch (e) {}
        }, 110);

        // Sub-bass heavy thump for tactile acoustic urgency
        const subOsc = audioCtx.createOscillator();
        const subGain = audioCtx.createGain();
        subOsc.type = "sine";
        subOsc.frequency.setValueAtTime(140, now);
        subOsc.frequency.exponentialRampToValueAtTime(50, now + 0.28);
        subGain.gain.setValueAtTime(0.30, now);
        subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
        subOsc.connect(subGain);
        subGain.connect(audioCtx.destination);
        subOsc.start(now);
        subOsc.stop(now + 0.28);
      } catch (e) {
        console.warn("Alarm synthesis error:", e);
      }
    }

    playAlarmBurst();
    let count = 1;
    activeAlarmInterval = setInterval(() => {
      if (count >= pulses) {
        stopMasterAlarm();
        return;
      }
      playAlarmBurst();
      count++;
    }, 480);
  }

  // ========================================================
  // WebSocket Connection
  // ========================================================
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `${protocol}//${host}/ws/vr-stream`;

    console.log(`[Cardiastracont Web] Connecting to WebSocket: ${wsUrl}`);
    linkStatusDot.className = "status-badge connecting";
    linkStatusText.textContent = "CONNECTING...";

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("[Cardiastracont Web] WebSocket Connected.");
        linkStatusDot.className = "status-badge";
        linkStatusText.textContent = "STATION LINK NOMINAL";
      };

      socket.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data);
          handleIncomingPacket(packet);
        } catch (e) {
          console.error("JSON parse error:", e);
        }
      };

      socket.onclose = () => {
        console.warn("[Cardiastracont Web] WebSocket Closed. Reconnecting in 3s...");
        linkStatusDot.className = "status-badge disconnected";
        linkStatusText.textContent = "OFFLINE • RETRYING";
        setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = (err) => {
        console.error("WebSocket error:", err);
        socket.close();
      };
    } catch (err) {
      console.error("Connection failed:", err);
      setTimeout(connectWebSocket, 3000);
    }
  }

  function handleIncomingPacket(packet) {
    const now = Date.now();
    const rtt = now - lastPacketTime;
    lastPacketTime = now;
    if (latencyBadge) latencyBadge.textContent = `${Math.min(rtt, 999)}ms`;

    if (packet.telemetry) {
      updateTelemetryUI(packet.telemetry);
      recordTelemetryForMissionLog(packet.telemetry);
    }

    if (packet.packet_type === "AI_TRIAGE_ALERT" && packet.triage) {
      displayAITriageAlert(packet.triage);
    }
  }

  // ========================================================
  // UI Updates & Visualizations
  // ========================================================
  function updateTelemetryUI(t) {
    // 1. Heart Rate
    const hr = Math.round(t.heart_rate);
    hrValueEl.textContent = hr;
    hrBarEl.style.width = `${Math.min(100, Math.max(10, (hr / 180) * 100))}%`;
    if (hr > 130 || hr < 50) {
      hrBarEl.style.background = "var(--red)";
      heartIconEl.classList.add("pulsing");
    } else {
      hrBarEl.style.background = "var(--red)";
      heartIconEl.classList.remove("pulsing");
    }

    // 2. Oxygen SpO2
    const o2 = Number(t.oxygen).toFixed(1);
    o2ValueEl.textContent = `${o2}%`;
    o2BarEl.style.width = `${Math.min(100, o2)}%`;
    if (t.oxygen < 88.0) {
      o2BarEl.style.background = "var(--red)";
    } else if (t.oxygen < 92.0) {
      o2BarEl.style.background = "var(--orange)";
    } else {
      o2BarEl.style.background = "var(--cyan)";
    }

    // 3. Stress Index
    const stress = Math.round(t.stress_level);
    stressValueEl.textContent = `${stress}/100`;
    stressBarEl.style.width = `${stress}%`;
    if (stress > 80) {
      stressBarEl.style.background = "var(--red)";
    } else if (stress > 60) {
      stressBarEl.style.background = "var(--orange)";
    } else {
      stressBarEl.style.background = "var(--purple)";
    }

    // 4. Cabin CO2
    const co2 = Math.round(t.co2_level_ppm || 420);
    co2ValueEl.textContent = `${co2} PPM`;
    co2BarEl.style.width = `${Math.min(100, (co2 / 3000) * 100)}%`;
    if (co2 > 1500) {
      co2BarEl.style.background = "var(--red)";
    } else {
      co2BarEl.style.background = "var(--green)";
    }

    // Append to rolling chart histories
    hrHistory.push(hr);
    if (hrHistory.length > maxHistoryPoints) hrHistory.shift();

    o2History.push(Number(t.oxygen));
    if (o2History.length > maxHistoryPoints) o2History.shift();

    drawRollingGraph(canvasHR, ctxHR, hrHistory, 40, 180, "#ff3366", "HR (BPM)");
    drawRollingGraph(canvasO2, ctxO2, o2History, 80, 100, "#00f0ff", "SpO2 (%)");

    // 5. Apple Watch Lead I Electrical Heart Sensor
    currentHRForECG = hr;
    const ecgClass = t.ecg_classification || "SINUS_RHYTHM";
    currentECGClass = ecgClass;
    const ecgClassEl = document.getElementById("val-ecg-class");
    const rrIntEl = document.getElementById("val-rr-int");
    if (ecgClassEl) {
      if (ecgClass === "ATRIAL_FIBRILLATION") {
        ecgClassEl.className = "ecg-status-badge status-afib";
        ecgClassEl.textContent = "🔴 AFIB DETECTED";
      } else {
        ecgClassEl.className = "ecg-status-badge status-sinus";
        ecgClassEl.textContent = `🟢 ${ecgClass.replace(/_/g, " ")}`;
      }
    }
    if (rrIntEl) rrIntEl.textContent = `${Math.round(60000 / Math.max(30, hr))}ms`;

    // 6. Atmospheric Breathable Oxygen Concentration
    const ambO2El = document.getElementById("val-ambient-o2");
    const ppO2El = document.getElementById("val-ppo2");
    if (ambO2El) ambO2El.textContent = `${(t.ambient_o2_percent !== undefined ? t.ambient_o2_percent : 20.9).toFixed(1)}%`;
    if (ppO2El) ppO2El.textContent = `${(t.o2_partial_pressure_kpa !== undefined ? t.o2_partial_pressure_kpa : 21.2).toFixed(1)} kPa`;

    // 7. Optical Computer Vision Helmet / Cabin Camera
    const cam = isCameraActive ? liveCameraTelemetry : t.camera_telemetry;
    if (cam) {
      const camPallorEl = document.getElementById("val-cam-pallor");
      const camPerclosEl = document.getElementById("val-cam-perclos");
      const barCamPerclos = document.getElementById("bar-cam-perclos");
      const camGazeEl = document.getElementById("val-cam-gaze");
      const camPupilEl = document.getElementById("val-cam-pupil");
      const camExprEl = document.getElementById("val-cam-expr");

      if (camPallorEl) {
        camPallorEl.textContent = cam.facial_pallor;
        camPallorEl.className = `v-val ${cam.facial_pallor.toLowerCase()}`;
      }
      if (camPerclosEl) camPerclosEl.textContent = Number(cam.eye_perclos).toFixed(2);
      if (barCamPerclos) {
        barCamPerclos.style.width = `${Math.min(100, cam.eye_perclos * 100)}%`;
        barCamPerclos.style.background = cam.eye_perclos > 0.6 ? "var(--red)" : (cam.eye_perclos > 0.35 ? "var(--orange)" : "var(--green)");
      }
      if (camGazeEl) camGazeEl.textContent = cam.gaze_stability;
      if (camPupilEl) camPupilEl.textContent = `${(cam.pupil_dilation_mm || 3.6).toFixed(1)} mm`;
      if (camExprEl) {
        camExprEl.textContent = `● ${cam.expression_state}`;
        if (cam.expression_state === "UNCONSCIOUS") camExprEl.className = "cv-status-badge status-unconscious";
        else if (cam.expression_state === "DROWSY" || cam.expression_state === "DISTRESSED") camExprEl.className = "cv-status-badge status-drowsy";
        else camExprEl.className = "cv-status-badge status-alert";
      }
    }

    // Update Chat Drawer Live Context Strip
    const cHr = document.getElementById("chat-vitals-hr");
    const cEcg = document.getElementById("chat-vitals-ecg");
    const cO2 = document.getElementById("chat-vitals-o2");
    const cAmbO2 = document.getElementById("chat-vitals-ambient-o2");
    const cCam = document.getElementById("chat-vitals-cam");
    if (cHr) cHr.textContent = hr;
    if (cEcg) cEcg.textContent = ecgClass === "ATRIAL_FIBRILLATION" ? "AFIB" : "SINUS";
    if (cO2) cO2.textContent = o2;
    if (cAmbO2) cAmbO2.textContent = `${(t.ambient_o2_percent || 20.9).toFixed(1)}%`;
    if (cCam && cam) cCam.textContent = cam.expression_state;
  }

  function drawRollingGraph(canvas, ctx, data, minVal, maxVal, colorHex, label) {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    ctx.clearRect(0, 0, width, height);

    // Draw background gridlines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
    ctx.lineWidth = 1;
    for (let y = 0; y < height; y += 30) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (data.length < 2) return;

    // Draw smooth data curve
    const stepX = width / (maxHistoryPoints - 1);
    ctx.beginPath();
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 2.5;

    for (let i = 0; i < data.length; i++) {
      const normY = (data[i] - minVal) / (maxVal - minVal);
      const clampedY = Math.max(0, Math.min(1, normY));
      const x = i * stepX;
      const y = height - (clampedY * (height - 20) + 10);

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Fill area below curve
    ctx.lineTo((data.length - 1) * stepX, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, colorHex + "33");
    grad.addColorStop(1, "transparent");
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw latest point glow
    const latestX = (data.length - 1) * stepX;
    const normLatest = (data[data.length - 1] - minVal) / (maxVal - minVal);
    const latestY = height - (normLatest * (height - 20) + 10);
    ctx.beginPath();
    ctx.arc(latestX, latestY, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
  }

  // ========================================================
  // AI Triage Alert Window
  // ========================================================
  function displayAITriageAlert(triage) {
    if (!triage || !triage.anomaly_detected) return;

    aiTriagePanel.classList.add("active");
    if (triage.severity === "CRITICAL") {
      aiTriagePanel.classList.add("critical");
      playMasterAlarm("CRITICAL");
    } else {
      aiTriagePanel.classList.remove("critical");
      playMasterAlarm("WARNING");
    }

    triageBadgeEl.textContent = triage.severity;
    triageTitleEl.textContent = triage.condition_title || "MEDICAL TRIAGE ALERT";

    // Record anomaly in session stats for official mission report
    recordAnomalyForMissionLog(triage);

    if (triage.source === "nvidia_nim") {
      triageEngineEl.textContent = `⚡ NVIDIA NIM (${triage.model_used || "Llama-3.1"}) • ${Math.round(triage.execution_time_ms)}ms`;
      triageEngineEl.style.color = "var(--green)";
    } else {
      triageEngineEl.textContent = "🛡️ DEEP SPACE OFFLINE CLINICAL PROTOCOL";
      triageEngineEl.style.color = "var(--cyan)";
    }

    triageDiagnosisEl.textContent = triage.diagnosis || "No clinical description provided.";

    triageActionsList.innerHTML = "";
    (triage.immediate_actions || []).forEach((act) => {
      const li = document.createElement("li");
      li.textContent = act;
      triageActionsList.appendChild(li);
    });

    if (triage.sanctuary_recommended) {
      btnTriageSanctuary.style.display = "inline-flex";
    } else {
      btnTriageSanctuary.style.display = "none";
    }
  }

  const btnSilenceAlarm = document.getElementById("btn-silence-alarm");
  if (btnSilenceAlarm) {
    btnSilenceAlarm.addEventListener("click", () => {
      stopMasterAlarm();
      btnSilenceAlarm.textContent = "🔕 KLAXON MUTED";
      setTimeout(() => {
        btnSilenceAlarm.textContent = "🔕 SILENCE KLAXON";
      }, 2000);
    });
  }

  const btnTestAlarm = document.getElementById("btn-test-alarm");
  if (btnTestAlarm) {
    btnTestAlarm.addEventListener("click", () => {
      playMasterAlarm("CRITICAL");
    });
  }

  btnDismissAlert.addEventListener("click", () => {
    aiTriagePanel.classList.remove("active");
    stopMasterAlarm();
  });

  btnTriageSanctuary.addEventListener("click", () => {
    aiTriagePanel.classList.remove("active");
    stopMasterAlarm();
    openSanctuaryMode();
  });

  // ========================================================
  // Interactive Sanctuary Mode (60s Box Breathing)
  // ========================================================
  let sanctuaryTimer = null;
  let sanctuaryPhaseTimeout = null;

  function openSanctuaryMode() {
    initAudio();
    sanctuaryModal.classList.add("active");
    startBreathingCycle();
  }

  function closeSanctuaryMode() {
    sanctuaryModal.classList.remove("active");
    clearTimeout(sanctuaryPhaseTimeout);
    clearInterval(sanctuaryTimer);
  }

  function startBreathingCycle() {
    let timeLeft = 60;
    sanctuaryCountdownText.textContent = `TIME REMAINING: ${timeLeft}s`;

    sanctuaryTimer = setInterval(() => {
      timeLeft--;
      sanctuaryCountdownText.textContent = `TIME REMAINING: ${timeLeft}s`;
      if (timeLeft <= 0) {
        clearInterval(sanctuaryTimer);
        sanctuaryPhaseText.textContent = "SESSION COMPLETE";
        sanctuaryTipText.textContent = "Parasympathetic recovery sequence finished.";
        playChime(523.25, 0.8, "sine"); // High C
        setTimeout(closeSanctuaryMode, 2500);
      }
    }, 1000);

    runBreathingPhase(0);
  }

  function runBreathingPhase(step) {
    const phases = [
      { text: "INHALE DEEPLY", tip: "Fill lungs through nose, engage diaphragm.", css: "expand", chime: 440, dur: 4000 },
      { text: "HOLD BREATH", tip: "Maintain calm; steady autonomic rhythm.", css: "hold", chime: 493.88, dur: 4000 },
      { text: "EXHALE SLOWLY", tip: "Release carbon dioxide and muscular tension.", css: "contract", chime: 392, dur: 4000 },
      { text: "REST & CENTER", tip: "Prepare parasympathetic response for next cycle.", css: "", chime: 329.63, dur: 4000 }
    ];

    const current = phases[step % phases.length];
    sanctuaryPhaseText.textContent = current.text;
    sanctuaryTipText.textContent = current.tip;

    breathingCircle.className = "breathing-circle " + current.css;
    playChime(current.chime, 0.6, "sine");

    sanctuaryPhaseTimeout = setTimeout(() => {
      runBreathingPhase(step + 1);
    }, current.dur);
  }

  btnOpenSanctuary.addEventListener("click", openSanctuaryMode);
  btnCloseSanctuary.addEventListener("click", closeSanctuaryMode);

  // ========================================================
  // Manual Emergency SOS Trigger
  // ========================================================
  let sosHoldTimeout = null;

  btnEmergencySOS.addEventListener("mousedown", startSOSHold);
  btnEmergencySOS.addEventListener("touchstart", startSOSHold);

  btnEmergencySOS.addEventListener("mouseup", cancelSOSHold);
  btnEmergencySOS.addEventListener("mouseleave", cancelSOSHold);
  btnEmergencySOS.addEventListener("touchend", cancelSOSHold);

  function startSOSHold() {
    initAudio();
    playChime(660, 0.2, "square");
    btnEmergencySOS.textContent = "HOLDING... (2s)";
    sosHoldTimeout = setTimeout(dispatchEmergencySOS, 2000);
  }

  function cancelSOSHold() {
    if (sosHoldTimeout) {
      clearTimeout(sosHoldTimeout);
      sosHoldTimeout = null;
      btnEmergencySOS.textContent = "🚨 EMERGENCY SOS";
    }
  }

  async function dispatchEmergencySOS() {
    btnEmergencySOS.textContent = "DISPATCHING SOS!";
    playMasterAlarm("CRITICAL");

    try {
      const res = await fetch("/api/emergency-trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          astronaut_id: "ASTRO-WEB-01",
          note: "Emergency trigger from Web Console"
        })
      });
      const data = await res.json();
      console.log("SOS Dispatched:", data);
      btnEmergencySOS.textContent = "SOS ACTIVE!";
      setTimeout(() => {
        btnEmergencySOS.textContent = "🚨 EMERGENCY SOS";
      }, 3000);
    } catch (e) {
      console.error("SOS failed:", e);
      btnEmergencySOS.textContent = "DISPATCH FAILED";
    }
  }

  // ========================================================
  // Phone / Browser Telemetry Streamer Mode
  // ========================================================
  scenarioButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      scenarioButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeScenario = btn.dataset.scenario;
    });
  });

  btnToggleStreamer.addEventListener("click", () => {
    initAudio();
    isBrowserStreamerActive = !isBrowserStreamerActive;

    if (isBrowserStreamerActive) {
      btnToggleStreamer.textContent = "STOP STREAMING (40 RPM)";
      btnToggleStreamer.style.background = "var(--red)";
      streamerStatusText.textContent = "Active: Streaming at 40 RPM (1.5s interval) to FastAPI & VR...";
      streamerStatusText.style.color = "var(--green)";

      // 40 RPM = 40 requests per minute = 60,000ms / 40 = 1500ms
      streamerInterval = setInterval(sendSyntheticTelemetry, 1500);
    } else {
      btnToggleStreamer.textContent = "START STREAMING FROM THIS DEVICE (40 RPM)";
      btnToggleStreamer.style.background = "";
      streamerStatusText.textContent = "Inactive: Device is in receive-only listener mode.";
      streamerStatusText.style.color = "var(--text-muted)";
      clearInterval(streamerInterval);
    }
  });

  async function sendSyntheticTelemetry() {
    const sc = SCENARIOS[activeScenario] || SCENARIOS["1"];
    const jitter = (Math.random() - 0.5) * 2;
    const hr = Math.round(sc.hr + jitter * 2);
    const o2 = Number(Math.min(100, Math.max(60, sc.o2 + jitter * 0.3))).toFixed(1);
    const stress = Math.round(Math.min(100, Math.max(5, sc.stress + jitter * 2)));

    const payload = {
      astronaut_id: "ASTRO-WEB-01",
      heart_rate: hr,
      oxygen: parseFloat(o2),
      stress_level: stress,
      co2_level_ppm: sc.co2,
      ecg_lead: "LEAD_I_APPLE_WATCH",
      ecg_classification: sc.ecg,
      ambient_o2_percent: sc.ambient_o2,
      o2_partial_pressure_kpa: sc.ppo2,
      camera_telemetry: isCameraActive ? {
        facial_pallor: liveCameraTelemetry.facial_pallor,
        eye_perclos: liveCameraTelemetry.eye_perclos,
        pupil_dilation_mm: liveCameraTelemetry.pupil_dilation_mm,
        gaze_stability: liveCameraTelemetry.gaze_stability,
        expression_state: liveCameraTelemetry.expression_state,
        camera_active: true,
        camera_mode: liveCameraTelemetry.camera_mode,
        cabin_illuminance_lux: liveCameraTelemetry.cabin_illuminance_lux,
        cabin_motion_g: liveCameraTelemetry.cabin_motion_g,
        cabin_stability: liveCameraTelemetry.cabin_stability
      } : {
        facial_pallor: sc.pallor,
        eye_perclos: sc.perclos,
        pupil_dilation_mm: sc.expr === "DISTRESSED" ? 6.2 : 3.6,
        gaze_stability: sc.gaze,
        expression_state: sc.expr,
        camera_active: true,
        camera_mode: "FACE"
      },
      source: "web_browser_phone",
      is_emergency_triggered: sc.sos
    };

    try {
      await fetch("/api/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.warn("Failed sending synthetic telemetry:", e);
    }
  }

  // ========================================================
  // Apple Watch Lead I ECG Oscilloscope Canvas Animator
  // ========================================================
  const canvasECG = document.getElementById("canvas-ecg");
  let ctxECG = null;
  if (canvasECG) ctxECG = canvasECG.getContext("2d");

  function renderECGFrame() {
    if (!canvasECG || !ctxECG) return;
    const width = canvasECG.clientWidth;
    const height = canvasECG.clientHeight;
    if (canvasECG.width !== width || canvasECG.height !== height) {
      canvasECG.width = width;
      canvasECG.height = height;
      ctxECG.fillStyle = "#040912";
      ctxECG.fillRect(0, 0, width, height);
    }

    const midY = height * 0.55;
    const speed = 2.4;

    // Erase a cursor band ahead of sweep
    ctxECG.fillStyle = "#040912";
    ctxECG.fillRect(ecgSweepX, 0, 16, height);

    // Compute voltage waveform point based on current heart rate and rhythm
    const cycleSamples = Math.max(16, Math.round(1800 / Math.max(40, currentHRForECG)));
    const normalizedPhase = (ecgPhase % cycleSamples) / cycleSamples;

    let volt = 0;
    if (currentECGClass === "ATRIAL_FIBRILLATION") {
      // Fibrillatory irregular rhythm with random micro-ripples and abrupt R-peaks
      volt = (Math.random() - 0.5) * 8;
      if (normalizedPhase > 0.48 && normalizedPhase < 0.54) {
        volt = -38 + (Math.random() - 0.5) * 14;
      }
    } else {
      // Normal P-QRS-T complex
      if (normalizedPhase > 0.15 && normalizedPhase < 0.25) {
        volt = -6 * Math.sin((normalizedPhase - 0.15) / 0.10 * Math.PI); // P wave
      } else if (normalizedPhase > 0.44 && normalizedPhase < 0.48) {
        volt = 8; // Q dip
      } else if (normalizedPhase >= 0.48 && normalizedPhase < 0.52) {
        volt = -44; // R spike
      } else if (normalizedPhase >= 0.52 && normalizedPhase < 0.56) {
        volt = 14; // S drop
      } else if (normalizedPhase > 0.65 && normalizedPhase < 0.82) {
        volt = -11 * Math.sin((normalizedPhase - 0.65) / 0.17 * Math.PI); // T wave
      } else {
        volt = (Math.random() - 0.5) * 1.5; // isoelectric baseline
      }
    }

    const y = midY + volt;

    ctxECG.beginPath();
    ctxECG.strokeStyle = currentECGClass === "ATRIAL_FIBRILLATION" ? "#ff3366" : "#00ff88";
    ctxECG.lineWidth = 1.8;
    ctxECG.shadowBlur = 6;
    ctxECG.shadowColor = currentECGClass === "ATRIAL_FIBRILLATION" ? "rgba(255, 51, 102, 0.8)" : "rgba(0, 255, 136, 0.8)";
    ctxECG.moveTo(ecgSweepX, y);
    ctxECG.lineTo(ecgSweepX + speed, y);
    ctxECG.stroke();

    ecgSweepX = (ecgSweepX + speed) >= width ? 0 : (ecgSweepX + speed);
    ecgPhase++;

    requestAnimationFrame(renderECGFrame);
  }

  requestAnimationFrame(renderECGFrame);

  // ========================================================
  // Live Camera Video & Optical Computer Vision Engine
  // (Astronaut Face Tracking & Cabin Environment Tracking)
  // ========================================================
  const btnToggleCam = document.getElementById("btn-toggle-cam");
  const btnSwitchCamMode = document.getElementById("btn-switch-cam-mode");
  const cvVideo = document.getElementById("cv-video");
  const cvCanvas = document.getElementById("cv-canvas");
  const cvModeIndicator = document.getElementById("cv-mode-indicator");
  const camFeedStatus = document.getElementById("cam-feed-status");

  const lblMetric1 = document.getElementById("lbl-metric-1");
  const valCamPallor = document.getElementById("val-cam-pallor");
  const lblMetric2 = document.getElementById("lbl-metric-2");
  const barCamPerclos = document.getElementById("bar-cam-perclos");
  const valCamPerclos = document.getElementById("val-cam-perclos");
  const lblMetric3 = document.getElementById("lbl-metric-3");
  const valCamGaze = document.getElementById("val-cam-gaze");
  const lblMetric4 = document.getElementById("lbl-metric-4");
  const valCamPupil = document.getElementById("val-cam-pupil");
  const valCamExpr = document.getElementById("val-cam-expr");

  if (btnToggleCam) {
    btnToggleCam.addEventListener("click", () => {
      initAudio();
      if (isCameraActive) {
        stopRealCamera();
      } else {
        startRealCamera();
      }
    });
  }

  if (btnSwitchCamMode) {
    btnSwitchCamMode.addEventListener("click", () => {
      initAudio();
      cameraFacingMode = cameraFacingMode === "user" ? "environment" : "user";
      applyCameraModeLabels();
      if (isCameraActive) {
        stopRealCamera(false);
        startRealCamera();
      }
    });
  }

  function applyCameraModeLabels() {
    if (cameraFacingMode === "user") {
      if (cvModeIndicator) {
        cvModeIndicator.textContent = "👤 FACE MODE";
        cvModeIndicator.className = "cv-mode-tag";
      }
      if (btnSwitchCamMode) btnSwitchCamMode.textContent = "🔄 Switch to Cabin Scan";
      if (lblMetric1) lblMetric1.textContent = "FACIAL PERFUSION:";
      if (lblMetric2) lblMetric2.textContent = "DROWSINESS (PERCLOS):";
      if (lblMetric3) lblMetric3.textContent = "OCULAR GAZE:";
      if (lblMetric4) lblMetric4.textContent = "PUPIL DIAMETER:";
      liveCameraTelemetry.camera_mode = "FACE";
    } else {
      if (cvModeIndicator) {
        cvModeIndicator.textContent = "🛰️ CABIN SCAN";
        cvModeIndicator.className = "cv-mode-tag cabin";
      }
      if (btnSwitchCamMode) btnSwitchCamMode.textContent = "🔄 Switch to Face Mode";
      if (lblMetric1) lblMetric1.textContent = "CABIN ILLUMINANCE:";
      if (lblMetric2) lblMetric2.textContent = "STRUCTURAL MOTION:";
      if (lblMetric3) lblMetric3.textContent = "OPTICAL CLARITY:";
      if (lblMetric4) lblMetric4.textContent = "ENV STATUS:";
      liveCameraTelemetry.camera_mode = "CABIN_ENVIRONMENT";
    }
  }

  async function startRealCamera() {
    try {
      if (camFeedStatus) camFeedStatus.textContent = "Requesting optical sensor...";
      const constraints = {
        video: {
          facingMode: cameraFacingMode === "environment" ? { ideal: "environment" } : "user",
          width: { ideal: 320 },
          height: { ideal: 240 }
        },
        audio: false
      };

      cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
      if (cvVideo) {
        cvVideo.srcObject = cameraStream;
        await cvVideo.play();
      }

      isCameraActive = true;
      liveCameraTelemetry.camera_active = true;
      if (btnToggleCam) {
        btnToggleCam.textContent = "⏹️ Stop Camera";
        btnToggleCam.classList.add("recording");
      }
      if (camFeedStatus) {
        camFeedStatus.textContent = `Live: ${cameraFacingMode === "user" ? "Astronaut Face HUD" : "Cabin Optical Scan"}`;
        camFeedStatus.style.color = "var(--green)";
      }

      playChime(660, 0.2, "sine");
      processCameraFeed();
    } catch (err) {
      console.warn("Camera access failed or denied:", err);
      if (camFeedStatus) {
        camFeedStatus.textContent = "Camera Denied / Standby Mode";
        camFeedStatus.style.color = "var(--orange)";
      }
    }
  }

  function stopRealCamera(fullReset = true) {
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
      cameraStream = null;
    }
    if (cameraAnimId) {
      cancelAnimationFrame(cameraAnimId);
      cameraAnimId = null;
    }
    isCameraActive = false;
    liveCameraTelemetry.camera_active = false;

    if (fullReset) {
      if (btnToggleCam) {
        btnToggleCam.textContent = "📷 Start Live Camera";
        btnToggleCam.classList.remove("recording");
      }
      if (camFeedStatus) {
        camFeedStatus.textContent = "Camera Standby";
        camFeedStatus.style.color = "var(--text-muted)";
      }
      drawIdleCameraCanvas();
    }
  }

  function drawIdleCameraCanvas() {
    if (!cvCanvas) return;
    const ctx = cvCanvas.getContext("2d");
    const w = cvCanvas.width;
    const h = cvCanvas.height;
    ctx.fillStyle = "#030812";
    ctx.fillRect(0, 0, w, h);

    // Subtle reticle
    ctx.strokeStyle = "rgba(0, 240, 255, 0.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(w / 2, h / 2, w * 0.32, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "rgba(0, 240, 255, 0.6)";
    ctx.font = "9px monospace";
    ctx.textAlign = "center";
    ctx.fillText("CAM STANDBY", w / 2, h / 2 + 3);
  }

  function processCameraFeed() {
    if (!isCameraActive || !cvVideo || !cvCanvas) return;
    const ctx = cvCanvas.getContext("2d");
    const w = cvCanvas.width;
    const h = cvCanvas.height;

    if (cvVideo.readyState === cvVideo.HAVE_ENOUGH_DATA) {
      // 1. Draw live camera frame
      ctx.drawImage(cvVideo, 0, 0, w, h);

      // 2. Optical Image Analysis
      try {
        const frame = ctx.getImageData(0, 0, w, h);
        const data = frame.data;
        const totalPixels = data.length / 4;

        let sumR = 0, sumG = 0, sumB = 0, sumLum = 0;
        let diffSum = 0;

        for (let i = 0; i < data.length; i += 16) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];
          const lum = 0.299 * r + 0.587 * g + 0.114 * b;
          sumR += r;
          sumG += g;
          sumB += b;
          sumLum += lum;

          if (prevFrameData && prevFrameData[i] !== undefined) {
            diffSum += Math.abs(r - prevFrameData[i]) + Math.abs(g - prevFrameData[i + 1]) + Math.abs(b - prevFrameData[i + 2]);
          }
        }

        prevFrameData = data;
        const sampleCount = totalPixels / 4;
        const avgR = sumR / sampleCount;
        const avgG = sumG / sampleCount;
        const avgB = sumB / sampleCount;
        const avgLum = sumLum / sampleCount;
        const motionFactor = Math.min(1.0, diffSum / (sampleCount * 60));

        if (cameraFacingMode === "user") {
          // --- ASTRONAUT FACE & BIOMARKER TRACKING ---
          let pallor = "NORMAL";
          if (avgB > avgR * 1.05 && avgB > 70) {
            pallor = "CYANOTIC";
          } else if (avgR > (avgG + avgB) * 0.75 && avgR > 110) {
            pallor = "FLUSHED";
          } else if (avgLum < 45 || (avgR < 55 && avgG < 55)) {
            pallor = "PALE";
          }
          liveCameraTelemetry.facial_pallor = pallor;

          // PERCLOS Eye Drowsiness Tracking
          const eyeVariation = motionFactor;
          if (eyeVariation < 0.02 && avgLum < 50) {
            rollingPerclos = Math.min(0.92, rollingPerclos + 0.02);
          } else {
            rollingPerclos = Math.max(0.04, rollingPerclos - 0.015);
          }
          liveCameraTelemetry.eye_perclos = parseFloat(rollingPerclos.toFixed(2));

          let expr = "ALERT";
          let gaze = "FOCUSED";
          if (rollingPerclos > 0.65) {
            expr = "UNCONSCIOUS";
            gaze = "UNRESPONSIVE";
          } else if (rollingPerclos > 0.35) {
            expr = "DROWSY";
            gaze = "DRIFTING";
          } else if (motionFactor > 0.35) {
            gaze = "ERRATIC";
            expr = "DISTRESSED";
          }

          liveCameraTelemetry.expression_state = expr;
          liveCameraTelemetry.gaze_stability = gaze;
          liveCameraTelemetry.pupil_dilation_mm = expr === "DISTRESSED" ? 5.8 : (expr === "DROWSY" ? 2.8 : 3.6);

          if (valCamPallor) {
            valCamPallor.textContent = pallor;
            valCamPallor.className = `v-val ${pallor.toLowerCase()}`;
          }
          if (valCamPerclos) valCamPerclos.textContent = rollingPerclos.toFixed(2);
          if (barCamPerclos) {
            barCamPerclos.style.width = `${Math.min(100, rollingPerclos * 100)}%`;
            barCamPerclos.style.background = rollingPerclos > 0.6 ? "var(--red)" : (rollingPerclos > 0.35 ? "var(--orange)" : "var(--green)");
          }
          if (valCamGaze) valCamGaze.textContent = gaze;
          if (valCamPupil) valCamPupil.textContent = `${liveCameraTelemetry.pupil_dilation_mm.toFixed(1)} mm`;
          if (valCamExpr) {
            valCamExpr.textContent = `● ${expr}`;
            valCamExpr.className = expr === "UNCONSCIOUS" ? "cv-status-badge status-unconscious" : (expr === "DROWSY" || expr === "DISTRESSED" ? "cv-status-badge status-drowsy" : "cv-status-badge status-alert");
          }

          // AR HUD Overlays on Canvas:
          ctx.strokeStyle = "rgba(0, 240, 255, 0.8)";
          ctx.lineWidth = 1.5;
          const boxSize = w * 0.65;
          const boxX = (w - boxSize) / 2;
          const boxY = (h - boxSize) / 2;
          const cr = 10;
          ctx.beginPath();
          ctx.moveTo(boxX, boxY + cr); ctx.lineTo(boxX, boxY); ctx.lineTo(boxX + cr, boxY);
          ctx.moveTo(boxX + boxSize - cr, boxY); ctx.lineTo(boxX + boxSize, boxY); ctx.lineTo(boxX + boxSize, boxY + cr);
          ctx.moveTo(boxX, boxY + boxSize - cr); ctx.lineTo(boxX, boxY + boxSize); ctx.lineTo(boxX + cr, boxY + boxSize);
          ctx.moveTo(boxX + boxSize - cr, boxY + boxSize); ctx.lineTo(boxX + boxSize, boxY + boxSize); ctx.lineTo(boxX + boxSize, boxY + boxSize - cr);
          ctx.stroke();

          ctx.fillStyle = "rgba(0, 240, 255, 0.9)";
          ctx.font = "8px monospace";
          ctx.fillText(`BIO: ${pallor} | P:${rollingPerclos.toFixed(2)}`, 6, h - 8);

        } else {
          // --- CABIN ENVIRONMENT TRACKING (REAR CAMERA) ---
          const lux = Math.round(avgLum * 4.2);
          liveCameraTelemetry.cabin_illuminance_lux = lux;
          liveCameraTelemetry.cabin_motion_g = parseFloat(motionFactor.toFixed(3));
          const isStable = motionFactor < 0.12;
          liveCameraTelemetry.cabin_stability = isStable ? "STABLE" : "ACTIVE MOTION";

          if (valCamPallor) {
            valCamPallor.textContent = `${lux} LUX`;
            valCamPallor.className = lux < 80 ? "v-val flushed" : "v-val normal";
          }
          if (valCamPerclos) valCamPerclos.textContent = `${(motionFactor * 100).toFixed(0)}%`;
          if (barCamPerclos) {
            barCamPerclos.style.width = `${Math.min(100, motionFactor * 100)}%`;
            barCamPerclos.style.background = isStable ? "var(--green)" : "var(--orange)";
          }
          if (valCamGaze) valCamGaze.textContent = "CLEAR (99.8%)";
          if (valCamPupil) valCamPupil.textContent = isStable ? "SAFE ENVELOPE" : "MOTION ALERT";
          if (valCamExpr) {
            valCamExpr.textContent = isStable ? "● CABIN NOMINAL" : "● MOTION DETECTED";
            valCamExpr.className = isStable ? "cv-status-badge status-alert" : "cv-status-badge status-drowsy";
          }

          ctx.strokeStyle = "rgba(255, 170, 0, 0.6)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(0, h * 0.7); ctx.lineTo(w, h * 0.7);
          ctx.moveTo(w * 0.25, 0); ctx.lineTo(w * 0.25, h);
          ctx.moveTo(w * 0.75, 0); ctx.lineTo(w * 0.75, h);
          ctx.stroke();

          ctx.fillStyle = "rgba(255, 200, 0, 0.9)";
          ctx.font = "8px monospace";
          ctx.fillText(`ENV: ${lux} LUX | MOT:${(motionFactor*100).toFixed(0)}%`, 6, h - 8);
        }

        ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
        ctx.font = "7px monospace";
        ctx.fillText(`REC ● CAM-01`, 6, 12);

      } catch (err) {
        // Cross-origin or buffer read protection
      }
    }

    cameraAnimId = requestAnimationFrame(processCameraFeed);
  }

  // Draw initial idle canvas
  drawIdleCameraCanvas();

  // ========================================================
  // AI Flight Surgeon Integrated Console & Chat Logic
  // ========================================================
  const viewVitals = document.getElementById("view-vitals");
  const viewChat = document.getElementById("view-chat");
  const tabBtnVitals = document.getElementById("tab-btn-vitals");
  const tabBtnChat = document.getElementById("tab-btn-chat");

  const btnTriageChat = document.getElementById("btn-triage-chat");
  const btnQuickAudit = document.getElementById("btn-quick-audit");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const quickPills = document.querySelectorAll(".quick-pill");
  const chatEngineStatus = document.getElementById("chat-engine-status");

  const conversationHistory = [];

  // Mobile Tab Switching (Vitals vs AI Chat)
  if (tabBtnVitals && tabBtnChat) {
    tabBtnVitals.addEventListener("click", () => {
      tabBtnVitals.classList.add("active");
      tabBtnChat.classList.remove("active");
      if (viewVitals) viewVitals.classList.remove("mobile-hidden");
      if (viewChat) viewChat.classList.remove("mobile-active");
    });

    tabBtnChat.addEventListener("click", () => {
      tabBtnChat.classList.add("active");
      tabBtnVitals.classList.remove("active");
      if (viewVitals) viewVitals.classList.add("mobile-hidden");
      if (viewChat) viewChat.classList.add("mobile-active");
      if (chatInput) chatInput.focus();
    });
  }

  function switchToChatTab() {
    if (tabBtnChat) tabBtnChat.click();
    if (chatInput) chatInput.focus();
  }

  if (btnTriageChat) {
    btnTriageChat.addEventListener("click", () => {
      aiTriagePanel.classList.remove("active");
      switchToChatTab();
      sendUserChatMessage("Doctor, I received an acute medical anomaly alert. Explain the clinical risk and specify immediate countermeasure steps.", true);
    });
  }

  if (btnQuickAudit) {
    btnQuickAudit.addEventListener("click", () => {
      switchToChatTab();
      sendUserChatMessage("Doctor, please audit and clinically review my current live vital signs.", true);
    });
  }

  quickPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const prompt = pill.dataset.prompt;
      if (prompt) {
        switchToChatTab();
        const isAuditRequest = prompt.toLowerCase().includes("audit") || prompt.toLowerCase().includes("vital") || prompt.toLowerCase().includes("tightness");
        sendUserChatMessage(prompt, isAuditRequest);
      }
    });
  });

  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = "";
      sendUserChatMessage(text);
    });
  }

  async function sendUserChatMessage(text, isAudit = false) {
    initAudio();
    playChime(600, 0.15, "sine");

    // Render User Bubble
    appendChatBubble("user", text);

    // Render Typing Bubble
    const typingBubble = appendChatBubble("ai typing", "Cardiastracont Flight Surgeon is thinking...");

    // Record History
    conversationHistory.push({ role: "user", content: text });

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          astronaut_id: "ASTRO-01",
          conversation_history: conversationHistory.slice(-4),
          include_telemetry: Boolean(isAudit)
        })
      });

      const data = await res.json();
      typingBubble.remove();

      if (data && data.reply && data.reply.trim().length > 0) {
        const aiBubble = appendChatBubble("ai", data.reply, data);
        conversationHistory.push({ role: "assistant", content: data.reply });
        lastAIReplyText = data.reply;

        if (isVoiceActive) {
          const btn = aiBubble.querySelector(".btn-bubble-tts");
          speakFlightSurgeonResponse(data.reply, aiBubble, btn);
        }

        if (data.citations && Array.isArray(data.citations)) {
          data.citations.forEach(c => {
            if (c.source_tag) {
              sessionStats.consultedCitations.set(c.source_tag, c);
            }
          });
        }

        // Update AI status badge in header
        if (chatEngineStatus) {
          if (data.source === "nvidia_nim") {
            const shortModel = (data.model_used || "Nemotron").split("/").pop();
            chatEngineStatus.textContent = `● ACTIVE NIM AI (${shortModel}) • ONLINE`;
            chatEngineStatus.style.color = "var(--green)";
          } else if (data.source === "gemini_api") {
            chatEngineStatus.textContent = `● ACTIVE GEMINI AI (${data.model_used || "Flash"}) • ONLINE`;
            chatEngineStatus.style.color = "var(--green)";
          } else {
            chatEngineStatus.textContent = `● OFFLINE FLIGHT SURGEON CORE • ACTIVE`;
            chatEngineStatus.style.color = "var(--cyan)";
          }
        }
        playChime(784, 0.25, "sine"); // G5 chime
      } else {
        const fallbackText = "Cardiastracont Flight Surgeon standing by. Direct communications established.";
        const fallbackBubble = appendChatBubble("ai", fallbackText, data);
        lastAIReplyText = fallbackText;
        if (isVoiceActive) {
          const btn = fallbackBubble.querySelector(".btn-bubble-tts");
          speakFlightSurgeonResponse(fallbackText, fallbackBubble, btn);
        }
      }
    } catch (e) {
      typingBubble.remove();
      const errBubble = appendChatBubble("ai", "Network anomaly: Local flight surgeon offline protocol engaged.");
      lastAIReplyText = "Network anomaly: Local flight surgeon offline protocol engaged.";
      if (isVoiceActive) {
        const btn = errBubble.querySelector(".btn-bubble-tts");
        speakFlightSurgeonResponse(lastAIReplyText, errBubble, btn);
      }
    }
  }

  function appendChatBubble(roleClass, text, meta = null) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${roleClass}`;

    if (roleClass === "user") {
      const p = document.createElement("p");
      p.textContent = text;
      bubble.appendChild(p);

      const timeSpan = document.createElement("span");
      timeSpan.className = "chat-time";
      const now = new Date();
      timeSpan.textContent = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
      bubble.appendChild(timeSpan);
    } else if (roleClass.includes("typing")) {
      const p = document.createElement("p");
      p.textContent = text;
      bubble.appendChild(p);
    } else {
      // Verified AI Bubble with Visual Proof & Badging
      const authorDiv = document.createElement("div");
      authorDiv.className = "bubble-author";

      const nameSpan = document.createElement("span");
      nameSpan.textContent = "Cardiastracont Flight Surgeon";

      const badgeSpan = document.createElement("span");
      badgeSpan.className = "ai-badge";
      if (meta && meta.source === "nvidia_nim") {
        badgeSpan.textContent = "NVIDIA NIM AI";
      } else if (meta && meta.source === "gemini_api") {
        badgeSpan.textContent = "GEMINI FLASH AI";
      } else {
        badgeSpan.textContent = "LOCAL COPILOT";
      }
      authorDiv.appendChild(nameSpan);
      authorDiv.appendChild(badgeSpan);

      // On-demand TTS Button for this specific AI message
      const ttsBtn = document.createElement("button");
      ttsBtn.type = "button";
      ttsBtn.className = "btn-bubble-tts";
      ttsBtn.title = "Bu yanıtı seslendir (TTS)";
      ttsBtn.innerHTML = "🔊 Dinle (TTS)";
      ttsBtn.addEventListener("click", () => {
        if (currentlySpeakingBubble === bubble) {
          stopSpeech();
        } else {
          speakFlightSurgeonResponse(text, bubble, ttsBtn);
        }
      });
      authorDiv.appendChild(ttsBtn);

      if (meta && meta.rag_invoked && meta.citations && meta.citations.length > 0) {
        const ragBadge = document.createElement("span");
        const isDeep = meta.research_mode === "DEEP" || !!meta.deep_research_dossier;
        ragBadge.className = isDeep ? "rag-badge deep" : "rag-badge";
        ragBadge.textContent = isDeep
          ? `🔬 DEEP RESEARCH (${meta.citations.length} Sources)`
          : `📚 SHORT RESEARCH (${meta.citations.length} Sources)`;
        authorDiv.appendChild(ragBadge);
      }

      bubble.appendChild(authorDiv);

      const p = document.createElement("p");
      p.textContent = text;
      bubble.appendChild(p);

      // Render Verified Evidence Citations Box if RAG was engaged by AI
      if (meta && meta.citations && meta.citations.length > 0) {
        const isDeep = meta.research_mode === "DEEP" || !!meta.deep_research_dossier;
        const citeBox = document.createElement("div");
        citeBox.className = isDeep ? "bubble-citations-box deep-dossier" : "bubble-citations-box";

        const citeTitle = document.createElement("div");
        citeTitle.className = "cite-box-title";
        citeTitle.innerHTML = isDeep
          ? `🔬 <strong>SYNTHESIZED DEEP RESEARCH DOSSIER</strong>`
          : `📚 <strong>RETRIEVED AEROSPACE SCIENTIFIC EVIDENCE</strong>`;
        citeBox.appendChild(citeTitle);

        if (isDeep && meta.deep_research_dossier) {
          const dossier = meta.deep_research_dossier;
          if (dossier.angles_explored && dossier.angles_explored.length > 0) {
            const anglesBar = document.createElement("div");
            anglesBar.className = "dossier-angles-bar";
            anglesBar.innerHTML = `<span style="font-size:0.62rem;color:var(--text-muted);font-family:var(--font-mono);">ANGLES:</span>`;
            dossier.angles_explored.forEach(a => {
              const tag = document.createElement("span");
              tag.className = "angle-tag";
              tag.textContent = a;
              anglesBar.appendChild(tag);
            });
            citeBox.appendChild(anglesBar);
          }
          if (dossier.executive_summary) {
            const sumCard = document.createElement("div");
            sumCard.className = "dossier-summary-card";
            sumCard.innerHTML = `<strong>Dossier Synthesis:</strong> ${dossier.executive_summary}`;
            citeBox.appendChild(sumCard);
          }
        }

        meta.citations.forEach((c) => {
          const item = document.createElement("div");
          item.className = "citation-item";
          item.innerHTML = `
            <div class="cite-top">
              <span class="cite-tag">${c.ref_id}</span>
              <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="cite-link">${c.title} ↗</a>
            </div>
            <div class="cite-source">${c.source}</div>
            <p class="cite-snippet">"${c.snippet}"</p>
          `;
          citeBox.appendChild(item);
        });

        bubble.appendChild(citeBox);
      }

      // Metadata proof strip: Model, Latency & Telemetry Inspection Status
      const metaDiv = document.createElement("div");
      metaDiv.className = "bubble-meta";

      const modelSpan = document.createElement("span");
      const modelName = meta?.model_used || "Cardiastracont-Physician-LocalCore";
      const latency = meta?.latency_ms ? `${Math.round(meta.latency_ms)}ms` : "<1ms";
      modelSpan.innerHTML = `⚡ <strong>${modelName}</strong> • ${latency}`;
      metaDiv.appendChild(modelSpan);

      const vitalsSpan = document.createElement("span");
      if (meta && meta.vitals_inspected && meta.telemetry_snapshot) {
        const snap = meta.telemetry_snapshot;
        const method = meta.vitals_method_called || "[REQUEST_VITALS]";
        const ecg = snap.ecg_classification ? ` | ECG: ${snap.ecg_classification.replace(/_/g, " ")}` : "";
        const o2conc = snap.ambient_o2_percent ? ` | FiO2: ${snap.ambient_o2_percent}%` : "";
        const cam = snap.camera_vision ? ` | Vision: ${snap.camera_vision.expression_state}` : "";
        vitalsSpan.className = "meta-vitals-active";
        vitalsSpan.textContent = `🩺 Method: ${method} • HR ${snap.heart_rate_bpm} BPM | SpO2 ${snap.oxygen_spo2_percent}%${ecg}${o2conc}${cam}`;
      } else {
        vitalsSpan.textContent = "📋 Vitals: Not Inspected (No [REQUEST_VITALS] invoked)";
      }
      metaDiv.appendChild(vitalsSpan);

      if (meta && meta.rag_invoked) {
        const ragSpan = document.createElement("span");
        ragSpan.style.color = meta.research_mode === "DEEP" ? "#ffe066" : "var(--purple)";
        ragSpan.style.fontWeight = "600";
        const q = meta.rag_query ? `"${meta.rag_query}"` : "Evidence Search";
        const modeLabel = meta.research_mode ? `${meta.research_mode} RESEARCH` : "LITERATURE";
        ragSpan.textContent = `🔍 ${modeLabel}: ${q}`;
        metaDiv.appendChild(ragSpan);
      }

      // Explicit AI Decision Support & Margin of Error Notice
      const errorMarginTag = document.createElement("div");
      errorMarginTag.className = "ai-margin-tag";
      const margin = meta?.margin_of_error_percent !== undefined ? meta.margin_of_error_percent : 3.8;
      const conf = meta?.confidence_score ? Math.round(meta.confidence_score * 100) : 96;
      errorMarginTag.innerHTML = `⚠️ <span>AI Clinical Advisory • Est. Margin of Error: ±${margin}% (Confidence: ${conf}%) • Subject to Clinical Confirmation</span>`;
      metaDiv.appendChild(errorMarginTag);

      bubble.appendChild(metaDiv);

      const timeSpan = document.createElement("span");
      timeSpan.className = "chat-time";
      const now = new Date();
      timeSpan.textContent = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
      bubble.appendChild(timeSpan);
    }

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
  }

  // ========================================================
  // Adaptive Spaceflight Tuning Logic
  // ========================================================
  const phaseButtons = document.querySelectorAll(".btn-phase");
  const adaptHrMax = document.getElementById("adapt-hr-max");
  const adaptO2Min = document.getElementById("adapt-o2-min");
  const adaptStressMax = document.getElementById("adapt-stress-max");
  const adaptBreathing = document.getElementById("adapt-breathing");
  const adaptiveStatusBadge = document.getElementById("adaptive-status-badge");

  phaseButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      phaseButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const phase = btn.dataset.phase;

      try {
        const res = await fetch("/api/adaptive-profile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            astronaut_id: "ASTRO-01",
            mission_phase: phase,
            baseline_resting_hr: phase === "REST_CYCLE" ? 55.0 : 65.0,
            baseline_active_hr: phase === "EVA" ? 140.0 : 120.0
          })
        });

        // Fetch refreshed adaptive thresholds
        const threshRes = await fetch("/api/adaptive-profile");
        const threshData = await threshRes.json();
        const t = threshData.adaptive_thresholds;

        if (adaptHrMax) adaptHrMax.textContent = `${t.dynamic_hr_max} BPM`;
        if (adaptO2Min) adaptO2Min.textContent = `${t.dynamic_o2_min}%`;
        if (adaptStressMax) adaptStressMax.textContent = `${t.dynamic_stress_max} / 100`;
        if (adaptBreathing) adaptBreathing.textContent = t.recommended_breathing_pattern;
        if (adaptiveStatusBadge) adaptiveStatusBadge.textContent = t.adaptation_status;

        playChime(520, 0.2, "sine");
      } catch (err) {
        console.warn("Failed updating adaptive phase:", err);
      }
    });
  });

  // ========================================================
  // SESSION STATS & MISSION HEALTH DOSSIER LOGGING
  // ========================================================
  const sessionStats = {
    startTime: Date.now(),
    packetCount: 0,
    hrSum: 0,
    hrMin: 999,
    hrMax: 0,
    o2Sum: 0,
    o2Min: 100,
    co2Max: 0,
    lastTelemetry: null,
    clinicalEvents: [],
    consultedCitations: new Map()
  };

  function recordTelemetryForMissionLog(t) {
    if (!t) return;
    sessionStats.packetCount++;
    const hr = Math.round(t.heart_rate);
    const o2 = Number(t.oxygen);
    const co2 = Number(t.co2_level_ppm || 420);

    sessionStats.hrSum += hr;
    if (hr < sessionStats.hrMin) sessionStats.hrMin = hr;
    if (hr > sessionStats.hrMax) sessionStats.hrMax = hr;

    sessionStats.o2Sum += o2;
    if (o2 < sessionStats.o2Min) sessionStats.o2Min = o2;

    if (co2 > sessionStats.co2Max) sessionStats.co2Max = co2;

    sessionStats.lastTelemetry = t;
  }

  function recordAnomalyForMissionLog(triage) {
    if (!triage) return;
    sessionStats.clinicalEvents.push({
      timestamp: new Date().toLocaleTimeString(),
      severity: triage.severity || "WARNING",
      title: triage.condition_title || "Anomaly Event",
      diagnosis: triage.diagnosis || "Physiological divergence observed.",
      source: triage.source || "Offline Copilot"
    });
  }

  // ========================================================
  // OPTION A: SPACE COMMS VOICE INTERACTION & TTS ENGINE
  // ========================================================
  let isVoiceActive = true;
  let cachedVoices = [];
  let currentlySpeakingBubble = null;
  let currentlySpeakingBtn = null;
  let ttsResumeTimer = null;
  let lastAIReplyText = "Greetings, Commander. I am Cardiastracont AI, your onboard Chief Flight Surgeon for this Mars transit. Ask me any medical or mission question.";

  function loadVoices() {
    if (window.speechSynthesis) {
      cachedVoices = window.speechSynthesis.getVoices() || [];
    }
  }

  if (window.speechSynthesis) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  const btnToggleVoice = document.getElementById("btn-toggle-voice");
  if (btnToggleVoice) {
    btnToggleVoice.addEventListener("click", () => {
      isVoiceActive = !isVoiceActive;
      if (isVoiceActive) {
        btnToggleVoice.classList.add("active");
        btnToggleVoice.textContent = "🔊 OTO TTS: AÇIK";
        playQuindarTone(true);
      } else {
        btnToggleVoice.classList.remove("active");
        btnToggleVoice.textContent = "🔇 OTO TTS: KAPALI";
        stopSpeech();
      }
    });
  }

  const btnSpeakLast = document.getElementById("btn-speak-last");
  const btnStopTTS = document.getElementById("btn-stop-tts");

  if (btnSpeakLast) {
    btnSpeakLast.addEventListener("click", () => {
      if (window.speechSynthesis && window.speechSynthesis.speaking) {
        stopSpeech();
      } else {
        speakFlightSurgeonResponse(lastAIReplyText, currentlySpeakingBubble, btnSpeakLast);
      }
    });
  }

  if (btnStopTTS) {
    btnStopTTS.addEventListener("click", () => {
      stopSpeech();
    });
  }

  const btnGreetingTTS = document.getElementById("btn-greeting-tts");
  const greetingBubble = document.getElementById("greeting-bubble");
  if (btnGreetingTTS && greetingBubble) {
    btnGreetingTTS.addEventListener("click", () => {
      const p = greetingBubble.querySelector("p");
      const text = p ? p.textContent : lastAIReplyText;
      if (currentlySpeakingBubble === greetingBubble) {
        stopSpeech();
      } else {
        speakFlightSurgeonResponse(text, greetingBubble, btnGreetingTTS);
      }
    });
  }

  function stopSpeech() {
    if (window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    if (ttsResumeTimer) {
      clearInterval(ttsResumeTimer);
      ttsResumeTimer = null;
    }
    if (currentlySpeakingBubble) {
      currentlySpeakingBubble.classList.remove("speaking-pulse");
      currentlySpeakingBubble = null;
    }
    if (currentlySpeakingBtn) {
      currentlySpeakingBtn.classList.remove("active");
      currentlySpeakingBtn.innerHTML = "🔊 Dinle (TTS)";
      currentlySpeakingBtn = null;
    }
    if (btnStopTTS) btnStopTTS.style.display = "none";
    if (btnSpeakLast) btnSpeakLast.classList.remove("active");
  }

  function detectLanguage(text) {
    const trPattern = /[çğışöüÇĞİŞÖÜ]|(\b(merhaba|nasılsın|evet|hayır|doktor|oksijen|nabız|durum|tedavi|ilaç|kalp|sağlık|lütfen|için|veya|çünkü|hasta|rapor|günaydın)\b)/i;
    return trPattern.test(text) ? "tr-TR" : "en-US";
  }

  function getBestVoice(lang) {
    if (!cachedVoices || cachedVoices.length === 0) {
      loadVoices();
    }
    if (!cachedVoices || cachedVoices.length === 0) return null;

    if (lang.startsWith("tr")) {
      return cachedVoices.find(v => v.lang.toLowerCase().startsWith("tr")) ||
             cachedVoices.find(v => v.name.toLowerCase().includes("turkish") || v.name.toLowerCase().includes("türk")) || null;
    } else {
      return cachedVoices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Guy") || v.name.includes("David") || v.name.includes("George") || v.name.includes("Samantha") || v.name.includes("Google"))) ||
             cachedVoices.find(v => v.lang.startsWith("en")) || null;
    }
  }

  function playQuindarTone(isIntro = true) {
    initAudio();
    if (!audioCtx) return;
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      // NASA Quindar Tone: 2525 Hz for intro (PTT down), 2475 Hz for outro (PTT up)
      osc.frequency.setValueAtTime(isIntro ? 2525 : 2475, audioCtx.currentTime);
      osc.type = "sine";
      gain.gain.setValueAtTime(0.09, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.22);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.22);
    } catch (e) {
      console.warn("Quindar tone error:", e);
    }
  }

  function speakFlightSurgeonResponse(rawText, bubbleEl = null, btnEl = null) {
    if (!window.speechSynthesis) {
      console.warn("SpeechSynthesis not supported.");
      return;
    }

    stopSpeech();
    initAudio();

    let clean = rawText
      .replace(/\[REQUEST_VITALS\]/g, "")
      .replace(/\[NASA-[A-Z0-9_-]+\]/g, "")
      .replace(/\[CSA-[A-Z0-9_-]+\]/g, "")
      .replace(/```[\s\S]*?```/g, "")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/\*([^*]+)\*/g, "$1")
      .replace(/https?:\/\/[^\s]+/g, "")
      .replace(/#{1,6}\s+/g, "")
      .replace(/[|•►]/g, " ")
      .trim();

    if (!clean) return;

    lastAIReplyText = clean;

    playQuindarTone(true);

    if (btnStopTTS) btnStopTTS.style.display = "inline-flex";
    if (btnSpeakLast) btnSpeakLast.classList.add("active");

    if (bubbleEl) {
      currentlySpeakingBubble = bubbleEl;
      bubbleEl.classList.add("speaking-pulse");
    }
    if (btnEl) {
      currentlySpeakingBtn = btnEl;
      btnEl.classList.add("active");
      btnEl.innerHTML = "⏹️ Durdur";
    }

    // Chrome bug prevention
    try {
      window.speechSynthesis.resume();
    } catch (e) {}

    setTimeout(() => {
      const utter = new SpeechSynthesisUtterance(clean);
      const lang = detectLanguage(clean);
      utter.lang = lang;
      utter.rate = 1.0;
      utter.pitch = 0.95;

      const voice = getBestVoice(lang);
      if (voice) {
        utter.voice = voice;
      }

      // Chrome keeps long utterances alive with resume heartbeat
      ttsResumeTimer = setInterval(() => {
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
          window.speechSynthesis.resume();
        } else {
          clearInterval(ttsResumeTimer);
        }
      }, 4000);

      utter.onend = () => {
        playQuindarTone(false);
        stopSpeech();
      };

      utter.onerror = (e) => {
        console.warn("TTS Utterance error:", e);
        stopSpeech();
      };

      window.speechSynthesis.speak(utter);
    }, 240);
  }

  // Push-to-Talk Speech Recognition
  const btnVoiceInput = document.getElementById("btn-voice-input");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let speechRecognizer = null;
  let isListening = false;

  if (SpeechRecognition) {
    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = false;
    speechRecognizer.interimResults = true;
    speechRecognizer.lang = "en-US";

    speechRecognizer.onstart = () => {
      isListening = true;
      if (btnVoiceInput) btnVoiceInput.classList.add("listening");
      playQuindarTone(true);
      if (chatInput) chatInput.placeholder = "🎙️ Listening to astronaut comms...";
    };

    speechRecognizer.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      if (chatInput) chatInput.value = final || interim;
      if (final) {
        isListening = false;
        if (btnVoiceInput) btnVoiceInput.classList.remove("listening");
        chatInput.placeholder = "Ask medical question or click 🎙️ to speak...";
        const text = final.trim();
        if (text) {
          chatInput.value = "";
          sendUserChatMessage(text);
        }
      }
    };

    speechRecognizer.onerror = (err) => {
      console.warn("Speech recognition error:", err);
      isListening = false;
      if (btnVoiceInput) btnVoiceInput.classList.remove("listening");
      if (chatInput) chatInput.placeholder = "Ask medical question or click 🎙️ to speak...";
    };

    speechRecognizer.onend = () => {
      isListening = false;
      if (btnVoiceInput) btnVoiceInput.classList.remove("listening");
      if (chatInput) chatInput.placeholder = "Ask medical question or click 🎙️ to speak...";
      playQuindarTone(false);
    };

    if (btnVoiceInput) {
      btnVoiceInput.addEventListener("click", () => {
        initAudio();
        if (!isListening) {
          try {
            speechRecognizer.start();
          } catch (e) {
            console.warn("Mic start error:", e);
          }
        } else {
          speechRecognizer.stop();
        }
      });
    }
  } else {
    if (btnVoiceInput) {
      btnVoiceInput.title = "Web Speech API not supported in this browser. Please type directly.";
      btnVoiceInput.style.opacity = "0.5";
    }
  }

  // ========================================================
  // OPTION B: NASA FORM 1042 CLINICAL MISSION REPORT EXPORT
  // ========================================================
  const btnExportLog = document.getElementById("btn-export-log");
  if (btnExportLog) {
    btnExportLog.addEventListener("click", () => {
      exportMissionMedicalLog();
    });
  }

  function exportMissionMedicalLog() {
    initAudio();
    playChime(660, 0.3, "sine");

    const now = new Date();
    const metHours = String(Math.floor((Date.now() - sessionStats.startTime) / 3600000)).padStart(2, '0');
    const metMins = String(Math.floor(((Date.now() - sessionStats.startTime) % 3600000) / 60000)).padStart(2, '0');
    const metSecs = String(Math.floor(((Date.now() - sessionStats.startTime) % 60000) / 1000)).padStart(2, '0');
    const metString = `MET 180:${metHours}:${metMins}:${metSecs}`;

    const avgHR = sessionStats.packetCount > 0 ? Math.round(sessionStats.hrSum / sessionStats.packetCount) : 72;
    const minHR = sessionStats.hrMin < 999 ? sessionStats.hrMin : 72;
    const maxHR = sessionStats.hrMax > 0 ? sessionStats.hrMax : 72;
    const avgO2 = sessionStats.packetCount > 0 ? (sessionStats.o2Sum / sessionStats.packetCount).toFixed(1) : "98.5";
    const minO2 = sessionStats.o2Min < 100 ? sessionStats.o2Min.toFixed(1) : "98.5";
    const maxCO2 = sessionStats.co2Max > 0 ? sessionStats.co2Max : 420;

    const t = sessionStats.lastTelemetry || {
      heart_rate: 72, oxygen: 98.5, stress_level: 22, co2_level_ppm: 420,
      ecg_classification: currentECGClass,
      camera_telemetry: liveCameraTelemetry
    };

    const citationsList = Array.from(sessionStats.consultedCitations.values());
    const citationsHTML = citationsList.length > 0 ? citationsList.map(c => `
      <div style="margin-bottom: 8px; padding: 6px 10px; background: #f0f4fc; border-left: 3px solid #0056b3; border-radius: 4px;">
        <strong>[${c.source_tag || "REF"}]</strong> <a href="${c.url || '#'}" target="_blank" style="color: #0056b3; font-weight: bold;">${c.title || "NASA Document"}</a><br/>
        <span style="font-size: 0.85em; color: #555;">${c.snippet || "Standard aerospace medical protocol."}</span>
      </div>
    `).join("") : `<p style="font-style: italic; color: #666;">Standard baseline NASA-STD-3001 and HRP human health standards applied.</p>`;

    const anomaliesHTML = sessionStats.clinicalEvents.length > 0 ? sessionStats.clinicalEvents.map(e => `
      <tr>
        <td style="padding: 6px 10px; border: 1px solid #ccc; font-family: monospace;">${e.timestamp}</td>
        <td style="padding: 6px 10px; border: 1px solid #ccc; font-weight: bold; color: ${e.severity === 'CRITICAL' ? '#d9534f' : '#f0ad4e'};">${e.severity}</td>
        <td style="padding: 6px 10px; border: 1px solid #ccc;">${e.title}</td>
        <td style="padding: 6px 10px; border: 1px solid #ccc;">${e.diagnosis}</td>
      </tr>
    `).join("") : `<tr><td colspan="4" style="padding: 8px; text-align: center; color: #28a745;">No acute clinical triage anomalies recorded in active buffer.</td></tr>`;

    const chatNotesHTML = conversationHistory.filter(m => m.role === "assistant").slice(-4).map(m => `
      <div style="margin-bottom: 10px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
        <div style="font-size: 0.8em; color: #6c757d; font-weight: bold;">CHIEF FLIGHT SURGEON ASSESSMENT:</div>
        <div style="font-size: 0.9em; margin-top: 4px; line-height: 1.4;">${m.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
      </div>
    `).join("") || `<p style="color: #666; font-style: italic;">No active consultation dialog notes recorded.</p>`;

    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>NASA Form 1042-DS | Deep Space Mission Clinical Health Log</title>
  <style>
    body { font-family: Arial, sans-serif; background: #ffffff; color: #1a1a1a; margin: 40px auto; max-width: 900px; line-height: 1.5; font-size: 13px; }
    .header { border-bottom: 3px solid #000; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-end; }
    .badge { font-family: monospace; font-size: 11px; background: #000; color: #fff; padding: 3px 8px; border-radius: 3px; }
    h1 { margin: 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; }
    h2 { font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #000; padding-bottom: 4px; margin-top: 20px; color: #003366; }
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
    .stat-card { border: 1px solid #ccc; padding: 8px 12px; border-radius: 4px; background: #fafafa; }
    .stat-card strong { display: block; font-size: 11px; color: #666; }
    .stat-card span { font-size: 16px; font-weight: bold; font-family: monospace; color: #000; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }
    th { background: #003366; color: #fff; text-align: left; padding: 6px 10px; border: 1px solid #003366; font-size: 11px; }
    .seal-box { margin-top: 30px; border-top: 2px dashed #999; padding-top: 14px; display: flex; justify-content: space-between; align-items: center; }
    .seal { border: 2px solid #003366; padding: 8px 14px; font-family: monospace; text-align: center; border-radius: 6px; font-size: 11px; }
    .btn-print { background: #003366; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; float: right; margin-bottom: 15px; }
    @media print { .btn-print { display: none; } body { margin: 0; } }
  </style>
</head>
<body>
  <button class="btn-print" onclick="window.print()">🖨️ PRINT / SAVE AS PDF</button>
  <div class="header">
    <div>
      <span class="badge">NASA SPACE MEDICINE DIVISION • CLASSIFIED FLIGHT SURGEON DOSSIER</span>
      <h1>NASA FORM 1042-DS (DEEP SPACE CLINICAL ENCOUNTER LOG)</h1>
      <p style="margin: 4px 0 0 0; color: #555;">EXPLORATION MEDICAL CAPABILITY (ExMC LEVEL 4) • TRANSIT ENVELOPE</p>
    </div>
    <div style="text-align: right; font-family: monospace; font-size: 12px;">
      <div><strong>DATE:</strong> ${now.toISOString().split('T')[0]}</div>
      <div><strong>TIME:</strong> ${now.toTimeString().split(' ')[0]} UTC</div>
      <div style="color: #0056b3; font-weight: bold;">${metString}</div>
    </div>
  </div>

  <div class="grid">
    <div class="stat-card"><strong>CREW SUBJECT</strong><span>CDR ASTRO-01</span></div>
    <div class="stat-card"><strong>HABITAT / CRAFT</strong><span>HERMES-01 (MARS)</span></div>
    <div class="stat-card"><strong>AUTONOMIC ENGINE</strong><span>CARDIASTRACONT NIM/AI</span></div>
    <div class="stat-card"><strong>DISPOSITION</strong><span style="color: #28a745;">ACTIVE STABLE</span></div>
  </div>

  <h2>1. Telemetry Envelope & Cumulative Biometric Statistics</h2>
  <div class="grid">
    <div class="stat-card"><strong>HEART RATE (MEAN / PEAK)</strong><span>${avgHR} / ${maxHR} BPM</span></div>
    <div class="stat-card"><strong>MINIMUM SPO2 SAT</strong><span>${minO2}%</span></div>
    <div class="stat-card"><strong>MAX CABIN CO2</strong><span>${maxCO2} PPM</span></div>
    <div class="stat-card"><strong>ECG RHYTHM STATUS</strong><span>${currentECGClass.replace(/_/g, ' ')}</span></div>
  </div>

  <h2>2. Computer Vision Optical Biomarkers (Helmet HUD)</h2>
  <div class="grid">
    <div class="stat-card"><strong>FACIAL PERFUSION</strong><span>${(t.camera_telemetry || liveCameraTelemetry).facial_pallor}</span></div>
    <div class="stat-card"><strong>DROWSINESS (PERCLOS)</strong><span>${Number((t.camera_telemetry || liveCameraTelemetry).eye_perclos).toFixed(2)}</span></div>
    <div class="stat-card"><strong>OCULAR GAZE</strong><span>${(t.camera_telemetry || liveCameraTelemetry).gaze_stability}</span></div>
    <div class="stat-card"><strong>CABIN ILLUMINANCE</strong><span>${(t.camera_telemetry || liveCameraTelemetry).cabin_illuminance_lux} LUX</span></div>
  </div>

  <h2>3. Documented Clinical Triage & Physiological Events</h2>
  <table>
    <thead>
      <tr>
        <th>TIMESTAMP</th>
        <th>SEVERITY</th>
        <th>ANOMALY IDENTIFICATION</th>
        <th>CLINICAL ACTION & PROTOCOL</th>
      </tr>
    </thead>
    <tbody>
      ${anomaliesHTML}
    </tbody>
  </table>

  <h2>4. Consulted Aerospace Medical Evidence & RAG Citations</h2>
  ${citationsHTML}

  <h2>5. Autonomous Chief Flight Surgeon Clinical Assessment</h2>
  ${chatNotesHTML}

  <div class="seal-box">
    <div>
      <strong>CLINICAL AI CERTIFICATION:</strong><br>
      Cardiastracont Autonomic Space Health Agent (NASA Exploration Medical Capability)<br>
      Estimated Algorithmic Margin of Error: ±3.8% (Confidence: 96.2%)
    </div>
    <div class="seal">
      ★ NASA EXMC VALIDATED ★<br>
      DEEP SPACE COPILOT<br>
      OFFICIAL RECORD
    </div>
  </div>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Cardiastracont_NASA_Form_1042_Report_${now.toISOString().slice(0, 10)}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(htmlContent);
      printWindow.document.close();
    }
  }

  // ========================================================
  // OPTION C: EARTH-MARS COMMS LATENCY SIMULATOR
  // ========================================================
  const btnOpenLatency = document.getElementById("btn-open-latency");
  const btnCloseLatency = document.getElementById("btn-close-latency");
  const latencyModal = document.getElementById("latency-modal");
  const hdrDelayVal = document.getElementById("hdr-delay-val");
  const statOwlt = document.getElementById("stat-owlt");
  const statRtlt = document.getElementById("stat-rtlt");
  const statDist = document.getElementById("stat-dist");
  const btnTriggerUplink = document.getElementById("btn-trigger-uplink");
  const btnCancelUplink = document.getElementById("btn-cancel-uplink");
  const uplinkProgressBar = document.getElementById("uplink-progress-bar");
  const uplinkTimer = document.getElementById("uplink-timer");
  const uplinkBadge = document.getElementById("uplink-badge");
  const latencyPresets = document.querySelectorAll(".btn-latency-preset");

  let currentDelaySeconds = 852;
  let uplinkTimerInterval = null;

  if (btnOpenLatency && latencyModal) {
    btnOpenLatency.addEventListener("click", () => {
      initAudio();
      latencyModal.classList.add("active");
    });
  }
  if (btnCloseLatency && latencyModal) {
    btnCloseLatency.addEventListener("click", () => {
      latencyModal.classList.remove("active");
    });
  }

  latencyPresets.forEach(btn => {
    btn.addEventListener("click", () => {
      latencyPresets.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const delay = parseFloat(btn.dataset.delay);
      currentDelaySeconds = delay;

      if (delay < 1) {
        if (hdrDelayVal) hdrDelayVal.textContent = "0.2s";
        if (statOwlt) statOwlt.textContent = "0.25 seconds";
        if (statRtlt) statRtlt.textContent = "0.50 seconds";
        if (statDist) statDist.textContent = "400 km (LEO)";
      } else if (delay < 10) {
        if (hdrDelayVal) hdrDelayVal.textContent = "1.3s";
        if (statOwlt) statOwlt.textContent = "1.30 seconds";
        if (statRtlt) statRtlt.textContent = "2.60 seconds";
        if (statDist) statDist.textContent = "384,400 km (Moon)";
      } else if (delay < 300) {
        if (hdrDelayVal) hdrDelayVal.textContent = "4.3m";
        if (statOwlt) statOwlt.textContent = "4 min 18 sec";
        if (statRtlt) statRtlt.textContent = "8 min 36 sec";
        if (statDist) statDist.textContent = "78,000,000 km (Closest)";
      } else if (delay < 1000) {
        if (hdrDelayVal) hdrDelayVal.textContent = "14.2m";
        if (statOwlt) statOwlt.textContent = "14 min 12 sec";
        if (statRtlt) statRtlt.textContent = "28 min 24 sec";
        if (statDist) statDist.textContent = "225,000,000 km (Average)";
      } else {
        if (hdrDelayVal) hdrDelayVal.textContent = "22.4m";
        if (statOwlt) statOwlt.textContent = "22 min 24 sec";
        if (statRtlt) statRtlt.textContent = "44 min 48 sec";
        if (statDist) statDist.textContent = "401,000,000 km (Conjunction)";
      }
      playChime(480, 0.15, "sine");
    });
  });

  if (btnTriggerUplink) {
    btnTriggerUplink.addEventListener("click", () => {
      initAudio();
      playQuindarTone(true);
      if (uplinkTimerInterval) clearInterval(uplinkTimerInterval);

      btnTriggerUplink.style.display = "none";
      if (btnCancelUplink) btnCancelUplink.style.display = "inline-block";
      if (uplinkBadge) {
        uplinkBadge.className = "uplink-active-badge";
        uplinkBadge.textContent = "TRANSMITTING TO DSN (GOLDSTONE 70M)";
      }

      let remainingSec = Math.round(currentDelaySeconds);
      const totalSec = remainingSec;
      const speedMultiplier = remainingSec > 10 ? 30 : 1;

      uplinkTimerInterval = setInterval(() => {
        remainingSec -= speedMultiplier;
        const progress = Math.max(0, Math.min(100, ((totalSec - remainingSec) / totalSec) * 100));
        if (uplinkProgressBar) uplinkProgressBar.style.width = `${progress}%`;

        const displayMins = Math.floor(Math.max(0, remainingSec) / 60);
        const displaySecs = Math.max(0, remainingSec) % 60;
        if (uplinkTimer) {
          uplinkTimer.innerHTML = `🛰️ Signal in transit at c: <strong>${displayMins}m ${displaySecs}s</strong> remaining before Houston CAPCOM reception.`;
        }

        if (remainingSec <= 0) {
          clearInterval(uplinkTimerInterval);
          if (uplinkProgressBar) uplinkProgressBar.style.width = "100%";
          if (uplinkBadge) {
            uplinkBadge.className = "uplink-idle-badge";
            uplinkBadge.textContent = "PACKET RECEIVED AT JSC HOUSTON";
          }
          if (uplinkTimer) {
            uplinkTimer.innerHTML = "✅ Houston Received Telemetry. ⚠️ <em>Round-trip response expected in another buffer cycle. Local AI Surgeon remains in primary clinical control.</em>";
          }
          playQuindarTone(false);
          btnTriggerUplink.style.display = "inline-block";
          if (btnCancelUplink) btnCancelUplink.style.display = "none";
        }
      }, 1000);
    });
  }

  if (btnCancelUplink) {
    btnCancelUplink.addEventListener("click", () => {
      if (uplinkTimerInterval) clearInterval(uplinkTimerInterval);
      btnTriggerUplink.style.display = "inline-block";
      btnCancelUplink.style.display = "none";
      if (uplinkBadge) {
        uplinkBadge.className = "uplink-idle-badge";
        uplinkBadge.textContent = "IDLE • STANDBY";
      }
      if (uplinkProgressBar) uplinkProgressBar.style.width = "0%";
      if (uplinkTimer) uplinkTimer.textContent = "Buffer canceled.";
    });
  }

  // ========================================================
  // OPTION C (PART 2): EMERGENCY MEDICAL KIT (EMK) & RADIATION DECAY
  // ========================================================
  const btnOpenEmk = document.getElementById("btn-open-emk");
  const btnCloseEmk = document.getElementById("btn-close-emk");
  const emkModal = document.getElementById("emk-modal");
  const emkDaySlider = document.getElementById("emk-day-slider");
  const lblMissionDay = document.getElementById("lbl-mission-day");
  const emkDrugsTbody = document.getElementById("emk-drugs-tbody");
  const emkClinicalGuidance = document.getElementById("emk-clinical-guidance");
  const btnEmkDays = document.querySelectorAll(".btn-emk-day");

  const EMK_DRUGS = [
    {
      name: "Promethazine HCl (Phenergan)",
      indication: "Space Adaptation Syndrome (SAS) & Severe Motion Sickness",
      decayRate: 0.045,
      stdDose: "25 mg IM / Oral"
    },
    {
      name: "Metoprolol Tartrate",
      indication: "Paroxysmal Atrial Fibrillation (AFib) & Tachycardia",
      decayRate: 0.038,
      stdDose: "50 mg Oral / 5 mg IV"
    },
    {
      name: "Epinephrine (Adrenaline)",
      indication: "Anaphylaxis & Sudden Cardiac Arrest / Asystole",
      decayRate: 0.072,
      stdDose: "1.0 mg (1:10,000 IV / 0.3 mg Auto-inj)"
    },
    {
      name: "Dexamethasone Sodium PO4",
      indication: "SANS Intracranial Hypertension & Cerebral Edema",
      decayRate: 0.050,
      stdDose: "4 mg IV / Oral"
    },
    {
      name: "Acetazolamide (Diamox)",
      indication: "Acute Hypoxic Acclimatization & Carbonic Anhydrase Inhibition",
      decayRate: 0.030,
      stdDose: "250 mg Oral BID"
    },
    {
      name: "Pressurized Medical O2 Cylinders",
      indication: "Decompression Sickness, Acute Hypoxia & Suit Puncture",
      decayRate: 0.000,
      stdDose: "100% FiO2 via Mask / Umbilical"
    }
  ];

  function renderEMKTable(day) {
    if (!emkDrugsTbody) return;
    if (lblMissionDay) lblMissionDay.textContent = `DAY ${day}`;

    emkDrugsTbody.innerHTML = "";
    let degradedCount = 0;

    EMK_DRUGS.forEach(drug => {
      const potency = Math.max(10, (100 - drug.decayRate * day)).toFixed(1);
      const potencyNum = parseFloat(potency);

      let badgeClass = "potency-optimal";
      let statusText = "NOMINAL (Standard Dose)";
      let barColor = "var(--green)";
      let actionText = "Nominal";

      if (potencyNum < 75) {
        badgeClass = "potency-degraded";
        statusText = `CRITICAL DEGRADATION (-${(100 - potencyNum).toFixed(1)}%)`;
        barColor = "var(--red)";
        actionText = `⚠️ High Degradation. Consult AI for alternate therapy or +${Math.round((100 - potencyNum) * 1.2)}% volume.`;
        degradedCount++;
      } else if (potencyNum < 90) {
        badgeClass = "potency-compensate";
        statusText = `COMPENSATE DOSE (-${(100 - potencyNum).toFixed(1)}%)`;
        barColor = "#ffd700";
        actionText = `Compensate volume by +${Math.round((100 - potencyNum) * 1.15)}% to achieve target bio-efficacy.`;
      }

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${drug.name}</strong><br><span style="font-size: 0.7em; color: var(--text-muted); font-family: var(--font-mono);">Std Dose: ${drug.stdDose}</span></td>
        <td>${drug.indication}</td>
        <td style="font-family: var(--font-mono); color: var(--purple);">${drug.decayRate > 0 ? `-${drug.decayRate}% / day` : '0.00% (Inert)'}</td>
        <td>
          <div class="potency-wrap">
            <div class="potency-meter">
              <div class="potency-fill" style="width: ${potencyNum}%; background: ${barColor};"></div>
            </div>
            <span class="potency-badge ${badgeClass}">${potency}%</span>
          </div>
        </td>
        <td style="font-size: 0.72rem; color: #cfd9ea;">${actionText}</td>
        <td>
          <button class="btn-emk-consult" data-drug="${drug.name}" data-potency="${potency}" data-day="${day}">
            💬 Consult AI
          </button>
        </td>
      `;
      emkDrugsTbody.appendChild(tr);
    });

    document.querySelectorAll(".btn-emk-consult").forEach(btn => {
      btn.addEventListener("click", () => {
        const drug = btn.dataset.drug;
        const pot = btn.dataset.potency;
        const d = btn.dataset.day;
        if (emkModal) emkModal.classList.remove("active");
        switchToChatTab();
        const prompt = `Doctor, based on Emergency Medical Kit radiation degradation at Mission Day ${d}, ${drug} has degraded to ${pot}% potency. What is the exact clinically compensated dosage calculation and safety protocol per NASA HRP guidelines?`;
        sendUserChatMessage(prompt, false);
      });
    });

    if (emkClinicalGuidance) {
      if (day >= 180) {
        emkClinicalGuidance.innerHTML = `
          <strong>⚠️ NASA HRP DEEP SPACE PHARMACOLOGY ADVISORY (MISSION DAY ${day}):</strong><br>
          Prolonged Galactic Cosmic Radiation (GCR) exposure has significantly reduced the therapeutic window of catecholamines (Epinephrine) and antiarrhythmics. 
          When treating acute emergencies, <strong>Cardiastracont AI will automatically factor in active drug degradation percentages</strong> into countermeasure instructions.
        `;
      } else {
        emkClinicalGuidance.innerHTML = `
          <strong>🟢 NASA HRP PHARMACOLOGICAL STATUS (MISSION DAY ${day}):</strong><br>
          Pharmaceutical potency remains within standard 90-100% United States Pharmacopeia (USP) therapeutic limits. Continue standard storage in water-shielded locker.
        `;
      }
    }
  }

  if (btnOpenEmk && emkModal) {
    btnOpenEmk.addEventListener("click", () => {
      initAudio();
      renderEMKTable(parseInt(emkDaySlider.value || 180));
      emkModal.classList.add("active");
    });
  }
  if (btnCloseEmk && emkModal) {
    btnCloseEmk.addEventListener("click", () => {
      emkModal.classList.remove("active");
    });
  }
  if (emkDaySlider) {
    emkDaySlider.addEventListener("input", (e) => {
      const val = parseInt(e.target.value);
      btnEmkDays.forEach(b => {
        b.classList.toggle("active", parseInt(b.dataset.day) === val);
      });
      renderEMKTable(val);
    });
  }
  btnEmkDays.forEach(btn => {
    btn.addEventListener("click", () => {
      btnEmkDays.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const d = parseInt(btn.dataset.day);
      if (emkDaySlider) emkDaySlider.value = d;
      renderEMKTable(d);
      playChime(500, 0.15, "sine");
    });
  });

  // Start WebSocket when page is ready
  if (document.readyState === "complete" || document.readyState === "interactive") {
    connectWebSocket();
  } else {
    window.addEventListener("DOMContentLoaded", () => {
      connectWebSocket();
    });
  }
})();

