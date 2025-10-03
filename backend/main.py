from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from config import settings
from routers import sessions, contracts, therapy, protocols, agents, affirmations, dashboard, voices, avatar, chat, livekit
from database import init_db, close_db
from services.memory import MemoryService


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

    # Initialize database connections
    await init_db()

    # Initialize memory service
    memory_service = MemoryService()
    await memory_service.initialize()
    app.state.memory = memory_service

    logger.info("Application startup complete")

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

# Mount static files for audio
audio_dir = Path("backend/audio_files")
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Mount static files for avatars
avatars_dir = Path("backend/avatars")
avatars_dir.mkdir(parents=True, exist_ok=True)
app.mount("/avatars", StaticFiles(directory=str(avatars_dir)), name="avatars")

logger.info(f"Audio files directory: {audio_dir.absolute()}")
logger.info(f"Avatars directory: {avatars_dir.absolute()}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )