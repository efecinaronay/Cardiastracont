using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Cardiastracont.VR.UI
{
    /// <summary>
    /// Lightweight, high-performance real-time telemetry graph for Meta Quest 3 VR.
    /// Draws dynamic rolling history curves for Heart Rate and SpO2.
    /// </summary>
    public class TelemetryGraph : MonoBehaviour
    {
        [Header("Graph Configuration")]
        [SerializeField] private LineRenderer lineRenderer;
        [SerializeField] private RectTransform graphContainer;
        [SerializeField] private int maxDataPoints = 40;
        [SerializeField] private float minValue = 40f;
        [SerializeField] private float maxValue = 180f;

        [Header("Styling")]
        [SerializeField] private Color nominalColor = new Color(0.2f, 0.9f, 0.4f, 1f);
        [SerializeField] private Color warningColor = new Color(1f, 0.6f, 0.1f, 1f);
        [SerializeField] private Color criticalColor = new Color(1f, 0.2f, 0.2f, 1f);

        private readonly Queue<float> _dataPoints = new Queue<float>();

        private void Awake()
        {
            if (lineRenderer == null)
                lineRenderer = GetComponent<LineRenderer>();

            if (lineRenderer != null)
            {
                lineRenderer.positionCount = 0;
                lineRenderer.useWorldSpace = false;
            }
        }

        public void AddValue(float value)
        {
            if (_dataPoints.Count >= maxDataPoints)
            {
                _dataPoints.Dequeue();
            }
            _dataPoints.Enqueue(value);

            UpdateGraphVisuals();
        }

        private void UpdateGraphVisuals()
        {
            if (lineRenderer == null) return;

            int count = _dataPoints.Count;
            if (count < 2) return;

            lineRenderer.positionCount = count;
            float[] points = _dataPoints.ToArray();

            float width = graphContainer != null ? graphContainer.rect.width : 300f;
            float height = graphContainer != null ? graphContainer.rect.height : 100f;
            float xStep = width / (maxDataPoints - 1);

            float latestVal = points[count - 1];
            Color activeColor = GetColorForValue(latestVal);
            lineRenderer.startColor = activeColor;
            lineRenderer.endColor = activeColor;

            for (int i = 0; i < count; i++)
            {
                float normalizedY = Mathf.InverseLerp(minValue, maxValue, points[i]);
                float xPos = i * xStep - (width * 0.5f);
                float yPos = (normalizedY * height) - (height * 0.5f);

                lineRenderer.SetPosition(i, new Vector3(xPos, yPos, 0f));
            }
        }

        private Color GetColorForValue(float val)
        {
            if (val > 140f || val < 50f) return criticalColor;
            if (val > 110f || val < 60f) return warningColor;
            return nominalColor;
        }

        public void Clear()
        {
            _dataPoints.Clear();
            if (lineRenderer != null)
                lineRenderer.positionCount = 0;
        }
    }
}

