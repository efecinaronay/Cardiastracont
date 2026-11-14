//
//  EmergencyTriggerView.swift
//  Cardiastracont Watch Companion
//

import SwiftUI
import WatchKit

public struct EmergencyTriggerView: View {
    @ObservedObject var network = NetworkManager.shared
    @State private var isArmed = false
    @State private var countdown = 3
    @State private var timer: Timer?
    @State private var alertDispatched = false
    @State private var dispatchSuccess = false

    public var body: some View {
        VStack(spacing: 8) {
            if alertDispatched {
                // Dispatched state
                VStack(spacing: 6) {
                    Image(systemName: "checkmark.shield.fill")
                        .font(.system(size: 38))
                        .foregroundColor(.green)
                    Text("SOS BROADCASTED")
                        .font(.system(size: 12, weight: .black, design: .monospaced))
                        .foregroundColor(.green)
                    Text("Triage protocols & VR HUD alerts initiated.")
                        .font(.system(size: 9))
                        .multilineTextAlignment(.center)
                        .foregroundColor(.secondary)

                    Button("RESET BEACON") {
                        alertDispatched = false
                        isArmed = false
                        countdown = 3
                    }
                    .tint(.gray)
                    .font(.system(size: 10, weight: .bold))
                    .padding(.top, 4)
                }
            } else if isArmed {
                // Countdown abort state
                VStack(spacing: 6) {
                    Text("TRANSMITTING IN")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundColor(.orange)

                    Text("\(countdown)")
                        .font(.system(size: 44, weight: .black, design: .rounded))
                        .foregroundColor(.red)

                    Button(action: cancelCountdown) {
                        Text("CANCEL SOS")
                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                            .frame(maxWidth: .infinity)
                    }
                    .tint(.gray)
                }
            } else {
                // Ready state: One-touch emergency trigger
                VStack(spacing: 6) {
                    Text("EMERGENCY BEACON")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundColor(.red)

                    Button(action: startEmergencySequence) {
                        VStack(spacing: 4) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 32))
                            Text("TRIGGER SOS")
                                .font(.system(size: 13, weight: .black, design: .monospaced))
                        }
                        .frame(maxWidth: .infinity, minHeight: 70)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.red)

                    Text("Press to broadcast instant medical distress beacon to Station AI & VR HUD.")
                        .font(.system(size: 8))
                        .multilineTextAlignment(.center)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 4)
    }

    private func startEmergencySequence() {
        WKInterfaceDevice.current().play(.start)
        isArmed = true
        countdown = 3

        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { t in
            if countdown > 1 {
                countdown -= 1
                WKInterfaceDevice.current().play(.click)
            } else {
                t.invalidate()
                dispatchSOS()
            }
        }
    }

    private func cancelCountdown() {
        timer?.invalidate()
        timer = nil
        isArmed = false
        countdown = 3
        WKInterfaceDevice.current().play(.stop)
    }

    private func dispatchSOS() {
        WKInterfaceDevice.current().play(.notification)
        network.triggerEmergencySOS(note: "EVA Emergency Panic Trigger") { success in
            self.dispatchSuccess = success
            self.alertDispatched = true
            self.isArmed = false
        }
    }
}

