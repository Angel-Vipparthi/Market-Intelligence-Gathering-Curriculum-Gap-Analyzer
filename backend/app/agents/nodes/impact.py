import json
from app.agents.nodes._llm import get_llm
from app.agents.prompts.gap_prompts import get_impact_prompt

async def impact_analyzer_node(state):
    gaps = state.get("scored_gaps", [])
    graph_context = state.get("graph_context", [])
    curriculum_matches = state.get("curriculum_matches", [])
    llm = get_llm()

    analyzed = []
    for gap in gaps:
        tools = [tv.get("tool", "") for tv in (state.get("digest_data", {}).get("tools_versions", []))]

        graph_str = json.dumps(graph_context[:10], default=str) if graph_context else "No graph data"
        curriculum_str = "\n".join([f"- {m.get('title', '')} ({m.get('document_type', '')})" for m in curriculum_matches[:30]])

        prompt = get_impact_prompt(
            gap_statement=gap.get("gap_statement", ""),
            tools=", ".join(tools),
            graph_context=graph_str,
            curriculum_list=curriculum_str or "No curriculum data",
        )

        try:
            response = await llm.ainvoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            impact = json.loads(content)

            tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
            tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

            analyzed.append({
                **gap,
                "impacted_courses": impact.get("impacted_courses", []),
                "impacted_sessions": impact.get("impacted_sessions", []),
                "impacted_projects": impact.get("impacted_projects", []),
                "impacted_assessments": impact.get("impacted_assessments", []),
                "impacted_quizzes": impact.get("impacted_quizzes", []),
                "impacted_tools": impact.get("impacted_tools", []),
                "impacted_content_area": impact.get("impact_summary", ""),
            })
            state = {**state,
                "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
                "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
            }
        except Exception as e:
            analyzed.append({**gap, "impacted_courses": [], "impacted_sessions": [], "impacted_projects": [], "impacted_assessments": [], "impacted_quizzes": [], "impacted_tools": []})

    return {**state, "impact_analyzed_gaps": analyzed}
