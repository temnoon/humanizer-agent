"""
Image Metadata Extraction Service

Extracts EXIF data, dimensions, and AI generation metadata from images.
Handles prompts from various AI image generators (DALL-E, Stable Diffusion, Midjourney).
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageMetadataExtractor:
    """
    Extract metadata from images including EXIF, dimensions, and AI prompts.
    """

    def extract_all_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract all available metadata from an image.

        Args:
            image_path: Path to image file

        Returns:
            {
                "dimensions": {"width": int, "height": int},
                "format": str,
                "mode": str,
                "file_size": int,
                "exif": dict,
                "ai_metadata": {
                    "prompt": str or None,
                    "generator": str or None,
                    "parameters": dict
                },
                "created_date": str or None,
                "camera": str or None
            }
        """
        metadata = {}

        try:
            with Image.open(image_path) as img:
                # Basic image info
                metadata["dimensions"] = {
                    "width": img.width,
                    "height": img.height
                }
                metadata["format"] = img.format
                metadata["mode"] = img.mode

                # File size
                file_size = Path(image_path).stat().st_size
                metadata["file_size"] = file_size

                # Extract EXIF data
                exif_data = self._extract_exif(img)
                metadata["exif"] = exif_data

                # Extract AI generation metadata
                ai_meta = self._extract_ai_metadata(img, exif_data)
                metadata["ai_metadata"] = ai_meta

                # Extract common useful fields
                metadata["created_date"] = exif_data.get("DateTime")
                metadata["camera"] = exif_data.get("Model")

                logger.info(f"Extracted metadata from {Path(image_path).name}")

        except Exception as e:
            logger.error(f"Failed to extract metadata from {image_path}: {e}")
            metadata["error"] = str(e)

        return metadata

    def _extract_exif(self, img: Image.Image) -> Dict[str, Any]:
        """
        Extract EXIF data from PIL Image.

        Returns:
            Dictionary of EXIF tags and values
        """
        exif_data = {}

        try:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    # Get human-readable tag name
                    tag = ExifTags.TAGS.get(tag_id, tag_id)

                    # Convert bytes to string
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)

                    exif_data[tag] = value

        except Exception as e:
            logger.warning(f"Failed to extract EXIF: {e}")

        return exif_data

    def _extract_ai_metadata(
        self,
        img: Image.Image,
        exif_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract AI generation metadata (prompts, parameters).

        Supports:
        - DALL-E (stored in UserComment or ImageDescription)
        - Stable Diffusion (stored in parameters PNG chunk)
        - Midjourney (stored in ImageDescription)
        - ComfyUI (stored in workflow PNG chunk)

        Returns:
            {
                "prompt": str or None,
                "negative_prompt": str or None,
                "generator": str or None,
                "parameters": dict
            }
        """
        ai_meta = {
            "prompt": None,
            "negative_prompt": None,
            "generator": None,
            "parameters": {}
        }

        # Check EXIF fields
        prompt_fields = ["UserComment", "ImageDescription", "XPComment", "XPSubject"]
        for field in prompt_fields:
            if field in exif_data:
                value = exif_data[field]
                if value and isinstance(value, str):
                    # Check if it's a prompt
                    if self._looks_like_prompt(value):
                        ai_meta["prompt"] = value
                        ai_meta["generator"] = self._detect_generator(value)
                        break

        # Check PNG metadata chunks (for Stable Diffusion)
        if img.format == "PNG" and hasattr(img, 'info'):
            info = img.info

            # Stable Diffusion stores parameters in "parameters" chunk
            if "parameters" in info:
                params_text = info["parameters"]
                parsed = self._parse_sd_parameters(params_text)
                ai_meta.update(parsed)
                ai_meta["generator"] = "Stable Diffusion"

            # ComfyUI stores workflow in "workflow" chunk
            elif "workflow" in info:
                ai_meta["generator"] = "ComfyUI"
                ai_meta["parameters"]["workflow"] = "present"

            # Check for prompt in PNG tEXt chunks
            elif "prompt" in info:
                ai_meta["prompt"] = info["prompt"]

        return ai_meta

    def _looks_like_prompt(self, text: str) -> bool:
        """
        Heuristic to detect if text is likely an AI image prompt.

        Returns:
            True if text appears to be a prompt
        """
        text_lower = text.lower()

        # Prompt-like keywords
        prompt_indicators = [
            "prompt:",
            "a detailed",
            "highly detailed",
            "digital art",
            "photorealistic",
            "concept art",
            "trending on",
            "artstation",
            "unreal engine",
            "8k",
            "4k",
            "masterpiece"
        ]

        # Check length (prompts usually 10-500 words)
        word_count = len(text.split())
        if word_count < 3 or word_count > 1000:
            return False

        # Check for indicators
        for indicator in prompt_indicators:
            if indicator in text_lower:
                return True

        # Check if contains typical prompt structure
        if any(word in text_lower for word in ["photograph", "painting", "illustration", "render", "scene"]):
            return True

        return False

    def _detect_generator(self, text: str) -> Optional[str]:
        """
        Detect which AI generator created the image based on metadata.

        Returns:
            Generator name or None
        """
        text_lower = text.lower()

        if "dall-e" in text_lower or "dalle" in text_lower:
            return "DALL-E"
        elif "midjourney" in text_lower:
            return "Midjourney"
        elif "stable diffusion" in text_lower:
            return "Stable Diffusion"
        elif "leonardo" in text_lower:
            return "Leonardo.ai"

        return None

    def _parse_sd_parameters(self, params_text: str) -> Dict[str, Any]:
        """
        Parse Stable Diffusion parameters string.

        Format:
        positive prompt
        Negative prompt: negative prompt text
        Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 123456, ...

        Returns:
            {
                "prompt": str,
                "negative_prompt": str,
                "parameters": {
                    "steps": int,
                    "sampler": str,
                    "cfg_scale": float,
                    "seed": int,
                    ...
                }
            }
        """
        result = {
            "prompt": None,
            "negative_prompt": None,
            "parameters": {}
        }

        lines = params_text.split('\n')

        # First line is usually the positive prompt
        if lines:
            result["prompt"] = lines[0].strip()

        # Parse subsequent lines
        for line in lines[1:]:
            line = line.strip()

            # Negative prompt
            if line.startswith("Negative prompt:"):
                result["negative_prompt"] = line.replace("Negative prompt:", "").strip()

            # Parameters line (Steps: 20, Sampler: Euler a, ...)
            elif ":" in line and "," in line:
                params = {}
                parts = line.split(',')
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()

                        # Try to convert to number
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass  # Keep as string

                        params[key] = value

                result["parameters"] = params

        return result

    def extract_dimensions(self, image_path: str) -> Tuple[int, int]:
        """
        Extract just image dimensions (fast).

        Args:
            image_path: Path to image file

        Returns:
            (width, height)
        """
        try:
            with Image.open(image_path) as img:
                return img.width, img.height
        except Exception as e:
            logger.error(f"Failed to get dimensions for {image_path}: {e}")
            return (None, None)

    def has_prompt(self, image_path: str) -> bool:
        """
        Quick check if image contains an AI prompt in metadata.

        Args:
            image_path: Path to image file

        Returns:
            True if prompt detected
        """
        metadata = self.extract_all_metadata(image_path)
        return metadata.get("ai_metadata", {}).get("prompt") is not None
