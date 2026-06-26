from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WorkflowCostResponse(BaseModel):
    id: UUID
    workflow_run_id: UUID
    workflow_type: str
    node_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CostSummary(BaseModel):
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int
    total_runs: int
    avg_cost_per_run: float


class CostByWorkflow(BaseModel):
    workflow_type: str
    total_cost: float
    total_runs: int
    avg_cost_per_run: float


class CostByNode(BaseModel):
    node_name: str
    model: str
    total_cost: float
    total_calls: int
    avg_latency_ms: Optional[float] = None


class DailyCost(BaseModel):
    date: date
    total_cost: float
    total_runs: int


class CostDashboard(BaseModel):
    summary: CostSummary
    by_workflow: list[CostByWorkflow]
    by_node: list[CostByNode]
    daily: list[DailyCost]
