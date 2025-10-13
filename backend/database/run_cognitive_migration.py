"""
Run Cognitive Assessment Migration (004)

This script executes the cognitive assessment database migration.
Run this to create the goal_assessments, belief_graphs, and cognitive_metrics tables.

Usage:
    python backend/database/run_cognitive_migration.py
    # OR from project root:
    python -m backend.database.run_cognitive_migration
"""

import asyncio
import asyncpg
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_migration():
    """Execute the cognitive assessment migration"""

    # Platform-safe path resolution
    base_dir = os.path.dirname(os.path.abspath(__file__))
    migrations_dir = os.path.join(base_dir, 'migrations')
    migration_file = os.path.join(migrations_dir, '004_cognitive_assessment_tables.sql')

    logger.info(f"🔍 Looking for migration file: {migration_file}")

    if not os.path.exists(migration_file):
        logger.error(f"❌ Migration file not found: {migration_file}")
        logger.error(f"   Current directory: {os.getcwd()}")
        logger.error(f"   Script directory: {base_dir}")
        logger.error(f"   Expected path: {migration_file}")
        return False

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        logger.info(f"📄 Loaded migration from {migration_file} ({len(migration_sql)} bytes)")

    except Exception as e:
        logger.error(f"❌ Failed to read migration file: {e}")
        return False

    # Connect to database with improved error handling
    try:
        # Read connection params from environment or use defaults
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = int(os.getenv('POSTGRES_PORT', 5432))
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_name = os.getenv('POSTGRES_DB', 'affirmation_db')

        logger.info(f"🔌 Connecting to {db_host}:{db_port}/{db_name} as {db_user}...")

        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            timeout=10
        )

        logger.info("✅ Connected to database")

        # Execute migration
        await conn.execute(migration_sql)

        logger.info("✅ Migration 004 executed successfully!")

        # Verify tables were created
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
                AND tablename IN ('goal_assessments', 'belief_graphs', 'cognitive_metrics', 'cognitive_schema_versions')
            ORDER BY tablename
        """)

        logger.info(f"✅ Verified {len(tables)} tables created: {[t['tablename'] for t in tables]}")

        # Verify default schema version was inserted
        schema_version = await conn.fetchrow("""
            SELECT version, description FROM cognitive_schema_versions WHERE is_default = TRUE
        """)

        if schema_version:
            logger.info(f"✅ Default schema version: {schema_version['version']} - {schema_version['description']}")
        else:
            logger.warning("⚠️  No default schema version found")

        await conn.close()
        return True

    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("\n📦 Remediation steps:")
        logger.error("   1. Install asyncpg: pip install asyncpg")
        logger.error("   2. Ensure PostgreSQL client libraries are installed")
        logger.error("   3. For Windows: Install Visual C++ Build Tools if needed")
        return False

    except asyncpg.exceptions.InvalidCatalogNameError:
        logger.error(f"❌ Database '{db_name}' does not exist")
        logger.error("\n📦 Remediation steps:")
        logger.error(f"   1. Create database: CREATE DATABASE {db_name};")
        logger.error(f"   2. Or set POSTGRES_DB environment variable to existing database")
        return False

    except asyncpg.exceptions.InvalidPasswordError:
        logger.error(f"❌ Invalid password for user '{db_user}'")
        logger.error("\n📦 Remediation steps:")
        logger.error(f"   1. Check POSTGRES_PASSWORD environment variable")
        logger.error(f"   2. Verify password for PostgreSQL user '{db_user}'")
        return False

    except asyncpg.exceptions.ConnectionRefusedError:
        logger.error(f"❌ Cannot connect to PostgreSQL at {db_host}:{db_port}")
        logger.error("\n📦 Remediation steps:")
        logger.error("   1. Ensure PostgreSQL is running")
        logger.error("   2. Check host and port settings")
        logger.error("   3. Verify firewall/network settings")
        return False

    except Exception as e:
        logger.error(f"❌ Migration failed: {type(e).__name__}: {e}")
        logger.error("\n📦 Remediation steps:")
        logger.error("   1. Check error message above for specific issue")
        logger.error("   2. Verify database connection parameters")
        logger.error("   3. Ensure user has CREATE TABLE permissions")
        logger.error("   4. Check PostgreSQL logs for more details")
        import traceback
        logger.debug(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())

    if success:
        print("\n✅ Cognitive assessment tables created successfully!")
        print("\nNext steps:")
        print("1. Test with: python backend/tests/test_cognitive_assessment.py")
        print("2. Enable cognitive assessment in agent contracts")
    else:
        print("\n❌ Migration failed. Check logs above.")
