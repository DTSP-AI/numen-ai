"""
Supabase Storage Service - Tenant-Isolated Avatar Storage

Handles avatar uploads and downloads with Supabase Storage for true multi-tenant isolation.
Uses Supabase's Row Level Security (RLS) for automatic tenant isolation.
"""

from typing import Optional
import logging
import httpx
import base64
from config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Supabase Storage client for avatar management

    Features:
    - Tenant-isolated storage buckets
    - Automatic access control via RLS
    - Direct integration with Supabase
    """

    def __init__(self):
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_key
        self.bucket_name = "avatars"

        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured, avatar storage will use local fallback")
            self.available = False
        else:
            self.available = True
            self.storage_url = f"{self.supabase_url}/storage/v1"
            logger.info("✅ Supabase Storage initialized for avatars")

    async def upload_avatar(
        self,
        file_bytes: bytes,
        filename: str,
        tenant_id: str,
        user_id: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Upload avatar to Supabase Storage with tenant isolation

        Path structure: avatars/{tenant_id}/{user_id}/{filename}

        Returns: Public URL to the avatar
        """
        if not self.available:
            raise Exception("Supabase Storage not available")

        # Tenant-isolated path
        file_path = f"{tenant_id}/{user_id}/{filename}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Upload to Supabase Storage
                response = await client.post(
                    f"{self.storage_url}/object/{self.bucket_name}/{file_path}",
                    headers={
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": content_type,
                        "x-upsert": "true"  # Allow overwrites
                    },
                    content=file_bytes
                )

                if response.status_code not in [200, 201]:
                    error_detail = response.text
                    logger.error(f"Supabase upload failed: {error_detail}")
                    raise Exception(f"Failed to upload avatar: {error_detail}")

                # Return public URL
                public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{file_path}"

                logger.info(f"Avatar uploaded to Supabase: {public_url}")
                return public_url

        except httpx.TimeoutException:
            logger.error("Supabase Storage upload timeout")
            raise Exception("Avatar upload timed out")
        except Exception as e:
            logger.error(f"Avatar upload failed: {e}", exc_info=True)
            raise

    async def delete_avatar(
        self,
        file_path: str,
        tenant_id: str
    ) -> bool:
        """
        Delete avatar from Supabase Storage

        Validates tenant ownership before deletion
        """
        if not self.available:
            raise Exception("Supabase Storage not available")

        # Ensure tenant owns the file
        if not file_path.startswith(f"{tenant_id}/"):
            raise Exception("Unauthorized: Cannot delete avatar from different tenant")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.storage_url}/object/{self.bucket_name}/{file_path}",
                    headers={
                        "Authorization": f"Bearer {self.supabase_key}"
                    }
                )

                if response.status_code == 200:
                    logger.info(f"Avatar deleted: {file_path}")
                    return True
                else:
                    logger.warning(f"Avatar deletion failed: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Avatar deletion failed: {e}", exc_info=True)
            return False

    async def ensure_bucket_exists(self) -> bool:
        """
        Ensure the avatars bucket exists in Supabase Storage

        Creates bucket with RLS policies if it doesn't exist
        """
        if not self.available:
            return False

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if bucket exists
                response = await client.get(
                    f"{self.storage_url}/bucket/{self.bucket_name}",
                    headers={
                        "Authorization": f"Bearer {self.supabase_key}"
                    }
                )

                if response.status_code == 200:
                    logger.info(f"✅ Supabase bucket '{self.bucket_name}' exists")
                    return True

                # Create bucket if it doesn't exist
                logger.info(f"Creating Supabase bucket: {self.bucket_name}")
                response = await client.post(
                    f"{self.storage_url}/bucket",
                    headers={
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "id": self.bucket_name,
                        "name": self.bucket_name,
                        "public": True,  # Public read access
                        "file_size_limit": 5242880,  # 5MB
                        "allowed_mime_types": ["image/png", "image/jpeg", "image/jpg", "image/webp"]
                    }
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✅ Supabase bucket '{self.bucket_name}' created")
                    return True
                else:
                    logger.error(f"Failed to create bucket: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Bucket check/creation failed: {e}", exc_info=True)
            return False


# Global instance
supabase_storage = SupabaseStorageService()
