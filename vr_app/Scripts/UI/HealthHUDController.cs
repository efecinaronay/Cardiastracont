using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using Cardiastracont.VR.Core;

namespace Cardiastracont.VR.UI
{
    /// <summary>
    /// Master Sci-Fi HUD Controller for Meta Quest 3 Space Health Command Center.
    /// Manages real-time vital readings, animated cardiac pulse, and telemetry graphs.
    /// </summary>
    public class HealthHUDController : MonoBehaviour
    {
        [Header("Connection Status UI")]
        [SerializeField] private Image linkStatusDot;
        [SerializeField] private Text linkStatusText;
        [SerializeField] private Text astronautIdText;

        [Header("Heart Rate UI")]
        [SerializeField] private Text heartRateText;
        [SerializeField] private Image heartIcon;
        [SerializeField] private TelemetryGraph heartRateGraph;

        [Header("Oxygen SpO2 UI")]
        [SerializeField] private Text oxygenText;
        [SerializeField] private Image oxygenFillBar;
        [SerializeField] private TelemetryGraph oxygenGraph;

        [Header("Autonomic Stress UI")]
        [SerializeField] private Text stressText;
        [SerializeField] private Image stressFillBar;

        [Header("Cabin / Suit Atmosphere")]
        [SerializeField] private Text co2Text;

        [Header("Audio Feedback")]
        [SerializeField] private AudioSource heartBeepAudio;
        [SerializeField] private AudioSource warningAudio;

        [Header("Theme Colors")]
        [SerializeField] private Color nominalColor = new Color(0.2f, 0.95f, 0.5f);
        [SerializeField] private Color warningColor = new Color(1.0f, 0.7f, 0.1f);
        [SerializeField] private Color criticalColor = new Color(1.0f, 0.2f, 0.2f);

        private Coroutine _pulseCoroutine;

        private void OnEnable()
        {
            if (VRWebSocketClient.Instance != null)
            {
                VRWebSocketClient.Instance.OnConnected += HandleConnected;
                VRWebSocketClient.Instance.OnDisconnected += HandleDisconnected;
                VRWebSocketClient.Instance.OnTelemetryReceived += HandleTelemetry;
            }
        }

        private void OnDisable()
        {
            if (VRWebSocketClient.Instance != null)
            {
                VRWebSocketClient.Instance.OnConnected -= HandleConnected;
                VRWebSocketClient.Instance.OnDisconnected -= HandleDisconnected;
                VRWebSocketClient.Instance.OnTelemetryReceived -= HandleTelemetry;
            }
        }

        private void Start()
        {
            SetConnectionState(false);
        }

        private void HandleConnected()
        {
            SetConnectionState(true);
        }

        private void HandleDisconnected()
        {
            SetConnectionState(false);
        }

        private void SetConnectionState(bool connected)
        {
            if (linkStatusDot != null)
                linkStatusDot.color = connected ? nominalColor : criticalColor;

            if (linkStatusText != null)
                linkStatusText.text = connected ? "STATION LINK • NOMINAL" : "STATION LINK • CONNECTING...";
        }

        private void HandleTelemetry(TelemetryData t)
        {
            if (t == null) return;

            // 1. Update Astronaut ID
            if (astronautIdText != null && !string.IsNullOrEmpty(t.astronaut_id))
                astronautIdText.text = t.astronaut_id.ToUpper();

            // 2. Update Heart Rate
            if (heartRateText != null)
            {
                heartRateText.text = $"{Mathf.RoundToInt(t.heart_rate)}";
                heartRateText.color = GetHRColor(t.heart_rate);
            }

            if (heartRateGraph != null)
                heartRateGraph.AddValue(t.heart_rate);

            TriggerHeartPulseAnimation(t.heart_rate);

            // 3. Update Oxygen (SpO2)
            if (oxygenText != null)
            {
                oxygenText.text = $"{t.oxygen:F1}%";
                oxygenText.color = GetO2Color(t.oxygen);
            }

            if (oxygenFillBar != null)
            {
                oxygenFillBar.fillAmount = Mathf.Clamp01(t.oxygen / 100f);
                oxygenFillBar.color = GetO2Color(t.oxygen);
            }

            if (oxygenGraph != null)
                oxygenGraph.AddValue(t.oxygen);

            // 4. Update Autonomic Stress
            if (stressText != null)
            {
                stressText.text = $"{Mathf.RoundToInt(t.stress_level)}/100";
                stressText.color = GetStressColor(t.stress_level);
            }

            if (stressFillBar != null)
            {
                stressFillBar.fillAmount = Mathf.Clamp01(t.stress_level / 100f);
                stressFillBar.color = GetStressColor(t.stress_level);
            }

            // 5. Update CO2
            if (co2Text != null)
            {
                co2Text.text = $"{Mathf.RoundToInt(t.co2_level_ppm)} PPM";
                co2Text.color = t.co2_level_ppm > 1000f ? warningColor : Color.white;
            }
        }

        private void TriggerHeartPulseAnimation(float bpm)
        {
            if (heartIcon == null) return;
            if (_pulseCoroutine != null) StopCoroutine(_pulseCoroutine);
            _pulseCoroutine = StartCoroutine(PulseIconRoutine());

            if (heartBeepAudio != null && bpm > 130f)
            {
                heartBeepAudio.pitch = Mathf.Clamp(bpm / 100f, 0.8f, 1.8f);
                heartBeepAudio.Play();
            }
        }

        private IEnumerator PulseIconRoutine()
        {
            Vector3 originalScale = Vector3.one;
            Vector3 targetScale = Vector3.one * 1.3f;
            float duration = 0.15f;

            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                heartIcon.transform.localScale = Vector3.Lerp(originalScale, targetScale, elapsed / duration);
                yield return null;
            }

            elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                heartIcon.transform.localScale = Vector3.Lerp(targetScale, originalScale, elapsed / duration);
                yield return null;
            }

            heartIcon.transform.localScale = originalScale;
        }

        private Color GetHRColor(float hr)
        {
            if (hr > 140f || hr < 45f) return criticalColor;
            if (hr > 110f || hr < 55f) return warningColor;
            return nominalColor;
        }

        private Color GetO2Color(float o2)
        {
            if (o2 < 88.0f) return criticalColor;
            if (o2 < 92.0f) return warningColor;
            return nominalColor;
        }

        private Color GetStressColor(float s)
        {
            if (s > 80.0f) return criticalColor;
            if (s > 60.0f) return warningColor;
            return nominalColor;
        }
    }
}

