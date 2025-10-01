"""
Seed database with default tenant and test user

This script creates the foundational tenant and user data needed
for the AGENT_CREATION_STANDARD implementation.

Usage:
    python backend/scripts/seed_data.py
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

import uuid
from database import init_db, get_pg_pool, close_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """Seed database with default tenant and user"""

    logger.info("🌱 Starting database seeding...")
    logger.info("Connecting to Supabase PostgreSQL...")

    try:
        # Initialize database connection
        await init_db()
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            # Check if tenant already exists
            existing_tenant = await conn.fetchrow(
                "SELECT id FROM tenants WHERE slug = $1",
                "numen-ai"
            )

            if existing_tenant:
                tenant_id = existing_tenant['id']
                logger.info(f"✓ Tenant already exists: {tenant_id}")
            else:
                # Create default tenant
                tenant_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO tenants (id, name, slug, status)
                    VALUES ($1, $2, $3, $4)
                """, tenant_id, "Numen AI", "numen-ai", "active")
                logger.info(f"✅ Created tenant: {tenant_id}")

            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                "admin@numen.ai"
            )

            if existing_user:
                user_id = existing_user['id']
                logger.info(f"✓ User already exists: {user_id}")
            else:
                # Create test user
                user_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO users (id, tenant_id, email, name, status)
                    VALUES ($1, $2, $3, $4, $5)
                """, user_id, tenant_id, "admin@numen.ai", "Admin User", "active")
                logger.info(f"✅ Created user: {user_id}")

        logger.info("\n" + "="*60)
        logger.info("🎉 Database seeding complete!")
        logger.info("="*60)
        logger.info(f"Tenant ID: {tenant_id}")
        logger.info(f"User ID:   {user_id}")
        logger.info(f"Email:     admin@numen.ai")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Use these IDs when creating agents")
        logger.info("2. Run: python backend/scripts/create_default_agents.py")
        logger.info("="*60 + "\n")

        # Store IDs in a file for easy access by other scripts
        ids_file = Path(__file__).parent / "tenant_ids.txt"
        with open(ids_file, 'w') as f:
            f.write(f"TENANT_ID={tenant_id}\n")
            f.write(f"USER_ID={user_id}\n")
        logger.info(f"💾 IDs saved to: {ids_file}")

    finally:
        # Clean up connections
        await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(seed_database())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Seeding cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
