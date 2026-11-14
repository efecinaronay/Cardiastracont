# Cardiastracont: Apple Watch Companion App (watchOS)

The Cardiastracont watchOS companion application gathers real-time biometric telemetry (Heart Rate, Blood Oxygen SpO2, and HRV-derived Autonomic Stress Index) using Apple's HealthKit framework and streams it via `URLSession` to the Cardiastracont FastAPI backend.

---

## ⌚ Key Features
1. **Live Biometric Telemetry:**
   - Real-time Heart Rate (BPM) with animated cardiac pulse.
   - SpO2 Oxygen Saturation (%) monitoring.
   - Heart Rate Variability (HRV SDNN) translated to Autonomic Stress (0-100).
2. **One-Tap Emergency SOS Trigger:**
   - Emergency panic button with tactile 3-second hold countdown and haptic feedback (`WKInterfaceDevice`).
   - Dispatches emergency payload to `/api/emergency-trigger` to activate instant Station Triage and VR HUD alerts.
3. **Offline-Resilient Telemetry Queue:**
   - If the astronaut steps into an unshielded or disconnected module, telemetry packets are automatically queued in memory and burst-synchronized once connectivity returns.
4. **Autonomous Simulation Fallback:**
   - Automatically detects if HealthKit permissions are pending or running on Xcode Simulator.
   - Built-in simulation injector allows one-tap injection of **Hypoxia**, **Tachycardia**, or **Panic** scenarios directly from the watch's Settings tab for live hackathon presentations!

---

## 🛠️ Xcode Setup & Sideloading Guide

### Prerequisites
- macOS Sonoma (14.0+) or macOS Sequoia (15.0+)
- Xcode 15.0+ or 16.0+
- Apple Watch Series 6+ (for native SpO2 sensor) or Apple Watch Simulator

### 1. Creating the Xcode Project
1. Open Xcode and select **File > New > Project...**
2. Choose **watchOS > App**.
3. Set:
   - **Product Name:** `CardiastracontWatch`
   - **Interface:** `SwiftUI`
   - **Language:** `Swift`
4. Copy the files from `watch_app/` into your Xcode project:
   - `CardiastracontWatchApp.swift` -> replace default App entrypoint.
   - `Models/TelemetryData.swift`
   - `Managers/HealthKitManager.swift`
   - `Managers/NetworkManager.swift`
   - `Views/ContentView.swift`
   - `Views/VitalsDashboardView.swift`
   - `Views/EmergencyTriggerView.swift`
   - `Views/SettingsView.swift`
   - `Info.plist` & `CardiastracontWatch.entitlements`

### 2. Capabilities & Signing
1. Select the `CardiastracontWatch` target in Xcode.
2. Go to **Signing & Capabilities**:
   - Add **HealthKit** capability.
   - Check **Background Modes** -> enable **Workout processing**.
3. Under **Build Settings**, ensure `ENABLE_PREVIEWS` is `YES`.

### 3. Physical Device Sideloading (Free Apple Developer Account)
1. Connect your iPhone via USB-C/Lightning.
2. Ensure your Apple Watch is paired and in **Developer Mode** (*Settings > Privacy & Security > Developer Mode > On*).
3. Select your paired Apple Watch as the run destination in Xcode.
4. Hit **Run (⌘ + R)**. Xcode will sign and install the app directly on your wrist!

### 4. Backend Connection Configuration
- Swipe to the **Settings** tab (third tab) on the watch.
- Enter your backend URL:
  - If on the same WiFi: `http://<YOUR_COMPUTER_LOCAL_IP>:8000` (e.g., `http://192.168.1.150:8000`).
  - If running across separate networks: use an ngrok or Cloudflare tunnel (e.g., `https://your-subdomain.ngrok-free.app`).
- The live indicator at the top of the vitals screen will switch to `STREAMING • 35ms`.

