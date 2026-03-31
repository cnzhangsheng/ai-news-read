# app/services/fetcher.py
from datetime import datetime
from typing import Any
import json

from app.core.config import app_config
from app.models.database import SourceDB, ArticleDB, FetchLogDB
from app.services.parser import parse_rss, ArticleData
from app.services.filter import filter_articles
from app.services.dedup import deduplicate_articles
from app.services.ai import process_article
from app.utils.similarity import compute_title_hash


async def fetch_source(source: dict[str, Any]) -> int:
    source_id = source["id"]
    source_type = source["type"]
    url = source["url"]
    filter_keywords = None

    if source.get("filter_keywords"):
        try:
            filter_keywords = json.loads(source["filter_keywords"])
        except:
            filter_keywords = None

    try:
        # 1. 抓取 RSS
        articles = parse_rss(url, app_config.settings.max_articles_per_fetch)

        # 2. InfoQ 类型需要过滤
        if source_type == "infoq":
            articles = filter_articles(articles, filter_keywords)

        # 3. 去重
        dedup_results = await deduplicate_articles(source_id, articles)

        # 4. 存储文章
        new_count = 0
        for article, is_duplicate in dedup_results:
            article_id = await ArticleDB.create(
                source_id=source_id,
                title=article.title,
                link=article.link,
                summary=article.summary,
                content=article.content,
                published_at=article.published_at,
                title_hash=compute_title_hash(article.title),
                is_duplicate=is_duplicate
            )

            if article_id and not is_duplicate:
                # 5. AI 处理（仅对新文章）
                ai_summary, category = await process_article(article)
                await ArticleDB.update_ai_fields(article_id, ai_summary, category)
                new_count += 1

        # 6. 记录日志
        await FetchLogDB.create(
            source_id=source_id,
            status="success",
            articles_count=new_count
        )

        return new_count

    except Exception as e:
        await FetchLogDB.create(
            source_id=source_id,
            status="error",
            articles_count=0,
            error_message=str(e)
        )
        return 0


async def fetch_all_sources() -> dict[str, int]:
    sources = await SourceDB.get_enabled()
    results = {}

    for source in sources:
        count = await fetch_source(source)
        results[source["name"]] = count

    return results


async def fetch_single_source(source_id: int) -> int:
    source = await SourceDB.get_by_id(source_id)
    if not source:
        return 0
    return await fetch_source(source)