//
//  SettingsView.swift
//  Cardiastracont Watch Companion
//

import SwiftUI

public struct SettingsView: View {
    @ObservedObject var network = NetworkManager.shared
    @ObservedObject var healthKit = HealthKitManager.shared

    @State private var serverUrl: String = ""

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                // Section 1: Server Config
                VStack(alignment: .leading, spacing: 4) {
                    Text("FASTAPI SERVER")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundColor(.gray)

                    TextField("http://<IP>:8000", text: $serverUrl)
                        .font(.system(size: 11, design: .monospaced))
                        .onSubmit {
                            network.serverBaseUrl = serverUrl
                        }

                    Text("Current: \(network.serverBaseUrl)")
                        .font(.system(size: 8, design: .monospaced))
                        .foregroundColor(.secondary)
                }
                .padding(8)
                .background(Color.black.opacity(0.3))
                .cornerRadius(8)

                // Section 2: Physiological Anomaly Injector (for Hackathon Demos)
                VStack(alignment: .leading, spacing: 6) {
                    Text("DEMO SIMULATION INJECTORS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundColor(.orange)

                    Button("Simulate Hypoxia (SpO2 83%)") {
                        healthKit.injectEmergencyAnomaly(type: "HYPOXIA")
                    }
                    .font(.system(size: 10))
                    .tint(.cyan)

                    Button("Simulate Tachycardia (164 BPM)") {
                        healthKit.injectEmergencyAnomaly(type: "TACHYCARDIA")
                    }
                    .font(.system(size: 10))
                    .tint(.red)

                    Button("Reset to Nominal (72 BPM, 98%)") {
                        healthKit.injectEmergencyAnomaly(type: "NOMINAL")
                    }
                    .font(.system(size: 10))
                    .tint(.green)
                }
                .padding(8)
                .background(Color.black.opacity(0.3))
                .cornerRadius(8)

                // Section 3: Diagnostic Telemetry
                VStack(alignment: .leading, spacing: 2) {
                    Text("DIAGNOSTICS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundColor(.gray)
                    Text("HealthKit: \(healthKit.isAuthorized ? "Authorized" : "Simulated/Denied")")
                        .font(.system(size: 8))
                    Text("Offline Buffer: \(network.offlineQueueCount) packets")
                        .font(.system(size: 8))
                    if let sync = network.lastSyncTime {
                        Text("Last Sync: \(sync.formatted(date: .omitted, time: .standard))")
                            .font(.system(size: 8))
                    }
                }
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.black.opacity(0.3))
                .cornerRadius(8)
            }
            .padding(.horizontal, 4)
        }
        .onAppear {
            serverUrl = network.serverBaseUrl
        }
    }
}

