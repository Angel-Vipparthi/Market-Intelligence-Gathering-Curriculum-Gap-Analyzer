from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class GapAnalyzerState(TypedDict):
    digest_id: str
    digest_data: Optional[dict]
    curriculum_matches: Optional[list[dict]]
    assessment_matches: Optional[list[dict]]
    graph_context: Optional[list[dict]]
    gap_candidates: Optional[list[dict]]
    classified_gaps: Optional[list[dict]]
    scored_gaps: Optional[list[dict]]
    impact_analyzed_gaps: Optional[list[dict]]
    timed_gaps: Optional[list[dict]]
    action_items: Optional[list[dict]]
    validated_gaps: Optional[list[dict]]
    final_gaps: Optional[list[dict]]
    total_tokens: int
    total_cost: float
    errors: list[str]

from app.agents.nodes.gap_detect import (
    digest_retriever_node, curriculum_retriever_node, graph_lookup_node, gap_candidate_generator_node
)
from app.agents.nodes.severity import gap_type_classifier_node, severity_engine_node
from app.agents.nodes.impact import impact_analyzer_node
from app.agents.nodes.when_to_act import when_to_act_node
from app.agents.nodes.critic import critic_validator_node
from app.agents.nodes.review_gate import gap_review_gate_node

def check_gaps_found(state: GapAnalyzerState) -> str:
    candidates = state.get("gap_candidates", [])
    if not candidates:
        return "end"
    return "gap_type_classifier"

def build_gap_graph():
    graph = StateGraph(GapAnalyzerState)

    graph.add_node("digest_retriever", digest_retriever_node)
    graph.add_node("curriculum_retriever", curriculum_retriever_node)
    graph.add_node("graph_lookup", graph_lookup_node)
    graph.add_node("gap_candidate_generator", gap_candidate_generator_node)
    graph.add_node("gap_type_classifier", gap_type_classifier_node)
    graph.add_node("severity_engine", severity_engine_node)
    graph.add_node("impact_analyzer", impact_analyzer_node)
    graph.add_node("when_to_act", when_to_act_node)
    graph.add_node("critic_validator", critic_validator_node)
    graph.add_node("review_gate", gap_review_gate_node)

    graph.set_entry_point("digest_retriever")
    graph.add_edge("digest_retriever", "curriculum_retriever")
    graph.add_edge("curriculum_retriever", "graph_lookup")
    graph.add_edge("graph_lookup", "gap_candidate_generator")
    graph.add_conditional_edges("gap_candidate_generator", check_gaps_found, {
        "end": END,
        "gap_type_classifier": "gap_type_classifier",
    })
    graph.add_edge("gap_type_classifier", "severity_engine")
    graph.add_edge("severity_engine", "impact_analyzer")
    graph.add_edge("impact_analyzer", "when_to_act")
    graph.add_edge("when_to_act", "critic_validator")
    graph.add_edge("critic_validator", "review_gate")
    graph.add_edge("review_gate", END)

    return graph.compile()

gap_graph = build_gap_graph()

async def run_gap_agent(digest_id: str) -> dict:
    initial_state = GapAnalyzerState(
        digest_id=digest_id,
        digest_data=None, curriculum_matches=None, assessment_matches=None, graph_context=None,
        gap_candidates=None, classified_gaps=None, scored_gaps=None,
        impact_analyzed_gaps=None, timed_gaps=None, action_items=None,
        validated_gaps=None, final_gaps=None,
        total_tokens=0, total_cost=0.0, errors=[],
    )
    result = await gap_graph.ainvoke(initial_state)
    return dict(result)
