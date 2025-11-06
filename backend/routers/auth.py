"""
Authentication Router

Provides login, registration, and token refresh endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.auth import auth_service, create_token_pair, get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr
    password: str
    name: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT tokens

    Args:
        request: Login credentials

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await auth_service.authenticate_user(
        email=request.email,
        password=request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    tokens = create_token_pair(user)
    return TokenResponse(**tokens)


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register new user and return JWT tokens

    Args:
        request: Registration data

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If email already exists
    """
    user = await auth_service.register_user(
        email=request.email,
        password=request.password,
        name=request.name,
        tenant_id=request.tenant_id
    )

    tokens = create_token_pair(user)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Decode refresh token
        payload = auth_service.decode_token(request.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Create new token pair
        user = {
            "id": payload["sub"],
            "tenant_id": payload["tenant_id"],
            "email": payload.get("email", "")
        }

        tokens = create_token_pair(user)
        return TokenResponse(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info

    Args:
        current_user: Current user from JWT

    Returns:
        User information
    """
    return {
        "user_id": current_user["user_id"],
        "tenant_id": current_user["tenant_id"],
        "email": current_user["email"]
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client should remove tokens)

    Args:
        current_user: Current user from JWT

    Returns:
        Success message
    """
    # In a production system, you might want to:
    # 1. Add the token to a blacklist
    # 2. Update last_logout timestamp in database
    # 3. Clear any server-side sessions

    return {"message": "Successfully logged out"}