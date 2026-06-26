"""
Batch process 97 URLs through the digest agent.
Looks up url_ids from url_registry, then runs digest agent for each.
Usage: cd backend && python -m scripts.batch_digest_97urls
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase import get_supabase_client
from app.agents.digest_agent import run_digest_agent

URLS = [
    "https://react.dev/blog/2024/04/25/react-19",
    "https://react.dev/blog/2024/12/05/react-19",
    "https://react.dev/blog/2025/02/14/sunsetting-create-react-app",
    "https://react.dev/blog/2024/02/15/react-labs-what-we-have-been-working-on-february-2024",
    "https://react.dev/reference/react/use",
    "https://react.dev/reference/react/useActionState",
    "https://react.dev/reference/react/useOptimistic",
    "https://react.dev/reference/react/Suspense",
    "https://react.dev/reference/rsc/server-components",
    "https://react.dev/reference/rsc/server-functions",
    "https://react.dev/learn/passing-data-deeply-with-context",
    "https://react.dev/reference/react/useTransition",
    "https://react.dev/reference/react-dom/hooks/useFormStatus",
    "https://react.dev/reference/react/useId",
    "https://react.dev/learn/typescript",
    "https://react.dev/learn/react-compiler",
    "https://react.dev/learn/keeping-components-pure",
    "https://react.dev/learn/you-might-not-need-an-effect",
    "https://react.dev/learn/managing-state",
    "https://react.dev/learn/render-and-commit",
    "https://react.dev/learn/tutorial-tic-tac-toe",
    "https://react.dev/learn/thinking-in-react",
    "https://react.dev/learn/start-a-new-react-project",
    "https://react.dev/reference/react/lazy",
    "https://react.dev/reference/react/memo",
    "https://react.dev/reference/react/useCallback",
    "https://react.dev/reference/react/useMemo",
    "https://react.dev/reference/react/useDeferredValue",
    "https://react.dev/reference/react-dom/client/hydrateRoot",
    "https://react.dev/reference/react-dom/components/form",
    "https://react.dev/reference/react/forwardRef",
    "https://react.dev/reference/react/useRef",
    "https://react.dev/reference/react/useContext",
    "https://react.dev/reference/react/useReducer",
    "https://react.dev/reference/react/useState",
    "https://react.dev/reference/react/useEffect",
    "https://react.dev/learn/synchronizing-with-effects",
    "https://react.dev/learn/lifecycle-of-reactive-effects",
    "https://react.dev/reference/react/Component",
    "https://react.dev/learn/manipulating-the-dom-with-refs",
    "https://react.dev/learn/conditional-rendering",
    "https://react.dev/learn/rendering-lists",
    "https://react.dev/reference/react/Fragment",
    "https://react.dev/reference/react/Children",
    "https://react.dev/learn/extracting-state-logic-into-a-reducer",
    "https://react.dev/learn/scaling-up-with-reducer-and-context",
    "https://react.dev/learn/escape-hatches",
    "https://react.dev/learn/reusing-logic-with-custom-hooks",
    "https://react.dev/reference/react/createContext",
    "https://react.dev/reference/react-dom/createPortal",
    "https://vite.dev/blog/announcing-vite6",
    "https://vite.dev/guide/",
    "https://vite.dev/guide/features",
    "https://vite.dev/guide/env-and-mode",
    "https://vite.dev/guide/build",
    "https://vite.dev/guide/dep-pre-bundling",
    "https://vite.dev/config/",
    "https://vite.dev/guide/ssr",
    "https://vite.dev/guide/performance",
    "https://vite.dev/guide/migration",
    "https://vite.dev/changes/",
    "https://www.npmjs.com/package/react-router-dom",
    "https://www.npmjs.com/package/zustand",
    "https://www.npmjs.com/package/@tanstack/react-query",
    "https://www.npmjs.com/package/react-hook-form",
    "https://www.npmjs.com/package/zod",
    "https://www.npmjs.com/package/axios",
    "https://www.npmjs.com/package/tailwindcss",
    "https://www.npmjs.com/package/framer-motion",
    "https://www.npmjs.com/package/react-icons",
    "https://www.npmjs.com/package/@reduxjs/toolkit",
    "https://www.npmjs.com/package/react-redux",
    "https://www.npmjs.com/package/styled-components",
    "https://www.npmjs.com/package/@emotion/react",
    "https://www.npmjs.com/package/classnames",
    "https://www.npmjs.com/package/react-toastify",
    "https://www.npmjs.com/package/recharts",
    "https://redux-toolkit.js.org/introduction/getting-started",
    "https://redux-toolkit.js.org/tutorials/quick-start",
    "https://redux-toolkit.js.org/rtk-query/overview",
    "https://redux-toolkit.js.org/api/createSlice",
    "https://redux-toolkit.js.org/api/createAsyncThunk",
    "https://redux-toolkit.js.org/api/configureStore",
    "https://redux-toolkit.js.org/usage/usage-with-typescript",
    "https://redux-toolkit.js.org/usage/migrating-to-modern-redux",
    "https://reactrouter.com/home",
    "https://reactrouter.com/start/framework/routing",
    "https://reactrouter.com/start/framework/data-loading",
    "https://reactrouter.com/start/framework/actions",
    "https://reactrouter.com/start/framework/rendering-strategies",
    "https://reactrouter.com/start/framework/pending-ui",
    "https://reactrouter.com/start/framework/navigating",
    "https://reactrouter.com/upgrading/v6",
    "https://reactrouter.com/upgrading/component-routes",
    "https://reactrouter.com/how-to/file-route-conventions",
    "https://reactrouter.com/how-to/pre-rendering",
    "https://reactrouter.com/explanation/type-safety",
]

async def main():
    db = get_supabase_client()

    # Look up all URLs in url_registry
    print(f"Looking up {len(URLS)} URLs in url_registry...")
    registry = db.table("url_registry").select("id, url").execute()
    url_map = {row["url"]: row["id"] for row in registry.data}

    # Match URLs to url_ids
    matched = []
    missing = []
    for url in URLS:
        url_id = url_map.get(url)
        if url_id:
            matched.append((url, url_id))
        else:
            missing.append(url)

    print(f"Matched: {len(matched)} | Missing from registry: {len(missing)}")

    if missing:
        print("\nMissing URLs (will be inserted into url_registry):")
        for url in missing:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            source_name = domain.replace("www.", "").split(".")[0]
            row = db.table("url_registry").insert({
                "url": url,
                "domain": domain,
                "source_name": source_name,
                "credibility_tier": "official_docs",
                "category": "documentation",
                "is_active": True,
            }).execute()
            url_id = row.data[0]["id"]
            matched.append((url, url_id))
            print(f"  Inserted: {url} -> {url_id}")

    print(f"\nProcessing {len(matched)} URLs through digest agent...")
    print("=" * 60)

    success = 0
    failed = 0
    archived = 0

    for i, (url, url_id) in enumerate(matched):
        print(f"\n[{i+1}/{len(matched)}] {url}")
        try:
            result = await run_digest_agent(url=url, url_id=url_id)
            status = result.get("status", "unknown")
            topic = result.get("topic", "")
            relevant = result.get("curriculum_relevant", "No")
            errors = result.get("errors", [])

            if errors:
                print(f"  ERRORS: {errors}")
                failed += 1
            elif status == "archived":
                print(f"  ARCHIVED (not curriculum relevant) | Topic: {topic}")
                archived += 1
            else:
                print(f"  OK | Status: {status} | Topic: {topic} | Curriculum Relevant: {relevant}")
                success += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"DONE: {success} success | {archived} archived | {failed} failed | {len(matched)} total")

if __name__ == "__main__":
    asyncio.run(main())
