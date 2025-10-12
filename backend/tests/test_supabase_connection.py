import asyncio
import asyncpg
from config import settings

async def test_connection():
    print(f"Testing Supabase connection...")
    print(f"Connection string: {settings.supabase_db_url[:50]}...")

    try:
        # Try direct connection
        conn = await asyncpg.connect(dsn=settings.supabase_db_url)
        print("✅ Connection successful!")

        # Test a simple query
        result = await conn.fetchval("SELECT 1")
        print(f"✅ Query test: {result}")

        # Check tables
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        print(f"✅ Tables found: {[t['table_name'] for t in tables]}")

        await conn.close()
        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection())
