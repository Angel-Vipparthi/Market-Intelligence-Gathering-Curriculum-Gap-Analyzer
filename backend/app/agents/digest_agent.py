from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END

class DigestState(TypedDict):
    url: str
    url_id: str
    raw_content: Optional[str]
    extraction_status: Literal["pending", "success", "failed"]
    extraction_error: Optional[str]
    source_title: Optional[str]
    source_type: Optional[str]
    credibility_score: Optional[float]
    digest_id: Optional[str]
    topic: Optional[str]
    summary: Optional[str]
    market_signal: Optional[str]
    evidence_snippet: Optional[str]
    tools_versions: Optional[list[dict]]
    curriculum_relevant: Optional[str]
    relevance_reason: Optional[str]
    status: Literal["pending", "extracted", "generated", "pending_review", "approved", "rejected"]
    total_tokens: int
    total_cost: float
    errors: list[str]
    retry_count: int

# Import all nodes
from app.agents.nodes.extraction import url_intake_node, content_extraction_node, error_handler_node
from app.agents.nodes.credibility import source_credibility_node
from app.agents.nodes.digest_gen import digest_generator_node
from app.agents.nodes.tool_extract import tool_version_extractor_node
from app.agents.nodes.signal_extract import market_signal_extractor_node
from app.agents.nodes.relevance import relevance_classifier_node, archive_node
from app.agents.nodes.review_gate import digest_review_gate_node

def check_extraction(state: DigestState) -> str:
    if state.get("extraction_status") == "failed":
        return "error_handler"
    return "source_credibility"

def check_relevance(state: DigestState) -> str:
    relevant = state.get("curriculum_relevant", "No")
    if relevant != "Yes":
        return "archive"
    return "review_gate"

def build_digest_graph():
    graph = StateGraph(DigestState)

    graph.add_node("url_intake", url_intake_node)
    graph.add_node("content_extraction", content_extraction_node)
    graph.add_node("error_handler", error_handler_node)
    graph.add_node("source_credibility", source_credibility_node)
    graph.add_node("digest_generator", digest_generator_node)
    graph.add_node("tool_version_extractor", tool_version_extractor_node)
    graph.add_node("market_signal_extractor", market_signal_extractor_node)
    graph.add_node("relevance_classifier", relevance_classifier_node)
    graph.add_node("archive", archive_node)
    graph.add_node("review_gate", digest_review_gate_node)

    graph.set_entry_point("url_intake")
    graph.add_edge("url_intake", "content_extraction")
    graph.add_conditional_edges("content_extraction", check_extraction, {
        "error_handler": "error_handler",
        "source_credibility": "source_credibility",
    })
    graph.add_edge("error_handler", END)
    graph.add_edge("source_credibility", "digest_generator")
    graph.add_edge("digest_generator", "tool_version_extractor")
    graph.add_edge("tool_version_extractor", "market_signal_extractor")
    graph.add_edge("market_signal_extractor", "relevance_classifier")
    graph.add_conditional_edges("relevance_classifier", check_relevance, {
        "archive": "archive",
        "review_gate": "review_gate",
    })
    graph.add_edge("archive", END)
    graph.add_edge("review_gate", END)

    return graph.compile()

digest_graph = build_digest_graph()

async def run_digest_agent(url: str, url_id: str) -> dict:
    initial_state = DigestState(
        url=url, url_id=url_id,
        raw_content=None, extraction_status="pending", extraction_error=None,
        source_title=None, source_type=None, credibility_score=None,
        digest_id=None, topic=None, summary=None,
        market_signal=None, evidence_snippet=None,
        tools_versions=None, curriculum_relevant=None, relevance_reason=None,
        status="pending",
        total_tokens=0, total_cost=0.0,
        errors=[], retry_count=0,
    )
    result = await digest_graph.ainvoke(initial_state)
    return dict(result)
