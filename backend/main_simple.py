"""Simple backend without database dependencies for testing"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HypnoAgent API (Simple)",
    description="Production-grade Manifestation/Hypnotherapy Voice Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
        "note": "Simple mode - no database required"
    }


@app.get("/")
async def root():
    return {"message": "HypnoAgent API is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting HypnoAgent backend (simple mode - no DB)...")
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )