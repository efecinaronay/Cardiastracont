//
//  TelemetryData.swift
//  Cardiastracont Watch Companion
//

import Foundation

public struct TelemetryPayload: Codable, Equatable {
    public let astronaut_id: String
    public let heart_rate: Double
    public let stress_level: Double
    public let oxygen: Double
    public let hrv: Double?
    public let co2_level_ppm: Double?
    public let ecg_lead: String?
    public let ecg_classification: String?
    public let ambient_o2_percent: Double?
    public let o2_partial_pressure_kpa: Double?
    public let timestamp: String
    public let source: String
    public let is_emergency_triggered: Bool

    public init(
        astronaut_id: String = "ASTRO-01",
        heart_rate: Double,
        stress_level: Double,
        oxygen: Double,
        hrv: Double? = nil,
        co2_level_ppm: Double? = nil,
        ecg_lead: String? = "LEAD_I_APPLE_WATCH",
        ecg_classification: String? = "SINUS_RHYTHM",
        ambient_o2_percent: Double? = 20.9,
        o2_partial_pressure_kpa: Double? = 21.2,
        timestamp: String = ISO8601DateFormatter().string(from: Date()),
        source: String = "apple_watch_watchos",
        is_emergency_triggered: Bool = false
    ) {
        self.astronaut_id = astronaut_id
        self.heart_rate = heart_rate
        self.stress_level = stress_level
        self.oxygen = oxygen
        self.hrv = hrv
        self.co2_level_ppm = co2_level_ppm
        self.ecg_lead = ecg_lead
        self.ecg_classification = ecg_classification
        self.ambient_o2_percent = ambient_o2_percent
        self.o2_partial_pressure_kpa = o2_partial_pressure_kpa
        self.timestamp = timestamp
        self.source = source
        self.is_emergency_triggered = is_emergency_triggered
    }
}

public struct EmergencyTriggerPayload: Codable {
    public let astronaut_id: String
    public let note: String
    public let timestamp: String

    public init(astronaut_id: String = "ASTRO-01", note: String = "Manual SOS triggered from Apple Watch") {
        self.astronaut_id = astronaut_id
        self.note = note
        self.timestamp = ISO8601DateFormatter().string(from: Date())
    }
}

public struct TelemetryResponse: Codable {
    public let status: String
    public let astronaut_id: String?
}

public enum StreamStatus: String {
    case disconnected = "DISCONNECTED"
    case connecting = "CONNECTING"
    case streaming = "STREAMING"
    case offlineQueue = "OFFLINE QUEUE"
    case error = "SYNC ERROR"
}

