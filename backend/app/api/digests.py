import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.db.supabase import get_supabase_client
from app.dependencies import get_current_user
from app.models.digest import DigestListResponse, DigestResponse, DigestReviewRequest

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_digest_agent(url_id: str, workflow_run_id: str):
    """Run the digest agent for a given URL in the background."""
    try:
        from app.agents.digest_agent import run_digest_agent

        client = get_supabase_client()
        url_row = client.table("url_registry").select("url").eq("id", url_id).execute()
        if not url_row.data:
            logger.error(f"URL not found for url_id={url_id}")
            return

        url = url_row.data[0]["url"]
        result = await run_digest_agent(url=url, url_id=url_id)

        total_tokens = result.get("total_tokens", 0)
        total_cost = result.get("total_cost", 0.0)
        if total_tokens > 0 or total_cost > 0:
            try:
                client.table("workflow_costs").insert({
                    "workflow_run_id": workflow_run_id,
                    "workflow_type": "digest_agent",
                    "node_name": "full_pipeline",
                    "model": "anthropic/claude-sonnet-4",
                    "input_tokens": int(total_tokens * 0.7),
                    "output_tokens": int(total_tokens * 0.3),
                    "total_tokens": total_tokens,
                    "estimated_cost": round(total_cost, 8),
                }).execute()
                logger.info(f"Recorded digest_agent cost: {total_tokens} tokens, ${total_cost:.6f}")
            except Exception as e:
                logger.error(f"Failed to record digest cost: {e}")

    except ImportError:
        logger.warning("Digest agent not yet implemented, skipping processing")
    except Exception as e:
        logger.error(f"Digest agent failed for url_id={url_id}: {e}")


@router.post("/process")
async def process_digest(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Trigger digest agent for a single URL."""
    url_id = payload.get("url_id")
    if not url_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="url_id is required",
        )

    client = get_supabase_client()

    url_result = client.table("url_registry").select("id").eq("id", url_id).execute()
    if not url_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with id {url_id} not found",
        )

    workflow_run_id = str(uuid4())
    background_tasks.add_task(_run_digest_agent, url_id, workflow_run_id)
    return {"workflow_run_id": workflow_run_id, "status": "processing"}


@router.post("/process-batch")
async def process_digest_batch(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Trigger digest agent for multiple URLs."""
    url_ids = payload.get("url_ids", [])
    if not url_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="url_ids list is required and must not be empty",
        )

    results = []
    for url_id in url_ids:
        workflow_run_id = str(uuid4())
        background_tasks.add_task(_run_digest_agent, url_id, workflow_run_id)
        results.append({"url_id": url_id, "workflow_run_id": workflow_run_id, "status": "processing"})

    return {"batch_results": results, "total": len(results)}


@router.post("/process-all")
async def process_all_unprocessed(background_tasks: BackgroundTasks):
    """Trigger digest agent for ALL URLs that haven't been digested yet."""
    client = get_supabase_client()

    all_urls = client.table("url_registry").select("id, url").eq("is_active", True).execute()
    if not all_urls.data:
        return {"message": "No active URLs found", "total": 0}

    existing = client.table("market_digests").select("url_id").execute()
    processed_ids = {d["url_id"] for d in (existing.data or []) if d.get("url_id")}

    unprocessed = [u for u in all_urls.data if u["id"] not in processed_ids]
    if not unprocessed:
        return {"message": "All URLs already processed", "total": 0}

    results = []
    for u in unprocessed:
        workflow_run_id = str(uuid4())
        background_tasks.add_task(_run_digest_agent, u["id"], workflow_run_id)
        results.append({"url_id": u["id"], "url": u["url"], "workflow_run_id": workflow_run_id})

    return {"batch_results": results, "total": len(results)}


@router.post("/batch-progress")
async def batch_progress(payload: dict):
    """Check progress for a batch of url_ids. Returns per-URL status."""
    url_ids = payload.get("url_ids", [])
    if not url_ids:
        return {"items": [], "completed": 0, "total": 0}

    client = get_supabase_client()

    digests = client.table("market_digests").select(
        "url_id, url, topic, status, curriculum_relevant, market_signal"
    ).in_("url_id", url_ids).execute()

    done_map = {}
    for d in (digests.data or []):
        done_map[d["url_id"]] = d

    urls = client.table("url_registry").select("id, url").in_("id", url_ids).execute()
    url_map = {u["id"]: u["url"] for u in (urls.data or [])}

    items = []
    for uid in url_ids:
        if uid in done_map:
            d = done_map[uid]
            items.append({
                "url_id": uid,
                "url": d.get("url", url_map.get(uid, "")),
                "status": "done",
                "topic": d.get("topic"),
                "curriculum_relevant": d.get("curriculum_relevant"),
                "market_signal": d.get("market_signal"),
            })
        else:
            items.append({
                "url_id": uid,
                "url": url_map.get(uid, ""),
                "status": "processing",
                "topic": None,
                "curriculum_relevant": None,
                "market_signal": None,
            })

    completed = sum(1 for i in items if i["status"] == "done")
    return {"items": items, "completed": completed, "total": len(items)}


@router.get("/status/summary")
async def digest_status_summary():
    """Return count of digests by status for progress tracking."""
    client = get_supabase_client()
    result = client.table("market_digests").select("status, curriculum_relevant").execute()
    rows = result.data or []

    by_status: dict[str, int] = {}
    relevant = 0
    for r in rows:
        s = r.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        if r.get("curriculum_relevant") == "Yes":
            relevant += 1

    url_count = client.table("url_registry").select("id", count="exact").eq("is_active", True).execute()

    return {
        "total_urls": url_count.count or 0,
        "total_digests": len(rows),
        "curriculum_relevant": relevant,
        "by_status": by_status,
    }


@router.get("", response_model=DigestListResponse)
async def list_digests(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    market_signal: str | None = Query(None, description="Filter by market signal type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List digests with optional filters."""
    client = get_supabase_client()

    query = client.table("market_digests").select("*", count="exact")

    if status_filter is not None:
        query = query.eq("status", status_filter)
    if market_signal is not None:
        query = query.eq("market_signal", market_signal)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    try:
        result = query.execute()
    except Exception as e:
        logger.error(f"Failed to list digests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list digests: {e}",
        )

    try:
        pending_result = (
            client.table("market_digests")
            .select("digest_id", count="exact")
            .eq("status", "pending")
            .execute()
        )
        pending_count = pending_result.count or 0
    except Exception:
        pending_count = 0

    return DigestListResponse(
        items=[DigestResponse(**row) for row in result.data],
        total=result.count or len(result.data),
        pending_review=pending_count,
    )


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_digest(digest_id: str):
    """Get a single digest with full detail."""
    client = get_supabase_client()

    try:
        result = client.table("market_digests").select("*").eq("digest_id", digest_id).execute()
    except Exception as e:
        logger.error(f"Failed to get digest {digest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get digest: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digest with id {digest_id} not found",
        )

    return DigestResponse(**result.data[0])


@router.post("/{digest_id}/review", response_model=DigestResponse)
async def review_digest(
    digest_id: str,
    review: DigestReviewRequest,
    user: dict = Depends(get_current_user),
):
    """Submit a review decision for a digest."""
    client = get_supabase_client()

    existing = client.table("market_digests").select("*").eq("digest_id", digest_id).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digest with id {digest_id} not found",
        )

    now = datetime.now(timezone.utc).isoformat()

    update_data = {
        "status": review.decision,
        "updated_at": now,
    }

    if review.edited_fields:
        update_data.update(review.edited_fields)

    try:
        result = (
            client.table("market_digests")
            .update(update_data)
            .eq("digest_id", digest_id)
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to update digest {digest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update digest: {e}",
        )

    try:
        client.table("review_decisions").insert({
            "entity_type": "digest",
            "entity_id": digest_id,
            "reviewer_id": user["id"],
            "decision": review.decision,
            "comments": review.comments,
            "edited_fields": review.edited_fields,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to insert review decision record: {e}")

    return DigestResponse(**result.data[0])
