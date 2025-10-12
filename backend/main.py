from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from config import settings
from routers import sessions, contracts, therapy, protocols, agents, affirmations, dashboard, voices, avatar, chat, livekit, intake
from database import init_db, close_db
# from services.memory import MemoryService  # TODO: Removed - using MemoryManager now
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
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


# Include routers
app.include_router(intake.router, prefix="/api", tags=["intake"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(voices.router, prefix="/api", tags=["voices"])
app.include_router(avatar.router, prefix="/api", tags=["avatar"])
app.include_router(affirmations.router, prefix="/api", tags=["affirmations"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
app.include_router(therapy.router, prefix="/api/therapy", tags=["therapy"])
app.include_router(protocols.router, prefix="/api/protocols", tags=["protocols"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(livekit.router, prefix="/api/livekit", tags=["livekit"])

# Create directories BEFORE mounting to avoid race conditions
audio_dir = Path("backend/audio_files")
audio_dir.mkdir(parents=True, exist_ok=True)

avatars_dir = Path("backend/avatars")
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