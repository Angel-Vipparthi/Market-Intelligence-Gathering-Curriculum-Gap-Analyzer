import logging
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.supabase import get_supabase_client
from app.models.url import URLCreate, URLListResponse, URLResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_domain(url: str) -> str:
    """Extract domain from a URL string."""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split("/")[0]


@router.post("", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_url(payload: URLCreate):
    """Create a new URL entry in the registry."""
    client = get_supabase_client()
    domain = _parse_domain(payload.url)

    data = {
        "id": str(uuid4()),
        "url": payload.url,
        "domain": domain,
        "category": payload.category,
        "tags": payload.tags,
        "source_name": payload.source_name,
        "is_active": True,
    }

    try:
        result = client.table("url_registry").insert(data).execute()
    except Exception as e:
        logger.error(f"Failed to insert URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create URL entry: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create URL entry",
        )

    return URLResponse(**result.data[0])


@router.get("", response_model=URLListResponse)
async def list_urls(
    category: str | None = Query(None, description="Filter by category"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List URL entries with optional filters."""
    client = get_supabase_client()

    query = client.table("url_registry").select("*", count="exact")

    if category is not None:
        query = query.eq("category", category)
    if is_active is not None:
        query = query.eq("is_active", is_active)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    try:
        result = query.execute()
    except Exception as e:
        logger.error(f"Failed to list URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list URLs: {e}",
        )

    return URLListResponse(
        items=[URLResponse(**row) for row in result.data],
        total=result.count or len(result.data),
    )


@router.get("/{url_id}", response_model=URLResponse)
async def get_url(url_id: str):
    """Get a single URL entry by ID."""
    client = get_supabase_client()

    try:
        result = client.table("url_registry").select("*").eq("id", url_id).execute()
    except Exception as e:
        logger.error(f"Failed to get URL {url_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get URL: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with id {url_id} not found",
        )

    return URLResponse(**result.data[0])


@router.delete("/{url_id}", response_model=URLResponse)
async def delete_url(url_id: str):
    """Soft delete a URL entry by setting is_active to false."""
    client = get_supabase_client()

    try:
        result = (
            client.table("url_registry")
            .update({"is_active": False})
            .eq("id", url_id)
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to delete URL {url_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete URL: {e}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with id {url_id} not found",
        )

    return URLResponse(**result.data[0])


@router.post("/import", response_model=URLListResponse, status_code=status.HTTP_201_CREATED)
async def bulk_import_urls(urls: list[URLCreate]):
    """Bulk import URLs from a JSON array."""
    client = get_supabase_client()

    records = []
    for url_entry in urls:
        domain = _parse_domain(url_entry.url)
        records.append(
            {
                "id": str(uuid4()),
                "url": url_entry.url,
                "domain": domain,
                "category": url_entry.category,
                "tags": url_entry.tags,
                "source_name": url_entry.source_name,
                "is_active": True,
            }
        )

    try:
        result = client.table("url_registry").insert(records).execute()
    except Exception as e:
        logger.error(f"Failed to bulk import URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk import URLs: {e}",
        )

    return URLListResponse(
        items=[URLResponse(**row) for row in result.data],
        total=len(result.data),
    )
