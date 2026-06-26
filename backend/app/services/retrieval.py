import json
from app.db.supabase import get_supabase_client
from app.services.embeddings import generate_embedding
import structlog

logger = structlog.get_logger()


class HybridRetriever:
    def __init__(self):
        self.db = get_supabase_client()

    async def structured_search(self, tools: list[str], versions: dict = None) -> list[dict]:
        results = []
        for tool in tools:
            query = self.db.table("curriculum_documents") \
                .select("*") \
                .contains("tools", [tool]) \
                .eq("is_active", True) \
                .limit(20)
            result = query.execute()
            results.extend(result.data or [])
        return results

    async def semantic_search(self, query_text: str, limit: int = 10) -> list[dict]:
        try:
            embedding = await generate_embedding(query_text)
            result = self.db.rpc(
                "match_curriculum",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.7,
                    "match_count": limit,
                },
            ).execute()

            if not result.data:
                return []

            doc_ids = [r["document_id"] for r in result.data]
            docs = self.db.table("curriculum_documents") \
                .select("*") \
                .in_("id", doc_ids) \
                .execute()

            similarity_map = {r["document_id"]: r["similarity"] for r in result.data}
            for doc in (docs.data or []):
                doc["similarity_score"] = similarity_map.get(doc["id"], 0)

            return docs.data or []
        except Exception as e:
            logger.error("semantic_search_failed", error=str(e))
            return []

    async def graph_search(self, tool_name: str) -> list[dict]:
        try:
            nodes = self.db.table("curriculum_graph_nodes") \
                .select("*") \
                .ilike("name", f"%{tool_name}%") \
                .execute()

            results = []
            for node in (nodes.data or []):
                edges = self.db.table("curriculum_graph_edges") \
                    .select("*, target:target_node_id(id, node_type, name, properties)") \
                    .eq("source_node_id", node["id"]) \
                    .execute()

                for edge in (edges.data or []):
                    target = edge.get("target")
                    if target and target.get("document_id"):
                        doc = self.db.table("curriculum_documents") \
                            .select("*") \
                            .eq("id", target["document_id"]) \
                            .execute()
                        if doc.data:
                            results.extend(doc.data)

            return results
        except Exception as e:
            logger.error("graph_search_failed", error=str(e))
            return []

    async def hybrid_retrieve(self, digest: dict) -> list[dict]:
        tools_versions = digest.get("tools_versions", [])
        tool_names = [tv.get("tool", "") for tv in tools_versions if tv.get("tool")]
        topic = digest.get("topic", "")
        summary = digest.get("summary", "")

        structured_results = await self.structured_search(tool_names) if tool_names else []
        semantic_results = await self.semantic_search(f"{topic} {summary}") if topic else []

        graph_results = []
        for tool in tool_names:
            graph_results.extend(await self.graph_search(tool))

        # Deduplicate by document id
        seen = set()
        combined = []
        for doc in structured_results + semantic_results + graph_results:
            doc_id = doc.get("id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                combined.append(doc)

        return combined


_retriever = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
