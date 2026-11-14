import os
from dotenv import load_dotenv
from typing import Optional, List

# Load .env file if present
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class Settings:
    # Server Settings (Supports Render.com dynamic $PORT)
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Primary / Alternative AI API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # NVIDIA NIM API Settings
    NVIDIA_NIM_API_KEY: Optional[str] = os.getenv("NVIDIA_NIM_API_KEY", None)
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "meta/llama-3.2-90b-vision-instruct")
    NVIDIA_TIMEOUT_SECONDS: float = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "25.0"))
    NVIDIA_MAX_RPM: int = int(os.getenv("NVIDIA_MAX_RPM", "40"))

    # Failover models to try if the primary model returns 404/410/5xx
    NVIDIA_FALLBACK_MODELS: List[str] = [
        "meta/llama-3.2-90b-vision-instruct",
        "deepseek-ai/deepseek-r1",
        "nvidia/nemotron-4-340b-instruct",
        "mistralai/mistral-large-2-instruct"
    ]

    # Space Medical Thresholds
    THRESHOLD_HR_MIN: float = float(os.getenv("THRESHOLD_HR_MIN", "45.0"))
    THRESHOLD_HR_MAX: float = float(os.getenv("THRESHOLD_HR_MAX", "125.0"))
    THRESHOLD_OXYGEN_MIN: float = float(os.getenv("THRESHOLD_OXYGEN_MIN", "92.0"))
    THRESHOLD_STRESS_MAX: float = float(os.getenv("THRESHOLD_STRESS_MAX", "80.0"))
    THRESHOLD_CO2_PPM_MAX: float = float(os.getenv("THRESHOLD_CO2_PPM_MAX", "1000.0"))

    # Rate Limiting & Cooldowns
    ALERT_COOLDOWN_SECONDS: float = float(os.getenv("ALERT_COOLDOWN_SECONDS", "1.5"))

settings = Settings()
