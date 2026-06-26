"""Generate embeddings for all curriculum documents."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client
from app.services.embeddings import embed_curriculum_document


async def main():
    db = get_supabase_client()
    docs = db.table("curriculum_documents").select("id, title, content").eq("is_active", True).execute()

    if not docs.data:
        print("No curriculum documents found. Run seed_curriculum.py first.")
        return

    print(f"Generating embeddings for {len(docs.data)} documents...\n")

    for doc in docs.data:
        try:
            chunks = await embed_curriculum_document(doc["id"], doc["content"])
            print(f"  [{chunks} chunks] {doc['title']}")
        except Exception as e:
            print(f"  [ERROR] {doc['title']}: {e}")

    print(f"\nDone. Embedded {len(docs.data)} documents.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
