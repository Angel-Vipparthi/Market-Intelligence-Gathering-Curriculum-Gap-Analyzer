"""Populate curriculum knowledge graph from curriculum documents."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client
from app.services.graph import CurriculumGraph


def populate():
    db = get_supabase_client()
    graph = CurriculumGraph()

    # Clear existing graph
    db.table("curriculum_graph_edges").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    db.table("curriculum_graph_nodes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    docs = db.table("curriculum_documents").select("*").eq("is_active", True).execute()
    if not docs.data:
        print("No curriculum documents found. Run seed_curriculum.py first.")
        return

    # Track created nodes to avoid duplicates
    course_nodes = {}
    module_nodes = {}
    tool_nodes = {}
    doc_nodes = {}

    for doc in docs.data:
        # Map document types to valid graph node types
        node_type = doc["document_type"]
        if node_type == "tool_registry":
            node_type = "tool"

        doc_node_id = graph.add_node(
            node_type=node_type,
            name=doc["title"],
            properties={"difficulty": doc.get("difficulty"), "versions": doc.get("versions", {})},
            document_id=doc["id"],
        )
        doc_nodes[doc["id"]] = doc_node_id
        print(f"  Node: [{doc['document_type']}] {doc['title']}")

        # Create/link course
        course = doc.get("course_name")
        if course:
            if course not in course_nodes:
                course_nodes[course] = graph.add_node("course", course)
                print(f"  Node: [course] {course}")
            graph.add_edge(doc_node_id, course_nodes[course], "PART_OF")

        # Create/link module
        module = doc.get("module_name")
        if module:
            key = f"{course}::{module}"
            if key not in module_nodes:
                module_nodes[key] = graph.add_node("module", module, properties={"course": course})
                print(f"  Node: [module] {module}")
                if course and course in course_nodes:
                    graph.add_edge(module_nodes[key], course_nodes[course], "PART_OF")
            graph.add_edge(doc_node_id, module_nodes[key], "PART_OF")

        # Create/link tools
        tools = doc.get("tools") or []
        versions = doc.get("versions") or {}
        for tool in tools:
            if tool not in tool_nodes:
                tool_nodes[tool] = graph.add_node(
                    "tool", tool,
                    properties={"current_version": versions.get(tool)},
                )
                print(f"  Node: [tool] {tool}")
            graph.add_edge(doc_node_id, tool_nodes[tool], "USES_TOOL")

            # Create version node if version exists
            version = versions.get(tool)
            if version:
                version_key = f"{tool}::{version}"
                version_node = graph.add_node(
                    "version", f"{tool} {version}",
                    properties={"tool": tool, "version": version},
                )
                graph.add_edge(doc_node_id, version_node, "USES_VERSION")
                graph.add_edge(version_node, tool_nodes[tool], "PART_OF")

        # Link assessments/quizzes to what they test
        if doc["document_type"] in ("assessment", "quiz", "coding_challenge"):
            for tool in tools:
                if tool in tool_nodes:
                    graph.add_edge(tool_nodes[tool], doc_node_id, "TESTED_BY")

        if doc["document_type"] == "project":
            for tool in tools:
                if tool in tool_nodes:
                    graph.add_edge(doc_node_id, tool_nodes[tool], "IMPLEMENTS")

    total_nodes = len(doc_nodes) + len(course_nodes) + len(module_nodes) + len(tool_nodes)
    print(f"\nGraph populated: {total_nodes} nodes created.")
    print(f"  Courses: {len(course_nodes)}")
    print(f"  Modules: {len(module_nodes)}")
    print(f"  Documents: {len(doc_nodes)}")
    print(f"  Tools: {len(tool_nodes)}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    populate()
