from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DigestResponse(BaseModel):
    digest_id: UUID
    url_id: Optional[UUID] = None
    url: str
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    topic: Optional[str] = None
    summary: Optional[str] = None
    market_signal: Optional[str] = None
    evidence_snippet: Optional[str] = None
    tools_versions: Optional[list] = None
    curriculum_relevant: Optional[str] = None
    relevance_reason: Optional[str] = None
    credibility_score: Optional[float] = None
    status: str = "pending"
    workflow_run_id: Optional[UUID] = None
    total_tokens: int = 0
    total_cost: float = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    items: list[DigestResponse]
    total: int
    pending_review: int


class DigestReviewRequest(BaseModel):
    decision: Literal["approved", "rejected", "needs_review"]
    comments: Optional[str] = None
    edited_fields: Optional[dict] = None
