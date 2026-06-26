import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def list_skills():
    """List all agent skills with current scores."""
    client = get_supabase_client()

    try:
        result = client.table("agent_skills").select("*").order("skill_name").execute()
    except Exception as e:
        logger.error(f"Failed to list skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {e}",
        )

    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    """Get skill detail with version history."""
    client = get_supabase_client()

    try:
        result = client.table("agent_skills").select("*").eq("id", skill_id).execute()
    except Exception as e:
        logger.error(f"Failed to get skill {skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found",
        )

    skill = result.data[0]

    # Fetch version history
    try:
        versions = (
            client.table("prompt_versions")
            .select("*")
            .eq("skill_id", skill_id)
            .order("version", desc=True)
            .execute()
        )
        skill["versions"] = versions.data or []
    except Exception:
        skill["versions"] = []

    return skill


@router.get("/{skill_id}/versions")
async def list_skill_versions(skill_id: str):
    """List prompt versions for a skill."""
    client = get_supabase_client()

    # Verify skill exists
    skill_result = client.table("agent_skills").select("id").eq("id", skill_id).execute()
    if not skill_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found",
        )

    try:
        result = (
            client.table("prompt_versions")
            .select("*")
            .eq("skill_id", skill_id)
            .order("version", desc=True)
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to list versions for skill {skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skill versions: {e}",
        )

    return {"items": result.data or [], "total": len(result.data or [])}
