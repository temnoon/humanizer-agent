"""Configuration management for Humanizer Agent."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Configuration
    anthropic_api_key: str
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    
    # Database - PostgreSQL with pgvector
    database_url: str = "postgresql+asyncpg://humanizer:humanizer@localhost:5432/humanizer"

    # Embedding Configuration
    embedding_model: str = "voyage-3"  # or "text-embedding-3-small" for OpenAI
    embedding_dimension: int = 1536
    enable_vector_search: bool = True
    
    # Agent Configuration
    default_model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.7  # Must be < 1.0 unless thinking is enabled
    
    # Token Limits by Tier
    free_tier_input_limit: int = 2000  # tokens
    premium_tier_input_limit: int = 50000  # tokens (~37,500 words)
    free_tier_output_limit: int = 2000  # tokens
    premium_tier_output_limit: int = 8192  # tokens
    
    # Chunking Configuration (for premium tier)
    enable_chunking: bool = True
    chunk_size: int = 3000  # tokens per chunk
    chunk_overlap: int = 200  # token overlap between chunks
    
    # File Upload
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = [".txt", ".md", ".doc", ".docx", ".pdf"]
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated string or list for allowed extensions."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [ext.strip() for ext in v.split(',') if ext.strip()]
        return v
    
    # Session Configuration
    session_timeout_hours: int = 24
    max_checkpoints: int = 10
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
