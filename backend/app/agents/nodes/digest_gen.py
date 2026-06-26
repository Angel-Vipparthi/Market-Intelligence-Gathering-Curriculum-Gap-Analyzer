import json
from app.agents.nodes._llm import get_llm
from app.agents.prompts.digest_prompts import get_digest_prompt

async def digest_generator_node(state):
    llm = get_llm()
    prompt = get_digest_prompt(
        content=state["raw_content"],
        url=state["url"],
        source_title=state.get("source_title", ""),
        source_type=state.get("source_type", "unknown"),
    )

    try:
        response = await llm.ainvoke(prompt)
        content = response.content

        # Track tokens
        tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

        # Parse JSON from response
        try:
            # Strip markdown code fences if present
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                **state,
                "errors": state["errors"] + ["Failed to parse digest JSON"],
                "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            }

        return {
            **state,
            "topic": data.get("topic", ""),
            "summary": data.get("summary", ""),
            "market_signal": data.get("market_signal", ""),
            "evidence_snippet": data.get("evidence_snippet", ""),
            "status": "generated",
            "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
        }
    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Digest generation failed: {e}"]}
