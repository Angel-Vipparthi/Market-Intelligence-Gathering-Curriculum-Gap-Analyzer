import json
from urllib.parse import urlparse
from app.db.supabase import get_supabase_client
from app.services.extraction import extract_content

async def url_intake_node(state):
    url = state["url"]
    db = get_supabase_client()

    existing = db.table("market_digests").select("digest_id").eq("url", url).execute()
    if existing.data:
        return {**state, "status": "duplicate", "errors": state["errors"] + ["URL already processed"]}

    if not url.startswith(("http://", "https://")):
        return {**state, "extraction_status": "failed", "errors": state["errors"] + ["Invalid URL format"]}

    return {**state, "status": "pending"}

async def content_extraction_node(state):
    try:
        result = await extract_content(state["url"])
        return {
            **state,
            "raw_content": result["content"][:15000],
            "source_title": result.get("title", ""),
            "extraction_status": "success",
            "status": "extracted",
        }
    except Exception as e:
        return {
            **state,
            "extraction_status": "failed",
            "extraction_error": str(e),
            "errors": state["errors"] + [f"Extraction failed: {e}"],
        }

async def error_handler_node(state):
    db = get_supabase_client()
    db.table("extracted_content").insert({
        "url_id": state["url_id"],
        "url": state["url"],
        "extraction_status": "failed",
        "error_message": state.get("extraction_error", "Unknown error"),
    }).execute()
    return {**state, "status": "failed"}
