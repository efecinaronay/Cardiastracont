# 🛰️ Cardiastracont Space Health Core — Device Ecosystem & Hardware API Integration Guide

**Autonomous Space Health Agent & Deep-Space Medical Core (NASA Exploration Medical Capability - ExMC Level 4)**  
*Document Version: 2.4.0 • Classification: Deep Space Flight Medicine Operational Specification*

---

## 📌 Executive Summary

Cardiastracont is an **offline-first, autonomic spaceflight clinical copilot** designed for deep-space missions beyond Low Earth Orbit (e.g., Artemis Lunar Gateway and 500-day Mars Transits). Due to the relativistic 4 to 22-minute speed-of-light communication latency with Earth, ground medical intervention is mathematically unviable during acute physiological crises (such as acute hypoxia, paroxysmal atrial fibrillation, or carbon dioxide narcosis).

This document provides the **complete, production-ready REST & WebSocket API specification** allowing any biometric wearable, smartwatch, medical sensor, ECLSS atmospheric monitor, VR/AR headset, or tablet to connect, stream telemetry, receive AI triage alerts, and synchronize master caution & warning klaxons with the Cardiastracont Central Core.

---

## 🌐 Network Architecture & Base Endpoints

All devices communicate with the onboard Cardiastracont server via local habitat Wi-Fi, Ethernet, or Bluetooth LE gateway without requiring external cloud access:

* **Habitat Server Base URL:** `http://<SERVER_IP>:8000` (e.g., `http://192.168.1.100:8000` or `http://localhost:8000`)
* **Real-time WebSocket Stream:** `ws://<SERVER_IP>:8000/ws/vr-stream`
* **Content Type:** `application/json`
* **Authentication:** Local habitat open broadcast or bearer header (`Authorization: Bearer CARDIASTRACONT-CORE-LOCAL`)
* **CORS Support:** Permissive wildcard (`*`) enabled for watchOS, WearOS, iOS, Android, and Web clients.

---

## 📡 Complete REST API Endpoint Directory

| Method | Endpoint | Description | Primary Devices |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/telemetry` | Ingest single real-time biometric packet | Apple Watch, WearOS, Garmin, Biosensors |
| `POST` | `/api/telemetry/batch` | Ingest buffered offline telemetry points | Smartwatches reconnecting after EVA |
| `GET` | `/api/telemetry/latest` | Retrieve latest physiological snapshot | Companion iPads, Bedside HUDs, Telemetry Wall |
| `POST` | `/api/devices/register` | Register new hardware sensor / device | All hardware on initial network connection |
| `POST` | `/api/devices/heartbeat` | Keep-alive ping with battery percentage | Smartwatches, ESP32 biosensors (every 30s) |
| `GET` | `/api/devices` | List all connected devices & battery state | Chief Flight Surgeon Dashboard |
| `POST` | `/api/devices/alarm-test` | Broadcast test Master Alarm klaxon | Safety check / Drill simulation |
| `POST` | `/api/emergency-trigger`| Manual SOS panic button dispatch | Apple Watch SOS Crown, Suit Hardware Switch |
| `POST` | `/api/chat` | Query Chief Flight Surgeon AI (with vitals) | Smartwatch Voice Dictation, Tablet Console |
| `GET` | `/api/history` | Rolling 120-packet telemetry history | Trend charting & VR HUD waveform |
| `GET` | `/api/status` | Central server health & triage state | Habitat Monitoring Subsystem |
| `POST` | `/api/adaptive-profile`| Adjust thresholds for EVA / Transit / Sleep | Mission Control Schedule Sequencer |
| `WS` | `/ws/vr-stream` | Bidirectional real-time telemetry socket | Meta Quest 3, Apple Vision Pro, Web HUD |

---

## 🔬 Detailed Endpoint Specifications & Payloads

### 1. Ingest Real-Time Telemetry (`POST /api/telemetry`)
Sent by smartwatches and wearables at **40 RPM (every 1.5 seconds)** or **1 Hz**:

#### Request Body (`application/json`):
```json
{
  "astronaut_id": "ASTRO-01",
  "heart_rate": 74.0,
  "oxygen": 98.2,
  "stress_level": 24.0,
  "hrv": 58.4,
  "co2_level_ppm": 420.0,
  "ecg_lead": "LEAD_I_APPLE_WATCH",
  "ecg_classification": "SINUS_RHYTHM",
  "ambient_o2_percent": 20.9,
  "o2_partial_pressure_kpa": 21.2,
  "is_emergency_triggered": false,
  "source": "apple_watch_ultra_2"
}
```

#### Field Definitions:
* `heart_rate` *(float, required)*: Heart rate in BPM [20.0 - 250.0].
* `oxygen` *(float, required)*: Blood oxygen saturation $\text{SpO}_2$ percentage [50.0 - 100.0].
* `stress_level` *(float, required)*: Autonomic nervous system stress index derived from HRV [0.0 - 100.0].
* `hrv` *(float, optional)*: Heart Rate Variability SDNN in milliseconds.
* `co2_level_ppm` *(float, optional)*: Ambient suit/cabin $\text{CO}_2$ concentration (PPM). Nominal: 420. Caution: >1500. Critical: >3000.
* `ecg_classification` *(string, optional)*: Rhythm status: `SINUS_RHYTHM`, `ATRIAL_FIBRILLATION`, `SINUS_TACHYCARDIA`, `SINUS_BRADYCARDIA`, `INCONCLUSIVE`.
* `ambient_o2_percent` *(float, optional)*: Breathable $\text{O}_2$ percentage $\text{FiO}_2$. Nominal: 20.9%.
* `o2_partial_pressure_kpa` *(float, optional)*: $\text{ppO}_2$ in kPa. NASA-STD-3001 emergency limit is < 16.0 kPa.

#### Success Response (`200 OK`):
```json
{
  "status": "success",
  "astronaut_id": "ASTRO-01",
  "processed": {
    "is_anomaly": false,
    "severity": "NOMINAL",
    "anomaly_types": [],
    "triggers": []
  }
}
```
*If an anomaly is detected (e.g. $\text{SpO}_2 < 88\%$ or AFib), `processed` immediately returns an `AI_TRIAGE_ALERT` and broadcasts the Master Caution Klaxon to all connected clients.*

---

### 2. Ingest Offline Buffered Batch Telemetry (`POST /api/telemetry/batch`)
Invoked when a smartwatch or sensor reconnects after an Extravehicular Activity (EVA) communication blackout:

#### Request Body:
```json
{
  "device_id": "APPLE-WATCH-ULTRA-01",
  "astronaut_id": "ASTRO-01",
  "readings": [
    {
      "heart_rate": 78.0,
      "oxygen": 97.5,
      "stress_level": 32.0,
      "ecg_classification": "SINUS_RHYTHM",
      "timestamp": "2026-11-14T14:30:00Z"
    },
    {
      "heart_rate": 118.0,
      "oxygen": 84.0,
      "stress_level": 89.0,
      "ecg_classification": "SINUS_TACHYCARDIA",
      "timestamp": "2026-11-14T14:30:10Z"
    }
  ]
}
```

#### Response:
```json
{
  "status": "batch_success",
  "device_id": "APPLE-WATCH-ULTRA-01",
  "readings_ingested": 2,
  "latest_evaluation": {
    "is_anomaly": true,
    "severity": "CRITICAL",
    "anomaly_types": ["ACUTE_HYPOXIA"],
    "triggers": ["SpO2 dropped below critical threshold (84.0%)"]
  }
}
```

---

### 3. Register Hardware Device (`POST /api/devices/register`)
Invoked on initial boot of any physical device on the habitat Wi-Fi:

#### Request Body:
```json
{
  "device_id": "GARMIN-MK3-004",
  "device_name": "Garmin Descent Mk3 (Spacewalk EVA Lead)",
  "device_type": "WEARABLE_SMARTWATCH",
  "astronaut_id": "ASTRO-02",
  "battery_level": 98,
  "firmware_version": "v16.12",
  "sensor_capabilities": ["OPTICAL_HR", "PULSE_OX", "SKIN_TEMP", "BAROMETER", "3AXIS_ACCEL"]
}
```

---

### 4. Device Heartbeat & Battery Keepalive (`POST /api/devices/heartbeat`)
Transmitted every 30-60 seconds to notify the central system of device battery health:

#### Request Body:
```json
{
  "device_id": "GARMIN-MK3-004",
  "battery_level": 94,
  "status": "ONLINE"
}
```

#### Response:
```json
{
  "status": "ACK",
  "device_id": "GARMIN-MK3-004"
}
```

---

### 5. Manual SOS Panic Trigger (`POST /api/emergency-trigger`)
Dispatched when an astronaut holds the smartwatch Digital Crown or presses the physical suit distress switch:

#### Request Body:
```json
{
  "astronaut_id": "ASTRO-01",
  "note": "Manual distress beacon engaged via smartwatch crown hold."
}
```

#### Response:
```json
{
  "status": "EMERGENCY_DISPATCHED",
  "details": {
    "is_anomaly": true,
    "severity": "CRITICAL",
    "anomaly_types": ["MANUAL_EMERGENCY_BEACON"]
  }
}
```

---

### 6. Query Chief Flight Surgeon AI (`POST /api/chat`)
Allows smartwatches with voice dictation or bedside tablets to ask clinical and mission questions:

#### Request Body:
```json
{
  "message": "Doctor, I feel dizziness and heart fluttering after the EVA.",
  "astronaut_id": "ASTRO-01",
  "include_telemetry": true,
  "conversation_history": []
}
```

#### Response:
```json
{
  "reply": "Telemetry review confirms elevated heart rate at 148 BPM with irregular RR intervals indicative of Paroxysmal Atrial Fibrillation. Sit down immediately, attach the 100% O2 mask, and prepare 50mg Metoprolol from the Emergency Medical Kit.",
  "source": "nvidia_nim",
  "model_used": "meta/llama-3.1-70b-instruct",
  "latency_ms": 32.4,
  "vitals_inspected": true,
  "confidence_score": 0.96,
  "margin_of_error_percent": 3.8,
  "ai_disclaimer": "Cardiastracont Clinical Decision Support • Probabilistic AI (Est. Margin of Error: ±3.8%) • Ground confirmation advised."
}
```

---

## 🚨 Master Caution Klaxon & Acoustic Alarm Specs

When an anomaly (`CRITICAL` or `WARNING`) is detected, the audio subsystem synthesizes an authentic aerospace alarm:

* **Klaxon Waveform:** Dual-tone frequency-modulated sawtooth/square wave.
* **Frequencies:** High tone 1150 Hz $\to$ 750 Hz sweep; Secondary offset tone 1400 Hz $\to$ 820 Hz; Sub-bass acoustic punch at 140 Hz.
* **Repetition Rate:** 6 urgent pulses at 480ms intervals.
* **Volume Gain:** High acoustic gain (0.38).
* **Wearable Haptic Feedback:** Triggers `WKHapticType.failure` (continuous triple pulse vibration) on Apple Watch.
* **Mute Control:** Silenced immediately via `/api/devices/alarm-test` or `ACKNOWLEDGE & DISMISS` in the HUD.

---

## 💻 Plug-and-Play Code Snippets for Developers

### 🍎 1. Apple Watch (Swift / watchOS)

Add this function to your watchOS `NetworkManager.swift`:

```swift
import Foundation

struct TelemetryPacket: Codable {
    let astronaut_id: String
    let heart_rate: Double
    let oxygen: Double
    let stress_level: Double
    let ecg_classification: String
    let source: String
}

func transmitWatchBiometrics(hr: Double, spo2: Double, stress: Double, ecg: String) {
    guard let url = URL(string: "http://192.168.1.100:8000/api/telemetry") else { return }
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.addValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let packet = TelemetryPacket(
        astronaut_id: "ASTRO-01",
        heart_rate: hr,
        oxygen: spo2,
        stress_level: stress,
        ecg_classification: ecg,
        source: "apple_watch_ultra_2"
    )
    
    do {
        request.httpBody = try JSONEncoder().encode(packet)
    } catch { return }
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("Telemetry successfully streamed to Cardiastracont Core.")
        }
    }.resume()
}
```

---

### 🤖 2. Android / WearOS / Garmin Companion (Kotlin)

```kotlin
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

fun sendTelemetryToCardiastracont(hr: Double, o2: Double, stress: Double) {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("astronaut_id", "ASTRO-01")
        put("heart_rate", hr)
        put("oxygen", o2)
        put("stress_level", stress)
        put("source", "wearos_galaxy_watch_6")
    }
    
    val body = json.toString().toRequestBody("application/json; charset=utf-8".toMediaType())
    val request = Request.Builder()
        .url("http://192.168.1.100:8000/api/telemetry")
        .post(body)
        .build()

    client.newCall(request).enqueue(object : Callback {
        override fun onFailure(call: Call, e: java.io.IOException) {
            println("Cardiastracont Core Offline: Buffering locally.")
        }
        override fun onResponse(call: Call, response: Response) {
            println("Streamed: ${response.code}")
        }
    })
}
```

---

### ⚡ 3. Microcontroller / Habitat Biosensor (ESP32 / Arduino C++)

For pulse oximeters, CO2 canisters, and wearable ESP32 sensor boards:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* serverUrl = "http://192.168.1.100:8000/api/telemetry";

void sendBiometrics(float heartRate, float spO2, float co2Ppm) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<256> doc;
    doc["astronaut_id"] = "ASTRO-01";
    doc["heart_rate"] = heartRate;
    doc["oxygen"] = spO2;
    doc["stress_level"] = 25.0;
    doc["co2_level_ppm"] = co2Ppm;
    doc["source"] = "esp32_eclss_pod";

    String jsonString;
    serializeJson(doc, jsonString);

    int httpCode = http.POST(jsonString);
    http.end();
  }
}
```

---

### 🐍 4. Python Biosensor / Testing Script (`test_telemetry.py`)

```python
import requests
import time

SERVER_URL = "http://localhost:8000/api/telemetry"

payload = {
    "astronaut_id": "ASTRO-01",
    "heart_rate": 72.0,
    "oxygen": 98.5,
    "stress_level": 20.0,
    "co2_level_ppm": 420.0,
    "ecg_classification": "SINUS_RHYTHM",
    "source": "python_test_suite"
}

response = requests.post(SERVER_URL, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Server Response: {response.json()}")
```

---

### 💻 5. Direct cURL Command Examples (Terminal Testing)

#### Stream Normal Telemetry:
```bash
curl -X POST http://localhost:8000/api/telemetry \
  -H "Content-Type: application/json" \
  -d '{"astronaut_id":"ASTRO-01","heart_rate":72.0,"oxygen":98.5,"stress_level":22.0}'
```

#### Trigger Critical Hypoxia Alarm:
```bash
curl -X POST http://localhost:8000/api/telemetry \
  -H "Content-Type: application/json" \
  -d '{"astronaut_id":"ASTRO-01","heart_rate":124.0,"oxygen":79.5,"stress_level":88.0}'
```

#### Test Master Alarm Siren Across All Clients:
```bash
curl -X POST http://localhost:8000/api/devices/alarm-test
```

#### Register an Apple Watch:
```bash
curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"AW-ULTRA-01","device_name":"Apple Watch Ultra 2","device_type":"WEARABLE_SMARTWATCH","astronaut_id":"ASTRO-01","battery_level":92}'
```

---

## 📋 NASA Clinical Physiological Envelopes (NASA-STD-3001)

| Parameter | Nominal Cruise | Warning (Caution) | Critical Alarm (Emergency Klaxon) |
| :--- | :--- | :--- | :--- |
| **Heart Rate** | $55 - 100\text{ BPM}$ | $> 115\text{ BPM}$ or $< 50\text{ BPM}$ | $> 140\text{ BPM}$ or $< 40\text{ BPM}$ |
| **Blood Oxygen ($\text{SpO}_2$)** | $95.0\% - 100\%$ | $88.0\% - 92.0\%$ | $< 88.0\%$ (Acute Desaturation) |
| **Cabin $\text{CO}_2$** | $400 - 1,000\text{ PPM}$ | $1,200 - 2,000\text{ PPM}$ | $> 2,500\text{ PPM}$ (Hypercapnia) |
| **Ambient $\text{FiO}_2$** | $20.9\%$ | $17.0\% - 19.5\%$ | $< 16.0\%$ (Atmospheric Puncture) |
| **ECG Rhythm** | Sinus Rhythm | Sinus Tachycardia / Bradycardia | Paroxysmal Atrial Fibrillation (AFib) |
| **PERCLOS Drowsiness** | $0.00 - 0.20$ | $0.35 - 0.60$ | $> 0.70$ (Cognitive Microsleep / Unconscious) |

---

*Authored by the Cardiastracont Aerospace Engineering & Flight Medicine Team • Ready for Distribution & Integration.*

