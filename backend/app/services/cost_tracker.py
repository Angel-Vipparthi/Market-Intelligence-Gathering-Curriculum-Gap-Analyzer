import logging
from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# Cost per 1M tokens — OpenRouter model IDs
MODEL_COSTS: dict[str, dict[str, float]] = {
    "anthropic/claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "anthropic/claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/text-embedding-3-small": {"input": 0.02, "output": 0.0},
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
}


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost based on model and token counts.

    Args:
        model: The model identifier.
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens used.

    Returns:
        Estimated cost in USD.
    """
    costs = MODEL_COSTS.get(model, {"input": 3.0, "output": 15.0})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 8)


class CostTracker:
    """Track and analyze workflow costs."""

    def __init__(self):
        self.client = get_supabase_client()

    def record_cost(
        self,
        workflow_run_id: str,
        workflow_type: str,
        node_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        """Record a cost entry for a workflow node execution.

        Args:
            workflow_run_id: UUID of the workflow run.
            workflow_type: Type of workflow (e.g., 'digest', 'gap_analysis').
            node_name: Name of the LangGraph node.
            model: Model identifier used.
            input_tokens: Number of input tokens consumed.
            output_tokens: Number of output tokens generated.
            latency_ms: Optional execution latency in milliseconds.

        Returns:
            The inserted cost record.
        """
        total_tokens = input_tokens + output_tokens
        estimated_cost = _calculate_cost(model, input_tokens, output_tokens)

        data = {
            "id": str(uuid4()),
            "workflow_run_id": workflow_run_id,
            "workflow_type": workflow_type,
            "node_name": node_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
        }

        if latency_ms is not None:
            data["latency_ms"] = latency_ms

        try:
            result = self.client.table("workflow_costs").insert(data).execute()
            logger.info(
                f"Recorded cost: {workflow_type}/{node_name} "
                f"tokens={total_tokens} cost=${estimated_cost:.6f}"
            )
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Failed to record cost: {e}")
            raise

    def get_run_cost(self, workflow_run_id: str) -> dict[str, Any]:
        """Get total cost for a specific workflow run.

        Args:
            workflow_run_id: UUID of the workflow run.

        Returns:
            Dict with total_cost, total_tokens, entries count, and breakdown.
        """
        try:
            result = (
                self.client.table("workflow_costs")
                .select("*")
                .eq("workflow_run_id", workflow_run_id)
                .execute()
            )

            entries = result.data or []
            total_cost = sum(e.get("estimated_cost", 0) for e in entries)
            total_input = sum(e.get("input_tokens", 0) for e in entries)
            total_output = sum(e.get("output_tokens", 0) for e in entries)

            return {
                "workflow_run_id": workflow_run_id,
                "total_cost": round(total_cost, 6),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "entries": len(entries),
                "breakdown": entries,
            }

        except Exception as e:
            logger.error(f"Failed to get run cost: {e}")
            raise

    def get_dashboard(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive cost dashboard data.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            CostDashboard-compatible dict with summary, by_workflow, by_node, daily.
        """
        try:
            query = self.client.table("workflow_costs").select("*")
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            result = query.execute()
            costs_data = result.data or []

            # Summary
            total_cost = sum(c.get("estimated_cost", 0) for c in costs_data)
            total_input = sum(c.get("input_tokens", 0) for c in costs_data)
            total_output = sum(c.get("output_tokens", 0) for c in costs_data)
            run_ids = set(c.get("workflow_run_id") for c in costs_data)
            total_runs = len(run_ids)
            avg_cost = total_cost / total_runs if total_runs > 0 else 0

            summary = {
                "total_cost": round(total_cost, 6),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_runs": total_runs,
                "avg_cost_per_run": round(avg_cost, 6),
            }

            # By workflow type
            wf_map: dict[str, dict] = {}
            for c in costs_data:
                wtype = c.get("workflow_type", "unknown")
                if wtype not in wf_map:
                    wf_map[wtype] = {"total_cost": 0.0, "run_ids": set()}
                wf_map[wtype]["total_cost"] += c.get("estimated_cost", 0)
                wf_map[wtype]["run_ids"].add(c.get("workflow_run_id"))

            by_workflow = []
            for wtype, data in wf_map.items():
                runs = len(data["run_ids"])
                by_workflow.append(
                    {
                        "workflow_type": wtype,
                        "total_cost": round(data["total_cost"], 6),
                        "total_runs": runs,
                        "avg_cost_per_run": round(data["total_cost"] / runs, 6)
                        if runs > 0
                        else 0,
                    }
                )

            # By node
            node_map: dict[str, dict] = {}
            for c in costs_data:
                key = f"{c.get('node_name', 'unknown')}:{c.get('model', 'unknown')}"
                if key not in node_map:
                    node_map[key] = {
                        "node_name": c.get("node_name", "unknown"),
                        "model": c.get("model", "unknown"),
                        "total_cost": 0.0,
                        "total_calls": 0,
                        "total_latency": 0,
                        "latency_count": 0,
                    }
                node_map[key]["total_cost"] += c.get("estimated_cost", 0)
                node_map[key]["total_calls"] += 1
                latency = c.get("latency_ms")
                if latency is not None:
                    node_map[key]["total_latency"] += latency
                    node_map[key]["latency_count"] += 1

            by_node = []
            for data in node_map.values():
                avg_lat = (
                    round(data["total_latency"] / data["latency_count"], 1)
                    if data["latency_count"] > 0
                    else None
                )
                by_node.append(
                    {
                        "node_name": data["node_name"],
                        "model": data["model"],
                        "total_cost": round(data["total_cost"], 6),
                        "total_calls": data["total_calls"],
                        "avg_latency_ms": avg_lat,
                    }
                )

            # Daily
            daily_map: dict[str, dict] = {}
            for c in costs_data:
                day = c.get("created_at", "")[:10]
                if day not in daily_map:
                    daily_map[day] = {"date": day, "total_cost": 0.0, "run_ids": set()}
                daily_map[day]["total_cost"] += c.get("estimated_cost", 0)
                daily_map[day]["run_ids"].add(c.get("workflow_run_id"))

            daily = [
                {
                    "date": data["date"],
                    "total_cost": round(data["total_cost"], 6),
                    "total_runs": len(data["run_ids"]),
                }
                for data in sorted(daily_map.values(), key=lambda d: d["date"])
            ]

            return {
                "summary": summary,
                "by_workflow": by_workflow,
                "by_node": by_node,
                "daily": daily,
            }

        except Exception as e:
            logger.error(f"Failed to get cost dashboard: {e}")
            raise
