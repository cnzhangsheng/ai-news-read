# app/services/dedup.py
from app.models.database import ArticleDB
from app.services.parser import ArticleData
from app.utils.similarity import compute_title_hash, check_duplicate_by_title


async def deduplicate_articles(source_id: int, articles: list[ArticleData]) -> list[tuple[ArticleData, bool]]:
    existing_hashes = await ArticleDB.get_title_hashes(source_id, limit=100)

    results = []
    existing_titles = []  # 用于相似度检查

    for article in articles:
        title_hash = compute_title_hash(article.title)

        # 检查标题哈希是否已存在
        if title_hash in existing_hashes:
            results.append((article, True))
            continue

        # 检查标题相似度
        if existing_titles and check_duplicate_by_title(article.title, existing_titles):
            results.append((article, True))
            continue

        # 不是重复
        results.append((article, False))
        existing_hashes.append(title_hash)
        existing_titles.append(article.title)

    return results