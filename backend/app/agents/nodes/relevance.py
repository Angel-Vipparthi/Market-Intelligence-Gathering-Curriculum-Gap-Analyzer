import json
from app.agents.nodes._llm import get_llm

RELEVANCE_PROMPT = """Determine if this content is relevant to a technology curriculum (frontend, backend, devops, testing, CSS, databases).

Topic: {topic}
Summary: {summary}
Tools: {tools}

Return JSON only:
{{"curriculum_relevant": "Yes", "relevance_reason": "Why this is/isn't relevant to curriculum"}}

curriculum_relevant must be exactly "Yes" or "No"."""

async def relevance_classifier_node(state):
    llm = get_llm()
    tools_str = ", ".join([t.get("tool", "") for t in (state.get("tools_versions") or [])])
    prompt = RELEVANCE_PROMPT.format(
        topic=state.get("topic", ""),
        summary=state.get("summary", ""),
        tools=tools_str or "None detected",
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(content)

        tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

        return {
            **state,
            "curriculum_relevant": data.get("curriculum_relevant", "No"),
            "relevance_reason": data.get("relevance_reason", ""),
            "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
        }
    except Exception as e:
        return {**state, "curriculum_relevant": "No", "errors": state["errors"] + [f"Relevance scoring failed: {e}"]}

async def archive_node(state):
    return {**state, "status": "archived"}
