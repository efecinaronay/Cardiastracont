//
//  HealthKitManager.swift
//  Cardiastracont Watch Companion
//

import Foundation
import HealthKit
import Combine

public class HealthKitManager: ObservableObject {
    public static let shared = HealthKitManager()

    private let healthStore = HKHealthStore()
    
    // Published biometrics consumed by SwiftUI views & NetworkManager
    @Published public var currentHeartRate: Double = 72.0
    @Published public var currentOxygen: Double = 98.5
    @Published public var currentStress: Double = 24.0
    @Published public var currentHRV: Double = 55.0
    @Published public var currentECGClassification: String = "SINUS_RHYTHM"
    @Published public var ecgVoltageSamples: [Double] = []
    @Published public var isAuthorized: Bool = false
    @Published public var isSimulated: Bool = false
    @Published public var statusMessage: String = "Initializing HealthKit..."

    private var heartRateQuery: HKQuery?
    private var oxygenQuery: HKQuery?
    private var simulationTimer: AnyCancellable?

    private init() {
        requestAuthorization()
    }

    public func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else {
            statusMessage = "HealthKit unavailable. Running Simulation Mode."
            startSimulationMode()
            return
        }

        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate),
              let oxygenType = HKObjectType.quantityType(forIdentifier: .oxygenSaturation),
              let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else {
            startSimulationMode()
            return
        }

        var typesToRead: Set<HKObjectType> = [heartRateType, oxygenType, hrvType]

        if #available(watchOS 7.0, *) {
            typesToRead.insert(HKObjectType.electrocardiogramType())
        }

        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { [weak self] success, error in
            DispatchQueue.main.async {
                if success {
                    self?.isAuthorized = true
                    self?.statusMessage = "Sensors & Apple Watch ECG Active"
                    self?.startLiveQueries()
                } else {
                    self?.isAuthorized = false
                    self?.statusMessage = "Authorization denied. Using Simulation Mode."
                    self?.startSimulationMode()
                }
            }
        }
    }

    private func startLiveQueries() {
        startHeartRateQuery()
        startOxygenQuery()
        startHRVQuery()
        if #available(watchOS 7.0, *) {
            startECGQuery()
        }
    }

    @available(watchOS 7.0, *)
    private func startECGQuery() {
        let ecgType = HKObjectType.electrocardiogramType()
        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)
        let query = HKSampleQuery(sampleType: ecgType, predicate: nil, limit: 1, sortDescriptors: [sortDescriptor]) { [weak self] _, samples, _ in
            guard let ecgSample = samples?.first as? HKElectrocardiogram else { return }
            self?.processECGSample(ecgSample)
        }
        healthStore.execute(query)
    }

    @available(watchOS 7.0, *)
    private func processECGSample(_ ecg: HKElectrocardiogram) {
        var classificationStr = "SINUS_RHYTHM"
        switch ecg.classification {
        case .sinusRhythm:
            classificationStr = "SINUS_RHYTHM"
        case .atrialFibrillation:
            classificationStr = "ATRIAL_FIBRILLATION"
        case .inconclusiveHighHeartRate, .inconclusivePoorReading, .inconclusiveOther:
            classificationStr = "INCONCLUSIVE"
        default:
            classificationStr = "SINUS_RHYTHM"
        }

        DispatchQueue.main.async {
            self.currentECGClassification = classificationStr
        }

        // Query voltage samples from Apple Watch Lead I sensor
        let ecgQuery = HKElectrocardiogramQuery(ecg) { [weak self] _, result in
            switch result {
            case .measurement(let voltageMeasurement):
                if let voltage = voltageMeasurement.quantity(for: .appleWatchSimilarToLeadI) {
                    let microvolts = voltage.doubleValue(for: HKUnit.voltUnit(with: .micro))
                    DispatchQueue.main.async {
                        self?.ecgVoltageSamples.append(microvolts / 1000.0) // convert to mV
                        if (self?.ecgVoltageSamples.count ?? 0) > 40 {
                            self?.ecgVoltageSamples.removeFirst()
                        }
                    }
                }
            case .done:
                break
            case .error(let error):
                print("ECG voltage read error: \(error.localizedDescription)")
            @unknown default:
                break
            }
        }
        healthStore.execute(ecgQuery)
    }

    private func startHeartRateQuery() {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }

        let query = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: nil,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] _, samples, _, _, _ in
            self?.processHeartRateSamples(samples)
        }

        query.updateHandler = { [weak self] _, samples, _, _, _ in
            self?.processHeartRateSamples(samples)
        }

        healthStore.execute(query)
        self.heartRateQuery = query
    }

    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let quantitySamples = samples as? [HKQuantitySample], let lastSample = quantitySamples.last else { return }
        let hrUnit = HKUnit(from: "count/min")
        let hrValue = lastSample.quantity.doubleValue(for: hrUnit)

        DispatchQueue.main.async {
            self.currentHeartRate = (hrValue * 10).rounded() / 10
        }
    }

    private func startOxygenQuery() {
        guard let oxygenType = HKObjectType.quantityType(forIdentifier: .oxygenSaturation) else { return }

        let query = HKAnchoredObjectQuery(
            type: oxygenType,
            predicate: nil,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] _, samples, _, _, _ in
            self?.processOxygenSamples(samples)
        }

        query.updateHandler = { [weak self] _, samples, _, _, _ in
            self?.processOxygenSamples(samples)
        }

        healthStore.execute(query)
        self.oxygenQuery = query
    }

    private func processOxygenSamples(_ samples: [HKSample]?) {
        guard let quantitySamples = samples as? [HKQuantitySample], let lastSample = quantitySamples.last else { return }
        let percentUnit = HKUnit.percent()
        let oxygenValue = lastSample.quantity.doubleValue(for: percentUnit) * 100.0

        DispatchQueue.main.async {
            self.currentOxygen = (oxygenValue * 10).rounded() / 10
        }
    }

    private func startHRVQuery() {
        guard let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else { return }

        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)
        let query = HKSampleQuery(sampleType: hrvType, predicate: nil, limit: 1, sortDescriptors: [sortDescriptor]) { [weak self] _, samples, _ in
            guard let sample = samples?.first as? HKQuantitySample else { return }
            let msUnit = HKUnit.secondUnit(with: .milli)
            let hrvVal = sample.quantity.doubleValue(for: msUnit)

            DispatchQueue.main.async {
                self?.currentHRV = (hrvVal * 10).rounded() / 10
                // Derive autonomic stress score (0-100) inversely proportional to HRV
                // Low HRV (<30ms) = High sympathetic stress; High HRV (>70ms) = Rested
                let rawStress = max(5.0, min(95.0, 100.0 - (hrvVal * 1.1)))
                self?.currentStress = (rawStress * 10).rounded() / 10
            }
        }

        healthStore.execute(query)
    }

    // MARK: - Realistic Simulation Generator
    public func startSimulationMode() {
        isSimulated = true
        simulationTimer?.cancel()

        var step: Double = 0.0
        simulationTimer = Timer.publish(every: 1.0, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self else { return }
                step += 0.1
                
                // Natural sinusoidal fluctuations with physiological micro-jitter
                let hrFluctuation = sin(step) * 2.5 + Double.random(in: -1.0...1.0)
                let o2Fluctuation = cos(step * 0.5) * 0.3 + Double.random(in: -0.2...0.2)
                let stressFluctuation = sin(step * 0.8) * 3.0 + Double.random(in: -1.5...1.5)

                self.currentHeartRate = max(50.0, min(140.0, (72.0 + hrFluctuation) * 10).rounded() / 10)
                self.currentOxygen = max(90.0, min(100.0, (98.5 + o2Fluctuation) * 10).rounded() / 10)
                self.currentStress = max(10.0, min(90.0, (26.0 + stressFluctuation) * 10).rounded() / 10)
            }
    }

    public func injectEmergencyAnomaly(type: String) {
        isSimulated = true
        switch type {
        case "HYPOXIA":
            currentOxygen = 83.5
            currentHeartRate = 114.0
            currentStress = 84.0
        case "TACHYCARDIA":
            currentHeartRate = 164.0
            currentStress = 95.0
            currentOxygen = 96.0
        case "PANIC":
            currentStress = 98.0
            currentHeartRate = 135.0
        default:
            currentHeartRate = 72.0
            currentOxygen = 98.5
            currentStress = 22.0
        }
    }
}

