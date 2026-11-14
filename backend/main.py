import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import settings
from routes.telemetry import router as telemetry_router
from routes.analysis import router as analysis_router
from routes.websocket import router as websocket_router
from routes.chat import router as chat_router

# Configure rich logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Cardiastracont.Main")

# Robust multi-path resolution for web_app across local, Render, Docker & Linux
_candidate_web_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web_app")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "web_app")),
    os.path.abspath(os.path.join(os.getcwd(), "web_app")),
    os.path.abspath(os.path.join(os.getcwd(), "..", "web_app")),
]
WEB_DIR = next((d for d in _candidate_web_dirs if os.path.exists(d)), _candidate_web_dirs[0])
logger.info(f"📁 Static Web Directory resolved to: {WEB_DIR}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=====================================================")
    logger.info("🚀 Cardiastracont: Offline-First Autonomic Space Health Agent")
    logger.info(f"🛰️  Server running at http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info(f"📱 Web Console & Health Pad: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/")
    logger.info(f"🧠 AI Engine: NVIDIA NIM ({settings.NVIDIA_MODEL})")
    logger.info(f"🛡️  Offline Deep-Space Fallback: ACTIVE")
    logger.info(f"👓 VR WebSocket Stream: ws://{settings.SERVER_HOST}:{settings.SERVER_PORT}/ws/vr-stream")
    logger.info("=====================================================")
    yield
    logger.info("🛑 Cardiastracont server shutting down gracefully...")

app = FastAPI(
    title="Cardiastracont Space Health Core",
    description="Offline-First Space Health Telemetry, NVIDIA NIM AI Autonomous Triage, Meta Quest 3 VR Stream, and Web Console",
    version="1.0.0",
    lifespan=lifespan
)

# Enable permissive CORS for Apple Watch, Meta Quest 3, and Mobile Web Browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(telemetry_router)
app.include_router(analysis_router)
app.include_router(websocket_router)
app.include_router(chat_router)

# Mount Web App Static Assets (CSS, JS, Manifest)
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/", tags=["Web App"])
async def serve_dashboard():
    """Serves the responsive Web Console & Mobile Phone Health Pad application."""
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Cardiastracont API Online. Web directory not found."}

@app.get("/dashboard", tags=["Web App"])
async def serve_dashboard_alias():
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Cardiastracont Dashboard"}

@app.get("/api/guide", tags=["Web App"])
async def serve_device_api_guide():
    """Serves the full Device Ecosystem & API Integration Guide markdown document."""
    guide_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DEVICE_API_AND_INTEGRATION_GUIDE.md")),
        os.path.abspath(os.path.join(os.getcwd(), "DEVICE_API_AND_INTEGRATION_GUIDE.md")),
    ]
    guide_file = next((f for f in guide_candidates if os.path.exists(f)), None)
    if guide_file:
        return FileResponse(guide_file, media_type="text/markdown", filename="Cardiastracont_Device_API_Guide.md")
    return {"message": "Guide document not found."}

@app.get("/api/info", tags=["Root"])
async def api_info():
    return {
        "project": "Cardiastracont: Offline-First Autonomic Space Health Agent",
        "mission": "Deep-Space Biometric Ingestion, Autonomous Countermeasures, & VR Sanctuary",
        "docs_url": "/docs",
        "endpoints": {
            "web_console": "/",
            "telemetry_ingest": "POST /api/telemetry",
            "emergency_sos": "POST /api/emergency-trigger",
            "analyze_anomaly": "POST /api/analyze-anomaly",
            "telemetry_history": "GET /api/history",
            "vr_websocket_stream": "ws://<host>:<port>/ws/vr-stream"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )
