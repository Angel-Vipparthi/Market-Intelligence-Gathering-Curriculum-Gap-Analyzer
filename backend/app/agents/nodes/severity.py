import json
from app.agents.nodes._llm import get_llm
from app.agents.prompts.gap_prompts import get_severity_prompt

GAP_TYPES = ["design_gap", "tool_gap", "version_gap", "practice_gap", "project_gap", "assessment_gap", "quiz_gap", "documentation_gap"]

async def gap_type_classifier_node(state):
    gaps = state.get("gap_candidates", [])
    classified = []
    for gap in gaps:
        gap_type = gap.get("gap_type", "design_gap")
        if gap_type not in GAP_TYPES:
            gap_type = "design_gap"
        classified.append({**gap, "gap_type": gap_type})
    return {**state, "classified_gaps": classified}

def calculate_severity(factors: dict) -> tuple[str, float]:
    weights = {
        "industry_adoption": 0.25,
        "deprecation_risk": 0.20,
        "employability_impact": 0.20,
        "assessment_impact": 0.10,
        "project_impact": 0.10,
        "coverage_impact": 0.10,
        "affected_sessions": 0.05,
    }

    score = (
        factors.get("industry_adoption", 0) * weights["industry_adoption"]
        + factors.get("deprecation_risk", 0) * weights["deprecation_risk"]
        + factors.get("employability_impact", 0) * weights["employability_impact"]
        + factors.get("assessment_impact", 0) * weights["assessment_impact"]
        + factors.get("project_impact", 0) * weights["project_impact"]
        + factors.get("coverage_impact", 0) * weights["coverage_impact"]
        + min(factors.get("affected_session_count", 0) / 10, 1.0) * weights["affected_sessions"]
    )

    if score >= 0.8:
        severity = "critical"
    elif score >= 0.6:
        severity = "high"
    elif score >= 0.4:
        severity = "medium"
    else:
        severity = "low"

    return severity, round(score, 3)

async def severity_engine_node(state):
    gaps = state.get("classified_gaps", [])
    llm = get_llm()
    scored = []

    for gap in gaps:
        prompt = get_severity_prompt(
            gap_statement=gap.get("gap_statement", ""),
            gap_type=gap.get("gap_type", ""),
            market_signal=gap.get("market_signal", ""),
            curriculum_evidence=gap.get("curriculum_evidence", ""),
            impacted_courses=str(gap.get("impacted_courses", [])),
            impacted_sessions=str(gap.get("impacted_sessions", [])),
            impacted_projects=str(gap.get("impacted_projects", [])),
            impacted_assessments=str(gap.get("impacted_assessments", [])),
        )

        try:
            response = await llm.ainvoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            factors = json.loads(content)
            severity, score = calculate_severity(factors)

            tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
            tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

            scored.append({
                **gap,
                "severity": severity,
                "severity_score": score,
                "severity_factors": factors,
                "total_tokens": tokens_in + tokens_out,
            })
            state = {**state,
                "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
                "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
            }
        except Exception as e:
            scored.append({**gap, "severity": "medium", "severity_score": 0.5, "severity_factors": {}})

    return {**state, "scored_gaps": scored}
