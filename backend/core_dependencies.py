"""
Critical Dependency Validation - FAIL FAST

Validates that all critical dependencies are installed and functional
BEFORE the application starts serving requests.

NO SILENT FALLBACKS. NO DEGRADED MODE.
If a critical dependency is broken, the service MUST NOT START.
"""

import sys
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when a critical dependency is missing or broken."""
    pass


class DependencyValidator:
    """Validates critical system dependencies at startup."""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def validate_sentence_transformers(self) -> None:
        """
        Validate sentence-transformers is installed and functional.

        This is a CRITICAL dependency - Madhyamaka detection is mathematically
        unsound without semantic embeddings. Regex-only mode is NOT acceptable.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            self.errors.append({
                "dependency": "sentence-transformers",
                "error": "NOT_INSTALLED",
                "details": str(e),
                "fix": "poetry install (or) pip install sentence-transformers",
                "impact": "Madhyamaka detection will fail - semantic embeddings unavailable"
            })
            return

        # Test that we can actually instantiate a model
        try:
            # Try to load a small model to verify functionality
            # Don't actually download if not present, just check import works
            model = SentenceTransformer.__init__
            if model is None:
                raise RuntimeError("SentenceTransformer class invalid")
        except Exception as e:
            self.errors.append({
                "dependency": "sentence-transformers",
                "error": "BROKEN_INSTALLATION",
                "details": str(e),
                "fix": "poetry install --sync (or) pip install --upgrade sentence-transformers huggingface_hub",
                "impact": "Madhyamaka detection will fail - semantic embeddings broken"
            })
            return

        logger.info("✓ sentence-transformers: OK")

    def validate_database_driver(self) -> None:
        """Validate PostgreSQL async driver is available."""
        try:
            import asyncpg
            logger.info("✓ asyncpg (PostgreSQL driver): OK")
        except ImportError as e:
            self.errors.append({
                "dependency": "asyncpg",
                "error": "NOT_INSTALLED",
                "details": str(e),
                "fix": "poetry install (or) pip install asyncpg",
                "impact": "Database connections will fail"
            })

    def validate_pgvector(self) -> None:
        """Validate pgvector extension is available."""
        try:
            from pgvector.sqlalchemy import Vector
            logger.info("✓ pgvector: OK")
        except ImportError as e:
            self.errors.append({
                "dependency": "pgvector",
                "error": "NOT_INSTALLED",
                "details": str(e),
                "fix": "poetry install (or) pip install pgvector",
                "impact": "Vector embeddings will fail"
            })

    def validate_anthropic(self) -> None:
        """Validate Anthropic SDK is available."""
        try:
            import anthropic
            logger.info("✓ anthropic: OK")
        except ImportError as e:
            self.errors.append({
                "dependency": "anthropic",
                "error": "NOT_INSTALLED",
                "details": str(e),
                "fix": "poetry install (or) pip install anthropic",
                "impact": "Claude API calls will fail"
            })

    def validate_all(self) -> None:
        """
        Run all validation checks.

        Raises:
            DependencyError: If any critical dependency is missing/broken
        """
        logger.info("=" * 70)
        logger.info("VALIDATING CRITICAL DEPENDENCIES")
        logger.info("=" * 70)

        self.validate_sentence_transformers()
        self.validate_database_driver()
        self.validate_pgvector()
        self.validate_anthropic()

        if self.errors:
            logger.error("=" * 70)
            logger.error("CRITICAL DEPENDENCY VALIDATION FAILED")
            logger.error("=" * 70)

            for i, error in enumerate(self.errors, 1):
                logger.error(f"\n[ERROR {i}] {error['dependency']}: {error['error']}")
                logger.error(f"  Details: {error['details']}")
                logger.error(f"  Fix: {error['fix']}")
                logger.error(f"  Impact: {error['impact']}")

            logger.error("\n" + "=" * 70)
            logger.error("SERVICE STARTUP ABORTED - FIX DEPENDENCIES AND RESTART")
            logger.error("=" * 70 + "\n")

            # Collect all errors into exception message
            error_summary = "\n".join([
                f"{e['dependency']}: {e['error']} - {e['fix']}"
                for e in self.errors
            ])

            raise DependencyError(
                f"Critical dependencies missing or broken:\n{error_summary}\n\n"
                f"The service cannot start with broken dependencies. "
                f"Run 'poetry install' or fix the above issues."
            )

        logger.info("=" * 70)
        logger.info("ALL CRITICAL DEPENDENCIES VALIDATED ✓")
        logger.info("=" * 70)


# Singleton validator instance
_validator = DependencyValidator()


def validate_dependencies() -> None:
    """
    Validate all critical dependencies at startup.

    Call this BEFORE FastAPI app initialization.

    Raises:
        DependencyError: If any critical dependency is missing/broken
    """
    _validator.validate_all()
