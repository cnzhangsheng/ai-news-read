# app/api/routes.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.models.schema import ArticleResponse, ArticleListResponse, StatusResponse, FetchLogResponse
from app.models.database import ArticleDB, FetchLogDB, SourceDB
from app.services.fetcher import fetch_all_sources, fetch_single_source
from app.core.scheduler import get_scheduler_status

router = APIRouter()


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    source_id: Optional[int] = None
):
    articles, total = await ArticleDB.get_list(page, page_size, category, source_id)

    return ArticleListResponse(
        articles=[
            ArticleResponse(
                id=a["id"],
                source_id=a["source_id"],
                source_name=a["source_name"],
                title=a["title"],
                summary=a["summary"],
                content=a["content"],
                ai_summary=a["ai_summary"],
                category=a["category"],
                link=a["link"],
                published_at=a["published_at"],
                fetched_at=a["fetched_at"],
                is_duplicate=a["is_duplicate"]
            )
            for a in articles
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    article = await ArticleDB.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleResponse(
        id=article["id"],
        source_id=article["source_id"],
        source_name=article["source_name"],
        title=article["title"],
        summary=article["summary"],
        content=article["content"],
        ai_summary=article["ai_summary"],
        category=article["category"],
        link=article["link"],
        published_at=article["published_at"],
        fetched_at=article["fetched_at"],
        is_duplicate=article["is_duplicate"]
    )


@router.get("/categories")
async def get_categories():
    categories = await ArticleDB.get_categories()
    return {"categories": categories}


@router.get("/status", response_model=StatusResponse)
async def get_status():
    running, next_time = get_scheduler_status()
    sources = await SourceDB.get_all()
    articles, total = await ArticleDB.get_list(1, 1)

    return StatusResponse(
        scheduler_running=running,
        next_fetch_time=next_time,
        total_sources=len(sources),
        enabled_sources=len([s for s in sources if s["enabled"]]),
        total_articles=total
    )


@router.get("/logs")
async def get_logs(limit: int = Query(50, ge=1, le=200)):
    logs = await FetchLogDB.get_recent(limit)
    return {
        "logs": [
            FetchLogResponse(
                id=l["id"],
                source_id=l["source_id"],
                source_name=l["source_name"],
                status=l["status"],
                articles_count=l["articles_count"],
                error_message=l["error_message"],
                fetched_at=l["fetched_at"]
            )
            for l in logs
        ]
    }


@router.post("/fetch")
async def trigger_fetch():
    results = await fetch_all_sources()
    return {"status": "completed", "results": results}


@router.post("/fetch/{source_id}")
async def trigger_fetch_source(source_id: int):
    count = await fetch_single_source(source_id)
    if count == 0:
        raise HTTPException(status_code=404, detail="Source not found or no new articles")
    return {"status": "completed", "articles_count": count}