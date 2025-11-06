"""
Shared FastAPI Dependencies

Centralized dependency injection functions for:
- Tenant isolation
- User authentication
- Header extraction

Eliminates code duplication across routers.
"""

from fastapi import Header
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Default tenant/user for development
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_tenant_id(x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id")) -> str:
    """
    Extract tenant ID from request header or use default.

    Use this as a FastAPI dependency:
    ```python
    @router.get("/endpoint")
    async def endpoint(tenant_id: str = Depends(get_tenant_id)):
        ...
    ```

    Args:
        x_tenant_id: Optional tenant ID from X-Tenant-ID header

    Returns:
        str: Tenant ID (from header or default for development)
    """
    if x_tenant_id:
        return x_tenant_id
    return DEFAULT_TENANT_ID


def get_user_id(x_user_id: Optional[str] = Header(None, alias="x-user-id")) -> str:
    """
    Extract user ID from request header or use default.

    Use this as a FastAPI dependency:
    ```python
    @router.post("/endpoint")
    async def endpoint(user_id: str = Depends(get_user_id)):
        ...
    ```

    Args:
        x_user_id: Optional user ID from X-User-ID header

    Returns:
        str: User ID (from header or default for development)
    """
    if x_user_id:
        return x_user_id
    return DEFAULT_USER_ID


def get_tenant_and_user(
    x_tenant_id: Optional[str] = Header(None, alias="x-tenant-id"),
    x_user_id: Optional[str] = Header(None, alias="x-user-id")
) -> tuple[str, str]:
    """
    Extract both tenant ID and user ID in one dependency.

    Use this as a FastAPI dependency when you need both:
    ```python
    @router.post("/endpoint")
    async def endpoint(tenant_user: tuple[str, str] = Depends(get_tenant_and_user)):
        tenant_id, user_id = tenant_user
        ...
    ```

    Args:
        x_tenant_id: Optional tenant ID from X-Tenant-ID header
        x_user_id: Optional user ID from X-User-ID header

    Returns:
        tuple[str, str]: (tenant_id, user_id)
    """
    tenant_id = x_tenant_id if x_tenant_id else DEFAULT_TENANT_ID
    user_id = x_user_id if x_user_id else DEFAULT_USER_ID
    return tenant_id, user_id
