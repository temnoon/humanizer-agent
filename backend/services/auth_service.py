"""Authentication and authorization service."""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User, SubscriptionTier
from database.connection import get_db


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """Handle authentication and authorization."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User's unique identifier
            email: User's email address
            jwt_secret_key: Secret key for JWT signing
            jwt_algorithm: Algorithm to use for JWT signing
            expires_delta: Token expiration time (default: 30 days)

        Returns:
            Encoded JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)

        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }

        encoded_jwt = jwt.encode(
            to_encode,
            jwt_secret_key,
            algorithm=jwt_algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, jwt_secret_key: str, jwt_algorithm: str = "HS256") -> dict:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string
            jwt_secret_key: Secret key for JWT verification
            jwt_algorithm: Algorithm used for JWT signing

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                jwt_secret_key,
                algorithms=[jwt_algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def generate_verification_token() -> str:
        """Generate secure random token for email verification."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_api_key() -> str:
        """Generate API key for enterprise users."""
        return f"ha_{secrets.token_urlsafe(32)}"

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Create new user account.

        Args:
            db: Database session
            email: User's email address
            password: Plain text password (will be hashed)
            full_name: Optional user's full name

        Returns:
            Created User object

        Raises:
            HTTPException: If email already exists
        """
        # Check if user exists
        existing_user = await db.execute(
            select(User).where(User.email == email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=AuthService.hash_password(password),  # Use password_hash to match schema
            full_name=full_name,
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow()
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user by email and password.

        Args:
            db: Database session
            email: User's email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not AuthService.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()

        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Current User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    # Import settings here to avoid circular imports
    from config import settings

    payload = AuthService.verify_token(token, settings.jwt_secret_key, settings.jwt_algorithm)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
