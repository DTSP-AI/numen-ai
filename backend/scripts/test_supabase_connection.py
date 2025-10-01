"""
Test Supabase database connection

Quick script to verify Supabase connection is working before running migrations.

Usage:
    python backend/scripts/test_supabase_connection.py
"""
import asyncio
import sys
from pathlib import Path
import os

# Add backend to path and set up environment
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load .env from project root
from dotenv import load_dotenv
project_root = backend_dir.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path)

from database import init_db, get_pg_pool, close_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test Supabase connection"""

    logger.info("🔌 Testing Supabase connection...")

    try:
        # Initialize database connection
        await init_db()
        pool = get_pg_pool()

        # Test query
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT version()")
            logger.info(f"✅ Connected to PostgreSQL!")
            logger.info(f"📊 Version: {result}")

            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            logger.info(f"\n📋 Found {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table['table_name']}")

        logger.info("\n✅ Supabase connection test passed!")

    except Exception as e:
        logger.error(f"\n❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(test_connection())
