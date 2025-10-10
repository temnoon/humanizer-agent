"""
Personifier Service

Transforms AI writing → conversational using embedding arithmetic.

Philosophy: Add "person-ness" (linguistic register) not "human-ness" (ontological claim).
This is honest transformation, not deceptive obfuscation.
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
import re
import requests

from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk_models import Chunk
from services.transformation_arithmetic import TransformationArithmeticService

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "mxbai-embed-large"


class PersonifierService:
    """
    Service for transforming AI writing to conversational register.

    Process:
    1. Detect AI patterns in input text
    2. Generate embedding for input
    3. Apply personify transformation vector
    4. Find similar conversational chunks
    5. Return transformed suggestions
    """

    def __init__(self):
        """Initialize service."""
        self.transform_service = TransformationArithmeticService()
        self._vector_loaded = False

    def _ensure_vector_loaded(self):
        """Lazy-load the personify vector."""
        if not self._vector_loaded:
            # Load curated transformation vector (396 pairs, Ollama mxbai-embed-large)
            self.transform_service.load_curated_vector(
                vector_path="data/personify_vector_curated_ollama.json",
                vector_name="personify"
            )
            self._vector_loaded = True

    def detect_ai_patterns(self, text: str) -> Dict[str, Any]:
        """
        Detect AI writing patterns in text.

        Returns:
            Dict with pattern counts and confidence score
        """
        text_lower = text.lower()

        patterns = {
            'hedging': [
                "it's worth noting", "it's important to", "you might want to",
                "it should be noted", "generally speaking", "in most cases",
                "typically", "usually", "often"
            ],
            'formal_transitions': [
                "furthermore", "moreover", "additionally", "consequently",
                "therefore", "thus", "hence", "accordingly"
            ],
            'passive_voice': [
                "can be", "should be", "may be", "could be",
                "is recommended", "are recommended", "is suggested"
            ],
            'list_markers': [
                "here are", "here's a", "following are", "these are",
                "there are several"
            ]
        }

        counts = {}
        total_score = 0.0

        for category, pattern_list in patterns.items():
            count = sum(text_lower.count(pattern) for pattern in pattern_list)
            counts[category] = count
            total_score += count

        # Check for numbered lists
        numbered_lists = len(re.findall(r'\n\s*\d+\.', text))
        counts['numbered_lists'] = numbered_lists
        total_score += numbered_lists

        # Check for bullet points
        bullet_points = text.count('- ') + text.count('* ')
        counts['bullet_points'] = bullet_points
        if bullet_points > 2:
            total_score += 1

        # Calculate confidence (0-100)
        # Normalize by text length
        words = len(text.split())
        confidence = min(100, (total_score / max(1, words / 100)) * 20)

        return {
            'patterns': counts,
            'total_score': total_score,
            'confidence': round(confidence, 1),
            'is_ai_likely': confidence > 30
        }

    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using Ollama.

        Args:
            text: Input text

        Returns:
            1024-dimensional embedding
        """
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": text
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.text}")

            embedding = response.json()['embedding']
            return np.array(embedding)

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def find_similar_conversational(
        self,
        session: AsyncSession,
        transformed_embedding: np.ndarray,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar conversational chunks from database.

        Args:
            session: Database session
            transformed_embedding: Personified embedding
            n_results: Number of results

        Returns:
            List of similar chunks with metadata

        Best Practice:
            pgvector with asyncpg requires vector type registration (done in database/connection.py).
            Once registered, use .tolist() to convert numpy arrays - pgvector handles the rest.
            The register_vector() call enables asyncpg to properly encode/decode vector types.
        """
        # Convert numpy array to pgvector string format for asyncpg
        # BEST PRACTICE: asyncpg requires vector as string "[val1,val2,val3]" with NO spaces
        # Must explicitly cast to vector type in SQL
        embedding_str = '[' + ','.join(str(float(x)) for x in transformed_embedding) + ']'

        # Query for similar chunks using cosine distance
        # Use text() with explicit cast to vector type for asyncpg compatibility
        query = select(
            Chunk,
            (1 - func.cosine_distance(Chunk.embedding, text(f"'{embedding_str}'::vector"))).label('similarity')
        ).where(
            and_(
                Chunk.embedding.is_not(None),
                Chunk.content_type == 'text',
                Chunk.token_count > 50  # Substantial chunks only
            )
        ).order_by(
            text('similarity DESC')
        ).limit(n_results)

        result = await session.execute(query)
        rows = result.all()

        similar_chunks = []
        for chunk, similarity in rows:
            similar_chunks.append({
                'chunk_id': str(chunk.id),
                'content': chunk.content,
                'token_count': chunk.token_count,
                'similarity': round(similarity, 4),
                'metadata': chunk.extra_metadata or {}  # Use extra_metadata (the JSONB column)
            })

        return similar_chunks

    async def personify(
        self,
        session: AsyncSession,
        text: str,
        strength: float = 1.0,
        return_similar: bool = True,
        n_similar: int = 5
    ) -> Dict[str, Any]:
        """
        Transform AI text to conversational register.

        Args:
            session: Database session
            text: Input text (AI-written)
            strength: Transformation strength (0.0 to 1.0+)
            return_similar: Include similar conversational examples
            n_similar: Number of similar examples to return

        Returns:
            Dict with:
            - original_text
            - ai_patterns (detected patterns)
            - transformed_embedding
            - similar_chunks (if return_similar=True)
            - suggestions (transformation guidance)
        """
        # Ensure vector is loaded
        self._ensure_vector_loaded()

        # Detect AI patterns
        logger.info(f"Analyzing text ({len(text)} chars)...")
        patterns = self.detect_ai_patterns(text)

        # Generate embedding
        logger.info("Generating embedding...")
        original_embedding = await self.generate_embedding(text)

        # Apply transformation
        logger.info(f"Applying personify transformation (strength={strength})...")
        transformed_embedding = self.transform_service.apply_transformation(
            original_embedding,
            transformation_name="personify",
            strength=strength
        )

        # Build result
        result = {
            'original_text': text,
            'ai_patterns': patterns,
            'transformation': {
                'vector': 'personify',
                'strength': strength,
                'original_magnitude': float(np.linalg.norm(original_embedding)),
                'transformed_magnitude': float(np.linalg.norm(transformed_embedding))
            }
        }

        # Find similar conversational chunks
        if return_similar:
            logger.info(f"Finding {n_similar} similar conversational examples...")
            similar = await self.find_similar_conversational(
                session,
                transformed_embedding,
                n_results=n_similar
            )
            result['similar_chunks'] = similar

        # Generate suggestions based on detected patterns
        suggestions = []

        if patterns['patterns']['hedging'] > 0:
            suggestions.append({
                'type': 'remove_hedging',
                'message': 'Remove hedging phrases like "it\'s worth noting" - be direct',
                'count': patterns['patterns']['hedging']
            })

        if patterns['patterns']['passive_voice'] > 0:
            suggestions.append({
                'type': 'active_voice',
                'message': 'Use active voice instead of "can be done" → "do it"',
                'count': patterns['patterns']['passive_voice']
            })

        if patterns['patterns']['formal_transitions'] > 0:
            suggestions.append({
                'type': 'casual_transitions',
                'message': 'Replace formal transitions (furthermore → also, plus)',
                'count': patterns['patterns']['formal_transitions']
            })

        if patterns['patterns']['numbered_lists'] > 0:
            suggestions.append({
                'type': 'vary_structure',
                'message': 'Vary structure - not every response needs a numbered list',
                'count': patterns['patterns']['numbered_lists']
            })

        result['suggestions'] = suggestions

        logger.info(
            f"Personification complete: {len(suggestions)} suggestions, "
            f"confidence={patterns['confidence']}%"
        )

        return result


# Singleton instance
_personifier_service = None


def get_personifier_service() -> PersonifierService:
    """Get or create personifier service instance."""
    global _personifier_service
    if _personifier_service is None:
        _personifier_service = PersonifierService()
    return _personifier_service
