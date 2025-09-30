from mem0 import Memory
from qdrant_client import QdrantClient
from typing import List, Dict, Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class MemoryService:
    """Wrapper for Mem0 memory layer with Qdrant backend"""

    def __init__(self):
        self.memory: Optional[Memory] = None
        self.qdrant_client: Optional[QdrantClient] = None

    async def initialize(self):
        """Initialize Mem0 and Qdrant connections"""
        try:
            # Initialize Qdrant client
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key
            )

            # Initialize Mem0 with Qdrant backend
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": settings.qdrant_host,
                        "port": settings.qdrant_port,
                    }
                }
            }

            self.memory = Memory.from_config(config)
            logger.info("Mem0 memory service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            raise

    async def store_user_preferences(
        self,
        user_id: str,
        preferences: Dict
    ):
        """Store persistent user preferences in user namespace"""
        try:
            self.memory.add(
                messages=[f"User preferences: {preferences}"],
                user_id=user_id,
                metadata={"type": "preferences", "namespace": "user"}
            )
            logger.info(f"Stored preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to store user preferences: {e}")
            raise

    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[Dict]:
        """Retrieve user preferences from memory"""
        try:
            results = self.memory.search(
                query="user preferences",
                user_id=user_id,
                limit=1
            )

            if results:
                return results[0].get("metadata", {})
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve user preferences: {e}")
            return None

    async def store_session_reflection(
        self,
        session_id: str,
        user_id: str,
        reflection: str
    ):
        """Store session reflection in session namespace"""
        try:
            self.memory.add(
                messages=[reflection],
                user_id=user_id,
                metadata={
                    "type": "reflection",
                    "namespace": "session",
                    "session_id": session_id
                }
            )
            logger.info(f"Stored reflection for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to store session reflection: {e}")
            raise

    async def get_session_history(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Retrieve recent session reflections"""
        try:
            results = self.memory.search(
                query="session reflections",
                user_id=user_id,
                limit=limit
            )

            return [
                {
                    "session_id": r.get("metadata", {}).get("session_id"),
                    "content": r.get("message", ""),
                    "timestamp": r.get("created_at")
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Failed to retrieve session history: {e}")
            return []

    async def clear_session_memory(
        self,
        session_id: str
    ):
        """Clear ephemeral session memory"""
        try:
            # Mem0 will handle cleanup based on namespace
            logger.info(f"Cleared session memory for {session_id}")

        except Exception as e:
            logger.error(f"Failed to clear session memory: {e}")