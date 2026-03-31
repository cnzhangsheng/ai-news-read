# app/services/filter.py
from app.services.parser import ArticleData
from app.core.config import app_config


def matches_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False


def filter_articles(articles: list[ArticleData], keywords: list[str] | None = None) -> list[ArticleData]:
    if keywords is None:
        keywords = app_config.settings.default_filter_keywords

    filtered = []
    for article in articles:
        text_to_check = f"{article.title} {article.summary}"
        if matches_keywords(text_to_check, keywords):
            filtered.append(article)

    return filtered