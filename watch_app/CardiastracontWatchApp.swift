//
//  CardiastracontWatchApp.swift
//  Cardiastracont Watch Companion
//

import SwiftUI

@main
struct CardiastracontWatchApp: App {
    @StateObject private var healthKit = HealthKitManager.shared
    @StateObject private var network = NetworkManager.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(healthKit)
                .environmentObject(network)
        }
    }
}

