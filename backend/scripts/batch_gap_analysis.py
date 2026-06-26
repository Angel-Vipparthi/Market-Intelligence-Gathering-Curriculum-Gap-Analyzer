"""
Batch run gap analysis on all pending_review digests that have curriculum_relevant = 'Yes'.
Usage: cd backend && python -m scripts.batch_gap_analysis
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client
from app.agents.gap_agent import run_gap_agent


async def main():
    db = get_supabase_client()

    print("Fetching curriculum-relevant digests...")
    result = db.table("market_digests").select("digest_id, url, topic, curriculum_relevant, status").eq("curriculum_relevant", "Yes").in_("status", ["pending_review", "approved"]).execute()

    digests = result.data or []
    print(f"Found {len(digests)} curriculum-relevant digests to analyze.\n")

    if not digests:
        print("No digests to process.")
        return

    success = 0
    failed = 0
    no_gaps = 0

    for i, d in enumerate(digests):
        digest_id = d["digest_id"]
        topic = d.get("topic", "Unknown")
        url = d.get("url", "")
        print(f"[{i+1}/{len(digests)}] {topic}")
        print(f"  URL: {url}")

        try:
            result = await run_gap_agent(digest_id=digest_id)
            errors = result.get("errors", [])
            final_gaps = result.get("final_gaps", [])
            validated = result.get("validated_gaps", [])

            if errors:
                print(f"  ERRORS: {errors}")
                failed += 1
            elif not final_gaps and not validated:
                print(f"  No gaps found")
                no_gaps += 1
            else:
                gap_count = len(final_gaps) if final_gaps else len(validated)
                for g in (final_gaps or validated or []):
                    print(f"  GAP: [{g.get('severity', '?')}] {g.get('gap_statement', '')[:80]}")
                print(f"  Total gaps: {gap_count}")
                success += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

        print()

    print("=" * 60)
    print(f"DONE: {success} with gaps | {no_gaps} no gaps | {failed} failed | {len(digests)} total")


if __name__ == "__main__":
    asyncio.run(main())
