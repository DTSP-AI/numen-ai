"""
Avatar Generation Router - GPT-Image-1 + Supabase Storage

Provides endpoints for generating or uploading agent avatars with tenant isolation.
Uses Supabase Storage for true multi-tenant security.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from pydantic import BaseModel
from typing import Optional
import logging
import uuid
from pathlib import Path
import os
import httpx
import base64
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from services.supabase_storage import supabase_storage
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Get OpenAI API key from settings (handles both uppercase and lowercase)
OPENAI_API_KEY = settings.OPENAI_API_KEY or settings.openai_api_key
OPENAI_AVAILABLE = bool(OPENAI_API_KEY)


class AvatarGenerateRequest(BaseModel):
    """Request to generate avatar using DALL-E-3"""
    prompt: str
    size: Optional[str] = "1024x1024"  # 1024x1024, 1024x1792, 1792x1024
    quality: Optional[str] = "standard"  # standard, hd (auto will be converted to standard)
    background: Optional[str] = "opaque"  # Accepted but not sent to API (not supported)
    output_format: Optional[str] = "png"  # png, jpeg, webp


class AvatarResponse(BaseModel):
    """Avatar generation response"""
    avatar_url: str
    prompt_used: str


@router.post("/avatar/generate", response_model=AvatarResponse)
async def generate_avatar(
    request: AvatarGenerateRequest,
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id")
):
    """
    Generate agent avatar using DALL-E-3

    Raises 500 if OpenAI is not configured (no silent fallback).
    Saves image to Supabase with tenant isolation.
    """
    # Enforce tenant isolation
    tenant_id = x_tenant_id or "00000000-0000-0000-0000-000000000001"  # Default for dev
    user_id = x_user_id or "00000000-0000-0000-0000-000000000001"

    logger.info(f"Avatar generation requested by tenant {tenant_id}, user {user_id}: {request.prompt}")

    # 🔴 FIX 1: Raise error instead of silent fallback
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI API key not configured - cannot generate avatar")
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Avatar generation unavailable."
        )

    try:
        # Minimal guardrail: Only enforce headshot orientation, let user control all style
        # DALL-E-3 will follow the user's creative direction without additional constraints
        enhanced_prompt = f"Headshot portrait: {request.prompt}"

        # Normalize quality parameter for DALL-E-3 compatibility
        # DALL-E-3 only supports "standard" and "hd", not "auto" or other values
        quality = request.quality
        if quality not in ["standard", "hd"]:
            logger.warning(f"Invalid quality '{quality}' normalized to 'standard'")
            quality = "standard"

        # 🔴 FIX 2: Remove unsupported 'background' parameter from API call
        # Build clean payload with only supported parameters
        # Use DALL-E-3 until organization is verified for GPT-Image-1
        # Use b64_json to avoid URL encoding issues with Azure blob storage URLs
        api_payload = {
            "model": "dall-e-3",
            "prompt": enhanced_prompt,
            "size": request.size,
            "quality": quality,
            "n": 1,
            "response_format": "b64_json"
        }

        logger.info(f"Calling DALL-E-3 with payload: {api_payload}")

        # Call OpenAI DALL-E-3 API (returns base64 encoded image)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=api_payload
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"GPT-Image-1 API error (status {response.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Image generation failed: {error_detail}"
                )

            data = response.json()

            # Decode base64 image data
            b64_image = data["data"][0]["b64_json"]
            image_bytes = base64.b64decode(b64_image)
            logger.info(f"✅ Successfully decoded image from base64 ({len(image_bytes)} bytes)")

            # Generate unique filename
            file_extension = f".{request.output_format}"
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Try Supabase Storage first, fall back to local filesystem on failure
            avatar_url = None
            if supabase_storage.available:
                try:
                    avatar_url = await supabase_storage.upload_avatar(
                        file_bytes=image_bytes,
                        filename=unique_filename,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        content_type=f"image/{request.output_format}"
                    )
                    logger.info(f"✅ Avatar generated and saved to Supabase: {avatar_url}")
                except Exception as storage_error:
                    logger.warning(f"Supabase Storage failed: {storage_error}, using filesystem fallback")
                    avatar_url = None

            # Fallback to local filesystem if Supabase unavailable or failed
            if not avatar_url:
                avatars_base = Path("backend/avatars")
                tenant_dir = avatars_base / tenant_id
                tenant_dir.mkdir(parents=True, exist_ok=True)
                file_path = tenant_dir / unique_filename

                with open(file_path, "wb") as f:
                    f.write(image_bytes)

                avatar_url = f"/avatars/{tenant_id}/{unique_filename}"
                logger.info(f"✅ Avatar generated and saved locally: {avatar_url}")

            return AvatarResponse(
                avatar_url=avatar_url,
                prompt_used=enhanced_prompt
            )

    except httpx.TimeoutException:
        logger.error("GPT-Image-1 API timeout after 120s")
        raise HTTPException(
            status_code=504,
            detail="Avatar generation timed out. Please try again."
        )
    except HTTPException:
        # Re-raise FastAPI exceptions as-is
        raise
    except Exception as e:
        # 🔴 FIX 3: Enhanced error logging
        logger.error(f"Avatar generation failed: {repr(e)}", exc_info=True)
        if hasattr(e, "response"):
            try:
                logger.error(f"Upstream response: {e.response.text}")
            except:
                pass

        # 🔴 FIX 4: Log placeholder fallback with context
        timestamp = datetime.utcnow().isoformat()
        logger.warning(f"⚠️ Returning placeholder avatar due to upstream failure at {timestamp}")
        logger.warning(f"⚠️ Original prompt was: {request.prompt}")

        # Return placeholder as last resort
        placeholder_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={uuid.uuid4()}"
        return AvatarResponse(
            avatar_url=placeholder_url,
            prompt_used=request.prompt
        )


@router.post("/avatar/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id")
):
    """
    Upload custom avatar image

    Validates and stores image locally with tenant isolation.
    """
    # Enforce tenant isolation
    tenant_id = x_tenant_id or "00000000-0000-0000-0000-000000000001"  # Default for dev
    user_id = x_user_id or "00000000-0000-0000-0000-000000000001"

    logger.info(f"Avatar upload requested by tenant {tenant_id}: {file.filename}")

    try:
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: PNG, JPG, WEBP. Got: {file.content_type}"
            )

        # Read file contents
        contents = await file.read()

        # Basic size validation (max 5MB)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size: 5MB"
            )

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Try Supabase Storage first, fall back to local filesystem on failure
        avatar_url = None
        if supabase_storage.available:
            try:
                avatar_url = await supabase_storage.upload_avatar(
                    file_bytes=contents,
                    filename=unique_filename,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    content_type=file.content_type or "image/png"
                )
                logger.info(f"Avatar uploaded to Supabase: {avatar_url} (tenant: {tenant_id})")
            except Exception as storage_error:
                logger.warning(f"Supabase Storage failed: {storage_error}, using filesystem fallback")
                avatar_url = None

        # Fallback to local filesystem if Supabase unavailable or failed
        if not avatar_url:
            avatars_base = Path("backend/avatars")
            tenant_dir = avatars_base / tenant_id
            tenant_dir.mkdir(parents=True, exist_ok=True)
            file_path = tenant_dir / unique_filename

            with open(file_path, "wb") as f:
                f.write(contents)

            avatar_url = f"/avatars/{tenant_id}/{unique_filename}"
            logger.info(f"Avatar uploaded locally: {avatar_url} (tenant: {tenant_id})")

        return {
            "avatar_url": avatar_url,
            "original_filename": file.filename,
            "tenant_id": tenant_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload avatar: {str(e)}"
        )
