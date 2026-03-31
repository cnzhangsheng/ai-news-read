# app/services/parser.py
import feedparser
from datetime import datetime
from typing import Any


class ArticleData:
    title: str
    link: str
    summary: str
    content: str
    published_at: datetime | None

    def __init__(self, title: str, link: str, summary: str = "",
                 content: str = "", published_at: datetime | None = None) -> None:
        self.title = title
        self.link = link
        self.summary = summary
        self.content = content
        self.published_at = published_at


def parse_rss(url: str, max_items: int = 50) -> list[ArticleData]:
    feed: Any = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        link = entry.get("link", "")

        summary = entry.get("summary", "")
        if not summary:
            summary = entry.get("description", "")

        content = entry.get("content", "")
        if not content:
            if "content" in entry:
                content_list = entry.get("content", [])
                if content_list:
                    content = content_list[0].get("value", "")

        published_at = None
        if "published_parsed" in entry and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6])
        elif "updated_parsed" in entry and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6])

        if title and link:
            articles.append(ArticleData(
                title=title,
                link=link,
                summary=summary,
                content=content,
                published_at=published_at
            ))

    return articles