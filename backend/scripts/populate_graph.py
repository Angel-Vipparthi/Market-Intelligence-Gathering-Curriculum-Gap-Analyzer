"""Populate curriculum knowledge graph with concept-level nodes and prerequisite edges."""
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client


def extract_concepts(content: str) -> list[str]:
    if not content:
        return []
    first_line = content.strip().split("\n")[0]
    return [c.strip() for c in first_line.split(",") if c.strip()]


def batch_insert(db, table, rows, batch_size=50):
    for i in range(0, len(rows), batch_size):
        db.table(table).insert(rows[i:i+batch_size]).execute()


def populate():
    db = get_supabase_client()

    print("Clearing old graph...")
    db.table("curriculum_graph_edges").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    db.table("curriculum_graph_nodes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    docs = db.table("curriculum_documents").select("*").eq("is_active", True).order("created_at").execute()
    if not docs.data:
        print("No curriculum documents found.")
        return

    node_rows = []
    edge_rows = []
    course_nodes = {}
    module_nodes = {}
    concept_nodes = {}
    tool_nodes = {}

    sessions = [d for d in docs.data if d["document_type"] == "session"]
    modules_sessions: dict[str, list] = {}
    for doc in sessions:
        module = doc.get("module_name", "Unknown")
        modules_sessions.setdefault(module, []).append(doc)

    # Course nodes
    for doc in docs.data:
        course = doc.get("course_name")
        if course and course not in course_nodes:
            nid = str(uuid.uuid4())
            course_nodes[course] = nid
            node_rows.append({"id": nid, "node_type": "course", "name": course, "properties": {}})

    # Module nodes
    for doc in docs.data:
        module = doc.get("module_name")
        course = doc.get("course_name")
        if module:
            key = f"{course}::{module}"
            if key not in module_nodes:
                nid = str(uuid.uuid4())
                module_nodes[key] = nid
                node_rows.append({"id": nid, "node_type": "module", "name": module, "properties": {"course": course}})
                if course in course_nodes:
                    edge_rows.append({
                        "id": str(uuid.uuid4()),
                        "source_node_id": nid,
                        "target_node_id": course_nodes[course],
                        "relationship_type": "PART_OF",
                        "properties": {},
                        "weight": 1.0,
                    })

    # Concept (topic) nodes from sessions
    module_order = list(modules_sessions.keys())
    prev_module_last_ids = []

    for module_name in module_order:
        module_sessions = modules_sessions[module_name]
        course = module_sessions[0].get("course_name", "")
        module_key = f"{course}::{module_name}"
        prev_session_ids = []

        for session_doc in module_sessions:
            concepts = extract_concepts(session_doc.get("content", ""))
            current_ids = []

            for concept in concepts:
                norm = concept.lower().strip()
                if norm not in concept_nodes:
                    nid = str(uuid.uuid4())
                    concept_nodes[norm] = nid
                    node_rows.append({
                        "id": nid,
                        "node_type": "topic",
                        "name": concept,
                        "properties": {"session": session_doc["title"], "module": module_name, "course": course},
                        "document_id": session_doc["id"],
                    })
                    if module_key in module_nodes:
                        edge_rows.append({
                            "id": str(uuid.uuid4()),
                            "source_node_id": nid,
                            "target_node_id": module_nodes[module_key],
                            "relationship_type": "PART_OF",
                            "properties": {},
                            "weight": 1.0,
                        })
                current_ids.append(concept_nodes[norm])

            # Prereq: prev session concepts -> current session concepts
            if prev_session_ids:
                # Only link last concept of prev to first concept of current (chain, not cartesian)
                edge_rows.append({
                    "id": str(uuid.uuid4()),
                    "source_node_id": prev_session_ids[-1],
                    "target_node_id": current_ids[0] if current_ids else prev_session_ids[-1],
                    "relationship_type": "PREREQUISITE_OF",
                    "properties": {},
                    "weight": 1.0,
                })

            # Within-session: chain concepts sequentially
            for i in range(len(current_ids) - 1):
                edge_rows.append({
                    "id": str(uuid.uuid4()),
                    "source_node_id": current_ids[i],
                    "target_node_id": current_ids[i + 1],
                    "relationship_type": "PREREQUISITE_OF",
                    "properties": {},
                    "weight": 0.5,
                })

            prev_session_ids = current_ids

        # Cross-module prereq
        if prev_module_last_ids and prev_session_ids:
            pass  # handled below
        if module_sessions:
            first_concepts = extract_concepts(module_sessions[0].get("content", ""))
            first_ids = [concept_nodes[c.lower().strip()] for c in first_concepts if c.lower().strip() in concept_nodes]
            if prev_module_last_ids and first_ids:
                edge_rows.append({
                    "id": str(uuid.uuid4()),
                    "source_node_id": prev_module_last_ids[-1],
                    "target_node_id": first_ids[0],
                    "relationship_type": "PREREQUISITE_OF",
                    "properties": {"cross_module": True},
                    "weight": 1.0,
                })
            last_concepts = extract_concepts(module_sessions[-1].get("content", ""))
            prev_module_last_ids = [concept_nodes[c.lower().strip()] for c in last_concepts if c.lower().strip() in concept_nodes]

    # Tool nodes
    for doc in docs.data:
        tools = doc.get("tools") or []
        for tool in tools:
            if tool not in tool_nodes:
                nid = str(uuid.uuid4())
                tool_nodes[tool] = nid
                node_rows.append({"id": nid, "node_type": "tool", "name": tool, "properties": {}})

        concepts = extract_concepts(doc.get("content", ""))
        for concept in concepts:
            norm = concept.lower().strip()
            if norm in concept_nodes:
                for tool in tools:
                    edge_rows.append({
                        "id": str(uuid.uuid4()),
                        "source_node_id": concept_nodes[norm],
                        "target_node_id": tool_nodes[tool],
                        "relationship_type": "USES_TOOL",
                        "properties": {},
                        "weight": 1.0,
                    })

    # Deduplicate edges by (source, target, relationship)
    seen_edges = set()
    deduped_edges = []
    for e in edge_rows:
        key = (e["source_node_id"], e["target_node_id"], e["relationship_type"])
        if key not in seen_edges:
            seen_edges.add(key)
            deduped_edges.append(e)
    edge_rows = deduped_edges

    print(f"Inserting {len(node_rows)} nodes...")
    batch_insert(db, "curriculum_graph_nodes", node_rows)

    print(f"Inserting {len(edge_rows)} edges...")
    batch_insert(db, "curriculum_graph_edges", edge_rows)

    print(f"\nGraph populated:")
    print(f"  Courses: {len(course_nodes)}")
    print(f"  Modules: {len(module_nodes)}")
    print(f"  Concepts (topics): {len(concept_nodes)}")
    print(f"  Tools: {len(tool_nodes)}")
    print(f"  Total nodes: {len(node_rows)}")
    print(f"  Total edges: {len(edge_rows)}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    populate()
