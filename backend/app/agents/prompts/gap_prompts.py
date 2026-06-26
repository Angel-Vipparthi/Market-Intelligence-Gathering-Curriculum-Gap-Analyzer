from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def get_gap_detect_prompt(
    market_signal: str,
    topic: str,
    summary: str,
    evidence_snippet: str,
    tools_versions: str,
    curriculum_context: str,
) -> str:
    template = load_prompt("gap_detector_v1.txt")
    return template.format(
        market_signal=market_signal,
        topic=topic,
        summary=summary,
        evidence_snippet=evidence_snippet,
        tools_versions=tools_versions,
        curriculum_context=curriculum_context,
    )


def get_severity_prompt(
    gap_statement: str,
    gap_type: str,
    market_signal: str,
    curriculum_evidence: str,
    impacted_courses: str,
    impacted_sessions: str,
    impacted_projects: str,
    impacted_assessments: str,
) -> str:
    template = load_prompt("severity_scorer_v1.txt")
    return template.format(
        gap_statement=gap_statement,
        gap_type=gap_type,
        market_signal=market_signal,
        curriculum_evidence=curriculum_evidence,
        impacted_courses=impacted_courses,
        impacted_sessions=impacted_sessions,
        impacted_projects=impacted_projects,
        impacted_assessments=impacted_assessments,
    )


def get_critic_prompt(
    gap_statement: str,
    gap_type: str,
    severity: str,
    market_signal: str,
    evidence_source: str,
    curriculum_evidence: str,
    impact_analysis: str,
) -> str:
    template = load_prompt("critic_v1.txt")
    return template.format(
        gap_statement=gap_statement,
        gap_type=gap_type,
        severity=severity,
        market_signal=market_signal,
        evidence_source=evidence_source,
        curriculum_evidence=curriculum_evidence,
        impact_analysis=impact_analysis,
    )


def get_impact_prompt(
    gap_statement: str,
    tools: str,
    graph_context: str,
    curriculum_list: str,
) -> str:
    template = load_prompt("impact_analyzer_v1.txt")
    return template.format(
        gap_statement=gap_statement,
        tools=tools,
        graph_context=graph_context,
        curriculum_list=curriculum_list,
    )
