"""
JWT Authentication Service for HypnoAgent

Provides JWT token generation, validation, and user authentication middleware
for FastAPI endpoints.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from database import get_pg_pool

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = settings.JWT_SECRET_KEY if hasattr(settings, 'JWT_SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


class AuthService:
    """Handles JWT authentication and user management"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash a password for storage"""
        return pwd_context.hash(password)

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            email: User email
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user_id,  # Subject (user ID)
            "tenant_id": tenant_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str
    ) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: User UUID
            tenant_id: Tenant UUID

        Returns:
            JWT refresh token string
        """
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User data if authenticated, None otherwise
        """
        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, tenant_id, email, password_hash, name, created_at
                    FROM users
                    WHERE email = $1 AND status = 'active'
                """, email)

                if not row:
                    return None

                if not self.verify_password(password, row["password_hash"]):
                    return None

                return {
                    "id": str(row["id"]),
                    "tenant_id": str(row["tenant_id"]),
                    "email": row["email"],
                    "name": row["name"],
                    "created_at": row["created_at"].isoformat()
                }

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    async def register_user(
        self,
        email: str,
        password: str,
        name: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register new user

        Args:
            email: User email
            password: Plain text password
            name: User name
            tenant_id: Optional tenant ID (creates new if not provided)

        Returns:
            Created user data

        Raises:
            HTTPException: If email already exists
        """
        pool = get_pg_pool()

        try:
            # Check if email exists
            async with pool.acquire() as conn:
                existing = await conn.fetchrow("""
                    SELECT id FROM users WHERE email = $1
                """, email)

                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )

                # Create new tenant if not provided
                if not tenant_id:
                    tenant_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO tenants (id, name, created_at)
                        VALUES ($1::uuid, $2, NOW())
                    """, tenant_id, f"{name}'s Organization")

                # Create user
                user_id = str(uuid.uuid4())
                password_hash = self.hash_password(password)

                await conn.execute("""
                    INSERT INTO users (
                        id, tenant_id, email, password_hash, name,
                        status, created_at, updated_at
                    )
                    VALUES ($1::uuid, $2::uuid, $3, $4, $5, 'active', NOW(), NOW())
                """, user_id, tenant_id, email, password_hash, name)

                return {
                    "id": user_id,
                    "tenant_id": tenant_id,
                    "email": email,
                    "name": name,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )


# Singleton instance
auth_service = AuthService()


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Args:
        credentials: Bearer token from request header

    Returns:
        User data from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        payload = auth_service.decode_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return {
            "user_id": payload["sub"],
            "tenant_id": payload["tenant_id"],
            "email": payload.get("email")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Optional dependency for routes that can work with or without auth
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to optionally get current user

    Args:
        credentials: Optional bearer token

    Returns:
        User data if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def create_token_pair(user: Dict[str, Any]) -> Dict[str, str]:
    """
    Create access and refresh token pair

    Args:
        user: User data dictionary with id, tenant_id, email

    Returns:
        Dictionary with access_token and refresh_token
    """
    access_token = auth_service.create_access_token(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"]
    )

    refresh_token = auth_service.create_refresh_token(
        user_id=user["id"],
        tenant_id=user["tenant_id"]
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }