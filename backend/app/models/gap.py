from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class GapResponse(BaseModel):
    gap_id: UUID
    digest_id: Optional[UUID] = None
    gap_type: Optional[str] = None
    market_signal: Optional[str] = None
    curriculum_evidence: Optional[str] = None
    gap_statement: str
    what_to_act: Optional[str] = None
    why_to_act: Optional[str] = None
    when_to_act: Optional[date] = None
    when_to_act_rationale: Optional[str] = None
    severity: Optional[str] = None
    severity_score: Optional[float] = None
    severity_factors: Optional[dict] = None
    impacted_content_area: Optional[str] = None
    impacted_courses: Optional[list[str]] = None
    impacted_sessions: Optional[list[str]] = None
    impacted_projects: Optional[list[str]] = None
    impacted_assessments: Optional[list[str]] = None
    impacted_quizzes: Optional[list[str]] = None
    impacted_tools: Optional[list[str]] = None
    action_items: Optional[list] = None
    recommended_owner: Optional[str] = None
    evidence_source: Optional[str] = None
    critic_feedback: Optional[list] = None
    decision_status: str = "pending_review"
    workflow_run_id: Optional[UUID] = None
    feedback_what: Optional[str] = None
    feedback_why: Optional[str] = None
    feedback_when: Optional[str] = None
    has_feedback: bool = False
    feedback_at: Optional[datetime] = None
    total_tokens: int = 0
    total_cost: float = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GapListResponse(BaseModel):
    items: list[GapResponse]
    total: int
    by_severity: dict


class GapReviewRequest(BaseModel):
    decision: Literal["approved", "rejected", "needs_review"]
    comments: Optional[str] = None
    edited_fields: Optional[dict] = None
    feedback: Optional[str] = None
