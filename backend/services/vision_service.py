"""
Vision Service - Claude Vision API Integration

Provides OCR, image analysis, and description capabilities using Claude's vision API.
Handles handwritten notebooks, printed documents, diagrams, and general image analysis.
"""

import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service for Claude vision API operations.

    Supports:
    - OCR (handwriting and printed text)
    - Image description and captioning
    - Visual Q&A
    - Diagram extraction
    """

    def __init__(self, anthropic_client: Anthropic):
        """
        Initialize vision service.

        Args:
            anthropic_client: Configured Anthropic client
        """
        self.client = anthropic_client
        self.model = "claude-sonnet-4-5-20250929"

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """
        Encode image to base64 for Claude API.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, media_type)

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If unsupported image format
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine media type from extension
        ext = path.suffix.lower()
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }

        media_type = media_type_map.get(ext)
        if not media_type:
            raise ValueError(f"Unsupported image format: {ext}")

        # Read and encode
        with open(path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        return image_data, media_type

    async def ocr_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        preserve_formatting: bool = True
    ) -> Dict[str, Any]:
        """
        Perform OCR on image using Claude vision.

        Optimized for handwritten and printed text extraction.

        Args:
            image_path: Path to image file
            prompt: Custom prompt (default: transcription prompt)
            preserve_formatting: Preserve document structure in markdown

        Returns:
            {
                "content": "Markdown transcription",
                "confidence": "high|medium|low",
                "notes": "Any transcription notes",
                "processing_time": float
            }

        Raises:
            Exception: If API call fails
        """
        import time
        start_time = time.time()

        try:
            # Encode image
            image_data, media_type = self._encode_image(image_path)

            # Default OCR prompt
            if not prompt:
                prompt = self._get_ocr_prompt(preserve_formatting)

            # Call Claude vision API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract text from response
            content = message.content[0].text

            # Calculate processing time
            processing_time = time.time() - start_time

            logger.info(f"OCR completed in {processing_time:.2f}s")

            return {
                "content": content,
                "confidence": "high",  # Claude vision is generally high confidence
                "notes": f"Processed with Claude {self.model}",
                "processing_time": processing_time,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise

    async def describe_image(
        self,
        image_path: str,
        detail_level: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Generate detailed description of image.

        Args:
            image_path: Path to image file
            detail_level: "brief", "detailed", or "comprehensive"

        Returns:
            {
                "content": "Image description",
                "processing_time": float
            }
        """
        import time
        start_time = time.time()

        try:
            image_data, media_type = self._encode_image(image_path)

            prompt = self._get_description_prompt(detail_level)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            content = message.content[0].text
            processing_time = time.time() - start_time

            logger.info(f"Description completed in {processing_time:.2f}s")

            return {
                "content": content,
                "processing_time": processing_time,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Description failed: {e}")
            raise

    async def analyze_image(
        self,
        image_path: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Answer question about image.

        Args:
            image_path: Path to image file
            question: User's question about the image

        Returns:
            {
                "content": "Answer to question",
                "processing_time": float
            }
        """
        import time
        start_time = time.time()

        try:
            image_data, media_type = self._encode_image(image_path)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }
                ]
            )

            content = message.content[0].text
            processing_time = time.time() - start_time

            logger.info(f"Analysis completed in {processing_time:.2f}s")

            return {
                "content": content,
                "processing_time": processing_time,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def extract_diagram(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Extract structure from diagram or flowchart.

        Args:
            image_path: Path to diagram image

        Returns:
            {
                "content": "Text description of diagram structure",
                "processing_time": float
            }
        """
        import time
        start_time = time.time()

        try:
            image_data, media_type = self._encode_image(image_path)

            prompt = self._get_diagram_prompt()

            message = self.client.messages.create(
                model=self.model,
                max_tokens=3072,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            content = message.content[0].text
            processing_time = time.time() - start_time

            logger.info(f"Diagram extraction completed in {processing_time:.2f}s")

            return {
                "content": content,
                "processing_time": processing_time,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Diagram extraction failed: {e}")
            raise

    # ========================================================================
    # Prompt Templates
    # ========================================================================

    def _get_ocr_prompt(self, preserve_formatting: bool) -> str:
        """Get OCR prompt based on formatting preference."""
        if preserve_formatting:
            return """Transcribe all text from this image to markdown.

Requirements:
- Preserve original formatting (headings, lists, paragraphs, indentation)
- Use markdown syntax for structure (# for headings, - for lists, etc.)
- If text is unclear or illegible, use [unclear: best guess] notation
- Preserve any diagrams as ASCII art or detailed descriptions
- Include page numbers if visible
- Maintain the reading order (top to bottom, left to right)
- For tables, use markdown table syntax
- For emphasized text (bold, italic, underline), use markdown equivalents

Return only the transcribed content as markdown. Do not add commentary or explanations."""

        else:
            return """Extract all text from this image.

Return the text exactly as it appears, line by line.
If text is unclear, use [unclear] notation."""

    def _get_description_prompt(self, detail_level: str) -> str:
        """Get description prompt based on detail level."""
        prompts = {
            "brief": "Provide a brief, one-paragraph description of this image.",

            "detailed": """Provide a detailed description of this image.

Include:
- Main subject/content
- Visual composition and style
- Notable details or features
- Any text present
- Overall purpose or context

Be specific and observant.""",

            "comprehensive": """Provide a comprehensive analysis of this image.

Include:
- Main subject and secondary elements
- Visual style, composition, and technique
- Color palette and lighting
- Spatial relationships
- Any text, symbols, or annotations
- Emotional tone or atmosphere
- Possible purpose, context, or genre
- Notable details or unique features

Be thorough and analytical."""
        }

        return prompts.get(detail_level, prompts["detailed"])

    def _get_diagram_prompt(self) -> str:
        """Get prompt for diagram extraction."""
        return """Analyze this diagram and extract its structure as text.

Provide:
1. **Type**: What kind of diagram (flowchart, mind map, architecture, etc.)
2. **Components**: List all nodes, boxes, or elements
3. **Connections**: Describe relationships and flow between elements
4. **Labels**: Include all text labels, annotations
5. **Structure**: Describe the overall organization and hierarchy

Format as markdown with clear sections.
Use lists, code blocks, or tables to represent the structure clearly."""
