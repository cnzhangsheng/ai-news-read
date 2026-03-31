# app/services/ai.py
from openai import AsyncOpenAI
from app.core.config import env_config
from app.services.parser import ArticleData
import json

CATEGORIES = ["技术动态", "产品发布", "研究进展", "行业资讯", "其他"]

client = AsyncOpenAI(api_key=env_config.openai_api_key)


async def process_article(article: ArticleData) -> tuple[str, str]:
    if not env_config.openai_api_key:
        return "", "其他"

    content_for_ai = f"标题: {article.title}\n摘要: {article.summary}\n内容: {article.content[:1000]}"

    prompt = f"""请对以下新闻文章进行处理：
1. 生成一个精简摘要（不超过200字）
2. 从以下分类中选择最合适的分类：{', '.join(CATEGORIES)}

文章内容：
{content_for_ai}

请以JSON格式返回：
{"summary": "精简摘要内容", "category": "分类名称"}
"""

    try:
        response = await client.chat.completions.create(
            model=env_config.ai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )

        content = response.choices[0].message.content or ""

        # 解析 JSON
        result = json.loads(content.strip())
        summary = result.get("summary", "")
        category = result.get("category", "其他")

        if category not in CATEGORIES:
            category = "其他"

        return summary, category
    except Exception:
        return article.summary[:200] if article.summary else "", "其他"


async def batch_process_articles(articles: list[ArticleData]) -> list[tuple[str, str]]:
    results = []
    for article in articles:
        summary, category = await process_article(article)
        results.append((summary, category))
    return results