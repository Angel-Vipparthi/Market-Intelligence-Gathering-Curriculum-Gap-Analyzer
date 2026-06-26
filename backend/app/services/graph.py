import uuid
from app.db.supabase import get_supabase_client
import structlog

logger = structlog.get_logger()


class CurriculumGraph:
    def __init__(self):
        self.db = get_supabase_client()

    def add_node(
        self,
        node_type: str,
        name: str,
        properties: dict = None,
        document_id: str = None,
    ) -> str:
        node_id = str(uuid.uuid4())
        self.db.table("curriculum_graph_nodes").insert({
            "id": node_id,
            "node_type": node_type,
            "name": name,
            "properties": properties or {},
            "document_id": document_id,
        }).execute()
        return node_id

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict = None,
        weight: float = 1.0,
    ) -> str:
        edge_id = str(uuid.uuid4())
        self.db.table("curriculum_graph_edges").upsert({
            "id": edge_id,
            "source_node_id": source_id,
            "target_node_id": target_id,
            "relationship_type": relationship_type,
            "properties": properties or {},
            "weight": weight,
        }).execute()
        return edge_id

    def get_connected_nodes(
        self,
        node_id: str,
        relationship_type: str = None,
        direction: str = "outgoing",
        max_depth: int = 2,
    ) -> list[dict]:
        if direction == "outgoing":
            query = self.db.table("curriculum_graph_edges") \
                .select("*, target:target_node_id(*)") \
                .eq("source_node_id", node_id)
        else:
            query = self.db.table("curriculum_graph_edges") \
                .select("*, source:source_node_id(*)") \
                .eq("target_node_id", node_id)

        if relationship_type:
            query = query.eq("relationship_type", relationship_type)

        result = query.execute()

        nodes = []
        for edge in (result.data or []):
            node = edge.get("target" if direction == "outgoing" else "source")
            if node:
                nodes.append({**node, "relationship": edge["relationship_type"], "weight": edge.get("weight", 1.0)})

        # Recurse for deeper traversal
        if max_depth > 1:
            for node in list(nodes):
                deeper = self.get_connected_nodes(node["id"], relationship_type, direction, max_depth - 1)
                for d in deeper:
                    if d["id"] not in {n["id"] for n in nodes}:
                        nodes.append(d)

        return nodes

    def find_nodes_by_tool(self, tool_name: str) -> list[dict]:
        tool_nodes = self.db.table("curriculum_graph_nodes") \
            .select("*") \
            .eq("node_type", "tool") \
            .ilike("name", f"%{tool_name}%") \
            .execute()

        results = []
        for node in (tool_nodes.data or []):
            connected = self.get_connected_nodes(node["id"], direction="incoming")
            results.extend(connected)

        return results

    def get_impact_subgraph(self, tool_name: str) -> dict:
        affected = self.find_nodes_by_tool(tool_name)

        impact = {
            "courses": [],
            "sessions": [],
            "projects": [],
            "assessments": [],
            "quizzes": [],
            "tools": [tool_name],
        }

        for node in affected:
            nt = node.get("node_type", "")
            name = node.get("name", "")
            if nt == "course" and name not in impact["courses"]:
                impact["courses"].append(name)
            elif nt == "session" and name not in impact["sessions"]:
                impact["sessions"].append(name)
            elif nt == "project" and name not in impact["projects"]:
                impact["projects"].append(name)
            elif nt == "assessment" and name not in impact["assessments"]:
                impact["assessments"].append(name)
            elif nt == "quiz" and name not in impact["quizzes"]:
                impact["quizzes"].append(name)

        return impact


_graph = None


def get_curriculum_graph() -> CurriculumGraph:
    global _graph
    if _graph is None:
        _graph = CurriculumGraph()
    return _graph
