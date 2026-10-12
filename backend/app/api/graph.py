import logging

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/courses")
async def list_graph_courses():
    """List distinct courses available in the graph."""
    client = get_supabase_client()
    result = client.table("curriculum_graph_nodes").select("name").eq("node_type", "course").execute()
    courses = sorted(set(n["name"] for n in (result.data or [])))
    return {"courses": courses}


@router.get("")
async def get_graph_overview(
    course: str | None = Query(None, description="Filter graph to a specific course"),
):
    """Get knowledge graph stats and all nodes/edges for visualization."""
    client = get_supabase_client()

    nodes_query = client.table("curriculum_graph_nodes").select("*")
    edges_query = client.table("curriculum_graph_edges").select("*")

    if course:
        course_node = client.table("curriculum_graph_nodes").select("id").eq("node_type", "course").eq("name", course).execute()
        if not course_node.data:
            return {"total_nodes": 0, "total_edges": 0, "nodes_by_type": {}, "edges_by_relationship": {}, "nodes": [], "edges": []}

        course_id = course_node.data[0]["id"]
        connected_edges = client.table("curriculum_graph_edges").select("source_node_id, target_node_id").or_(
            f"source_node_id.eq.{course_id},target_node_id.eq.{course_id}"
        ).execute()

        connected_ids = {course_id}
        for e in (connected_edges.data or []):
            connected_ids.add(e["source_node_id"])
            connected_ids.add(e["target_node_id"])

        all_edges = client.table("curriculum_graph_edges").select("source_node_id, target_node_id").execute()
        changed = True
        while changed:
            changed = False
            for e in (all_edges.data or []):
                if e["source_node_id"] in connected_ids and e["target_node_id"] not in connected_ids:
                    connected_ids.add(e["target_node_id"])
                    changed = True
                elif e["target_node_id"] in connected_ids and e["source_node_id"] not in connected_ids:
                    connected_ids.add(e["source_node_id"])
                    changed = True

        nodes_data_raw = client.table("curriculum_graph_nodes").select("*").execute()
        nodes_data = [n for n in (nodes_data_raw.data or []) if n["id"] in connected_ids]
        node_ids = {n["id"] for n in nodes_data}
        edges_data = [e for e in (all_edges.data or [])
                      if e["source_node_id"] in node_ids and e["target_node_id"] in node_ids]
        edges_full = client.table("curriculum_graph_edges").select("*").execute()
        edges_data = [e for e in (edges_full.data or [])
                      if e["source_node_id"] in node_ids and e["target_node_id"] in node_ids]
    else:
        nodes_result = nodes_query.execute()
        edges_result = edges_query.execute()
        nodes_data = nodes_result.data or []
        edges_data = edges_result.data or []

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
