# Humanizer Tiered Subscription System - Implementation Plan

**Status**: Ready for Implementation
**Priority**: HIGH - Required for production launch
**Estimated Time**: 4-5 hours
**Created**: October 10, 2025

---

## Executive Summary

This document outlines the complete architecture for a tiered subscription system with content length limits, smart chunking for premium users, and enforcement middleware. The system enables monetization while providing a smooth upgrade path from free to premium tiers.

---

## 1. Subscription Tiers

### Tier Structure

| Tier | Monthly Cost | Max Tokens/Transform | Monthly Transforms | API Access | Smart Chunking |
|------|-------------|---------------------|-------------------|------------|----------------|
| **FREE** | $0 | 500 | 10 | ❌ | ❌ |
| **MEMBER** | $9 | 2,000 | 50 | ❌ | ❌ |
| **PRO** | $29 | 8,000 | 200 | ❌ | ❌ |
| **PREMIUM** | $99 | UNLIMITED | UNLIMITED | ❌ | ✅ |
| **ENTERPRISE** | Custom | UNLIMITED | UNLIMITED | ✅ | ✅ |

### Tier Features Breakdown

**FREE**
- Perfect for trying the service
- 500 tokens ≈ 1-2 paragraphs
- 10 transforms/month = casual use
- Reset on 1st of month

**MEMBER**
- For regular users
- 2,000 tokens ≈ 1 page of text
- 50 transforms/month = multiple uses per week
- Email support

**PRO**
- For professionals
- 8,000 tokens ≈ 3-4 pages
- 200 transforms/month = daily use
- Priority processing
- Priority support

**PREMIUM**
- For power users & content creators
- UNLIMITED token length (with smart chunking)
- UNLIMITED transforms
- Smart semantic chunking for long documents
- Artifact lineage for each chunk
- Premium support

**ENTERPRISE**
- For businesses & integrations
- All PREMIUM features
- API access with key
- Custom integration support
- SLA guarantees
- Dedicated account manager

---

## 2. Implementation Architecture

### 2.1 Database Schema Updates

#### User Model Enhancement (`backend/models/user.py`)

```python
from sqlalchemy import Column, String, Integer, JSON
from datetime import datetime
import enum

class SubscriptionTier(str, enum.Enum):
    """Available subscription tiers."""
    FREE = "free"
    MEMBER = "member"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# Add to User model:
class User(Base):
    # ... existing fields ...

    # Subscription
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)

    # Usage tracking (reset monthly)
    monthly_transformations = Column(Integer, default=0)
    monthly_tokens_used = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

    # Tier limits cache (denormalized for performance)
    tier_limits = Column(JSON, default={})
```

#### Alembic Migration

```python
# backend/alembic/versions/006_add_subscription_tiers.py

"""Add member and pro tiers

Revision ID: 006_add_tiers
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new enum values to subscription_tier
    op.execute("ALTER TYPE subscriptiontier ADD VALUE IF NOT EXISTS 'member'")
    op.execute("ALTER TYPE subscriptiontier ADD VALUE IF NOT EXISTS 'pro'")

def downgrade():
    # Note: PostgreSQL doesn't support removing enum values
    pass
```

---

### 2.2 Tier Service (`backend/services/tier_service.py`)

**NEW FILE** - Core tier logic and validation

```python
"""
Tier Management Service

Handles:
- Tier limit validation
- Usage tracking
- Monthly resets
- Upgrade recommendations
"""

from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, SubscriptionTier


class TierLimits:
    """Tier limit constants."""

    LIMITS = {
        SubscriptionTier.FREE: {
            "max_tokens_per_transform": 500,
            "monthly_transforms": 10,
            "features": ["basic_transform"]
        },
        SubscriptionTier.MEMBER: {
            "max_tokens_per_transform": 2000,
            "monthly_transforms": 50,
            "features": ["basic_transform", "email_support"]
        },
        SubscriptionTier.PRO: {
            "max_tokens_per_transform": 8000,
            "monthly_transforms": 200,
            "features": ["basic_transform", "priority_processing", "priority_support"]
        },
        SubscriptionTier.PREMIUM: {
            "max_tokens_per_transform": None,  # Unlimited
            "monthly_transforms": None,  # Unlimited
            "features": ["basic_transform", "smart_chunking", "unlimited_length", "premium_support"]
        },
        SubscriptionTier.ENTERPRISE: {
            "max_tokens_per_transform": None,  # Unlimited
            "monthly_transforms": None,  # Unlimited
            "features": ["basic_transform", "smart_chunking", "unlimited_length", "api_access", "enterprise_support"]
        }
    }


class TierService:
    """Manage subscription tiers and usage limits."""

    @staticmethod
    async def check_transform_allowed(
        user: User,
        token_count: int,
        db: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if transformation is allowed for user's tier.

        Returns:
            (allowed: bool, error_message: Optional[str])
        """
        # Reset monthly counters if needed
        await TierService.reset_monthly_usage_if_needed(user, db)

        limits = TierLimits.LIMITS[user.subscription_tier]

        # Check token limit
        max_tokens = limits["max_tokens_per_transform"]
        if max_tokens is not None and token_count > max_tokens:
            upgrade_tier = TierService.recommend_tier_for_tokens(token_count)
            return False, (
                f"Content too long ({token_count} tokens). "
                f"Your {user.subscription_tier} tier allows max {max_tokens} tokens. "
                f"Upgrade to {upgrade_tier} tier for longer content."
            )

        # Check monthly transform limit
        monthly_limit = limits["monthly_transforms"]
        if monthly_limit is not None and user.monthly_transformations >= monthly_limit:
            return False, (
                f"Monthly transformation limit reached ({monthly_limit}). "
                f"Upgrade to a higher tier or wait until next month."
            )

        return True, None

    @staticmethod
    async def reset_monthly_usage_if_needed(user: User, db: AsyncSession):
        """Reset monthly counters if it's a new month."""
        now = datetime.utcnow()
        if user.last_reset_date.month != now.month or user.last_reset_date.year != now.year:
            user.monthly_transformations = 0
            user.monthly_tokens_used = 0
            user.last_reset_date = now
            await db.commit()

    @staticmethod
    async def increment_usage(user: User, token_count: int, db: AsyncSession):
        """Increment usage counters after successful transformation."""
        user.monthly_transformations += 1
        user.monthly_tokens_used += token_count
        await db.commit()

    @staticmethod
    def recommend_tier_for_tokens(token_count: int) -> SubscriptionTier:
        """Recommend appropriate tier based on token count."""
        if token_count <= 500:
            return SubscriptionTier.FREE
        elif token_count <= 2000:
            return SubscriptionTier.MEMBER
        elif token_count <= 8000:
            return SubscriptionTier.PRO
        else:
            return SubscriptionTier.PREMIUM

    @staticmethod
    def has_feature(user: User, feature: str) -> bool:
        """Check if user's tier includes a specific feature."""
        limits = TierLimits.LIMITS[user.subscription_tier]
        return feature in limits["features"]
```

---

### 2.3 Smart Chunking Service (`backend/services/chunking_service.py`)

**NEW FILE** - Intelligent content splitting for PREMIUM+ users

```python
"""
Smart Semantic Chunking Service

For PREMIUM/ENTERPRISE tiers: Split long content into semantically coherent chunks
while preserving context and enabling reassembly.
"""

from typing import List, Dict, Optional
import re
import tiktoken
from dataclasses import dataclass


@dataclass
class ContentChunk:
    """A semantically coherent chunk of content."""
    index: int
    content: str
    token_count: int
    starts_paragraph: bool
    ends_paragraph: bool
    context_from_previous: Optional[str] = None


class ChunkingService:
    """Smart chunking for long-form content processing."""

    def __init__(self, model: str = "cl100k_base", max_chunk_tokens: int = 6000):
        """
        Initialize chunking service.

        Args:
            model: Tokenizer model (default: OpenAI cl100k_base)
            max_chunk_tokens: Target tokens per chunk (leave room for context)
        """
        self.encoding = tiktoken.get_encoding(model)
        self.max_chunk_tokens = max_chunk_tokens

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def split_into_chunks(self, text: str, overlap_sentences: int = 2) -> List[ContentChunk]:
        """
        Split text into semantically coherent chunks.

        Strategy:
        1. Split at paragraph boundaries (double newline)
        2. If paragraph too long, split at sentence boundaries
        3. Include context from previous chunk (last N sentences)
        4. Maintain metadata for reassembly

        Args:
            text: Full content to split
            overlap_sentences: Number of sentences to include as context

        Returns:
            List of ContentChunk objects
        """
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk_text = []
        current_token_count = 0
        chunk_index = 0
        previous_sentences = []

        for para_idx, paragraph in enumerate(paragraphs):
            para_tokens = self.count_tokens(paragraph)

            # If single paragraph exceeds limit, split at sentences
            if para_tokens > self.max_chunk_tokens:
                sentences = self._split_into_sentences(paragraph)

                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)

                    if current_token_count + sent_tokens > self.max_chunk_tokens:
                        # Save current chunk
                        chunks.append(self._create_chunk(
                            index=chunk_index,
                            content='\n\n'.join(current_chunk_text),
                            context=self._build_context(previous_sentences, overlap_sentences),
                            starts_paragraph=True,
                            ends_paragraph=False
                        ))

                        # Start new chunk
                        chunk_index += 1
                        previous_sentences = self._extract_sentences('\n\n'.join(current_chunk_text))
                        current_chunk_text = [sentence]
                        current_token_count = sent_tokens
                    else:
                        current_chunk_text.append(sentence)
                        current_token_count += sent_tokens
            else:
                # Paragraph fits, check if adding it exceeds limit
                if current_token_count + para_tokens > self.max_chunk_tokens:
                    # Save current chunk
                    chunks.append(self._create_chunk(
                        index=chunk_index,
                        content='\n\n'.join(current_chunk_text),
                        context=self._build_context(previous_sentences, overlap_sentences),
                        starts_paragraph=True,
                        ends_paragraph=True
                    ))

                    # Start new chunk
                    chunk_index += 1
                    previous_sentences = self._extract_sentences('\n\n'.join(current_chunk_text))
                    current_chunk_text = [paragraph]
                    current_token_count = para_tokens
                else:
                    current_chunk_text.append(paragraph)
                    current_token_count += para_tokens

        # Add final chunk
        if current_chunk_text:
            chunks.append(self._create_chunk(
                index=chunk_index,
                content='\n\n'.join(current_chunk_text),
                context=self._build_context(previous_sentences, overlap_sentences),
                starts_paragraph=True,
                ends_paragraph=True
            ))

        return chunks

    def _create_chunk(self, index: int, content: str, context: Optional[str],
                     starts_paragraph: bool, ends_paragraph: bool) -> ContentChunk:
        """Create ContentChunk object with metadata."""
        return ContentChunk(
            index=index,
            content=content,
            token_count=self.count_tokens(content),
            starts_paragraph=starts_paragraph,
            ends_paragraph=ends_paragraph,
            context_from_previous=context
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (basic regex)."""
        # Simple sentence splitting - can be enhanced
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text for context building."""
        return self._split_into_sentences(text)

    def _build_context(self, previous_sentences: List[str], count: int) -> Optional[str]:
        """Build context string from previous sentences."""
        if not previous_sentences or count == 0:
            return None
        return ' '.join(previous_sentences[-count:])

    def reassemble_chunks(self, transformed_chunks: List[str],
                         original_chunks: List[ContentChunk]) -> str:
        """
        Reassemble transformed chunks into final document.

        Removes duplicate context and smooths transitions.
        """
        if len(transformed_chunks) != len(original_chunks):
            raise ValueError("Chunk count mismatch")

        # For now, simple concatenation
        # TODO: Implement smart deduplication of overlapping context
        return '\n\n'.join(transformed_chunks)
```

---

### 2.4 API Middleware (`backend/api/personifier_routes.py`)

**UPDATE EXISTING FILE** - Add tier checking

```python
from fastapi import Depends, HTTPException, status
from services.auth_service import get_current_user
from services.tier_service import TierService
from services.chunking_service import ChunkingService
from models.user import User

# Add to PersonifyRewriteRequest
class PersonifyRewriteRequest(BaseModel):
    text: str
    strength: float = 1.0
    use_examples: bool = True
    n_examples: int = 3
    save_as_artifact: bool = False
    artifact_topics: Optional[List[str]] = None
    # NEW:
    process_as_chunks: bool = False  # For long content, PREMIUM+ only


@router.post("/api/personify/rewrite")
async def personify_rewrite(
    request: PersonifyRewriteRequest,
    current_user: User = Depends(get_current_user),  # NEW: Require auth
    db: AsyncSession = Depends(get_db)
):
    """
    Transform AI text to conversational style.

    Tier Limits:
    - FREE: 500 tokens, 10/month
    - MEMBER: 2000 tokens, 50/month
    - PRO: 8000 tokens, 200/month
    - PREMIUM: Unlimited (with chunking)
    - ENTERPRISE: Unlimited + API access
    """
    # Count tokens in input
    chunker = ChunkingService()
    token_count = chunker.count_tokens(request.text)

    # Check tier limits
    allowed, error_msg = await TierService.check_transform_allowed(
        current_user, token_count, db
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=error_msg
        )

    # For PREMIUM+ with long content, use chunking
    if token_count > 8000 and TierService.has_feature(current_user, "smart_chunking"):
        return await process_long_content(request, current_user, chunker, db)

    # Regular processing for shorter content
    result = await process_single_transform(request, current_user, db)

    # Increment usage
    await TierService.increment_usage(current_user, token_count, db)

    return result


async def process_long_content(
    request: PersonifyRewriteRequest,
    user: User,
    chunker: ChunkingService,
    db: AsyncSession
):
    """Process long content by chunking (PREMIUM+ only)."""
    # Split into chunks
    chunks = chunker.split_into_chunks(request.text)

    transformed_chunks = []
    chunk_artifacts = []

    for chunk in chunks:
        # Process each chunk
        chunk_request = PersonifyRewriteRequest(
            text=chunk.content,
            strength=request.strength,
            use_examples=request.use_examples,
            n_examples=request.n_examples,
            save_as_artifact=True,  # Save each chunk as artifact
            artifact_topics=(request.artifact_topics or []) + [f"chunk_{chunk.index}"]
        )

        result = await process_single_transform(chunk_request, user, db)
        transformed_chunks.append(result["rewritten_text"])

        if "artifact_id" in result:
            chunk_artifacts.append(result["artifact_id"])

    # Reassemble
    final_text = chunker.reassemble_chunks(transformed_chunks, chunks)

    # Save final artifact with lineage
    if request.save_as_artifact:
        final_artifact_id = await save_final_artifact(
            final_text,
            chunk_artifacts,
            request.artifact_topics,
            db
        )

        return {
            "original_text": request.text,
            "rewritten_text": final_text,
            "chunks_processed": len(chunks),
            "chunk_artifacts": chunk_artifacts,
            "artifact_id": final_artifact_id,
            "processing_mode": "chunked"
        }

    return {
        "original_text": request.text,
        "rewritten_text": final_text,
        "chunks_processed": len(chunks),
        "processing_mode": "chunked"
    }
```

---

## 3. Testing Strategy

### 3.1 Unit Tests

**Test File**: `backend/tests/test_tier_service.py`

```python
import pytest
from services.tier_service import TierService, TierLimits
from models.user import User, SubscriptionTier

@pytest.mark.asyncio
async def test_free_tier_token_limit():
    """Test FREE tier rejects content over 500 tokens."""
    user = User(subscription_tier=SubscriptionTier.FREE)
    allowed, error = await TierService.check_transform_allowed(user, 600, db)
    assert not allowed
    assert "500 tokens" in error

@pytest.mark.asyncio
async def test_premium_tier_unlimited():
    """Test PREMIUM tier accepts unlimited tokens."""
    user = User(subscription_tier=SubscriptionTier.PREMIUM)
    allowed, error = await TierService.check_transform_allowed(user, 50000, db)
    assert allowed
    assert error is None

# More tests...
```

### 3.2 Integration Tests

**Test File**: `backend/tests/test_chunking_integration.py`

```python
@pytest.mark.asyncio
async def test_long_content_chunking():
    """Test that long content is properly chunked and reassembled."""
    long_text = "..." * 10000  # 10k+ tokens
    chunker = ChunkingService()
    chunks = chunker.split_into_chunks(long_text)

    assert len(chunks) > 1
    assert all(c.token_count <= chunker.max_chunk_tokens for c in chunks)
```

### 3.3 Manual Testing Checklist

- [ ] FREE tier: Submit 400 tokens (should work)
- [ ] FREE tier: Submit 600 tokens (should fail with upgrade message)
- [ ] FREE tier: Exhaust 10 transforms (11th should fail)
- [ ] MEMBER tier: Submit 1800 tokens (should work)
- [ ] MEMBER tier: Submit 2500 tokens (should fail)
- [ ] PRO tier: Submit 7500 tokens (should work)
- [ ] PRO tier: Submit 9000 tokens (should fail)
- [ ] PREMIUM tier: Submit 20,000 tokens (should chunk and process)
- [ ] PREMIUM tier: Verify chunk artifacts created
- [ ] PREMIUM tier: Verify final reassembly coherent
- [ ] Monthly reset: Test counters reset on month change

---

## 4. Stripe Integration (Future Phase)

### Webhooks Required

```python
# backend/api/stripe_webhooks.py

@router.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Stripe webhook events:
    - checkout.session.completed → Activate subscription
    - customer.subscription.updated → Update tier
    - customer.subscription.deleted → Downgrade to FREE
    - invoice.payment_failed → Mark PAST_DUE
    """
    # Implementation in future session
    pass
```

### Pricing Page (Frontend)

```jsx
// frontend/src/components/PricingPage.jsx
// Show tier comparison table
// Link to Stripe Checkout for each tier
```

---

## 5. Migration Path

### Phase 1 (Next Session - 4-5 hours)
- ✅ Update SubscriptionTier enum
- ✅ Create TierService
- ✅ Create ChunkingService
- ✅ Add middleware to personifier
- ✅ Create database migration
- ✅ Write unit tests
- ✅ Manual testing

### Phase 2 (Future Session - 3-4 hours)
- Stripe integration
- Pricing page UI
- Subscription management UI
- Email notifications
- Webhooks for tier updates

### Phase 3 (Future Session - 2-3 hours)
- Analytics dashboard
- Usage reports for users
- Admin panel for tier management
- Refund handling

---

## 6. Success Metrics

### Technical Metrics
- ✅ All tier limits enforced
- ✅ Zero over-limit transformations
- ✅ Chunking works for 50k+ token content
- ✅ Reassembly maintains coherence
- ✅ No token counting errors

### Business Metrics
- Track conversion from FREE → MEMBER
- Track conversion from PRO → PREMIUM
- Monitor churn rate by tier
- Measure average monthly usage per tier
- Identify optimal pricing

---

## 7. Files Modified Summary

### New Files
1. `backend/services/tier_service.py` - Core tier logic
2. `backend/services/chunking_service.py` - Smart splitting
3. `backend/alembic/versions/006_add_tiers.py` - Migration
4. `backend/tests/test_tier_service.py` - Unit tests
5. `backend/tests/test_chunking_integration.py` - Integration tests

### Modified Files
1. `backend/models/user.py` - Add MEMBER, PRO tiers
2. `backend/api/personifier_routes.py` - Add auth + tier checking
3. `backend/api/auth_routes.py` - Ensure user context available

---

## 8. Edge Cases & Error Handling

### Edge Cases
1. **User on FREE tier with 9/10 transforms used, submits 499 tokens**
   - Should work (under limit)

2. **User on FREE tier with 10/10 transforms used, submits 400 tokens**
   - Should fail with "limit reached" message

3. **PREMIUM user submits 100,000 token novel**
   - Should chunk into ~15-20 chunks
   - Process each sequentially
   - Save 15-20 chunk artifacts
   - Save 1 final artifact with lineage

4. **User upgrades mid-month from FREE to PRO**
   - Reset counters immediately
   - Apply new limits

5. **Month boundary crossed during transformation**
   - Check at start, counters reset automatically

### Error Messages

**Over Token Limit**:
```json
{
  "error": "content_too_long",
  "message": "Content too long (3000 tokens). Your free tier allows max 500 tokens.",
  "current_tier": "free",
  "recommended_tier": "pro",
  "upgrade_url": "/pricing"
}
```

**Monthly Limit Reached**:
```json
{
  "error": "monthly_limit_reached",
  "message": "Monthly transformation limit reached (10/10). Upgrade or wait until November 1.",
  "resets_at": "2025-11-01T00:00:00Z",
  "current_tier": "free",
  "recommended_tier": "member"
}
```

---

## 9. Performance Considerations

### Chunking Performance
- **Target**: Process 10,000 tokens in < 5 seconds
- **Strategy**: Async processing of chunks in batches
- **Caching**: Cache tokenizer model

### Database Performance
- **Index**: `users.subscription_tier` for tier queries
- **Index**: `users.monthly_transformations` for limit checks
- **Connection pooling**: Ensure sufficient pool size

---

## 10. Next Session Checklist

When implementing, follow this order:

1. ✅ **Read this document** (5 min)
2. ✅ **Update SubscriptionTier enum** in `user.py` (2 min)
3. ✅ **Create tier_service.py** with TierLimits and TierService (1 hour)
4. ✅ **Create chunking_service.py** with ChunkingService (1.5 hours)
5. ✅ **Update personifier_routes.py** - add auth + tier checks (1 hour)
6. ✅ **Create migration** `006_add_tiers.py` (15 min)
7. ✅ **Write unit tests** for tier validation (30 min)
8. ✅ **Manual testing** all tiers (30 min)
9. ✅ **Update CLAUDE.md** with new tier system info (5 min)

**Total**: ~5 hours

---

*Plan created: October 10, 2025*
*Ready for implementation: YES*
*Dependencies: User authentication system (already exists)*
