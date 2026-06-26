import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.db.supabase import get_supabase_client
from app.services.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_cost_dashboard(
    start_date: date | None = Query(None, description="Start date for cost data"),
    end_date: date | None = Query(None, description="End date for cost data"),
):
    """Get cost dashboard data."""
    tracker = CostTracker()
    try:
        dashboard = tracker.get_dashboard(start_date=start_date, end_date=end_date)
        return dashboard
    except Exception as e:
        logger.error(f"Failed to get cost dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost dashboard: {e}",
        )


@router.get("/by-workflow")
async def cost_by_workflow(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    """Get cost breakdown by workflow type."""
    client = get_supabase_client()

    try:
        query = client.table("workflow_costs").select("*")
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())

        result = query.execute()
        costs_data = result.data or []

        # Aggregate by workflow type
        by_workflow: dict[str, dict] = {}
        for cost in costs_data:
            wtype = cost.get("workflow_type", "unknown")
            if wtype not in by_workflow:
                by_workflow[wtype] = {
                    "workflow_type": wtype,
                    "total_cost": 0.0,
                    "total_runs": set(),
                    "count": 0,
                }
            by_workflow[wtype]["total_cost"] += cost.get("estimated_cost", 0)
            by_workflow[wtype]["total_runs"].add(cost.get("workflow_run_id"))
            by_workflow[wtype]["count"] += 1

        breakdown = []
        for wtype, data in by_workflow.items():
            total_runs = len(data["total_runs"])
            breakdown.append(
                {
                    "workflow_type": wtype,
                    "total_cost": round(data["total_cost"], 6),
                    "total_runs": total_runs,
                    "avg_cost_per_run": round(data["total_cost"] / total_runs, 6)
                    if total_runs > 0
                    else 0,
                }
            )

        return {"by_workflow": breakdown}

    except Exception as e:
        logger.error(f"Failed to get cost by workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost by workflow: {e}",
        )


@router.get("/by-node")
async def cost_by_node(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    """Get cost breakdown by node."""
    client = get_supabase_client()

    try:
        query = client.table("workflow_costs").select("*")
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())

        result = query.execute()
        costs_data = result.data or []

        # Aggregate by node + model
        by_node: dict[str, dict] = {}
        for cost in costs_data:
            key = f"{cost.get('node_name', 'unknown')}:{cost.get('model', 'unknown')}"
            if key not in by_node:
                by_node[key] = {
                    "node_name": cost.get("node_name", "unknown"),
                    "model": cost.get("model", "unknown"),
                    "total_cost": 0.0,
                    "total_calls": 0,
                    "total_latency": 0,
                    "latency_count": 0,
                }
            by_node[key]["total_cost"] += cost.get("estimated_cost", 0)
            by_node[key]["total_calls"] += 1
            latency = cost.get("latency_ms")
            if latency is not None:
                by_node[key]["total_latency"] += latency
                by_node[key]["latency_count"] += 1

        breakdown = []
        for data in by_node.values():
            avg_latency = (
                round(data["total_latency"] / data["latency_count"], 1)
                if data["latency_count"] > 0
                else None
            )
            breakdown.append(
                {
                    "node_name": data["node_name"],
                    "model": data["model"],
                    "total_cost": round(data["total_cost"], 6),
                    "total_calls": data["total_calls"],
                    "avg_latency_ms": avg_latency,
                }
            )

        return {"by_node": breakdown}

    except Exception as e:
        logger.error(f"Failed to get cost by node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost by node: {e}",
        )


@router.get("/daily")
async def daily_costs(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    """Get daily cost time series."""
    client = get_supabase_client()

    try:
        query = client.table("workflow_costs").select("*")
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())

        query = query.order("created_at")
        result = query.execute()
        costs_data = result.data or []

        # Aggregate by day
        daily: dict[str, dict] = {}
        for cost in costs_data:
            day = cost.get("created_at", "")[:10]  # Extract date portion
            if day not in daily:
                daily[day] = {"date": day, "total_cost": 0.0, "run_ids": set()}
            daily[day]["total_cost"] += cost.get("estimated_cost", 0)
            daily[day]["run_ids"].add(cost.get("workflow_run_id"))

        time_series = [
            {
                "date": data["date"],
                "total_cost": round(data["total_cost"], 6),
                "total_runs": len(data["run_ids"]),
            }
            for data in sorted(daily.values(), key=lambda d: d["date"])
        ]

        return {"daily": time_series}

    except Exception as e:
        logger.error(f"Failed to get daily costs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily costs: {e}",
        )
