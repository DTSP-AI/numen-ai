"""
Embeddings Service - OpenAI Integration

Generates embeddings for semantic memory storage and retrieval.
"""

import logging
from typing import Optional, List
import httpx
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Service for generating text embeddings using OpenAI
    """

    def __init__(self):
        self.api_key = settings.openai_api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective

        if not self.api_key:
            logger.warning("WARNING: OPENAI_API_KEY not set. Embeddings will be disabled.")

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text

        Args:
            text: Text to embed

        Returns:
            List of floats (1536 dimensions) or None if failed
        """
        if not self.api_key:
            logger.warning("Embeddings skipped (no API key)")
            return None

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": text[:8000]  # Limit to 8k chars to avoid token limits
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data["data"][0]["embedding"]
                    logger.debug(f"Generated embedding: {len(embedding)} dimensions")
                    return embedding
                else:
                    logger.error(f"OpenAI embeddings API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (batch)

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (or None for failures)
        """
        if not self.api_key:
            return [None] * len(texts)

        if not texts:
            return []

        try:
            # Filter empty texts
            valid_texts = [t[:8000] if t and t.strip() else "" for t in texts]

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": valid_texts
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embeddings = [item["embedding"] for item in data["data"]]
                    logger.info(f"Generated {len(embeddings)} embeddings")
                    return embeddings
                else:
                    logger.error(f"OpenAI batch embeddings error: {response.status_code}")
                    return [None] * len(texts)

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)


# Global service instance
embeddings_service = EmbeddingsService()
