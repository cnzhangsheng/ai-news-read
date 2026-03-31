from datetime import datetime
from pydantic import BaseModel


class SourceCreate(BaseModel):
    name: str
    type: str
    url: str
    enabled: bool = True
    filter_keywords: list[str] | None = None


class SourceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    url: str | None = None
    enabled: bool | None = None
    filter_keywords: list[str] | None = None


class SourceResponse(BaseModel):
    id: int
    name: str
    type: str
    url: str
    enabled: bool
    filter_keywords: list[str] | None


class ArticleResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    title: str
    summary: str | None
    content: str | None
    ai_summary: str | None
    category: str | None
    link: str
    published_at: datetime | None
    fetched_at: datetime
    is_duplicate: bool


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    page: int
    page_size: int


class FetchLogResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    status: str
    articles_count: int
    error_message: str | None
    fetched_at: datetime


class StatusResponse(BaseModel):
    scheduler_running: bool
    next_fetch_time: datetime | None
    total_sources: int
    enabled_sources: int
    total_articles: int