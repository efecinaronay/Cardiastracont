# Cardiastracont: Web Console & Mobile Health Pad

A responsive, zero-install Web Application designed to run seamlessly on **smartphones (iOS Safari, Android Chrome)**, **tablets**, and **laptops/desktops**.

---

## 🌟 Key Capabilities

1. **Dual Operating Modes:**
   - **Mission Control Dashboard (Laptop/Desktop):** Real-time biometric charts, live telemetry feeds, ECLSS atmosphere indicators, and NVIDIA NIM / Offline AI Triage alert windows.
   - **Astronaut Health Pad (Mobile Phone):** Touch-optimized interface with tactile vital dials, live pulse animation, and quick-action emergency controls.
2. **Real-Time WebSocket Sync:**
   - Connects to `ws://<server-ip>:8000/ws/vr-stream`.
   - Synchronizes biometrics and alerts simultaneously with Meta Quest 3 VR headsets and Apple Watch streams.
3. **Interactive Guided Sanctuary Mode:**
   - Fullscreen 60-second guided box breathing session (Inhale 4s, Hold 4s, Exhale 4s, Rest 4s).
   - Generates soothing harmonic audio chimes via the **Web Audio API** with zero external audio assets required.
4. **Phone Biometric Streamer Mode (No Hardware Required):**
   - Toggle **"START STREAMING FROM THIS DEVICE"** on any smartphone browser.
   - Streams live biometric payloads directly into the FastAPI server via `POST /api/telemetry` at 1Hz, with selectable scenarios:
     - 🟢 Nominal Cruise
     - 🔴 Critical Hypoxia Event
     - 🟠 Autonomic Panic Storm
     - 🟣 ECLSS Hypercapnia (CO2 Buildup)
5. **Progressive Web App (PWA) Ready:**
   - Includes `manifest.json` for "Add to Home Screen" installation on iPhones and Android phones for a native full-screen app experience.

---

## 🚀 How to Access

1. Start the Cardiastracont backend:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Open your browser:
   - **On your laptop:** Navigate to `http://localhost:8000/` or `http://localhost:8000/dashboard`
   - **On your phone:** Connect to the same Wi-Fi network and open `http://<YOUR_COMPUTER_LOCAL_IP>:8000/` (e.g. `http://192.168.1.150:8000/`)

