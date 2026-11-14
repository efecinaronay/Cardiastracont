using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace Cardiastracont.VR.Core
{
    /// <summary>
    /// High-performance asynchronous WebSocket client for Meta Quest 3 / OpenXR.
    /// Streams real-time biometrics and AI alerts from the Cardiastracont FastAPI server.
    /// Handles background thread to Unity main thread dispatching safely.
    /// </summary>
    public class VRWebSocketClient : MonoBehaviour
    {
        public static VRWebSocketClient Instance { get; private set; }

        [Header("Server Connection")]
        [Tooltip("WebSocket endpoint, e.g. ws://192.168.1.100:8000/ws/vr-stream")]
        public string serverWebSocketUri = "ws://127.0.0.1:8000/ws/vr-stream";
        public bool connectOnStart = true;
        public float reconnectIntervalSeconds = 3.0f;

        [Header("Connection Diagnostics")]
        [SerializeField] private bool isConnected = false;
        public bool IsConnected => isConnected;

        // Public Events for HUD and UI Listeners
        public event Action OnConnected;
        public event Action OnDisconnected;
        public event Action<TelemetryData> OnTelemetryReceived;
        public event Action<TriageData> OnTriageAlertReceived;

        private ClientWebSocket _webSocket;
        private CancellationTokenSource _cts;
        private readonly ConcurrentQueue<Action> _mainThreadQueue = new ConcurrentQueue<Action>();
        private bool _isReconnecting = false;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            if (connectOnStart)
            {
                ConnectToServer();
            }
        }

        private void Update()
        {
            // Drain main thread action queue to update Unity UI safely
            while (_mainThreadQueue.TryDequeue(out var action))
            {
                action?.Invoke();
            }
        }

        public void ConnectToServer()
        {
            if (isConnected || _isReconnecting) return;
            _cts = new CancellationTokenSource();
            _ = ConnectAsync(serverWebSocketUri, _cts.Token);
        }

        private async Task ConnectAsync(string uriString, CancellationToken ct)
        {
            _isReconnecting = true;

            while (!ct.IsCancellationRequested && !isConnected)
            {
                try
                {
                    _webSocket?.Dispose();
                    _webSocket = new ClientWebSocket();

                    Uri serverUri = new Uri(uriString);
                    Debug.Log($"[Cardiastracont VR] Connecting to: {serverUri}");

                    await _webSocket.ConnectAsync(serverUri, ct);

                    isConnected = true;
                    _isReconnecting = false;

                    _mainThreadQueue.Enqueue(() =>
                    {
                        Debug.Log("<color=green>[Cardiastracont VR] WebSocket Connected to Space Health Server.</color>");
                        OnConnected?.Invoke();
                    });

                    // Start background receive loop
                    await ReceiveLoopAsync(_webSocket, ct);
                }
                catch (Exception ex)
                {
                    if (ct.IsCancellationRequested) break;

                    isConnected = false;
                    _mainThreadQueue.Enqueue(() =>
                    {
                        OnDisconnected?.Invoke();
                    });

                    Debug.LogWarning($"[Cardiastracont VR] Connection attempt failed: {ex.Message}. Retrying in {reconnectIntervalSeconds}s...");
                    await Task.Delay(TimeSpan.FromSeconds(reconnectIntervalSeconds), ct);
                }
            }

            _isReconnecting = false;
        }

        private async Task ReceiveLoopAsync(ClientWebSocket ws, CancellationToken ct)
        {
            byte[] buffer = new byte[8192];

            while (ws.State == WebSocketState.Open && !ct.IsCancellationRequested)
            {
                var sb = new StringBuilder();
                WebSocketReceiveResult result;

                do
                {
                    result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", ct);
                        isConnected = false;
                        _mainThreadQueue.Enqueue(() => OnDisconnected?.Invoke());
                        return;
                    }

                    string chunk = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    sb.Append(chunk);
                }
                while (!result.EndOfMessage);

                string messageText = sb.ToString();
                ProcessInboundMessage(messageText);
            }
        }

        private void ProcessInboundMessage(string json)
        {
            try
            {
                VRStreamPacket packet = JsonUtility.FromJson<VRStreamPacket>(json);
                if (packet == null) return;

                if (packet.packet_type == "TELEMETRY_UPDATE" && packet.telemetry != null)
                {
                    _mainThreadQueue.Enqueue(() =>
                    {
                        OnTelemetryReceived?.Invoke(packet.telemetry);
                    });
                }
                else if (packet.packet_type == "AI_TRIAGE_ALERT" && packet.triage != null)
                {
                    _mainThreadQueue.Enqueue(() =>
                    {
                        if (packet.telemetry != null)
                            OnTelemetryReceived?.Invoke(packet.telemetry);

                        OnTriageAlertReceived?.Invoke(packet.triage);
                    });
                }
                else if (packet.packet_type == "SYSTEM_STATUS")
                {
                    _mainThreadQueue.Enqueue(() =>
                    {
                        if (packet.telemetry != null)
                            OnTelemetryReceived?.Invoke(packet.telemetry);
                        if (packet.triage != null)
                            OnTriageAlertReceived?.Invoke(packet.triage);
                    });
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[Cardiastracont VR] JSON Parse Error: {e.Message}\nRaw: {json}");
            }
        }

        public async Task SendMessageAsync(string jsonPayload)
        {
            if (_webSocket != null && _webSocket.State == WebSocketState.Open)
            {
                byte[] bytes = Encoding.UTF8.GetBytes(jsonPayload);
                await _webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
            }
        }

        public void NotifySanctuaryStateChanged(bool isActive)
        {
            SanctuarySyncMessage msg = new SanctuarySyncMessage
            {
                is_active = isActive,
                timestamp = DateTime.UtcNow.ToString("o")
            };
            string json = JsonUtility.FromJson<string>(JsonUtility.ToJson(msg));
            _ = SendMessageAsync(JsonUtility.ToJson(msg));
        }

        private void OnDestroy()
        {
            _cts?.Cancel();
            _webSocket?.Dispose();
        }

        private void OnApplicationQuit()
        {
            _cts?.Cancel();
            _webSocket?.Dispose();
        }
    }
}

