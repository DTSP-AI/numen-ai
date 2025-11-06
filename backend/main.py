from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from config import settings
from routers import sessions, contracts, protocols, agents, affirmations, dashboard, voices, avatar, chat, livekit, intake
# auth router excluded - not part of baseline working code
# therapy router disabled - TherapyAgent module not implemented
from database import init_db, close_db
from services.supabase_storage import supabase_storage


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    logger.info("Starting HypnoAgent backend...")

    # Validate critical API keys
    validation_errors = []
    if not settings.openai_api_key and not settings.OPENAI_API_KEY:
        validation_errors.append("OPENAI_API_KEY is not set (required for LLM and embeddings)")

    if not settings.supabase_db_url:
        validation_errors.append("SUPABASE_DB_URL is not set (required for database)")

    # Warnings for optional services
    if not settings.elevenlabs_api_key and not settings.ELEVENLABS_API_KEY:
        logger.warning("⚠️  ELEVENLABS_API_KEY not set - voice synthesis will be disabled")

    if not settings.deepgram_api_key and not settings.DEEPGRAM_API_KEY:
        logger.warning("⚠️  DEEPGRAM_API_KEY not set - STT will be disabled")

    if not settings.livekit_api_key and not settings.LIVEKIT_API_KEY:
        logger.warning("⚠️  LIVEKIT_API_KEY not set - real-time voice will be disabled")

    if validation_errors:
        for error in validation_errors:
            logger.error(f"❌ {error}")
        raise RuntimeError(f"Missing required configuration: {', '.join(validation_errors)}")

    logger.info("✅ All required API keys validated")

    # Initialize database connections
    await init_db()

    # Memory service initialization removed - using MemoryManager per agent
    # Each agent creates its own MemoryManager instance with tenant/agent context

    # Initialize Supabase Storage bucket for avatars
    if supabase_storage.available:
        bucket_ready = await supabase_storage.ensure_bucket_exists()
        if bucket_ready:
            logger.info("✅ Supabase Storage bucket ready for avatars")
        else:
            logger.warning("⚠️  Supabase Storage bucket initialization failed - using filesystem fallback")
    else:
        logger.info("ℹ️  Supabase Storage not configured - using filesystem fallback for avatars")

    logger.info("✅ Application startup complete")

    yield

    # Cleanup
    logger.info("Shutting down HypnoAgent backend...")
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="HypnoAgent API",
    description="Production-grade Manifestation/Hypnotherapy Voice Agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check showing all service statuses"""
    from database import pg_pool

    services = {}

    # Check database
    if pg_pool:
        try:
            async with pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            services["database"] = {"status": "connected", "type": "supabase_postgresql"}
        except Exception as e:
            services["database"] = {"status": "error", "error": str(e)}
    else:
        services["database"] = {"status": "not_initialized"}

    # Check OpenAI API key
    openai_key = settings.openai_api_key or settings.OPENAI_API_KEY
    services["openai"] = {
        "status": "configured" if openai_key else "missing",
        "required": True
    }

    # Check optional services
    elevenlabs_key = settings.elevenlabs_api_key or settings.ELEVENLABS_API_KEY
    services["elevenlabs"] = {
        "status": "configured" if elevenlabs_key else "not_configured",
        "required": False,
        "feature": "voice_synthesis"
    }

    deepgram_key = settings.deepgram_api_key or settings.DEEPGRAM_API_KEY
    services["deepgram"] = {
        "status": "configured" if deepgram_key else "not_configured",
        "required": False,
        "feature": "speech_to_text"
    }

    livekit_key = settings.livekit_api_key or settings.LIVEKIT_API_KEY
    livekit_secret = settings.livekit_api_secret or settings.LIVEKIT_API_SECRET
    services["livekit"] = {
        "status": "configured" if (livekit_key and livekit_secret) else "not_configured",
        "required": False,
        "feature": "realtime_voice"
    }

    mem0_key = settings.mem0_api_key or settings.MEM0_API_KEY
    services["mem0"] = {
        "status": "configured" if mem0_key else "local_mode",
        "required": False,
        "feature": "semantic_memory"
    }

    # Overall health
    required_services = [s for s in services.values() if s.get("required", False)]
    all_required_ok = all(s["status"] in ["connected", "configured"] for s in required_services)

    overall_status = "healthy" if all_required_ok else "degraded"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "environment": settings.environment,
        "services": services,
        "capabilities": {
            "text_chat": True,
            "voice_synthesis": services["elevenlabs"]["status"] == "configured",
            "speech_recognition": services["deepgram"]["status"] == "configured",
            "realtime_voice": services["livekit"]["status"] == "configured",
            "semantic_memory": True
        }
    }


# Include routers
# Authentication must be first so other routers can use the dependencies
# app.include_router(auth.router, tags=["authentication"])  # Disabled - not part of baseline working code
app.include_router(intake.router, prefix="/api", tags=["intake"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(voices.router, prefix="/api", tags=["voices"])
app.include_router(avatar.router, prefix="/api", tags=["avatar"])
app.include_router(affirmations.router, prefix="/api", tags=["affirmations"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
# app.include_router(therapy.router, prefix="/api/therapy", tags=["therapy"])  # Disabled - TherapyAgent not implemented
app.include_router(protocols.router, prefix="/api/protocols", tags=["protocols"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(livekit.router, prefix="/api/livekit", tags=["livekit"])

# Create directories BEFORE mounting to avoid race conditions
# Use paths relative to this file's location
base_dir = Path(__file__).parent
audio_dir = base_dir / "audio_files"
audio_dir.mkdir(parents=True, exist_ok=True)

avatars_dir = base_dir / "avatars"
avatars_dir.mkdir(parents=True, exist_ok=True)

# Mount static files for audio (after directory creation)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Mount static files for avatars (after directory creation)
app.mount("/avatars", StaticFiles(directory=str(avatars_dir)), name="avatars")

logger.info(f"Audio files directory: {audio_dir.absolute()}")
logger.info(f"Avatars directory: {avatars_dir.absolute()}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.environment == "development"
    )