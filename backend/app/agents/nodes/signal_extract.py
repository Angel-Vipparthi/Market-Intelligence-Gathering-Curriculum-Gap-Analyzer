import json
from app.agents.nodes._llm import get_llm

SIGNAL_PROMPT = """Classify the primary market signal for this content.

Topic: {topic}
Summary: {summary}

Signal types: new_release, deprecation, breaking_change, best_practice_change, security_update, new_tool, trend_shift, performance_improvement

Return JSON only:
{{"market_signal": "type", "confidence": 0.85}}"""

async def market_signal_extractor_node(state):
    if state.get("market_signal"):
        return state

    llm = get_llm()
    prompt = SIGNAL_PROMPT.format(topic=state.get("topic", ""), summary=state.get("summary", ""))

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
            "market_signal": data.get("market_signal", state.get("market_signal", "")),
            "confidence": data.get("confidence", state.get("confidence", 0.5)),
            "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
        }
    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Signal extraction failed: {e}"]}
