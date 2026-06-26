"""Embedding generation via OpenRouter (OpenAI-compatible API)."""

from openai import AsyncOpenAI
from app.config import settings
from app.db.supabase import get_supabase_client
import structlog

logger = structlog.get_logger()

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


async def generate_embedding(text: str) -> list[float]:
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text[:8000],
    )
    return response.data[0].embedding


async def embed_curriculum_document(
    doc_id: str, content: str, chunk_size: int = 1000
) -> int:
    db = get_supabase_client()

    chunks = []
    words = content.split()
    current_chunk = []
    current_len = 0

    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    db.table("curriculum_embeddings").delete().eq("document_id", doc_id).execute()

    for i, chunk in enumerate(chunks):
        try:
            embedding = await generate_embedding(chunk)
            db.table("curriculum_embeddings").insert({
                "document_id": doc_id,
                "embedding": embedding,
                "chunk_index": i,
                "chunk_text": chunk,
            }).execute()
        except Exception as e:
            logger.error("embedding_failed", doc_id=doc_id, chunk=i, error=str(e))

    return len(chunks)
