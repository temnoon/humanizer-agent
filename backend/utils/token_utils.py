"""Token counting and text chunking utilities for Anthropic Claude API."""

import tiktoken
from typing import List, Tuple
from config import settings


class TokenCounter:
    """Utility class for counting tokens in text."""
    
    def __init__(self, model: str = None):
        """Initialize token counter with specified model encoding."""
        self.model = model or settings.default_model
        # Use cl100k_base encoding for Claude models (similar to GPT-4)
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages: List[dict]) -> int:
        """Count tokens in a list of messages."""
        total_tokens = 0
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                total_tokens += self.count_tokens(str(message['content']))
            elif isinstance(message, str):
                total_tokens += self.count_tokens(message)
        return total_tokens
    
    def estimate_words(self, token_count: int) -> int:
        """Estimate word count from token count (rough approximation)."""
        # Rough approximation: 1 token ≈ 0.75 words for English text
        return int(token_count * 0.75)


class TextChunker:
    """Utility class for chunking text based on token limits."""
    
    def __init__(self, max_tokens: int = None, overlap_tokens: int = 100):
        """Initialize text chunker with token limits."""
        self.max_tokens = max_tokens or settings.max_tokens
        self.overlap_tokens = overlap_tokens
        self.token_counter = TokenCounter()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks that fit within token limits."""
        if not text:
            return []
        
        total_tokens = self.token_counter.count_tokens(text)
        
        # If text fits in one chunk, return it as is
        if total_tokens <= self.max_tokens:
            return [text]
        
        # Split text into paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.token_counter.count_tokens(paragraph)
            
            # If adding this paragraph would exceed limit, save current chunk
            if current_tokens + paragraph_tokens > self.max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from previous chunk
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                current_tokens = self.token_counter.count_tokens(current_chunk)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens = self.token_counter.count_tokens(current_chunk)
            
            # If single paragraph is too long, split it further
            if paragraph_tokens > self.max_tokens:
                sub_chunks = self._split_long_paragraph(paragraph)
                chunks.extend(sub_chunks[:-1])  # Add all but last chunk
                current_chunk = sub_chunks[-1]  # Continue with last chunk
                current_tokens = self.token_counter.count_tokens(current_chunk)
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if not text or self.overlap_tokens <= 0:
            return ""
        
        # Split into sentences and take last few that fit in overlap
        sentences = text.split('. ')
        overlap_text = ""
        overlap_tokens = 0
        
        for sentence in reversed(sentences):
            sentence_tokens = self.token_counter.count_tokens(sentence + ". ")
            if overlap_tokens + sentence_tokens <= self.overlap_tokens:
                if overlap_text:
                    overlap_text = sentence + ". " + overlap_text
                else:
                    overlap_text = sentence + ". "
                overlap_tokens += sentence_tokens
            else:
                break
        
        return overlap_text
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split a very long paragraph into smaller chunks."""
        sentences = paragraph.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence_with_period = sentence + ". "
            test_chunk = current_chunk + sentence_with_period
            
            if self.token_counter.count_tokens(test_chunk) <= self.max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence_with_period
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


def check_token_limit(text: str, tier: str = "free", check_type: str = "input") -> Tuple[bool, int, int, str]:
    """Check if text exceeds token limit for the given tier and return status, count, limit, and message."""
    counter = TokenCounter()
    token_count = counter.count_tokens(text)
    
    # Define token limits by tier and type
    limits = {
        "free": {
            "input": 4000,
            "output": 4000
        },
        "premium": {
            "input": 32000,
            "output": 32000
        },
        "enterprise": {
            "input": 100000,
            "output": 100000
        }
    }
    
    # Get limit for this tier and check type
    limit = limits.get(tier, limits["free"]).get(check_type, limits["free"]["input"])
    
    is_within = token_count <= limit
    
    if is_within:
        message = f"Document is within {tier} tier limit ({token_count:,}/{limit:,} tokens)"
    else:
        message = f"Document exceeds {tier} tier limit ({token_count:,}/{limit:,} tokens)"
    
    return is_within, token_count, limit, message


def should_chunk(text: str, tier: str = "free") -> Tuple[bool, int, int]:
    """Determine if text should be chunked based on token count and return chunking info."""
    within_limit, token_count, limit, _ = check_token_limit(text, tier, "input")
    
    if within_limit:
        return False, token_count, 1
    
    # Calculate number of chunks needed
    chunker = TextChunker(max_tokens=limit)
    chunks = chunker.chunk_text(text)
    num_chunks = len(chunks)
    
    return True, token_count, num_chunks