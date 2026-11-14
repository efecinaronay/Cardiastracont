using System;
using System.Collections.Generic;
using UnityEngine;

namespace Cardiastracont.VR.Core
{
    [Serializable]
    public class TelemetryData
    {
        public string astronaut_id = "ASTRO-01";
        public float heart_rate = 72.0f;
        public float stress_level = 20.0f;
        public float oxygen = 98.5f;
        public float hrv = 55.0f;
        public float co2_level_ppm = 420.0f;
        public string timestamp = "";
        public string source = "apple_watch";
        public bool is_emergency_triggered = false;
    }

    [Serializable]
    public class TriageData
    {
        public bool anomaly_detected = false;
        public string severity = "NOMINAL"; // NOMINAL, WARNING, CRITICAL
        public string condition_title = "";
        public string diagnosis = "";
        public string[] immediate_actions = new string[0];
        public string[] countermeasures = new string[0];
        public bool sanctuary_recommended = false;
        public string source = "nvidia_nim"; // "nvidia_nim" or "offline_protocol"
        public string model_used = "";
        public float execution_time_ms = 0.0f;
        public string timestamp = "";
    }

    [Serializable]
    public class VRStreamPacket
    {
        public string packet_type = "TELEMETRY_UPDATE"; // "TELEMETRY_UPDATE", "AI_TRIAGE_ALERT", "SYSTEM_STATUS"
        public TelemetryData telemetry;
        public TriageData triage;
        public string timestamp = "";
    }

    [Serializable]
    public class SanctuarySyncMessage
    {
        public string type = "SANCTUARY_STATE_CHANGE";
        public bool is_active = false;
        public string timestamp = "";
    }
}

