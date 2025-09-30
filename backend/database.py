import asyncpg
from redis import asyncio as aioredis
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)

# Global connection pools
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[aioredis.Redis] = None


async def init_db():
    """Initialize database connections"""
    global pg_pool, redis_client

    # PostgreSQL connection pool
    try:
        pg_pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=2,
            max_size=10
        )
        logger.info("PostgreSQL connection pool created")

        # Create tables
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    room_name TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id UUID PRIMARY KEY,
                    session_id UUID REFERENCES sessions(id),
                    user_id TEXT NOT NULL,
                    goals JSONB NOT NULL,
                    tone TEXT NOT NULL,
                    voice_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id UUID PRIMARY KEY,
                    session_id UUID REFERENCES sessions(id),
                    speaker TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)

        logger.info("Database tables initialized")

    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise

    # Redis connection
    try:
        redis_url = f"redis://{settings.redis_host}:{settings.redis_port}"
        if settings.redis_password:
            redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}"

        redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")

    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_db():
    """Close database connections"""
    global pg_pool, redis_client

    if pg_pool:
        await pg_pool.close()
        logger.info("PostgreSQL connection pool closed")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


def get_pg_pool() -> asyncpg.Pool:
    """Get PostgreSQL connection pool"""
    if not pg_pool:
        raise RuntimeError("PostgreSQL pool not initialized")
    return pg_pool


def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    if not redis_client:
        raise RuntimeError("Redis client not initialized")
    return redis_client