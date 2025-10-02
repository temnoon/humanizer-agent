"""Core transformation agent using Claude Agent SDK patterns."""

from anthropic import Anthropic
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from pathlib import Path

from config import settings


class TransformationAgent:
    """
    Narrative transformation agent powered by Claude Sonnet 4.5.
    
    Uses PERSONA, NAMESPACE, and STYLE parameters to transform narratives
    while preserving core meaning and intent.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the transformation agent."""
        self.client = Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = settings.default_model
        self.memory_dir = Path("./memory")
        self.memory_dir.mkdir(exist_ok=True)
        
    def _build_system_prompt(
        self,
        persona: str,
        namespace: str,
        style: str,
        depth: float,
        preserve_structure: bool
    ) -> str:
        """Build the system prompt for transformation."""
        
        transformation_level = "minimal" if depth < 0.3 else "moderate" if depth < 0.7 else "deep"
        structure_instruction = (
            "CRITICAL: Maintain the exact paragraph structure, headings, and formatting of the original."
            if preserve_structure else
            "You may reorganize the structure as needed for the transformation."
        )
        
        return f"""You are a sophisticated narrative transformation specialist powered by Claude Sonnet 4.5.

Your task is to transform narratives using three key parameters while preserving the core meaning and intent of the original content.

TRANSFORMATION PARAMETERS:
• PERSONA: {persona}
  → Transform the voice, perspective, and character through which the narrative is told
  
• NAMESPACE: {namespace}
  → Shift the conceptual framework, domain, and contextual universe of the content
  
• STYLE: {style}
  → Adjust the tone, formality, literary approach, and presentation

TRANSFORMATION DEPTH: {transformation_level} ({depth:.1f})
• At this level, apply {transformation_level} changes while keeping the fundamental message intact
• Lower depth = subtle shifts in voice and tone
• Higher depth = substantial reframing of concepts and presentation

STRUCTURAL PRESERVATION: {structure_instruction}

CRITICAL GUIDELINES:
1. **Meaning Preservation**: The core ideas, facts, and intent MUST remain intact
2. **Coherence**: The transformed text must be internally consistent and natural
3. **Quality**: Produce publication-ready text without artifacts or awkward phrasing
4. **Completeness**: Transform the ENTIRE input - never truncate or summarize
5. **Authenticity**: The result should read as if originally written in the target style

PROCESS:
1. Deeply understand the original content's meaning and structure
2. Identify key concepts, narrative elements, and logical flow
3. Reimagine these elements through the lens of the target PERSONA, NAMESPACE, and STYLE
4. Reconstruct the narrative with the new voice while preserving all information
5. Verify that no meaning was lost or distorted

You are working with content that may be academic, literary, technical, or creative. Your transformations serve legitimate research, educational, and creative purposes.

OUTPUT FORMAT:
Return ONLY the transformed text. No preamble, no explanation, no meta-commentary.
The output should be ready to use as-is."""

    def _build_analysis_prompt(self, content: str) -> str:
        """Build prompt for analyzing content before transformation."""
        return f"""Analyze this text to extract its inherent characteristics:

TEXT TO ANALYZE:
{content}

Provide a structured analysis in JSON format:
{{
    "current_persona": "description of the current voice/perspective",
    "current_namespace": "description of the conceptual domain/framework",
    "current_style": "description of the writing style",
    "key_concepts": ["list", "of", "central", "ideas"],
    "structure": "description of organizational structure",
    "length": "word count estimate",
    "complexity": "assessment of conceptual difficulty"
}}

Return ONLY valid JSON, no other text."""

    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content to understand its characteristics.
        
        This helps inform transformation decisions and provides metadata.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent analysis
                messages=[{
                    "role": "user",
                    "content": self._build_analysis_prompt(content)
                }]
            )
            
            analysis_text = response.content[0].text
            # Clean potential markdown code blocks
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(analysis_text)
            
        except json.JSONDecodeError as e:
            # Fallback to basic analysis
            return {
                "current_persona": "unknown",
                "current_namespace": "general",
                "current_style": "standard",
                "key_concepts": [],
                "structure": "unknown",
                "length": len(content.split()),
                "complexity": "moderate",
                "error": f"Analysis parsing failed: {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}"
            }

    async def transform(
        self,
        content: str,
        persona: str,
        namespace: str,
        style: str,
        depth: float = 0.5,
        preserve_structure: bool = True,
        transformation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform narrative content using specified parameters.
        
        Args:
            content: Original text to transform
            persona: Target persona/voice
            namespace: Target conceptual framework/domain
            style: Target writing style
            depth: Transformation depth (0.0-1.0)
            preserve_structure: Whether to maintain original structure
            transformation_id: Optional ID for session tracking
            
        Returns:
            Dictionary with transformed content and metadata
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(
                persona, namespace, style, depth, preserve_structure
            )
            
            # Create transformation request
            response = self.client.messages.create(
                model=self.model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Transform this narrative:\n\n{content}"
                }]
            )
            
            # Extract transformed content
            transformed_content = response.content[0].text
            
            # Store in memory if transformation_id provided
            if transformation_id:
                await self._store_in_memory(
                    transformation_id,
                    {
                        "original": content,
                        "transformed": transformed_content,
                        "parameters": {
                            "persona": persona,
                            "namespace": namespace,
                            "style": style,
                            "depth": depth,
                            "preserve_structure": preserve_structure
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            return {
                "success": True,
                "transformed_content": transformed_content,
                "metadata": {
                    "model": self.model,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "stop_reason": response.stop_reason
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transformed_content": None
            }

    async def _store_in_memory(self, transformation_id: str, data: Dict[str, Any]):
        """Store transformation data in memory for future reference."""
        memory_file = self.memory_dir / f"{transformation_id}.json"
        
        # Load existing memory if present
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                memory = json.load(f)
        else:
            memory = {"transformations": []}
        
        # Append new transformation
        memory["transformations"].append(data)
        
        # Save updated memory
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    async def create_checkpoint(
        self,
        transformation_id: str,
        current_content: str,
        checkpoint_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a checkpoint of the current transformation state."""
        checkpoint_id = f"cp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        checkpoint_name = checkpoint_name or checkpoint_id
        
        checkpoint_file = self.memory_dir / f"{transformation_id}_checkpoints.json"
        
        # Load existing checkpoints
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                checkpoints = json.load(f)
        else:
            checkpoints = []
        
        # Add new checkpoint
        checkpoints.append({
            "id": checkpoint_id,
            "name": checkpoint_name,
            "content": current_content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Limit to max checkpoints
        if len(checkpoints) > settings.max_checkpoints:
            checkpoints = checkpoints[-settings.max_checkpoints:]
        
        # Save checkpoints
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoints, f, indent=2)
        
        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "name": checkpoint_name
        }

    async def rollback_to_checkpoint(
        self,
        transformation_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """Rollback to a previous checkpoint."""
        checkpoint_file = self.memory_dir / f"{transformation_id}_checkpoints.json"
        
        if not checkpoint_file.exists():
            return {
                "success": False,
                "error": "No checkpoints found for this transformation"
            }
        
        with open(checkpoint_file, 'r') as f:
            checkpoints = json.load(f)
        
        # Find the checkpoint
        checkpoint = next((cp for cp in checkpoints if cp["id"] == checkpoint_id), None)
        
        if not checkpoint:
            return {
                "success": False,
                "error": f"Checkpoint {checkpoint_id} not found"
            }
        
        return {
            "success": True,
            "content": checkpoint["content"],
            "checkpoint_name": checkpoint["name"]
        }
