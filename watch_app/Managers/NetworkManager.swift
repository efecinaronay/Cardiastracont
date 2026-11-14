//
//  NetworkManager.swift
//  Cardiastracont Watch Companion
//

import Foundation
import Combine

public class NetworkManager: ObservableObject {
    public static let shared = NetworkManager()

    // Configuration
    @Published public var serverBaseUrl: String {
        didSet {
            UserDefaults.standard.set(serverBaseUrl, forKey: "cardiastracont_server_url")
        }
    }
    @Published public var streamStatus: StreamStatus = .disconnected
    @Published public var lastSyncTime: Date?
    @Published public var lastLatencyMs: Double = 0.0
    @Published public var offlineQueueCount: Int = 0

    private var streamingTimer: AnyCancellable?
    private var offlineQueue: [TelemetryPayload] = []
    private let urlSession: URLSession

    private init() {
        // Default to local server, editable in SettingsView
        let savedUrl = UserDefaults.standard.string(forKey: "cardiastracont_server_url")
        self.serverBaseUrl = savedUrl ?? "http://192.168.1.100:8000"

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 3.0
        config.timeoutIntervalForResource = 5.0
        config.waitsForConnectivity = false
        self.urlSession = URLSession(configuration: config)
    }

    public func startStreaming(intervalSeconds: Double = 1.5) { // 40 RPM (60s / 40 = 1.5s)
        stopStreaming()
        streamStatus = .connecting

        streamingTimer = Timer.publish(every: intervalSeconds, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.sendCurrentTelemetry()
            }
    }

    public func stopStreaming() {
        streamingTimer?.cancel()
        streamingTimer = nil
        streamStatus = .disconnected
    }

    public func sendCurrentTelemetry(isEmergency: Bool = false) {
        let hk = HealthKitManager.shared
        let payload = TelemetryPayload(
            astronaut_id: "ASTRO-01",
            heart_rate: hk.currentHeartRate,
            stress_level: hk.currentStress,
            oxygen: hk.currentOxygen,
            hrv: hk.currentHRV,
            co2_level_ppm: 420.0,
            ecg_lead: "LEAD_I_APPLE_WATCH",
            ecg_classification: hk.currentECGClassification,
            ambient_o2_percent: 20.9,
            o2_partial_pressure_kpa: 21.2,
            is_emergency_triggered: isEmergency
        )

        sendPayload(payload)
    }

    public func triggerEmergencySOS(note: String = "Manual Watch SOS", completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(cleanBaseUrl())/api/emergency-trigger") else {
            completion(false)
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let emergencyPayload = EmergencyTriggerPayload(astronaut_id: "ASTRO-01", note: note)

        do {
            request.httpBody = try JSONEncoder().encode(emergencyPayload)
        } catch {
            completion(false)
            return
        }

        urlSession.dataTask(with: request) { _, response, error in
            DispatchQueue.main.async {
                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    completion(true)
                } else {
                    completion(false)
                }
            }
        }.resume()
    }

    private func sendPayload(_ payload: TelemetryPayload) {
        guard let url = URL(string: "\(cleanBaseUrl())/api/telemetry") else {
            self.streamStatus = .error
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            request.httpBody = try JSONEncoder().encode(payload)
        } catch {
            return
        }

        let startTime = CFAbsoluteTimeGetCurrent()

        urlSession.dataTask(with: request) { [weak self] _, response, error in
            let elapsed = (CFAbsoluteTimeGetCurrent() - startTime) * 1000.0

            DispatchQueue.main.async {
                guard let self = self else { return }

                if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    self.streamStatus = .streaming
                    self.lastSyncTime = Date()
                    self.lastLatencyMs = (elapsed * 10).rounded() / 10
                    self.flushOfflineQueueIfAny()
                } else {
                    // Offline or unreachable - queue payload for deep space recovery
                    self.queueOffline(payload)
                    self.streamStatus = .offlineQueue
                }
            }
        }.resume()
    }

    private func queueOffline(_ payload: TelemetryPayload) {
        if offlineQueue.count >= 100 {
            offlineQueue.removeFirst()
        }
        offlineQueue.append(payload)
        offlineQueueCount = offlineQueue.count
    }

    private func flushOfflineQueueIfAny() {
        guard !offlineQueue.isEmpty else { return }
        
        let pending = offlineQueue
        offlineQueue.removeAll()
        offlineQueueCount = 0

        // In burst mode, send the most critical recent entries
        for p in pending.suffix(10) {
            sendPayload(p)
        }
    }

    private func cleanBaseUrl() -> String {
        return serverBaseUrl.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }
}

