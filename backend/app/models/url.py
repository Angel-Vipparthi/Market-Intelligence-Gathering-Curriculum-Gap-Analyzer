from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    url: str
    category: Optional[str] = None
    tags: list[str] = []
    source_name: Optional[str] = None
    course_name: Optional[str] = None


class URLResponse(BaseModel):
    id: UUID
    url: str
    domain: str
    source_name: Optional[str] = None
    credibility_tier: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = []
    is_active: bool = True
    last_crawled_at: Optional[datetime] = None
    crawl_frequency: Optional[str] = None
    added_by: Optional[str] = None
    course_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class URLListResponse(BaseModel):
    items: list[URLResponse]
    total: int
