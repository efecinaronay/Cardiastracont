using UnityEngine;
using UnityEngine.Events;

namespace Cardiastracont.VR.Interaction
{
    /// <summary>
    /// OpenXR & Meta Quest 3 compatible 3D spatial interactable button.
    /// Supports direct fingertip poke (Hand Tracking) and VR controller raycast triggers.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public class VRInteractableButton : MonoBehaviour
    {
        [Header("Button Motion")]
        [SerializeField] private Transform visualTransform;
        [SerializeField] private float pressDepth = 0.015f;
        [SerializeField] private float returnSpeed = 10.0f;

        [Header("Audio Feedback")]
        [SerializeField] private AudioSource clickAudio;

        [Header("Events")]
        public UnityEvent onButtonPressed;

        private Vector3 _initialLocalPosition;
        private bool _isPressed = false;

        private void Awake()
        {
            if (visualTransform == null)
                visualTransform = transform;

            _initialLocalPosition = visualTransform.localPosition;
        }

        private void Update()
        {
            if (!_isPressed)
            {
                visualTransform.localPosition = Vector3.Lerp(visualTransform.localPosition, _initialLocalPosition, Time.deltaTime * returnSpeed);
            }
        }

        private void OnTriggerEnter(Collider other)
        {
            // Triggered by Hand Tracking fingertip collider or Controller Poke Interactor
            if (!_isPressed && (other.CompareTag("PlayerHand") || other.name.Contains("Hand") || other.name.Contains("Finger") || other.name.Contains("Poke")))
            {
                PressButton();
            }
        }

        private void OnTriggerExit(Collider other)
        {
            if (other.CompareTag("PlayerHand") || other.name.Contains("Hand") || other.name.Contains("Finger") || other.name.Contains("Poke"))
            {
                ReleaseButton();
            }
        }

        public void PressButton()
        {
            _isPressed = true;
            visualTransform.localPosition = _initialLocalPosition + (Vector3.forward * pressDepth);

            if (clickAudio != null)
                clickAudio.Play();

            onButtonPressed?.Invoke();
        }

        public void ReleaseButton()
        {
            _isPressed = false;
        }
    }
}

