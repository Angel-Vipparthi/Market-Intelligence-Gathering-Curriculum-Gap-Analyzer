import logging
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_evaluation(suite_name: str, eval_run_id: str):
    """Run a promptfoo evaluation suite in the background."""
    client = get_supabase_client()
    try:
        # Attempt to import and run the evaluation
        from app.agents.evaluation_runner import run_evaluation

        results = await run_evaluation(suite_name=suite_name, eval_run_id=eval_run_id)

        client.table("evaluation_runs").update(
            {"status": "completed", "results": results}
        ).eq("id", eval_run_id).execute()

    except ImportError:
        logger.warning("Evaluation runner not yet implemented")
        try:
            client.table("evaluation_runs").update(
                {"status": "failed", "error": "Evaluation runner not implemented"}
            ).eq("id", eval_run_id).execute()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Evaluation failed for suite={suite_name}: {e}")
        try:
            client.table("evaluation_runs").update(
                {"status": "failed", "error": str(e)}
            ).eq("id", eval_run_id).execute()
        except Exception:
            pass


@router.get("")
async def list_evaluations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List evaluation runs."""
    client = get_supabase_client()

    try:
        result = (
            client.table("evaluation_runs")
            .select("*", count="exact")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to list evaluations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evaluations: {e}",
        )

    return {
        "items": result.data or [],
        "total": result.count or len(result.data or []),
    }


@router.get("/{eval_id}")
async def get_evaluation(eval_id: str):
    """Get evaluation detail with results."""
    client = get_supabase_client()

    try:
        result = (
            client.table("evaluation_runs").select("*").eq("id", eval_id).execute()
        )
    except Exception as e:
        logger.error(f"Failed to get evaluation {eval_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evaluation: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation with id {eval_id} not found",
        )

    return result.data[0]


@router.post("/run")
async def run_evaluation_suite(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Trigger a promptfoo evaluation run."""
    suite_name = payload.get("suite_name")
    if not suite_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="suite_name is required",
        )

    client = get_supabase_client()
    eval_run_id = str(uuid4())

    try:
        client.table("evaluation_runs").insert(
            {
                "id": eval_run_id,
                "suite_name": suite_name,
                "status": "running",
            }
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to create evaluation run record: {e}")

    background_tasks.add_task(_run_evaluation, suite_name, eval_run_id)

    return {"eval_run_id": eval_run_id, "suite_name": suite_name, "status": "running"}
