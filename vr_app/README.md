# Cardiastracont: VR Command Center & Sanctuary (Meta Quest 3 / OpenXR)

The Cardiastracont VR Command Center provides astronauts with an immersive 3D sci-fi holographic HUD aboard a spacecraft. It streams real-time biometrics from the FastAPI backend via high-speed WebSockets, visualizes cardiac & oxygen telemetry graphs, presents autonomous AI medical triage protocols during anomalies, and features an interactive psychological **Sanctuary Mode** (60-second guided box breathing countermeasure).

---

## 🥽 System Architecture & Components

```
+-----------------------------------------------------------+
|              Meta Quest 3 (Unity 2022.3 / 6000 LTS)        |
|                                                           |
|  +-------------------------+   +-----------------------+  |
|  |   VRWebSocketClient     |<--|  ws://<server>/ws/... |  |
|  +------------+------------+   +-----------------------+  |
|               | (Main Thread Dispatch)                    |
|       +-------v-------+                                   |
|       | HealthHUD     | ---> Heart Rate, SpO2, Graphs     |
|       | Controller    |                                   |
|       +-------+-------+                                   |
|               |                                           |
|       +-------v-------+                                   |
|       | AIAlertPanel  | ---> NVIDIA NIM / Offline Triage  |
|       | Controller    |                                   |
|       +-------+-------+                                   |
|               | (Sanctuary Trigger)                       |
|       +-------v-------+                                   |
|       | SanctuaryMode | ---> Dims HUD, Guided 4-7-8       |
|       | Controller    |      Breathing Circle, Audio      |
|       +---------------+                                   |
+-----------------------------------------------------------+
```

---

## 📁 Source Code Organization

- **`Scripts/Core/VRWebSocketClient.cs`**:
  - High-performance asynchronous WebSocket client using standard .NET `ClientWebSocket`.
  - Dispatches messages to Unity's main thread via thread-safe queue.
  - Automatically reconnects if link drops.
  - Zero external paid dependencies.
- **`Scripts/Core/VRTelemetryModels.cs`**:
  - Serializable data structures matching the FastAPI backend schemas (`VRStreamPacket`, `TelemetryData`, `TriageData`).
- **`Scripts/UI/HealthHUDController.cs`**:
  - Controls the main curved holographic canvas: Heart Rate, SpO2 fill bar, Stress index, ambient CO2, and animated cardiac pulse.
- **`Scripts/UI/TelemetryGraph.cs`**:
  - Real-time procedural line graph displaying dynamic trends for Heart Rate and Oxygen.
- **`Scripts/UI/AIAlertPanelController.cs`**:
  - Pops up when an anomaly occurs: displays condition title, severity color badge, NVIDIA NIM model details, clinical diagnosis, and immediate action steps.
- **`Scripts/UI/SanctuaryModeController.cs`**:
  - Interactive psychological countermeasure mode: dims the mission HUD, spawns floating stardust particles, and animates a 60-second expanding/contracting breathing circle with audio-haptic pacing.
- **`Scripts/Interaction/VRInteractableButton.cs`**:
  - 3D physical spatial push buttons compatible with Meta Quest Hand Tracking and VR controller triggers.
- **`Shaders/HologramHUD.shader`**:
  - Lightweight single-pass stereo instanced mobile holographic shader with oscillating scanlines and edge fresnel glow.

---

## 🚀 Unity Project Setup (Step-by-Step)

### 1. Unity Version & Packages
- Recommended Unity Version: **Unity 2022.3 LTS** or **Unity 6 (6000.0+)**.
- Install via Unity Package Manager (`Window > Package Manager`):
  - **XR Plugin Management**
  - **OpenXR Plugin** (enable Meta Quest Feature Group)
  - **Meta XR All-in-One SDK** (or Meta XR Core SDK)
  - **TextMeshPro**

### 2. Project Settings
1. Go to **Project Settings > XR Plug-in Management**:
   - Under **Android (Quest)** tab: Check **OpenXR**.
   - Under **OpenXR**: Add **Meta Quest Support** feature.
   - Set **Render Mode** to **Multi-Pass** or **Single Pass Instanced**.
2. Go to **Project Settings > Player > Android**:
   - Minimum API Level: **Android 10.0 (API Level 29)** or **12.0 (API Level 32)**.
   - Scripting Backend: **IL2CPP**.
   - Target Architectures: **ARM64** (uncheck ARMv7).

### 3. Scene Hierarchy Setup
Create a new Scene `Cardiastracont_CommandCenter`:
```
Cardiastracont_CommandCenter
├── XR Origin (XR Rig)
│   ├── Camera Offset
│   │   ├── Main Camera
│   │   ├── Left Hand Controller / Poke Interactor
│   │   └── Right Hand Controller / Poke Interactor
├── [MANAGERS]
│   └── VRWebSocketClient
│       └── Server WebSocket URI: ws://192.168.1.100:8000/ws/vr-stream
├── [WORLD_SPACE_HUD_CANVAS] (Position: 0, 1.4, 1.8 | Rotation: 0, 0, 0)
│   ├── HealthHUDController
│   │   ├── HeartRateCard (Text, Pulse Icon)
│   │   ├── HeartRateGraph (TelemetryGraph)
│   │   ├── OxygenCard (Text, Fill Bar)
│   │   ├── OxygenGraph (TelemetryGraph)
│   │   └── StressCard (Text, Fill Bar)
│   └── AIAlertPanelController (AlertPanel GameObject)
│       ├── ConditionTitleText
│       ├── SeverityBadge
│       ├── AIEngineSourceBadge
│       ├── ImmediateActionsListText
│       └── ActionButtons (Acknowledge, Launch Sanctuary)
└── [SANCTUARY_ENVIRONMENT]
    ├── SanctuaryModeController
    ├── StardustParticleSystem
    └── BreathingCircleCanvas
        ├── ExpandingCircleImage
        ├── PhaseInstructionText ("INHALE", "HOLD", "EXHALE")
        └── CountdownText ("TIME REMAINING: 48s")
```

### 4. Running & Testing
1. **Editor Testing (via Quest Link / Air Link):**
   - Connect Quest 3 to PC via USB-C or Air Link.
   - Ensure the FastAPI backend is running (`python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000`).
   - In `VRWebSocketClient`, set URI to `ws://127.0.0.1:8000/ws/vr-stream`.
   - Hit **Play** in the Unity Editor.
2. **Quest 3 Standalone Build:**
   - In `VRWebSocketClient`, set URI to your workstation's LAN IP, e.g. `ws://192.168.1.150:8000/ws/vr-stream`.
   - File > Build Settings > Switch Platform to **Android**.
   - Hit **Build and Run** to deploy the APK directly to Meta Quest 3 over USB-C or Meta Quest Developer Hub (MQDH).

