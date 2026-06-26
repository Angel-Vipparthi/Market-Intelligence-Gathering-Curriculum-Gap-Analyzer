from datetime import date, timedelta

SEVERITY_OFFSETS = {
    "critical": 7,
    "high": 30,
    "medium": 90,
    "low": 180,
}

async def when_to_act_node(state):
    gaps = state.get("impact_analyzed_gaps", [])
    today = date.today()
    timed = []

    for gap in gaps:
        severity = gap.get("severity", "medium")
        offset = SEVERITY_OFFSETS.get(severity, 90)
        action_date = today + timedelta(days=offset)

        rationale = f"{severity.capitalize()} severity: action within {offset} days. "
        if severity == "critical":
            rationale += "Immediate attention needed — deprecated or breaking change."
        elif severity == "high":
            rationale += "High industry adoption — schedule within next sprint."
        elif severity == "medium":
            rationale += "Growing trend — plan for next quarter."
        else:
            rationale += "Low urgency — include in next review cycle."

        timed.append({
            **gap,
            "when_to_act": action_date.isoformat(),
            "when_to_act_rationale": rationale,
        })

    return {**state, "timed_gaps": timed}
