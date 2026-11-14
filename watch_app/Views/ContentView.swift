//
//  ContentView.swift
//  Cardiastracont Watch Companion
//

import SwiftUI

public struct ContentView: View {
    @State private var selectedTab = 0

    public var body: some View {
        TabView(selection: $selectedTab) {
            VitalsDashboardView()
                .tag(0)

            EmergencyTriggerView()
                .tag(1)

            SettingsView()
                .tag(2)
        }
        .tabViewStyle(.page)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

