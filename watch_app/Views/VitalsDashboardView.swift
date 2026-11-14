//
//  VitalsDashboardView.swift
//  Cardiastracont Watch Companion
//

import SwiftUI

public struct VitalsDashboardView: View {
    @ObservedObject var healthKit = HealthKitManager.shared
    @ObservedObject var network = NetworkManager.shared

    @State private var isPulsing = false

    public var body: some View {
        ScrollView {
            VStack(spacing: 8) {
                // Header: Stream Status & Latency
                HStack {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 8, height: 8)
                    Text(network.streamStatus.rawValue)
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundColor(.secondary)
                    Spacer()
                    if network.streamStatus == .streaming {
                        Text("\(Int(network.lastLatencyMs))ms")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.green)
                    }
                }
                .padding(.horizontal, 4)

                // 1. Heart Rate & ECG Card
                VStack(spacing: 4) {
                    HStack {
                        Image(systemName: "heart.fill")
                            .foregroundColor(.red)
                            .scaleEffect(isPulsing ? 1.25 : 1.0)
                            .animation(Animation.easeInOut(duration: 0.6).repeatForever(autoreverses: true), value: isPulsing)
                            .font(.title3)

                        VStack(alignment: .leading) {
                            Text("HEART RATE")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundColor(.gray)
                            HStack(alignment: .firstTextBaseline, spacing: 2) {
                                Text("\(Int(healthKit.currentHeartRate))")
                                    .font(.system(size: 26, weight: .black, design: .rounded))
                                    .foregroundColor(heartRateColor)
                                Text("BPM")
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                    }

                    // Apple Watch Lead I Electrical Heart Sensor Status
                    HStack {
                        Image(systemName: "waveform.path.ecg")
                            .foregroundColor(healthKit.currentECGClassification == "ATRIAL_FIBRILLATION" ? .red : .green)
                            .font(.system(size: 10))
                        Text(healthKit.currentECGClassification)
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundColor(healthKit.currentECGClassification == "ATRIAL_FIBRILLATION" ? .red : .green)
                        Spacer()
                        Text("LEAD I")
                            .font(.system(size: 8, weight: .semibold, design: .monospaced))
                            .foregroundColor(.secondary)
                    }
                    .padding(4)
                    .background(Color.black.opacity(0.3))
                    .cornerRadius(6)
                }
                .padding(8)
                .background(Color.black.opacity(0.4))
                .cornerRadius(10)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(heartRateColor.opacity(0.3), lineWidth: 1)
                )

                // 2. Dual Biometric Row: Oxygen (SpO2) & Stress Index
                HStack(spacing: 6) {
                    // SpO2 Gauge
                    VStack(alignment: .leading, spacing: 2) {
                        HStack {
                            Image(systemName: "lungs.fill")
                                .font(.system(size: 11))
                                .foregroundColor(.cyan)
                            Text("SPO2")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundColor(.gray)
                        }
                        Text("\(String(format: "%.1f", healthKit.currentOxygen))%")
                            .font(.system(size: 16, weight: .bold, design: .rounded))
                            .foregroundColor(oxygenColor)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
                    .background(Color.black.opacity(0.4))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(oxygenColor.opacity(0.3), lineWidth: 1)
                    )

                    // Stress Index
                    VStack(alignment: .leading, spacing: 2) {
                        HStack {
                            Image(systemName: "brain.head.profile")
                                .font(.system(size: 11))
                                .foregroundColor(.purple)
                            Text("STRESS")
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundColor(.gray)
                        }
                        Text("\(Int(healthKit.currentStress))/100")
                            .font(.system(size: 16, weight: .bold, design: .rounded))
                            .foregroundColor(stressColor)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(8)
                    .background(Color.black.opacity(0.4))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(stressColor.opacity(0.3), lineWidth: 1)
                    )
                }

                // Stream Control Toggle Button
                Button(action: {
                    if network.streamStatus == .streaming {
                        network.stopStreaming()
                    } else {
                        network.startStreaming()
                    }
                }) {
                    HStack {
                        Image(systemName: network.streamStatus == .streaming ? "pause.fill" : "antenna.radiowaves.left.and.right")
                        Text(network.streamStatus == .streaming ? "PAUSE STREAM" : "START STREAM")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                    }
                    .frame(maxWidth: .infinity)
                }
                .tint(network.streamStatus == .streaming ? .orange : .blue)
                .padding(.top, 4)
            }
            .padding(.horizontal, 4)
        }
        .onAppear {
            isPulsing = true
            if network.streamStatus == .disconnected {
                network.startStreaming()
            }
        }
    }

    private var statusColor: Color {
        switch network.streamStatus {
        case .streaming: return .green
        case .connecting: return .yellow
        case .offlineQueue: return .orange
        case .disconnected: return .gray
        case .error: return .red
        }
    }

    private var heartRateColor: Color {
        if healthKit.currentHeartRate > 130 || healthKit.currentHeartRate < 45 {
            return .red
        } else if healthKit.currentHeartRate > 105 {
            return .orange
        }
        return .green
    }

    private var oxygenColor: Color {
        if healthKit.currentOxygen < 88.0 {
            return .red
        } else if healthKit.currentOxygen < 92.0 {
            return .orange
        }
        return .cyan
    }

    private var stressColor: Color {
        if healthKit.currentStress > 80.0 {
            return .red
        } else if healthKit.currentStress > 60.0 {
            return .orange
        }
        return .purple
    }
}

