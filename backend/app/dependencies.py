from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from supabase import Client

from app.db.supabase import get_supabase_client


def get_supabase() -> Client:
    """Return the cached Supabase client."""
    return get_supabase_client()


def get_langfuse(request: Request):
    """Return the Langfuse client from app state, or None if not configured."""
    return getattr(request.app.state, "langfuse", None)


async def get_current_user(request: Request) -> dict:
    """Placeholder auth dependency.

    In production this should validate a JWT from Supabase Auth and return
    the authenticated user record. For now it returns a stub user dict so
    that downstream handlers have a consistent interface.
    """
    # TODO: implement real JWT validation via Supabase Auth
    return {
        "id": "placeholder-user-id",
        "email": "reviewer@gap-analyzer.local",
        "role": "reviewer",
    }
