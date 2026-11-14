# 🚀 Cardiastracont: Offline-First Autonomic Space Health Agent & Flight Surgeon
> **NASA Space Apps Challenge 2026**  
> **Target:** Deep-Space Medical Autonomy & Emergency Clinical Decision Support (ExMC Tier 4/5)  
> **Operational Profile:** Interplanetary Missions (Mars Transit with 4 to 22-minute bidirectional Earth communication latency)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-Llama--3.1--70B-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![OpenXR](https://img.shields.io/badge/OpenXR-Meta%20Quest%203-0081FB?logo=meta&logoColor=white)](https://www.openxr.org/)
[![watchOS](https://img.shields.io/badge/watchOS-HealthKit%20SwiftUI-black?logo=apple&logoColor=white)](https://developer.apple.com/watchos/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌌 System Architecture Overview

When humans travel beyond Low Earth Orbit (LEO) toward Mars, evacuation to Earth is impossible and communication latency ranges between **4 to 22 minutes each way**. Medical emergencies must be diagnosed and managed **100% autonomously on-craft without waiting for Mission Control**.

**Cardiastracont** delivers an offline-first autonomic medical command ecosystem:

```
+-----------------------------------------------------------------------------------------------------------------+
|                                            CARDIASTRACONT HEALTH ECOSYSTEM                                      |
+-----------------------------------------------------------------------------------------------------------------+
|                                                                                                                 |
|   ⌚ Apple Watch (watchOS)           📱 Astronaut Health Pad (PWA)         📷 Contactless Optical rPPG          |
|   - Real-time HealthKit stream       - Zero-install mobile/tablet UI       - Webcam PPG pulse wave analysis     |
|   - 3s tactile hold SOS beacon       - Device telemetry streamer mode      - Facial fatigue & pallor tracking   |
|   - Offline burst-sync queue         - 60s Box Breathing Sanctuary         - Zero contact cardiac monitoring    |
|               \                                     |                                     /                     |
|                \                                    |                                    /                      |
|                 v                                   v                                   v                       |
|   +---------------------------------------------------------------------------------------------------------+   |
|   |                              🛰️ CARDIASTRACONT AUTONOMOUS CORE (FastAPI)                                 |   |
|   |                                                                                                         |   |
|   |  1. Ingestion & Normalization:                                                                          |   |
|   |     - POST /api/telemetry (HR, SpO2, HRV, Systolic/Diastolic BP, Respiration, Core Temp, ECG Waveform)  |   |
|   |     - POST /api/emergency-trigger (Instant station-wide Red Alert & emergency broadcast)                |   |
|   |                                                                                                         |   |
|   |  2. Clinical Decision & Autonomic Triage Engine:                                                        |   |
|   |     ├── Deterministic Rules Engine (NASA JSC/ExMC Critical Boundary protocols, <1ms response)            |   |
|   |     ├── Local RAG Vector Knowledge Base (TF-IDF & Embeddings, offline NASA flight surgeon manuals)      |   |
|   |     ├── Adaptive Baseline Engine (Autonomous crew biometric drift learning & circadian adaptation)      |   |
|   |     └── Primary Cloud AI: NVIDIA NIM Microservice (Meta Llama-3.1-70B-Instruct)                         |   |
|   |                                                                                                         |   |
|   |  3. Advanced Mission Capabilities:                                                                      |   |
|   |     ├── Interactive Voice Flight Surgeon: Real-time STT / TTS + NASA Quindar radio audio telemetry cues  |   |
|   |     ├── Earth-Mars Latency Simulator: Configurable delay queues (Real-Time, Lunar, Mars 4m to 22m)      |   |
|   |     ├── Master Caution Klaxon: Synthesized 2500Hz/1500Hz aerospace alarm with acoustic mute             |   |
|   |     ├── NASA Form 1042 Clinical Report: 1-click export of clinical mission logs & vitals                |   |
|   |     └── EMK Radiation Drug Degradation: Galactic Cosmic Ray (GCR) half-life tracker & dosage adjuster   |   |
|   |                                                                                                         |   |
|   |  4. Low-Latency WebSocket Hub (GET /ws/vr-stream):                                                      |   |
|   |     - Bi-directional 30Hz broadcast to VR Headsets, Web Command Centers, and Telemetry Bridges         |   |
|   +---------------------------------------------------------------------------------------------------------+   |
|                                                     |                                                           |
|                                                     v                                                           |
|                        🥽 Meta Quest 3 VR Holographic Command HUD (Unity / OpenXR)                               |
|                        - 3D Curved Holographic Spatial HUD with animated cardiac waveform                       |
|                        - Real-time procedural Heart Rate, SpO2 & HRV rolling trend graphs                       |
|                        - Instant Clinical AI Triage Window (Diagnostic assessment & step-by-step checklist)     |
|                        - Sanctuary Mode: Guided 4-7-8 box breathing countermeasure for acute panic/stress       |
|                                                                                                                 |
+-----------------------------------------------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── config.py                 # Environment loader & dynamic $PORT binding for cloud/Render
│   ├── main.py                   # FastAPI server entrypoint, web static server & CORS middleware
│   ├── models.py                 # Telemetry, Triage & NASA Form 1042 Pydantic schemas
│   ├── requirements.txt          # Python dependencies
│   ├── Procfile                  # Cloud deployment process definition (uvicorn runner)
│   ├── .env.example              # Environment variables template (NVIDIA NIM / Gemini keys)
│   ├── simulator.py              # Interactive terminal telemetry simulator for testing
│   ├── test_suite.py             # Validation test suite covering 5 critical space scenarios
│   ├── routes/
│   │   ├── analysis.py           # POST /api/analyze-anomaly (Direct AI clinical triage)
│   │   ├── chat.py               # POST /api/chat (Flight Surgeon dialog with latency emulation)
│   │   ├── telemetry.py          # POST /api/telemetry, /api/emergency-trigger, GET /api/history
│   │   └── websocket.py          # GET /ws/vr-stream (High-speed bi-directional telemetry)
│   └── services/
│       ├── adaptive_engine.py    # Crew baseline drift tracking & autonomic trend calculation
│       ├── chat_service.py       # Autonomous Flight Surgeon dialog coordinator & RAG integrator
│       ├── nim_service.py        # NVIDIA NIM API integration with automatic offline fallback
│       ├── rag_service.py        # Offline Vector RAG knowledge base for NASA space medicine
│       ├── rules_engine.py       # Deterministic Space Medicine Decision Protocol Engine
│       └── telemetry_service.py  # WebSocket client hub & live telemetry state manager
│
├── web_app/                      # 📱 Astronaut Health Pad & Desktop Mission Control
│   ├── index.html                # Responsive glassmorphism Command Center UI & EKG Canvas
│   ├── styles.css                # Aerospace cyber-HUD styling (responsive for Mobile, Tablet, 4K)
│   ├── app.js                    # WebSockets, EKG waveform, Voice STT/TTS, Quindar audio, rPPG
│   ├── manifest.json             # Progressive Web App (PWA) manifest for offline home screen
│   └── README.md                 # Web console technical documentation
│
├── watch_app/                    # ⌚ Apple Watch Companion (watchOS / Swift)
│   ├── CardiastracontWatchApp.swift   # @main watchOS application entrypoint
│   ├── Info.plist                # HealthKit permissions & network transport configuration
│   ├── CardiastracontWatch.entitlements # HealthKit entitlement setup
│   ├── Models/
│   │   └── TelemetryData.swift   # Swift Codable telemetry & emergency SOS models
│   ├── Managers/
│   │   ├── HealthKitManager.swift# Real-time HealthStore biometric queries + simulation injector
│   │   └── NetworkManager.swift  # URLSession telemetry streaming with offline burst-sync queue
│   └── Views/
│       ├── ContentView.swift     # TabView container
│       ├── VitalsDashboardView.swift # Biometric meters, cardiac pulse & stream toggle
│       ├── EmergencyTriggerView.swift # 3-second tactile hold SOS beacon with haptics
│       └── SettingsView.swift    # Server IP address configuration & test scenario injectors
│
├── vr_app/                       # 🥽 Meta Quest 3 VR Command Center (Unity / OpenXR)
│   ├── Scripts/
│   │   ├── Core/
│   │   │   ├── VRWebSocketClient.cs    # Async .NET WebSocket client with main-thread dispatcher
│   │   │   └── VRTelemetryModels.cs    # Unity Serializable JSON data structures
│   │   ├── UI/
│   │   │   ├── HealthHUDController.cs  # Main holographic HUD & vital meters
│   │   │   ├── TelemetryGraph.cs       # Procedural rolling telemetry curve renderer
│   │   │   ├── AIAlertPanelController.cs # AI triage action checklist & severity badges
│   │   │   └── SanctuaryModeController.cs # Guided 60-second breathing countermeasure
│   │   └── Interaction/
│   │       └── VRInteractableButton.cs # Spatial 3D finger-poke / trigger button interactor
│   └── Shaders/
│       └── HologramHUD.shader          # Mobile-optimized Quest 3 holographic scanline shader
│
├── DEVICE_API_AND_INTEGRATION_GUIDE.md # Comprehensive hardware & API integration guide
├── Procfile                      # Root Procfile for 1-click cloud deployment
├── requirements.txt              # Root dependencies for cloud builders
└── .gitignore                    # Production gitignore shielding sensitive API keys
```

---

## ⚡ Quickstart Guide

### 1. Local Installation & Launch
Ensure Python 3.10+ is installed:

```bash
# Clone the repository
git clone https://github.com/your-username/Cardiastracont.git
cd Cardiastracont

# Install dependencies
pip install -r requirements.txt

# Start the unified server (Backend API + Web Command Center)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- **Command Center & Mobile Web App:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Stream:** `ws://localhost:8000/ws/vr-stream`

---

## 🌟 Advanced Features Walkthrough

### 1. Dual Operating Modes (Desktop & Mobile)
- **Mission Control (Desktop/Laptop):** High-density telemetry cards, dynamic canvas EKG monitor, atmospheric ECLSS sensors, and autonomous AI triage windows.
- **Astronaut Health Pad (Mobile Smartphone):** Open `http://<YOUR_COMPUTER_IP>:8000` on your iPhone or Android phone. Tap **"START STREAMING FROM THIS DEVICE"** to transform any mobile browser into an active biometric telemetry transmitter!

### 2. Autonomous AI Chief Flight Surgeon & Voice Interaction
- **Speech-to-Text (STT) & Text-to-Speech (TTS):** Hands-free voice dialog with the AI Flight Surgeon using authentic NASA Quindar radio tones.
- **Offline RAG Knowledge Engine:** Pre-loaded with NASA ExMC clinical protocols, space flight medical checklists, and clinical triage decision trees.
- **Hybrid AI Fallback:** When online, leverages NVIDIA NIM (Meta Llama-3.1-70B); when offline, seamlessly switches to the deterministic local clinical engine in `<1ms`.

### 3. Contactless Biometrics (Optical rPPG Camera)
- Toggle the **Camera Biometrics** button to activate the computer vision pipeline.
- Uses remote photoplethysmography (rPPG) on the green channel to measure cardiac pulse through subtle facial blood volume variations—completely touchless!

### 4. Deep-Space Earth-Mars Latency Simulator
- Realistic interplanetary signal delay simulation:
  - **Real-Time (0s)**: Earth Orbit / LEO
  - **Lunar Orbit (1.3s)**: Artemis Lunar Gateway
  - **Mars Closest Approach (4 min)**
  - **Mars Mean Distance (14 min)**
  - **Mars Solar Conjunction / Opposition (22 min)**
- Demonstrates why on-craft AI autonomy is an existential requirement for deep space exploration.

### 5. Piercing Dual-Frequency Master Caution Klaxon
- Built using the Web Audio API without external audio files.
- Generates a 2500Hz/1500Hz alternating alarm during Critical Tachycardia, Severe Hypoxia, or SOS triggers.
- Includes an emergency **Mute / Acknowledge** button in accordance with aerospace Human Factors guidelines.

### 6. Emergency Medical Kit (EMK) Radiation Drug Degradation
- Tracks Galactic Cosmic Ray (GCR) and Solar Particle Event (SPE) radiation dosage in millisieverts (mSv).
- Dynamically models drug potency loss (Epinephrine, Morphine, Atropine, Ceftriaxone) and automatically calculates compensatory dosage adjustments.

### 7. NASA Form 1042 Clinical Mission Report Export
- 1-click generation of the official **NASA Flight Physical & Aeromedical Incident Form (Form 1042)**.
- Formats vital signs, diagnostic summaries, and medical interventions into an auditable mission archive document.

---

## ☁️ 1-Click Cloud Deployment (Render.com)

1. Fork or push this repository to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **"New +" > "Web Service"**.
3. Connect your GitHub repository.
4. Set the configuration:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**. Your deep-space health center is live in seconds!

---

## 🛠️ Testing & Verification Suite

Cardiastracont includes an automated clinical test suite covering 5 critical space medicine scenarios:
```bash
python backend/test_suite.py
```
- **Scenario 1:** Nominal Cruise vitals validation.
- **Scenario 2:** Acute Hypoxic Decompression event detection.
- **Scenario 3:** Paroxysmal Ventricular Tachycardia (VTach) detection.
- **Scenario 4:** Spaceflight-induced Panic Storm & Sanctuary countermeasure.
- **Scenario 5:** Hypercapnic ECLSS CO2 scrubber saturation.

---

## 📄 License
This project is developed for the **NASA Space Apps Challenge 2026** and licensed under the **MIT License**.
