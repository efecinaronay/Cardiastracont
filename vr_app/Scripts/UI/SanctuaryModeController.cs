using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using Cardiastracont.VR.Core;

namespace Cardiastracont.VR.UI
{
    /// <summary>
    /// Interactive Psychological Sanctuary & Guided Respiration Countermeasure.
    /// Dims mission-critical combat/station HUDs and runs a 60-second parasympathetic
    /// box-breathing cycle to reduce astronaut cortisol and autonomic panic in deep space.
    /// </summary>
    public class SanctuaryModeController : MonoBehaviour
    {
        [Header("Sanctuary Environment")]
        [SerializeField] private GameObject sanctuaryEnvironment;
        [SerializeField] private CanvasGroup mainHudCanvasGroup;
        [SerializeField] private Light mainCabinLight;
        [SerializeField] private ParticleSystem stardustParticleSystem;

        [Header("Breathing Circle Visuals")]
        [SerializeField] private RectTransform breathingCircle;
        [SerializeField] private Image breathingCircleGlow;
        [SerializeField] private Text breathingPhaseText;
        [SerializeField] private Text countdownTimerText;
        [SerializeField] private Text stressReductionTipText;

        [Header("Audio & Ambiance")]
        [SerializeField] private AudioSource ambientMusicAudio;
        [SerializeField] private AudioSource inhaleAudio;
        [SerializeField] private AudioSource exhaleAudio;

        [Header("Interactive Controls")]
        [SerializeField] private Button sanctuaryToggleButton;
        [SerializeField] private Button exitSanctuaryButton;

        [Header("Pacing Timers (Seconds)")]
        [SerializeField] private float inhaleDuration = 4.0f;
        [SerializeField] private float holdDuration = 4.0f;
        [SerializeField] private float exhaleDuration = 4.0f;
        [SerializeField] private float restDuration = 4.0f;
        [SerializeField] private float totalSessionDuration = 60.0f;

        private Coroutine _sessionCoroutine;
        private bool _isSanctuaryActive = false;
        public bool IsSanctuaryActive => _isSanctuaryActive;

        private void OnEnable()
        {
            if (sanctuaryToggleButton != null)
                sanctuaryToggleButton.onClick.AddListener(() => ToggleSanctuaryMode(!_isSanctuaryActive));

            if (exitSanctuaryButton != null)
                exitSanctuaryButton.onClick.AddListener(() => ToggleSanctuaryMode(false));
        }

        private void OnDisable()
        {
            if (sanctuaryToggleButton != null)
                sanctuaryToggleButton.onClick.RemoveAllListeners();

            if (exitSanctuaryButton != null)
                exitSanctuaryButton.onClick.RemoveAllListeners();
        }

        private void Start()
        {
            // Initial state: Sanctuary disabled
            if (sanctuaryEnvironment != null)
                sanctuaryEnvironment.SetActive(false);
        }

        public void ToggleSanctuaryMode(bool enable)
        {
            _isSanctuaryActive = enable;

            if (_isSanctuaryActive)
            {
                StartSanctuarySession();
            }
            else
            {
                StopSanctuarySession();
            }

            // Sync state with FastAPI backend
            if (VRWebSocketClient.Instance != null)
            {
                VRWebSocketClient.Instance.NotifySanctuaryStateChanged(_isSanctuaryActive);
            }
        }

        private void StartSanctuarySession()
        {
            if (sanctuaryEnvironment != null)
                sanctuaryEnvironment.SetActive(true);

            // Dim station HUD to reduce visual stimulus
            if (mainHudCanvasGroup != null)
                StartCoroutine(FadeCanvasGroup(mainHudCanvasGroup, 0.15f, 0.5f));

            if (mainCabinLight != null)
                StartCoroutine(FadeLightIntensity(mainCabinLight, 0.2f, 1.0f));

            if (stardustParticleSystem != null)
                stardustParticleSystem.Play();

            if (ambientMusicAudio != null)
                ambientMusicAudio.Play();

            if (_sessionCoroutine != null)
                StopCoroutine(_sessionCoroutine);

            _sessionCoroutine = StartCoroutine(SanctuaryBreathingLoop());
        }

        private void StopSanctuarySession()
        {
            if (_sessionCoroutine != null)
            {
                StopCoroutine(_sessionCoroutine);
                _sessionCoroutine = null;
            }

            if (sanctuaryEnvironment != null)
                sanctuaryEnvironment.SetActive(false);

            // Restore station HUD
            if (mainHudCanvasGroup != null)
                StartCoroutine(FadeCanvasGroup(mainHudCanvasGroup, 1.0f, 0.5f));

            if (mainCabinLight != null)
                StartCoroutine(FadeLightIntensity(mainCabinLight, 1.0f, 0.5f));

            if (stardustParticleSystem != null)
                stardustParticleSystem.Stop();

            if (ambientMusicAudio != null && ambientMusicAudio.isPlaying)
                ambientMusicAudio.Stop();
        }

        private IEnumerator SanctuaryBreathingLoop()
        {
            float sessionTimeRemaining = totalSessionDuration;
            Vector3 minScale = Vector3.one * 0.6f;
            Vector3 maxScale = Vector3.one * 1.5f;

            Color cyanColor = new Color(0.1f, 0.8f, 1.0f, 0.9f);
            Color violetColor = new Color(0.6f, 0.3f, 1.0f, 0.9f);
            Color softWhite = new Color(0.9f, 0.95f, 1.0f, 0.9f);

            while (sessionTimeRemaining > 0f)
            {
                // PHASE 1: INHALE (4 seconds)
                SetPhase("INHALE DEEPLY", "Fill lungs with oxygen; engage diaphragm.", softWhite);
                if (inhaleAudio != null) inhaleAudio.Play();
                yield return AnimateBreathingCircle(minScale, maxScale, inhaleDuration, (dt) => {
                    sessionTimeRemaining -= dt;
                    UpdateCountdown(sessionTimeRemaining);
                });

                if (sessionTimeRemaining <= 0) break;

                // PHASE 2: HOLD (4 seconds)
                SetPhase("HOLD BREATH", "Calm autonomic response; steady heart rhythm.", cyanColor);
                yield return WaitPhase(holdDuration, (dt) => {
                    sessionTimeRemaining -= dt;
                    UpdateCountdown(sessionTimeRemaining);
                });

                if (sessionTimeRemaining <= 0) break;

                // PHASE 3: EXHALE (4 seconds)
                SetPhase("EXHALE SLOWLY", "Release carbon dioxide and muscular tension.", violetColor);
                if (exhaleAudio != null) exhaleAudio.Play();
                yield return AnimateBreathingCircle(maxScale, minScale, exhaleDuration, (dt) => {
                    sessionTimeRemaining -= dt;
                    UpdateCountdown(sessionTimeRemaining);
                });

                if (sessionTimeRemaining <= 0) break;

                // PHASE 4: REST (4 seconds)
                SetPhase("REST & CENTER", "Prepare for next recovery cycle.", softWhite);
                yield return WaitPhase(restDuration, (dt) => {
                    sessionTimeRemaining -= dt;
                    UpdateCountdown(sessionTimeRemaining);
                });
            }

            // Session completed
            SetPhase("SESSION COMPLETE", "Physiological parasympathetic recovery protocol completed.", Color.green);
            yield return new WaitForSeconds(3.0f);
            ToggleSanctuaryMode(false);
        }

        private void SetPhase(string phaseTitle, string tip, Color glowColor)
        {
            if (breathingPhaseText != null)
                breathingPhaseText.text = phaseTitle;

            if (stressReductionTipText != null)
                stressReductionTipText.text = tip;

            if (breathingCircleGlow != null)
                breathingCircleGlow.color = glowColor;
        }

        private void UpdateCountdown(float remaining)
        {
            if (countdownTimerText != null)
            {
                int seconds = Mathf.Max(0, Mathf.CeilToInt(remaining));
                countdownTimerText.text = $"TIME REMAINING: {seconds}s";
            }
        }

        private IEnumerator AnimateBreathingCircle(Vector3 fromScale, Vector3 toScale, float duration, System.Action<float> onTick)
        {
            float elapsed = 0f;
            while (elapsed < duration)
            {
                float dt = Time.deltaTime;
                elapsed += dt;
                onTick?.Invoke(dt);

                float t = Mathf.SmoothStep(0f, 1f, elapsed / duration);
                if (breathingCircle != null)
                    breathingCircle.localScale = Vector3.Lerp(fromScale, toScale, t);

                yield return null;
            }
        }

        private IEnumerator WaitPhase(float duration, System.Action<float> onTick)
        {
            float elapsed = 0f;
            while (elapsed < duration)
            {
                float dt = Time.deltaTime;
                elapsed += dt;
                onTick?.Invoke(dt);
                yield return null;
            }
        }

        private IEnumerator FadeCanvasGroup(CanvasGroup cg, float targetAlpha, float duration)
        {
            float startAlpha = cg.alpha;
            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                cg.alpha = Mathf.Lerp(startAlpha, targetAlpha, elapsed / duration);
                yield return null;
            }
            cg.alpha = targetAlpha;
        }

        private IEnumerator FadeLightIntensity(Light l, float targetIntensity, float duration)
        {
            float start = l.intensity;
            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                l.intensity = Mathf.Lerp(start, targetIntensity, elapsed / duration);
                yield return null;
            }
            l.intensity = targetIntensity;
        }
    }
}

