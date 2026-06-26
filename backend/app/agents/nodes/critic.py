import json
from app.agents.nodes._llm import get_llm
from app.agents.prompts.gap_prompts import get_critic_prompt

async def critic_validator_node(state):
    gaps = state.get("timed_gaps", [])
    llm = get_llm()
    validated = []

    for gap in gaps:
        prompt = get_critic_prompt(
            gap_statement=gap.get("gap_statement", ""),
            gap_type=gap.get("gap_type", ""),
            severity=gap.get("severity", ""),
            market_signal=gap.get("market_signal", ""),
            evidence_source=state.get("digest_data", {}).get("url", ""),
            curriculum_evidence=gap.get("curriculum_evidence", ""),
            impact_analysis=json.dumps({
                "courses": gap.get("impacted_courses", []),
                "sessions": gap.get("impacted_sessions", []),
                "projects": gap.get("impacted_projects", []),
            }),
        )

        try:
            response = await llm.ainvoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            review = json.loads(content)

            tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
            tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

            if review.get("is_valid", True):
                if review.get("severity_adjustment") == "downgrade":
                    gap["severity"] = review.get("revised_severity", gap["severity"])
                elif review.get("severity_adjustment") == "upgrade":
                    gap["severity"] = review.get("revised_severity", gap["severity"])

                validated.append({
                    **gap,
                    "critic_feedback": [review],
                })

            state = {**state,
                "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
                "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
            }
        except Exception as e:
            validated.append({**gap, "critic_feedback": [{"error": str(e)}]})

    return {**state, "validated_gaps": validated}
