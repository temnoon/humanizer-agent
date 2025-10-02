"""Storage utilities for managing transformations."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from models.schemas import TransformationStatus, TransformationStatusEnum


class TransformationStorage:
    """
    In-memory storage for transformations (MVP version).
    
    In production, this would use SQLAlchemy with a real database.
    For MVP, we use a simple in-memory dict that persists to JSON.
    """
    
    def __init__(self):
        """Initialize storage."""
        self.transformations: Dict[str, Dict[str, Any]] = {}
        
    async def create_transformation(
        self,
        id: str,
        original_content: str,
        persona: str,
        namespace: str,
        style: str,
        depth: float,
        preserve_structure: bool
    ) -> str:
        """Create a new transformation record."""
        self.transformations[id] = {
            "id": id,
            "status": TransformationStatusEnum.PENDING,
            "progress": 0.0,
            "original_content": original_content,
            "transformed_content": None,
            "persona": persona,
            "namespace": namespace,
            "style": style,
            "depth": depth,
            "preserve_structure": preserve_structure,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "error": None,
            "checkpoints": [],
            "metadata": {}
        }
        return id
    
    async def get_transformation(self, transformation_id: str) -> Optional[TransformationStatus]:
        """Get transformation by ID."""
        data = self.transformations.get(transformation_id)
        if not data:
            return None
        
        return TransformationStatus(
            id=data["id"],
            status=data["status"],
            progress=data["progress"],
            original_content=data["original_content"],
            transformed_content=data["transformed_content"],
            persona=data["persona"],
            namespace=data["namespace"],
            style=data["style"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            completed_at=data["completed_at"],
            error=data["error"],
            checkpoints=data["checkpoints"]
        )
    
    async def update_status(
        self,
        transformation_id: str,
        status: TransformationStatusEnum,
        progress: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Update transformation status."""
        if transformation_id not in self.transformations:
            return
        
        self.transformations[transformation_id]["status"] = status
        self.transformations[transformation_id]["updated_at"] = datetime.utcnow()
        
        if progress is not None:
            self.transformations[transformation_id]["progress"] = progress
        
        if error is not None:
            self.transformations[transformation_id]["error"] = error
        
        if status == TransformationStatusEnum.COMPLETED:
            self.transformations[transformation_id]["completed_at"] = datetime.utcnow()
    
    async def update_transformation(
        self,
        transformation_id: str,
        transformed_content: Optional[str] = None,
        status: Optional[TransformationStatusEnum] = None,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update transformation with new content or status."""
        if transformation_id not in self.transformations:
            return
        
        if transformed_content is not None:
            self.transformations[transformation_id]["transformed_content"] = transformed_content
        
        if status is not None:
            self.transformations[transformation_id]["status"] = status
        
        if progress is not None:
            self.transformations[transformation_id]["progress"] = progress
        
        if metadata is not None:
            self.transformations[transformation_id]["metadata"] = metadata
        
        self.transformations[transformation_id]["updated_at"] = datetime.utcnow()
        
        if status == TransformationStatusEnum.COMPLETED:
            self.transformations[transformation_id]["completed_at"] = datetime.utcnow()
    
    async def get_all_transformations(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[TransformationStatus]:
        """Get all transformations with pagination."""
        all_transformations = sorted(
            self.transformations.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        paginated = all_transformations[offset:offset + limit]
        
        return [
            TransformationStatus(
                id=t["id"],
                status=t["status"],
                progress=t["progress"],
                original_content=t["original_content"],
                transformed_content=t["transformed_content"],
                persona=t["persona"],
                namespace=t["namespace"],
                style=t["style"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
                completed_at=t["completed_at"],
                error=t["error"],
                checkpoints=t["checkpoints"]
            )
            for t in paginated
        ]
    
    async def delete_transformation(self, transformation_id: str) -> bool:
        """Delete a transformation."""
        if transformation_id in self.transformations:
            del self.transformations[transformation_id]
            return True
        return False
