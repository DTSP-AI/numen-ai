# Streamlined Architecture: Supabase + Mem0 Only
**Eliminating Redis and Qdrant Redundancy**

---

## 🎯 New Architecture (Simplified)

```
┌─────────────────────────────────────────────┐
│           Supabase PostgreSQL               │
│  (with pgvector extension enabled)          │
├─────────────────────────────────────────────┤
│                                             │
│  📦 Structured Data (PostgreSQL)            │
│  - agents (JSON contracts)                  │
│  - threads (conversations)                  │
│  - thread_messages                          │
│  - sessions                                 │
│  - users, tenants                           │
│                                             │
│  🧠 Vector Memory (pgvector)                │
│  - embeddings table                         │
│  - semantic search via pgvector             │
│  - Mem0 backend                             │
│                                             │
│  💾 Session State (PostgreSQL)              │
│  - sessions table (replaces Redis)          │
│  - TTL via PostgreSQL triggers              │
│                                             │
└─────────────────────────────────────────────┘
         ↑
         │
    ┌───┴────┐
    │  Mem0  │  (Memory abstraction layer)
    └────────┘
         ↑
         │
    ┌───┴────────────┐
    │ FastAPI Backend │
    └────────────────┘
```

---

## What We Eliminate

### ❌ Redis (Session/Cache)
**Replaced by**: PostgreSQL sessions table with TTL
- Supabase has connection pooling (no need for external cache)
- PostgreSQL handles session state efficiently
- Can add materialized views for caching if needed

### ❌ Qdrant (Vector Store)
**Replaced by**: Supabase pgvector extension
- Supabase includes pgvector (free tier)
- Native PostgreSQL vector similarity search
- No separate service to manage
- Better data locality

---

## Benefits

### 1. **Single Database Connection**
```python
# Before (3 connections)
pg_pool = await asyncpg.create_pool(...)
redis_client = await aioredis.from_url(...)
qdrant_client = QdrantClient(...)

# After (1 connection)
pg_pool = await asyncpg.create_pool(...)  # That's it!
```

### 2. **Simpler Deployment**
- One service to configure (Supabase)
- No Docker containers for Qdrant/Redis
- Reduced infrastructure complexity

### 3. **Better Performance**
- No network hops between services
- Data locality (vectors + structured data together)
- Supabase's connection pooling handles load

### 4. **Lower Cost**
- Supabase free tier includes pgvector
- No separate Qdrant/Redis hosting
- Single bill

### 5. **Easier Backups**
- One database to backup
- Supabase handles it automatically
- Point-in-time recovery included

---

## Implementation Plan

### Phase 1: Enable pgvector in Supabase ✅

**In Supabase Dashboard**:
1. Go to **Database** → **Extensions**
2. Search for `vector`
3. Enable `pgvector` extension

**Or via SQL**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Phase 2: Create Memory Tables

```sql
-- Memory embeddings table
CREATE TABLE memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    agent_id UUID NOT NULL REFERENCES agents(id),
    user_id UUID REFERENCES users(id),

    -- Memory content
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension

    -- Memory metadata
    namespace VARCHAR(255) NOT NULL,  -- {tenant_id}:{agent_id}:{context}
    memory_type VARCHAR(50),  -- reflection, fact, preference, etc.
    metadata JSONB,

    -- Access tracking
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_memory_tenant_agent ON memory_embeddings(tenant_id, agent_id);
CREATE INDEX idx_memory_namespace ON memory_embeddings(namespace);
CREATE INDEX idx_memory_type ON memory_embeddings(memory_type);

-- Vector similarity index (HNSW for fast search)
CREATE INDEX idx_memory_embedding ON memory_embeddings
USING hnsw (embedding vector_cosine_ops);
```

### Phase 3: Session Management (Replace Redis)

```sql
-- Sessions table (already exists, enhance it)
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS session_data JSONB,
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;

-- Index for TTL cleanup
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Function to auto-delete expired sessions
CREATE OR REPLACE FUNCTION delete_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (Supabase pg_cron extension)
SELECT cron.schedule(
    'delete-expired-sessions',
    '*/5 * * * *',  -- Every 5 minutes
    'SELECT delete_expired_sessions();'
);
```

### Phase 4: Configure Mem0 with Supabase

**New**: `backend/services/unified_memory_manager.py`

```python
from mem0 import Memory
from typing import Dict, Any, List, Optional
import os

class UnifiedMemoryManager:
    """
    Unified memory manager using Supabase pgvector

    Replaces:
    - Qdrant (vector store)
    - Redis (session cache)
    - Separate memory services
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        agent_traits: Dict[str, Any]
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.agent_traits = agent_traits

        # Namespace pattern: {tenant_id}:{agent_id}:{context}
        self.namespace = f"{tenant_id}:{agent_id}"

        # Initialize Mem0 with Supabase pgvector backend
        self.memory = Memory.from_config({
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "connection_string": os.getenv("SUPABASE_DB_URL"),
                    "table_name": "memory_embeddings",
                    "embedding_model": "text-embedding-ada-002",
                    "embedding_dimension": 1536
                }
            }
        })

    async def add_memory(
        self,
        content: str,
        memory_type: str = "reflection",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store memory in Supabase pgvector"""
        await self.memory.add(
            messages=[content],
            user_id=self.namespace,
            metadata={
                "tenant_id": self.tenant_id,
                "agent_id": self.agent_id,
                "namespace": self.namespace,
                "memory_type": memory_type,
                **(metadata or {})
            }
        )

    async def search_memories(
        self,
        query: str,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """Search memories via pgvector similarity"""
        results = await self.memory.search(
            query=query,
            user_id=self.namespace,
            limit=limit
        )
        return results
```

### Phase 5: Session Management (No Redis)

**New**: `backend/services/session_manager.py`

```python
from database import get_pg_pool
from datetime import datetime, timedelta
import json
from uuid import UUID

class SessionManager:
    """
    Session management using PostgreSQL
    Replaces Redis for session storage
    """

    @staticmethod
    async def create_session(
        session_id: str,
        user_id: str,
        agent_id: str,
        tenant_id: str,
        data: dict,
        ttl_seconds: int = 3600
    ):
        """Create session in PostgreSQL"""
        pool = get_pg_pool()
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO sessions (
                    id, user_id, agent_id, tenant_id,
                    session_data, expires_at, status,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    session_data = $5,
                    expires_at = $6,
                    updated_at = NOW()
            """,
                UUID(session_id),
                user_id,
                UUID(agent_id) if agent_id else None,
                UUID(tenant_id),
                json.dumps(data),
                expires_at,
                'active'
            )

    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        """Get session from PostgreSQL"""
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT session_data, expires_at
                FROM sessions
                WHERE id = $1 AND expires_at > NOW()
            """, UUID(session_id))

            if row:
                return json.loads(row['session_data'])
            return None

    @staticmethod
    async def delete_session(session_id: str):
        """Delete session"""
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM sessions WHERE id = $1",
                UUID(session_id)
            )
```

---

## Migration Steps

### 1. Enable pgvector in Supabase
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Create memory tables
Run the SQL from Phase 2 above

### 3. Update environment variables

**Remove**:
```bash
# DELETE THESE
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

**Keep**:
```bash
# ONLY NEED THESE
SUPABASE_DB_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

### 4. Update `database.py`

Remove Redis/Qdrant initialization, keep only PostgreSQL:

```python
async def init_db():
    """Initialize database connections"""
    global pg_pool

    # Only PostgreSQL (Supabase)
    if settings.supabase_db_url:
        logger.info("Connecting to Supabase PostgreSQL...")
        pg_pool = await asyncpg.create_pool(
            dsn=settings.supabase_db_url,
            min_size=2,
            max_size=10
        )
        logger.info("✅ Supabase PostgreSQL connected (with pgvector)")

    # Create tables + enable pgvector
    async with pg_pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # ... rest of table creation
```

### 5. Update `config.py`

Remove Redis/Qdrant settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Database - Only Supabase needed
    supabase_db_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # Remove these:
    # redis_host: str = "localhost"
    # qdrant_host: str = "localhost"
```

---

## Comparison

| Feature | Old Stack | New Stack |
|---------|-----------|-----------|
| **Structured Data** | PostgreSQL | ✅ Supabase PostgreSQL |
| **Vector Search** | Qdrant | ✅ Supabase pgvector |
| **Session Cache** | Redis | ✅ PostgreSQL sessions |
| **Memory Layer** | Mem0 + Qdrant | ✅ Mem0 + pgvector |
| **Services to Manage** | 3 | **1** |
| **Connection Pools** | 3 | **1** |
| **Docker Containers** | 2 (Redis, Qdrant) | **0** |
| **Configuration** | Complex | **Simple** |
| **Cost** | Higher | **Lower** |
| **Backups** | 3 systems | **1 system** |

---

## Performance Notes

### pgvector vs Qdrant

**pgvector Advantages**:
- Data locality (no network hop)
- Native PostgreSQL integration
- HNSW indexing (fast)
- Good for <10M vectors

**When to use Qdrant instead**:
- >10M vectors
- Need sub-millisecond search
- Require advanced filtering

**For Numen AI**: pgvector is perfect!
- Typical: <100K memories per tenant
- Response time: <50ms is fine for hypnotherapy
- Simpler is better

### PostgreSQL Sessions vs Redis

**PostgreSQL Advantages**:
- No separate service
- ACID guarantees
- Better for persistent sessions

**Redis Advantages**:
- Slightly faster (in-memory)
- Built-in TTL

**For Numen AI**: PostgreSQL is better!
- Sessions last 1+ hour (not milliseconds)
- Need durability (don't lose therapy sessions)
- Connection pooling handles speed

---

## Next Steps

1. ✅ Enable pgvector in Supabase
2. ✅ Create memory_embeddings table
3. ✅ Add session_data column to sessions
4. ✅ Update UnifiedMemoryManager to use pgvector
5. ✅ Remove Redis/Qdrant dependencies
6. ✅ Update config.py and .env
7. ✅ Test memory operations

---

**Result**: Single Supabase connection handles everything!

```python
# That's all you need!
pg_pool = await asyncpg.create_pool(dsn=settings.supabase_db_url)

# Memory, sessions, agents, threads - all in one place
```

Clean, simple, maintainable. ✨
