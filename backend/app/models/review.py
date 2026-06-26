from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ReviewDecisionResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    reviewer_id: UUID
    decision: str
    comments: Optional[str] = None
    edited_fields: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewFeedbackResponse(BaseModel):
    id: UUID
    decision_id: UUID
    feedback_type: str
    feedback_content: Optional[str] = None
    is_actionable: bool = False
    is_processed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
