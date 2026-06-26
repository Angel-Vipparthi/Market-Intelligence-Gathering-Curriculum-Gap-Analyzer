import json
from app.db.supabase import get_supabase_client
from app.agents.nodes._llm import get_llm
from app.agents.prompts.gap_prompts import get_gap_detect_prompt

async def digest_retriever_node(state):
    db = get_supabase_client()
    result = db.table("market_digests").select("*").eq("digest_id", state["digest_id"]).in_("status", ["approved", "pending_review"]).execute()

    if not result.data:
        return {**state, "errors": state["errors"] + ["Digest not found or not approved"]}

    return {**state, "digest_data": result.data[0]}

async def curriculum_retriever_node(state):
    db = get_supabase_client()
    digest = state.get("digest_data", {})
    tools_versions = digest.get("tools_versions", [])

    matches = []

    # Structured search by tools
    tool_names = [tv.get("tool", "") for tv in tools_versions if tv.get("tool")]
    if tool_names:
        for tool in tool_names:
            result = db.table("curriculum_documents").select("*").contains("tools", [tool]).execute()
            matches.extend(result.data or [])

    # Keyword search by topic using ilike
    topic = digest.get("topic", "")
    if topic:
        keywords = [w for w in topic.split() if len(w) > 3][:3]
        for kw in keywords:
            result = db.table("curriculum_documents").select("*").ilike("content", f"%{kw}%").limit(10).execute()
            matches.extend(result.data or [])

    # Deduplicate
    seen = set()
    unique = []
    for m in matches:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)

    # Search assessments for related questions
    assessment_matches = []
    if topic:
        keywords = [w for w in topic.split() if len(w) > 3][:3]
        for kw in keywords:
            try:
                result = db.table("curriculum_assessments").select(
                    "unit_id, exam_title, exam_type, question_content, question_type"
                ).ilike("question_content", f"%{kw}%").limit(10).execute()
                assessment_matches.extend(result.data or [])
            except Exception:
                pass

    if tool_names:
        for tool in tool_names:
            try:
                result = db.table("curriculum_assessments").select(
                    "unit_id, exam_title, exam_type, question_content, question_type"
                ).ilike("question_content", f"%{tool}%").limit(10).execute()
                assessment_matches.extend(result.data or [])
            except Exception:
                pass

    # Deduplicate assessments
    seen_q = set()
    unique_assessments = []
    for a in assessment_matches:
        key = (a.get("unit_id"), a.get("question_content", "")[:100])
        if key not in seen_q:
            seen_q.add(key)
            unique_assessments.append(a)

    return {**state, "curriculum_matches": unique, "assessment_matches": unique_assessments}

async def graph_lookup_node(state):
    db = get_supabase_client()
    digest = state.get("digest_data", {})
    tools_versions = digest.get("tools_versions", [])

    graph_context = []
    for tv in tools_versions:
        tool = tv.get("tool", "")
        if not tool:
            continue
        nodes = db.table("curriculum_graph_nodes").select("*").ilike("name", f"%{tool}%").execute()
        for node in (nodes.data or []):
            edges = db.table("curriculum_graph_edges").select("*, target:target_node_id(*)").eq("source_node_id", node["id"]).execute()
            graph_context.append({"node": node, "edges": edges.data or []})

    return {**state, "graph_context": graph_context}

def _fetch_feedback_context(db) -> str:
    """Fetch past user feedback on gaps to improve future analysis."""
    try:
        result = (
            db.table("curriculum_gaps")
            .select("gap_type, gap_statement, what_to_act, feedback_what, why_to_act, feedback_why, when_to_act, feedback_when")
            .eq("has_feedback", True)
            .order("feedback_at", desc=True)
            .limit(10)
            .execute()
        )
        if not result.data:
            return ""

        lines = []
        for fb in result.data:
            parts = [f"Gap: {fb.get('gap_statement', '')[:100]}"]
            if fb.get("feedback_what"):
                parts.append(f"  AI said what: {fb.get('what_to_act', '')[:80]} → User corrected: {fb['feedback_what'][:120]}")
            if fb.get("feedback_why"):
                parts.append(f"  AI said why: {fb.get('why_to_act', '')[:80]} → User corrected: {fb['feedback_why'][:120]}")
            if fb.get("feedback_when"):
                parts.append(f"  AI said when: {fb.get('when_to_act', '')} → User corrected: {fb['feedback_when'][:80]}")
            lines.append("\n".join(parts))

        return "\n\n## Past Feedback (learn from these corrections):\n" + "\n---\n".join(lines)
    except Exception:
        return ""


async def gap_candidate_generator_node(state):
    digest = state.get("digest_data", {})
    matches = state.get("curriculum_matches", [])

    curriculum_context = "\n".join([
        f"[{m.get('document_type', 'unknown')}] {m.get('title', '')}: {m.get('content', '')[:500]}"
        for m in matches[:20]
    ])

    assessments = state.get("assessment_matches", [])
    if assessments:
        assessment_context = "\n".join([
            f"[{a.get('exam_type', 'quiz')}] {a.get('exam_title', '')}: {a.get('question_content', '')}"
            for a in assessments[:15]
        ])
        curriculum_context += f"\n\n## Existing Assessments/Quizzes:\n{assessment_context}"

    if not curriculum_context.strip():
        curriculum_context = "No matching curriculum content found."

    db = get_supabase_client()
    feedback_context = _fetch_feedback_context(db)
    if feedback_context:
        curriculum_context += feedback_context

    llm = get_llm()
    prompt = get_gap_detect_prompt(
        market_signal=digest.get("market_signal", ""),
        topic=digest.get("topic", ""),
        summary=digest.get("summary", ""),
        evidence_snippet=digest.get("evidence_snippet", ""),
        tools_versions=json.dumps(digest.get("tools_versions", [])),
        curriculum_context=curriculum_context,
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        gaps = json.loads(content)

        tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

        return {
            **state,
            "gap_candidates": gaps if isinstance(gaps, list) else [],
            "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
        }
    except Exception as e:
        return {**state, "gap_candidates": [], "errors": state["errors"] + [f"Gap detection failed: {e}"]}
