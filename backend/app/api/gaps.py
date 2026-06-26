import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.db.supabase import get_supabase_client
from app.dependencies import get_current_user
from app.models.gap import GapListResponse, GapResponse, GapReviewRequest

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_gap_analyzer(digest_id: str, workflow_run_id: str):
    """Run gap analysis agent for a given digest in the background."""
    try:
        from app.agents.gap_agent import run_gap_agent

        result = await run_gap_agent(digest_id=digest_id)

        total_tokens = result.get("total_tokens", 0)
        total_cost = result.get("total_cost", 0.0)
        if total_tokens > 0 or total_cost > 0:
            client = get_supabase_client()
            try:
                client.table("workflow_costs").insert({
                    "workflow_run_id": workflow_run_id,
                    "workflow_type": "gap_agent",
                    "node_name": "full_pipeline",
                    "model": "anthropic/claude-sonnet-4",
                    "input_tokens": int(total_tokens * 0.7),
                    "output_tokens": int(total_tokens * 0.3),
                    "total_tokens": total_tokens,
                    "estimated_cost": round(total_cost, 8),
                }).execute()
                logger.info(f"Recorded gap_agent cost: {total_tokens} tokens, ${total_cost:.6f}")
            except Exception as e:
                logger.error(f"Failed to record gap cost: {e}")

    except ImportError:
        logger.warning("Gap agent not yet implemented, skipping processing")
    except Exception as e:
        logger.error(f"Gap agent failed for digest_id={digest_id}: {e}")


@router.post("/gap-analysis/run")
async def run_gap_analysis(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Trigger gap analyzer for an approved digest."""
    digest_id = payload.get("digest_id")
    if not digest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="digest_id is required",
        )

    client = get_supabase_client()

    digest_result = (
        client.table("market_digests").select("digest_id, status").eq("digest_id", digest_id).execute()
    )
    if not digest_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digest with id {digest_id} not found",
        )

    digest_status = digest_result.data[0].get("status")
    if digest_status not in ("approved", "pending_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Digest must be approved or pending_review to run gap analysis",
        )

    workflow_run_id = str(uuid4())
    background_tasks.add_task(_run_gap_analyzer, digest_id, workflow_run_id)
    return {"workflow_run_id": workflow_run_id, "status": "processing"}


@router.post("/gap-analysis/run-all")
async def run_all_gap_analysis(background_tasks: BackgroundTasks):
    """Trigger gap analyzer for ALL approved but unprocessed digests."""
    client = get_supabase_client()

    try:
        approved = (
            client.table("market_digests")
            .select("digest_id")
            .in_("status", ["approved", "pending_review"])
            .eq("curriculum_relevant", "Yes")
            .execute()
        )

        if not approved.data:
            return {"message": "No approved digests to process", "total": 0}

        digest_ids = [d["digest_id"] for d in approved.data]
        existing_gaps = (
            client.table("curriculum_gaps")
            .select("digest_id")
            .in_("digest_id", digest_ids)
            .execute()
        )
        processed_ids = {g["digest_id"] for g in (existing_gaps.data or [])}
        unprocessed_ids = [did for did in digest_ids if did not in processed_ids]

        if not unprocessed_ids:
            return {"message": "All approved digests already processed", "total": 0}

        results = []
        for digest_id in unprocessed_ids:
            workflow_run_id = str(uuid4())
            background_tasks.add_task(_run_gap_analyzer, digest_id, workflow_run_id)
            results.append(
                {"digest_id": digest_id, "workflow_run_id": workflow_run_id, "status": "processing"}
            )

        return {"batch_results": results, "total": len(results)}

    except Exception as e:
        logger.error(f"Failed to run batch gap analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run batch gap analysis: {e}",
        )


@router.post("/gap-analysis/batch-progress")
async def gap_batch_progress(payload: dict):
    """Check progress for a batch of digest_ids being gap-analyzed."""
    digest_ids = payload.get("digest_ids", [])
    if not digest_ids:
        return {"items": [], "completed": 0, "total": 0}

    client = get_supabase_client()

    digests = client.table("market_digests").select(
        "digest_id, url, topic"
    ).in_("digest_id", digest_ids).execute()
    digest_map = {d["digest_id"]: d for d in (digests.data or [])}

    gaps = client.table("curriculum_gaps").select(
        "digest_id, gap_id, gap_statement, severity, gap_type"
    ).in_("digest_id", digest_ids).execute()

    gap_by_digest: dict[str, list] = {}
    for g in (gaps.data or []):
        did = g["digest_id"]
        if did not in gap_by_digest:
            gap_by_digest[did] = []
        gap_by_digest[did].append(g)

    items = []
    for did in digest_ids:
        d = digest_map.get(did, {})
        found_gaps = gap_by_digest.get(did)
        if found_gaps is not None:
            items.append({
                "digest_id": did,
                "url": d.get("url", ""),
                "topic": d.get("topic", ""),
                "status": "done",
                "gaps_found": len(found_gaps),
                "gaps": found_gaps[:5],
            })
        else:
            items.append({
                "digest_id": did,
                "url": d.get("url", ""),
                "topic": d.get("topic", ""),
                "status": "processing",
                "gaps_found": 0,
                "gaps": [],
            })

    completed = sum(1 for i in items if i["status"] == "done")
    return {"items": items, "completed": completed, "total": len(items)}


@router.get("/gaps", response_model=GapListResponse)
async def list_gaps(
    decision_status: str | None = Query(None, description="Filter by decision status"),
    severity: str | None = Query(None, description="Filter by severity"),
    gap_type: str | None = Query(None, description="Filter by gap type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List gaps with optional filters and severity counts."""
    client = get_supabase_client()

    query = client.table("curriculum_gaps").select("*", count="exact")

    if decision_status is not None:
        query = query.eq("decision_status", decision_status)
    if severity is not None:
        query = query.eq("severity", severity)
    if gap_type is not None:
        query = query.eq("gap_type", gap_type)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    try:
        result = query.execute()
    except Exception as e:
        logger.error(f"Failed to list gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list gaps: {e}",
        )

    by_severity: dict[str, int] = {}
    try:
        all_gaps = client.table("curriculum_gaps").select("severity").execute()
        for gap in all_gaps.data or []:
            sev = gap.get("severity") or "unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1
    except Exception:
        pass

    return GapListResponse(
        items=[GapResponse(**row) for row in result.data],
        total=result.count or len(result.data),
        by_severity=by_severity,
    )


@router.get("/gaps/summary")
async def gap_summary():
    """Return summary stats: total, by_severity, by_type, by_status."""
    client = get_supabase_client()

    try:
        all_gaps = client.table("curriculum_gaps").select("severity, gap_type, decision_status").execute()
    except Exception as e:
        logger.error(f"Failed to get gap summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gap summary: {e}",
        )

    gaps_data = all_gaps.data or []

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}

    for gap in gaps_data:
        sev = gap.get("severity") or "unknown"
        by_severity[sev] = by_severity.get(sev, 0) + 1

        gtype = gap.get("gap_type") or "unknown"
        by_type[gtype] = by_type.get(gtype, 0) + 1

        dstatus = gap.get("decision_status") or "unknown"
        by_status[dstatus] = by_status.get(dstatus, 0) + 1

    return {
        "total": len(gaps_data),
        "by_severity": by_severity,
        "by_type": by_type,
        "by_status": by_status,
    }


@router.get("/gaps/report")
async def gap_report():
    """Get approved gaps as a structured report grouped by severity and type."""
    client = get_supabase_client()

    result = client.table("curriculum_gaps").select("*").eq(
        "decision_status", "approved"
    ).order("severity_score", desc=True).execute()

    gaps = result.data or []

    by_severity: dict[str, list] = {}
    by_type: dict[str, list] = {}
    action_timeline: list[dict] = []

    for g in gaps:
        sev = g.get("severity", "unknown")
        by_severity.setdefault(sev, []).append(g)

        gtype = g.get("gap_type", "unknown")
        by_type.setdefault(gtype, []).append(g)

        action_timeline.append({
            "gap_id": g["gap_id"],
            "gap_statement": g.get("gap_statement"),
            "severity": sev,
            "when_to_act": g.get("when_to_act"),
            "what_to_act": g.get("what_to_act"),
            "impacted_courses": g.get("impacted_courses", []),
            "impacted_sessions": g.get("impacted_sessions", []),
            "impacted_tools": g.get("impacted_tools", []),
        })

    all_courses = set()
    all_sessions = set()
    all_tools = set()
    for g in gaps:
        for c in (g.get("impacted_courses") or []):
            all_courses.add(c)
        for s in (g.get("impacted_sessions") or []):
            all_sessions.add(s)
        for t in (g.get("impacted_tools") or []):
            all_tools.add(t)

    return {
        "total_approved": len(gaps),
        "gaps": [GapResponse(**g).model_dump(mode="json") for g in gaps],
        "by_severity": {k: len(v) for k, v in by_severity.items()},
        "by_type": {k: len(v) for k, v in by_type.items()},
        "action_timeline": sorted(action_timeline, key=lambda x: x.get("when_to_act") or "9999"),
        "impact_summary": {
            "total_courses_affected": len(all_courses),
            "total_sessions_affected": len(all_sessions),
            "total_tools_affected": len(all_tools),
            "courses": sorted(all_courses),
            "sessions": sorted(all_sessions),
            "tools": sorted(all_tools),
        },
    }


@router.get("/gaps/{gap_id}", response_model=GapResponse)
async def get_gap(gap_id: str):
    """Get a single gap with full detail."""
    client = get_supabase_client()

    try:
        result = client.table("curriculum_gaps").select("*").eq("gap_id", gap_id).execute()
    except Exception as e:
        logger.error(f"Failed to get gap {gap_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gap: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap with id {gap_id} not found",
        )

    return GapResponse(**result.data[0])


@router.post("/gaps/{gap_id}/feedback")
async def submit_gap_feedback(gap_id: str, payload: dict):
    """Submit user feedback on what/why/when to act for a gap."""
    client = get_supabase_client()

    existing = client.table("curriculum_gaps").select("gap_id").eq("gap_id", gap_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Gap not found")

    update = {
        "has_feedback": True,
        "feedback_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if "feedback_what" in payload:
        update["feedback_what"] = payload["feedback_what"]
    if "feedback_why" in payload:
        update["feedback_why"] = payload["feedback_why"]
    if "feedback_when" in payload:
        update["feedback_when"] = payload["feedback_when"]

    result = client.table("curriculum_gaps").update(update).eq("gap_id", gap_id).execute()

    try:
        client.table("review_feedback").insert({
            "feedback_type": "gap_action_feedback",
            "feedback_content": f"What: {payload.get('feedback_what', '')}\nWhy: {payload.get('feedback_why', '')}\nWhen: {payload.get('feedback_when', '')}",
            "is_actionable": True,
            "is_processed": False,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to log feedback: {e}")

    return result.data[0] if result.data else {"status": "updated"}


@router.get("/gaps/feedback-history")
async def get_feedback_history():
    """Get all gaps with user feedback for system improvement."""
    client = get_supabase_client()
    result = (
        client.table("curriculum_gaps")
        .select("gap_id, gap_type, gap_statement, what_to_act, why_to_act, when_to_act, feedback_what, feedback_why, feedback_when, severity")
        .eq("has_feedback", True)
        .order("feedback_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"items": result.data or [], "total": len(result.data or [])}


@router.post("/gaps/{gap_id}/review", response_model=GapResponse)
async def review_gap(
    gap_id: str,
    review: GapReviewRequest,
    user: dict = Depends(get_current_user),
):
    """Submit a review decision for a gap."""
    client = get_supabase_client()

    existing = client.table("curriculum_gaps").select("*").eq("gap_id", gap_id).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gap with id {gap_id} not found",
        )

    now = datetime.now(timezone.utc).isoformat()

    update_data = {
        "decision_status": review.decision,
        "updated_at": now,
    }

    if review.edited_fields:
        update_data.update(review.edited_fields)

    try:
        result = (
            client.table("curriculum_gaps")
            .update(update_data)
            .eq("gap_id", gap_id)
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to update gap {gap_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update gap: {e}",
        )

    try:
        client.table("review_decisions").insert({
            "entity_type": "gap",
            "entity_id": gap_id,
            "reviewer_id": user["id"],
            "decision": review.decision,
            "comments": review.comments,
            "edited_fields": review.edited_fields,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to insert review decision record: {e}")

    if review.feedback:
        try:
            client.table("review_feedback").insert({
                "feedback_type": "reviewer_comment",
                "feedback_content": review.feedback,
                "is_actionable": True,
                "is_processed": False,
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to insert review feedback: {e}")

    return GapResponse(**result.data[0])
