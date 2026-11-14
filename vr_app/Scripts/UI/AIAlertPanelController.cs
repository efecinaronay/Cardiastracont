using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.UI;
using Cardiastracont.VR.Core;

namespace Cardiastracont.VR.UI
{
    /// <summary>
    /// AI Alert & Triage Panel for Meta Quest 3 VR.
    /// Pops up in front of the astronaut when biometric anomalies trigger NVIDIA NIM AI triage
    /// or deep space offline flight surgeon safety protocols.
    /// </summary>
    public class AIAlertPanelController : MonoBehaviour
    {
        [Header("Panel Containers")]
        [SerializeField] private GameObject alertPanelCanvas;
        [SerializeField] private CanvasGroup canvasGroup;

        [Header("Alert Information Elements")]
        [SerializeField] private Text conditionTitleText;
        [SerializeField] private Text severityBadgeText;
        [SerializeField] private Image severityBadgeBackground;
        [SerializeField] private Text aiSourceBadgeText;
        [SerializeField] private Text diagnosisText;
        [SerializeField] private Text immediateActionsListText;
        [SerializeField] private Text countermeasuresListText;

        [Header("Interactive Buttons")]
        [SerializeField] private Button acknowledgeButton;
        [SerializeField] private Button launchSanctuaryButton;

        [Header("Audio")]
        [SerializeField] private AudioSource alertAlarmAudio;

        [Header("Colors")]
        [SerializeField] private Color criticalRed = new Color(1.0f, 0.2f, 0.2f, 1f);
        [SerializeField] private Color warningOrange = new Color(1.0f, 0.6f, 0.0f, 1f);
        [SerializeField] private Color nominalGreen = new Color(0.2f, 0.9f, 0.4f, 1f);

        [Header("Sanctuary Controller Reference")]
        [SerializeField] private SanctuaryModeController sanctuaryController;

        private void OnEnable()
        {
            if (VRWebSocketClient.Instance != null)
            {
                VRWebSocketClient.Instance.OnTriageAlertReceived += HandleTriageAlert;
            }

            if (acknowledgeButton != null)
                acknowledgeButton.onClick.AddListener(DismissAlert);

            if (launchSanctuaryButton != null)
                launchSanctuaryButton.onClick.AddListener(TriggerSanctuary);
        }

        private void OnDisable()
        {
            if (VRWebSocketClient.Instance != null)
            {
                VRWebSocketClient.Instance.OnTriageAlertReceived -= HandleTriageAlert;
            }

            if (acknowledgeButton != null)
                acknowledgeButton.onClick.RemoveListener(DismissAlert);

            if (launchSanctuaryButton != null)
                launchSanctuaryButton.onClick.RemoveListener(TriggerSanctuary);
        }

        private void Start()
        {
            // Start hidden until an anomaly occurs
            if (alertPanelCanvas != null)
                alertPanelCanvas.SetActive(false);
        }

        public void HandleTriageAlert(TriageData triage)
        {
            if (triage == null || !triage.anomaly_detected) return;

            // 1. Populate Alert Title & Severity
            if (conditionTitleText != null)
                conditionTitleText.text = triage.condition_title.ToUpper();

            Color alertColor = triage.severity == "CRITICAL" ? criticalRed : warningOrange;

            if (severityBadgeText != null)
            {
                severityBadgeText.text = $"SEVERITY: {triage.severity}";
                severityBadgeText.color = Color.white;
            }

            if (severityBadgeBackground != null)
                severityBadgeBackground.color = alertColor;

            // 2. AI Source Badge
            if (aiSourceBadgeText != null)
            {
                if (triage.source == "nvidia_nim")
                {
                    aiSourceBadgeText.text = $"⚡ NVIDIA NIM AI ({triage.model_used}) • {triage.execution_time_ms:F0}ms";
                    aiSourceBadgeText.color = new Color(0.45f, 0.9f, 0.2f); // Nvidia green
                }
                else
                {
                    aiSourceBadgeText.text = $"🛡️ OFFLINE SPACE SURGEON PROTOCOL (Deep-Space Safe)";
                    aiSourceBadgeText.color = new Color(0.4f, 0.8f, 1.0f); // Cyan
                }
            }

            // 3. Clinical Assessment / Diagnosis
            if (diagnosisText != null)
                diagnosisText.text = triage.diagnosis;

            // 4. Immediate Tactile & Life-Support Actions
            if (immediateActionsListText != null)
            {
                StringBuilder sb = new StringBuilder();
                if (triage.immediate_actions != null && triage.immediate_actions.Length > 0)
                {
                    for (int i = 0; i < triage.immediate_actions.Length; i++)
                    {
                        sb.AppendLine($"<color=#FFD700>[{i + 1}]</color> {triage.immediate_actions[i]}");
                    }
                }
                else
                {
                    sb.AppendLine("• Maintain current station position and await vitals stabilization.");
                }
                immediateActionsListText.text = sb.ToString();
            }

            // 5. Countermeasures
            if (countermeasuresListText != null && triage.countermeasures != null && triage.countermeasures.Length > 0)
            {
                StringBuilder sb = new StringBuilder();
                foreach (var cm in triage.countermeasures)
                {
                    sb.AppendLine($"• {cm}");
                }
                countermeasuresListText.text = sb.ToString();
            }

            // 6. Highlight Sanctuary Button if recommended (e.g. panic, acute stress, tachycardia)
            if (launchSanctuaryButton != null)
            {
                launchSanctuaryButton.gameObject.SetActive(triage.sanctuary_recommended);
            }

            // Show Panel with fade-in and audio alert
            if (alertPanelCanvas != null)
            {
                alertPanelCanvas.SetActive(true);
                StartCoroutine(FadePanelIn());
            }

            if (alertAlarmAudio != null)
            {
                alertAlarmAudio.Play();
            }
        }

        public void DismissAlert()
        {
            if (alertPanelCanvas != null)
                alertPanelCanvas.SetActive(false);

            if (alertAlarmAudio != null && alertAlarmAudio.isPlaying)
                alertAlarmAudio.Stop();
        }

        public void TriggerSanctuary()
        {
            DismissAlert();
            if (sanctuaryController != null)
            {
                sanctuaryController.ToggleSanctuaryMode(true);
            }
        }

        private IEnumerator FadePanelIn()
        {
            if (canvasGroup == null) yield break;
            canvasGroup.alpha = 0f;
            float duration = 0.3f;
            float elapsed = 0f;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                canvasGroup.alpha = Mathf.Lerp(0f, 1f, elapsed / duration);
                yield return null;
            }
            canvasGroup.alpha = 1f;
        }
    }
}

