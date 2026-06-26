import logging

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_graph_overview():
    """Get knowledge graph stats and all nodes/edges for visualization."""
    client = get_supabase_client()

    nodes = client.table("curriculum_graph_nodes").select("*").execute()
    edges = client.table("curriculum_graph_edges").select("*").execute()

    nodes_data = nodes.data or []
    edges_data = edges.data or []

    by_type = {}
    for n in nodes_data:
        t = n.get("node_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    by_rel = {}
    for e in edges_data:
        r = e.get("relationship_type", "unknown")
        by_rel[r] = by_rel.get(r, 0) + 1

    return {
        "total_nodes": len(nodes_data),
        "total_edges": len(edges_data),
        "nodes_by_type": by_type,
        "edges_by_relationship": by_rel,
        "nodes": [
            {
                "id": n["id"],
                "type": n["node_type"],
                "name": n["name"],
                "properties": n.get("properties"),
                "document_id": n.get("document_id"),
            }
            for n in nodes_data
        ],
        "edges": [
            {
                "id": e["id"],
                "source": e["source_node_id"],
                "target": e["target_node_id"],
                "relationship": e["relationship_type"],
                "weight": e.get("weight", 1.0),
            }
            for e in edges_data
        ],
    }


@router.get("/nodes")
async def list_nodes(
    node_type: str | None = Query(None, description="Filter by node type"),
    limit: int = Query(100, ge=1, le=500),
):
    """List graph nodes with optional type filter."""
    client = get_supabase_client()
    query = client.table("curriculum_graph_nodes").select("*")
    if node_type:
        query = query.eq("node_type", node_type)
    query = query.limit(limit)
    result = query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/impact/{tool_name}")
async def get_tool_impact(tool_name: str):
    """Get impact subgraph for a specific tool — shows all connected curriculum items."""
    from app.services.graph import get_curriculum_graph
    graph = get_curriculum_graph()
    impact = graph.get_impact_subgraph(tool_name)
    return impact
