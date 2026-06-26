import uuid
from app.db.supabase import get_supabase_client

async def digest_review_gate_node(state):
    db = get_supabase_client()
    digest_id = str(uuid.uuid4())

    db.table("market_digests").insert({
        "digest_id": digest_id,
        "url_id": state["url_id"],
        "url": state["url"],
        "source_title": state.get("source_title"),
        "source_type": state.get("source_type"),
        "topic": state.get("topic"),
        "summary": state.get("summary"),
        "market_signal": state.get("market_signal"),
        "evidence_snippet": state.get("evidence_snippet"),
        "tools_versions": state.get("tools_versions", []),
        "curriculum_relevant": state.get("curriculum_relevant", "No"),
        "relevance_reason": state.get("relevance_reason"),
        "credibility_score": state.get("credibility_score"),
        "status": "pending_review",
        "total_tokens": state.get("total_tokens", 0),
        "total_cost": state.get("total_cost", 0),
    }).execute()

    return {**state, "digest_id": digest_id, "status": "pending_review"}

async def gap_review_gate_node(state):
    db = get_supabase_client()
    gaps = state.get("validated_gaps", [])
    final = []

    for gap in gaps:
        gap_id = str(uuid.uuid4())
        record = {
            "gap_id": gap_id,
            "digest_id": state["digest_id"],
            "gap_type": gap.get("gap_type", "design_gap"),
            "market_signal": gap.get("market_signal", ""),
            "curriculum_evidence": gap.get("curriculum_evidence", ""),
            "gap_statement": gap.get("gap_statement", ""),
            "what_to_act": gap.get("what_to_act", ""),
            "why_to_act": gap.get("why_to_act", ""),
            "when_to_act": gap.get("when_to_act"),
            "when_to_act_rationale": gap.get("when_to_act_rationale", ""),
            "severity": gap.get("severity", "medium"),
            "severity_score": gap.get("severity_score", 0.5),
            "severity_factors": gap.get("severity_factors", {}),
            "impacted_content_area": gap.get("impacted_content_area", ""),
            "impacted_courses": gap.get("impacted_courses", []),
            "impacted_sessions": gap.get("impacted_sessions", []),
            "impacted_projects": gap.get("impacted_projects", []),
            "impacted_assessments": gap.get("impacted_assessments", []),
            "impacted_quizzes": gap.get("impacted_quizzes", []),
            "impacted_tools": gap.get("impacted_tools", []),
            "evidence_source": state.get("digest_data", {}).get("url", ""),
            "critic_feedback": gap.get("critic_feedback", []),
            "decision_status": "pending_review",
            "total_tokens": gap.get("total_tokens", 0),
            "total_cost": state.get("total_cost", 0),
        }
        db.table("curriculum_gaps").insert(record).execute()
        final.append({**record, "gap_id": gap_id})

    return {**state, "final_gaps": final}
