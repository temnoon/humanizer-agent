"""User authentication and subscription models."""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class SubscriptionTier(str, enum.Enum):
    """Available subscription tiers."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class User(Base):
    """User account with subscription and usage tracking."""

    __tablename__ = "users"

    # Core Identity (matching existing schema)
    id = Column(String, primary_key=True)  # UUID
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # Renamed to match existing schema
    username = Column(String, nullable=True)  # Existing column
    full_name = Column(String, nullable=True)

    # Account Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)  # Use existing column
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # Existing column

    # Subscription Management
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)

    # Stripe Integration
    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    subscription_expires_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)

    # Usage Tracking (reset monthly)
    monthly_transformations = Column(Integer, default=0)
    monthly_tokens_used = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

    # API Access (Enterprise feature)
    api_key = Column(String, unique=True, nullable=True, index=True)
    api_key_created_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    # Note: transformations relationship will be added when transformation model is updated

    def __repr__(self):
        return f"<User {self.email} ({self.subscription_tier})>"
