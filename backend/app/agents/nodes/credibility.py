from urllib.parse import urlparse
from app.db.supabase import get_supabase_client

CREDIBILITY_TIERS = {
    "official_docs": 0.95,
    "major_blog": 0.85,
    "tech_publication": 0.80,
    "personal_blog": 0.60,
    "social_media": 0.40,
    "unknown": 0.50,
}

async def source_credibility_node(state):
    db = get_supabase_client()
    domain = urlparse(state["url"]).netloc.lower()

    registry = db.table("url_registry").select("credibility_tier").eq("domain", domain).execute()

    tier = "unknown"
    if registry.data:
        tier = registry.data[0].get("credibility_tier", "unknown")

    return {
        **state,
        "source_type": tier,
        "credibility_score": CREDIBILITY_TIERS.get(tier, 0.50),
    }
