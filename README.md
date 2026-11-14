# 🚀 Cardiastracont: Offline-First Autonomic Space Health Agent
> **Target:** Space Health Monitoring & Autonomous Countermeasure System  
> **Mission Profile:** Deep-Space Exploration (e.g., Mars Transit with 4–22 minute Earth communication latency)

---

## 🌌 System Architecture Overview

```
+---------------------------------------------------------------------------------------------------------+
|                                           CARDIASTRACONT ECOSYSTEM                                           |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|   ⌚ Apple Watch Companion (watchOS)                  📱 Mobile Phone & Laptop Web App                  |
|   - HealthKit biometrics (HR, SpO2, HRV Stress)       - Responsive PWA for Safari / Chrome              |
|   - 3-second tactile hold Emergency SOS button        - Browser Biometric Streamer Mode (No HW needed)  |
|   - Offline-resilient burst-sync queue                - Web Audio Guided Box Breathing Sanctuary        |
|                                \                                 /                                      |
|                                 \                               /                                       |
|                                  v                             v                                        |
|                          🛰️ FastAPI Space Health Server (Python 3.10+)                                  |
|   +-------------------------------------------------------------------------------------------------+   |
|   | 1. Ingestion: POST /api/telemetry, POST /api/emergency-trigger, POST /api/analyze-anomaly       |   |
|   | 2. Anomaly Boundary Check (Hypoxia, Tachycardia, Arrhythmia, Hypercapnia, Panic storm)          |   |
|   | 3. Autonomous AI Engine:                                                                        |   |
|   |    ├── Primary: NVIDIA NIM API (Meta Llama-3.1-70b-instruct)                                    |   |
|   |    └── Fallback: Deterministic Flight Surgeon Clinical Decision Engine (< 1ms deep-space safe)  |   |
|   | 4. Real-Time WebSocket Hub: GET /ws/vr-stream                                                    |   |
|   +-------------------------------------------------------------------------------------------------+   |
|                                                 |                                                       |
|                                                 v                                                       |
|                     🥽 Meta Quest 3 VR Command Center & Sanctuary (Unity / OpenXR)                      |
|                     - 3D Holographic Curved Biometric HUD with animated cardiac pulse                   |
|                     - Real-time procedural Heart Rate & SpO2 trend curves                               |
|                     - AI Triage Alert Window (Diagnostic assessment & immediate action checklist)       |
|                     - Interactive "Sanctuary Mode" (60s guided 4-7-8 box breathing countermeasure)       |
|                                                                                                         |
+---------------------------------------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── config.py                 # Pydantic environment configuration (.env loader)
│   ├── main.py                   # FastAPI server entrypoint, web static server & CORS
│   ├── models.py                 # Telemetry & Triage Pydantic schemas
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template (NVIDIA NIM API key)
│   ├── simulator.py              # Interactive terminal telemetry simulator for testing
│   ├── test_suite.py             # Validation test suite covering 5 clinical space scenarios
│   ├── routes/
│   │   ├── telemetry.py          # POST /api/telemetry, POST /api/emergency-trigger, GET /api/history
│   │   ├── analysis.py           # POST /api/analyze-anomaly
│   │   └── websocket.py          # GET /ws/vr-stream (Bi-directional stream for VR and Web)
│   └── services/
│       ├── nim_service.py        # NVIDIA NIM API integration with automatic offline fallback
│       ├── rules_engine.py       # Deterministic Space Medicine Decision Protocol Engine
│       └── telemetry_service.py  # WebSocket client manager & telemetry state coordinator
│
├── web_app/                      # 📱 Mobile Phone & Laptop Web Application
│   ├── index.html                # Single-page glassmorphism Mission Control & Health Pad
│   ├── styles.css                # Aerospace responsive cyber-HUD CSS (Phone/Tablet/Laptop)
│   ├── app.js                    # WebSockets, Canvas chart curves, Web Audio chimes, Streamer
│   ├── manifest.json             # Progressive Web App (PWA) manifest for home screen install
│   └── README.md                 # Web app feature & usage documentation
│
├── watch_app/                    # ⌚ Apple Watch Companion (watchOS / Swift)
│   ├── CardiastracontWatchApp.swift   # @main watchOS application entrypoint
│   ├── Info.plist                # HealthKit permissions & network security descriptors
│   ├── CardiastracontWatch.entitlements # HealthKit entitlements
│   ├── Models/
│   │   └── TelemetryData.swift   # Swift Codable telemetry & SOS payload models
│   ├── Managers/
│   │   ├── HealthKitManager.swift# HealthStore queries + sensor simulation generator
│   │   └── NetworkManager.swift  # Low-latency URLSession streaming & offline recovery queue
│   └── Views/
│       ├── ContentView.swift     # TabView container
│       ├── VitalsDashboardView.swift # Real-time vitals card & streaming toggle
│       ├── EmergencyTriggerView.swift # 3-second tactile hold SOS beacon with haptics
│       └── SettingsView.swift    # Server IP config & demo anomaly injectors
│
└── vr_app/                       # 🥽 Meta Quest 3 VR Command Center (Unity / OpenXR)
    ├── Scripts/
    │   ├── Core/
    │   │   ├── VRWebSocketClient.cs    # Async .NET WebSocket client with main-thread dispatcher
    │   │   └── VRTelemetryModels.cs    # Unity Serializable JSON data structures
    │   ├── UI/
    │   │   ├── HealthHUDController.cs  # Main holographic HUD & vital meters
    │   │   ├── TelemetryGraph.cs       # Procedural rolling telemetry curve renderer
    │   │   ├── AIAlertPanelController.cs # AI triage action checklist & severity badges
    │   │   └── SanctuaryModeController.cs # Guided 60-second breathing countermeasure
    │   └── Interaction/
    │       └── VRInteractableButton.cs # Spatial 3D finger-poke / trigger button interactor
    └── Shaders/
        └── HologramHUD.shader          # Mobile-optimized Quest 3 holographic scanline shader
```

---

## ⚡ Quickstart Guide

### 1. Start the Backend & Web Console
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Web App (Phone & Laptop):** Open [http://localhost:8000/](http://localhost:8000/) or `http://<your-ip>:8000/` on your smartphone!
- **Interactive REST API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Stream:** `ws://localhost:8000/ws/vr-stream`

---

### 2. Using Your Phone as an Astronaut Health Pad
1. Connect your smartphone to the same Wi-Fi network as your laptop.
2. In your phone's browser (Safari or Chrome), navigate to `http://<YOUR_COMPUTER_IP>:8000/`.
3. Tap **"START STREAMING FROM THIS DEVICE"**:
   - Your phone is now actively transmitting real-time biometric telemetry to the server!
   - You can toggle scenarios (**Nominal**, **Hypoxia**, **Panic**, **Hypercapnia**) or hold the **EMERGENCY SOS** button to see the Meta Quest 3 VR HUD and Laptop Dashboard react instantly!
4. Tap **"🧘 SANCTUARY"** to launch the interactive 60-second box breathing countermeasure with relaxing Web Audio soundscapes.
