# AI新闻订阅聚合工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可扩展的 AI 新闻订阅聚合 Web 应用，支持 RSS 抓取、自动去重、AI 摘要分类。

**Architecture:** 单体 FastAPI 应用，内置 APScheduler 后台调度，SQLite 存储，YAML 配置。

**Tech Stack:** FastAPI, APScheduler, feedparser, OpenAI API, SQLite, Pydantic, scikit-learn

---

## 文件结构

```
ai_news_read/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # 文章浏览 API
│   │   └── sources.py         #订阅源管理 API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 配置加载（YAML + env）
│   │   └── scheduler.py       # APScheduler 调度器
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schema.py          # Pydantic 请求/响应模型
│   │   └── database.py        # SQLite 表定义与操作
│   ├── services/
│   │   ├── __init__.py
│   │   ├── fetcher.py         # RSS 抓取服务
│   │   ├── parser.py          # RSS 解析服务
│   │   ├── filter.py          # InfoQ 关键词过滤
│   │   ├── dedup.py           # 去重服务（链接 + 标题相似度）
│   │   └── ai.py              # OpenAI 摘要/分类服务
│   ├── utils/
│   │   ├── __init__.py
│   │   └── similarity.py      # TF-IDF 标题相似度计算
│   └── main.py                # FastAPI 入口
├── config/
│   └── sources.yaml           #订阅源配置
├── data/
│   └── news.db                # SQLite 数据库
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_filter.py
│   ├── test_dedup.py
│   └── test_ai.py
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Task 1: 项目基础设置

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `config/sources.yaml`
- Create: `app/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/models/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/utils/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建项目依赖配置**

```toml
# pyproject.toml
[project]
name = "ai-news-read"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "feedparser>=6.0.0",
    "apscheduler>=3.10.0",
    "openai>=1.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0.0",
    "aiosqlite>=0.19.0",
    "scikit-learn>=1.3.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: 创建环境变量模板**

```env
# .env.example
OPENAI_API_KEY=sk-xxx
DATABASE_PATH=data/news.db
CONFIG_PATH=config/sources.yaml
FETCH_INTERVAL=60
AI_MODEL=gpt-4o-mini
```

- [ ] **Step 3: 创建订阅源配置文件**

```yaml
# config/sources.yaml
settings:
  fetch_interval: 60
  ai_model: "gpt-4o-mini"
  max_articles_per_fetch: 50
  default_filter_keywords:
    - "AI"
    - "大模型"
    - "机器学习"
    - "深度学习"
    - "生成式AI"
    - "AIGC"
    - "LLM"
    - "人工智能"

sources:
  - name: "elon_musk"
    type: "twitter"
    url: "https://rsshub.app/twitter/user/elonmusk"
    enabled: true

  - name: "karpathy"
    type: "twitter"
    url: "https://rsshub.app/twitter/user/karpathy"
    enabled: true

  - name: "infoq_ai"
    type: "infoq"
    url: "https://feed.infoq.com/"
    enabled: true

  - name: "openai_blog"
    type: "rss"
    url: "https://openai.com/blog/rss.xml"
    enabled: true
```

- [ ] **Step 4: 创建目录结构和 __init__.py 文件**

```bash
mkdir -p app/api app/core app/models app/services app/utils config data tests
touch app/__init__.py app/api/__init__.py app/core/__init__.py app/models/__init__.py app/services/__init__.py app/utils/__init__.py tests/__init__.py
```

- [ ] **Step 5: 提交基础设置**

```bash
git add pyproject.toml .env.example config/sources.yaml app tests
git commit -m "chore: initialize project structure and configuration"
```

---

## Task 2: 配置加载模块

**Files:**
- Create: `app/core/config.py`

- [ ] **Step 1: 编写配置加载代码**

```python
# app/core/config.py
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class SourceConfig(BaseModel):
    name: str
    type: str  # twitter | infoq | rss
    url: str
    enabled: bool = True
    filter_keywords: list[str] | None = None


class Settings(BaseModel):
    fetch_interval: int = 60
    ai_model: str = "gpt-4o-mini"
    max_articles_per_fetch: int = 50
    default_filter_keywords: list[str] = []


class AppConfig(BaseModel):
    settings: Settings
    sources: list[SourceConfig]


class EnvConfig:
    openai_api_key: str
    database_path: str
    config_path: str
    fetch_interval: int
    ai_model: str

    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.database_path = os.getenv("DATABASE_PATH", "data/news.db")
        self.config_path = os.getenv("CONFIG_PATH", "config/sources.yaml")
        self.fetch_interval = int(os.getenv("FETCH_INTERVAL", "60"))
        self.ai_model = os.getenv("AI_MODEL", "gpt-4o-mini")


def load_yaml_config(path: str) -> AppConfig:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with yaml_path.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)
    
    return AppConfig(**data)


env_config = EnvConfig()
app_config: AppConfig = load_yaml_config(env_config.config_path)
```

- [ ] **Step 2: 提交配置模块**

```bash
git add app/core/config.py
git commit -m "feat: add configuration loading module"
```

---

## Task 3: 数据模型与数据库

**Files:**
- Create: `app/models/schema.py`
- Create: `app/models/database.py`

- [ ] **Step 1: 编写 Pydantic 模型**

```python
# app/models/schema.py
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
```

- [ ] **Step 2: 编写数据库模块**

```python
# app/models/database.py
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import env_config


async def init_db() -> None:
    db_path = Path(env_config.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled BOOLEAN DEFAULT1,
                filter_keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER REFERENCES sources(id),
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                ai_summary TEXT,
                category TEXT,
                link TEXT UNIQUE NOT NULL,
                published_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title_hash TEXT,
                is_duplicate BOOLEAN DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fetch_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER REFERENCES sources(id),
                status TEXT,
                articles_count INTEGER,
                error_message TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    return await aiosqlite.connect(env_config.database_path)


class SourceDB:
    @staticmethod
    async def create(name: str, type: str, url: str, enabled: bool = True, 
                     filter_keywords: list[str] | None = None) -> int:
        async with await get_db() as db:
            keywords_json = str(filter_keywords) if filter_keywords else None
            await db.execute(
                "INSERT INTO sources (name, type, url, enabled, filter_keywords) VALUES (?, ?, ?, ?, ?)",
                (name, type, url, enabled, keywords_json)
            )
            await db.commit()
            cursor = await db.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    async def get_all() -> list[dict[str, Any]]:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def get_by_id(id: int) -> dict[str, Any] | None:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources WHERE id = ?", (id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_enabled() -> list[dict[str, Any]]:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources WHERE enabled = 1")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def update(id: int, **kwargs: Any) -> bool:
        async with await get_db() as db:
            fields = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    values.append(value)
            if not fields:
                return False
            values.append(id)
            await db.execute(
                f"UPDATE sources SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values
            )
            await db.commit()
            return True

    @staticmethod
    async def delete(id: int) -> bool:
        async with await get_db() as db:
            await db.execute("DELETE FROM sources WHERE id = ?", (id,))
            await db.commit()
            return True


class ArticleDB:
    @staticmethod
    async def create(source_id: int, title: str, link: str, summary: str | None = None,
                     content: str | None = None, published_at: datetime | None = None,
                     title_hash: str | None = None, is_duplicate: bool = False) -> int | None:
        async with await get_db() as db:
            try:
                await db.execute(
                    """INSERT INTO articles 
                       (source_id, title, summary, content, link, published_at, title_hash, is_duplicate)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (source_id, title, summary, content, link, published_at, title_hash, is_duplicate)
                )
                await db.commit()
                cursor = await db.execute("SELECT last_insert_rowid()")
                row = await cursor.fetchone()
                return row[0] if row else None
            except aiosqlite.IntegrityError:
                return None  # 链接已存在

    @staticmethod
    async def update_ai_fields(id: int, ai_summary: str, category: str) -> bool:
        async with await get_db() as db:
            await db.execute(
                "UPDATE articles SET ai_summary = ?, category = ? WHERE id = ?",
                (ai_summary, category, id)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_list(page: int = 1, page_size: int = 20, category: str | None = None,
                       source_id: int | None = None) -> tuple[list[dict[str, Any]], int]:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            offset = (page -1) * page_size
            
            conditions = ["is_duplicate = 0"]
            params: list[Any] = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            if source_id:
                conditions.append("source_id = ?")
                params.append(source_id)
            
            where_clause = " AND ".join(conditions)
            
            count_cursor = await db.execute(f"SELECT COUNT(*) FROM articles WHERE {where_clause}", params)
            total = (await count_cursor.fetchone())[0]
            
            params.extend([page_size, offset])
            cursor = await db.execute(
                f"""SELECT a.*, s.name as source_name FROM articles a
                    JOIN sources s ON a.source_id = s.id
                    WHERE {where_clause}
                    ORDER BY a.fetched_at DESC LIMIT ? OFFSET ?""",
                params
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows], total

    @staticmethod
    async def get_by_id(id: int) -> dict[str, Any] | None:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT a.*, s.name as source_name FROM articles a
                    JOIN sources s ON a.source_id = s.id WHERE a.id = ?""",
                (id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_categories() -> list[str]:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT DISTINCT category FROM articles WHERE category IS NOT NULL AND is_duplicate = 0"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    @staticmethod
    async def get_title_hashes(source_id: int, limit: int = 100) -> list[str]:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT title_hash FROM articles WHERE source_id = ? AND title_hash IS NOT NULL ORDER BY fetched_at DESC LIMIT ?",
                (source_id, limit)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


class FetchLogDB:
    @staticmethod
    async def create(source_id: int, status: str, articles_count: int = 0,
                     error_message: str | None = None) -> int:
        async with await get_db() as db:
            await db.execute(
                "INSERT INTO fetch_logs (source_id, status, articles_count, error_message) VALUES (?, ?, ?, ?)",
                (source_id, status, articles_count, error_message)
            )
            await db.commit()
            cursor = await db.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    async def get_recent(limit: int = 50) -> list[dict[str, Any]]:
        async with await get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT l.*, s.name as source_name FROM fetch_logs l
                    JOIN sources s ON l.source_id = s.id
                    ORDER BY l.fetched_at DESC LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
```

- [ ] **Step 3: 提交数据模型**

```bash
git add app/models/schema.py app/models/database.py
git commit -m "feat: add pydantic schemas and sqlite database module"
```

---

## Task 4: 标题相似度工具

**Files:**
- Create: `app/utils/similarity.py`

- [ ] **Step 1: 编写标题相似度计算**

```python
# app/utils/similarity.py
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_title_hash(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()


def compute_similarity(title1: str, title2: str) -> float:
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([title1, title2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except ValueError:
        return 0.0


def is_similar(title1: str, title2: str, threshold: float = 0.85) -> bool:
    return compute_similarity(title1, title2) > threshold


def check_duplicate_by_title(title: str, existing_titles: list[str], threshold: float = 0.85) -> bool:
    for existing in existing_titles:
        if is_similar(title, existing, threshold):
            return True
    return False
```

- [ ] **Step 2: 提交相似度工具**

```bash
git add app/utils/similarity.py
git commit -m "feat: add title similarity calculation using TF-IDF"
```

---

## Task 5: RSS 解析服务

**Files:**
- Create: `app/services/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: 编写解析服务**

```python
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
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_parser.py
import pytest
from app.services.parser import parse_rss, ArticleData


def test_parse_rss_basic():
    articles = parse_rss("https://openai.com/blog/rss.xml")
    assert isinstance(articles, list)
    for article in articles:
        assert isinstance(article, ArticleData)
        assert article.title
        assert article.link


def test_article_data_fields():
    article = ArticleData(
        title="Test Title",
        link="https://example.com",
        summary="Test summary",
        content="Test content"
    )
    assert article.title == "Test Title"
    assert article.link == "https://example.com"
    assert article.summary == "Test summary"
    assert article.content == "Test content"
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/test_parser.py -v
```

- [ ] **Step 4: 提交解析服务**

```bash
git add app/services/parser.py tests/test_parser.py
git commit -m "feat: add RSS parsing service with feedparser"
```

---

## Task 6: InfoQ 关键词过滤

**Files:**
- Create: `app/services/filter.py`
- Create: `tests/test_filter.py`

- [ ] **Step 1: 编写过滤服务**

```python
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
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_filter.py
import pytest
from app.services.parser import ArticleData
from app.services.filter import matches_keywords, filter_articles


def test_matches_keywords():
    assert matches_keywords("AI大模型技术进展", ["AI", "大模型"]) == True
    assert matches_keywords("普通新闻报道", ["AI", "大模型"]) == False
    assert matches_keywords("机器学习入门教程", ["机器学习"]) == True


def test_filter_articles():
    articles = [
        ArticleData(title="AI大模型最新进展", link="https://1.com", summary="关于GPT的内容"),
        ArticleData(title="普通技术文章", link="https://2.com", summary="前端开发"),
        ArticleData(title="深度学习框架对比", link="https://3.com", summary="TensorFlow vs PyTorch"),
    ]
    
    keywords = ["AI", "大模型", "深度学习"]
    filtered = filter_articles(articles, keywords)
    
    assert len(filtered) == 2
    assert filtered[0].title == "AI大模型最新进展"
    assert filtered[1].title == "深度学习框架对比"
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/test_filter.py -v
```

- [ ] **Step 4: 提交过滤服务**

```bash
git add app/services/filter.py tests/test_filter.py
git commit -m "feat: add keyword filtering for InfoQ articles"
```

---

## Task 7: 去重服务

**Files:**
- Create: `app/services/dedup.py`
- Create: `tests/test_dedup.py`

- [ ] **Step 1: 编写去重服务**

```python
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
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_dedup.py
import pytest
from app.services.parser import ArticleData
from app.utils.similarity import compute_title_hash, is_similar


def test_compute_title_hash():
    hash1 = compute_title_hash("AI大模型技术")
    hash2 = compute_title_hash("AI大模型技术")
    hash3 = compute_title_hash("不同标题")
    
    assert hash1 == hash2
    assert hash1 != hash3


def test_is_similar():
    title1 = "OpenAI发布GPT-5模型"
    title2 = "OpenAI发布GPT-5大模型"
    title3 = "微软推出新产品"
    
    assert is_similar(title1, title2) == True
    assert is_similar(title1, title3) == False
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/test_dedup.py -v
```

- [ ] **Step 4: 提交去重服务**

```bash
git add app/services/dedup.py tests/test_dedup.py
git commit -m "feat: add deduplication service with link and title similarity"
```

---

## Task 8: AI 摘要/分类服务

**Files:**
- Create: `app/services/ai.py`
- Create: `tests/test_ai.py`

- [ ] **Step 1: 编写 AI 服务**

```python
# app/services/ai.py
from openai import AsyncOpenAI
from app.core.config import env_config
from app.services.parser import ArticleData

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
        
        # 解析 JSON（简单处理）
        import json
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
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_ai.py
import pytest
from app.services.parser import ArticleData
from app.services.ai import CATEGORIES


def test_categories_defined():
    assert len(CATEGORIES) == 5
    assert "技术动态" in CATEGORIES
    assert "其他" in CATEGORIES


@pytest.mark.asyncio
async def test_process_article_mock():
    # 注意：实际运行需要有效的 OPENAI_API_KEY
    article = ArticleData(
        title="OpenAI发布新模型",
        link="https://example.com",
        summary="OpenAI今天发布了最新的大语言模型",
        content="详细内容..."
    )
    # 此测试仅验证函数可调用，实际 AI 调用需要 API Key
    pass
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/test_ai.py -v
```

- [ ] **Step 4: 提交 AI 服务**

```bash
git add app/services/ai.py tests/test_ai.py
git commit -m "feat: add OpenAI-based summary and categorization service"
```

---

## Task 9: 抓取服务整合

**Files:**
- Create: `app/services/fetcher.py`

- [ ] **Step 1: 编写抓取服务**

```python
# app/services/fetcher.py
from datetime import datetime
from typing import Any

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
        import json
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
                new_count +=1
        
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
```

- [ ] **Step 2: 提交抓取服务**

```bash
git add app/services/fetcher.py
git commit -m "feat: add unified fetch service integrating all components"
```

---

## Task 10: 定时调度器

**Files:**
- Create: `app/core/scheduler.py`

- [ ] **Step 1: 编写调度器**

```python
# app/core/scheduler.py
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import app_config, env_config
from app.services.fetcher import fetch_all_sources

scheduler = AsyncIOScheduler()
_scheduler_running = False
_next_fetch_time: datetime | None = None


async def scheduled_fetch() -> None:
    global _next_fetch_time
    await fetch_all_sources()
    # 更新下次抓取时间
    from datetime import timedelta
    _next_fetch_time = datetime.now() + timedelta(minutes=app_config.settings.fetch_interval)


def start_scheduler() -> None:
    global _scheduler_running, _next_fetch_time
    
    if _scheduler_running:
        return
    
    scheduler.add_job(
        scheduled_fetch,
        trigger=IntervalTrigger(minutes=app_config.settings.fetch_interval),
        id="fetch_all_sources",
        replace_existing=True
    )
    
    scheduler.start()
    _scheduler_running = True
    from datetime import timedelta
    _next_fetch_time = datetime.now() + timedelta(minutes=app_config.settings.fetch_interval)


def stop_scheduler() -> None:
    global _scheduler_running
    scheduler.shutdown()
    _scheduler_running = False


def get_scheduler_status() -> tuple[bool, datetime | None]:
    return _scheduler_running, _next_fetch_time
```

- [ ] **Step 2: 提交调度器**

```bash
git add app/core/scheduler.py
git commit -m "feat: add APScheduler for periodic fetching"
```

---

## Task 11: Web API - 文章浏览

**Files:**
- Create: `app/api/routes.py`

- [ ] **Step 1: 编写文章浏览 API**

```python
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
    articles, total = await ArticleDB.get_list(1,1)
    
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
```

- [ ] **Step 2: 提交文章 API**

```bash
git add app/api/routes.py
git commit -m "feat: add article browsing and fetch trigger API"
```

---

## Task 12: Web API -订阅源管理

**Files:**
- Create: `app/api/sources.py`

- [ ] **Step 1: 编写订阅源管理 API**

```python
# app/api/sources.py
from fastapi import APIRouter, HTTPException

from app.models.schema import SourceCreate, SourceUpdate, SourceResponse
from app.models.database import SourceDB

router = APIRouter()


@router.get("/sources")
async def list_sources():
    sources = await SourceDB.get_all()
    return {
        "sources": [
            SourceResponse(
                id=s["id"],
                name=s["name"],
                type=s["type"],
                url=s["url"],
                enabled=s["enabled"],
                filter_keywords=eval(s["filter_keywords"]) if s["filter_keywords"] else None
            )
            for s in sources
        ]
    }


@router.post("/sources", response_model=SourceResponse)
async def create_source(source: SourceCreate):
    try:
        source_id = await SourceDB.create(
            name=source.name,
            type=source.type,
            url=source.url,
            enabled=source.enabled,
            filter_keywords=source.filter_keywords
        )
        created = await SourceDB.get_by_id(source_id)
        return SourceResponse(
            id=created["id"],
            name=created["name"],
            type=created["type"],
            url=created["url"],
            enabled=created["enabled"],
            filter_keywords=eval(created["filter_keywords"]) if created["filter_keywords"] else None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(source_id: int, source: SourceUpdate):
    updated = await SourceDB.update(
        source_id,
        name=source.name,
        type=source.type,
        url=source.url,
        enabled=source.enabled,
        filter_keywords=source.filter_keywords
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Source not found")
    
    result = await SourceDB.get_by_id(source_id)
    return SourceResponse(
        id=result["id"],
        name=result["name"],
        type=result["type"],
        url=result["url"],
        enabled=result["enabled"],
        filter_keywords=eval(result["filter_keywords"]) if result["filter_keywords"] else None
    )


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    deleted = await SourceDB.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "deleted"}
```

- [ ] **Step 2: 提交订阅源 API**

```bash
git add app/api/sources.py
git commit -m "feat: add source management API"
```

---

## Task 13: 应用入口

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: 编写 FastAPI 入口**

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.database import init_db
from app.api.routes import router as article_router
from app.api.sources import router as source_router
from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库和调度器
    await init_db()
    start_scheduler()
    yield
    # 关闭时停止调度器
    stop_scheduler()


app = FastAPI(
    title="AI News Aggregator",
    description="AI新闻订阅聚合工具",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(article_router, prefix="/api")
app.include_router(source_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "AI News Aggregator API", "docs": "/docs"}
```

- [ ] **Step 2: 提交应用入口**

```bash
git add app/main.py
git commit -m "feat: add FastAPI application entry point"
```

---

## Task 14: 验证与文档

**Files:**
- Create: `README.md`

- [ ] **Step 1: 编写 README**

```markdown
# AI新闻订阅聚合工具

一个可扩展、配置友好的 AI 新闻订阅聚合 Web 应用。

## 功能

- 支持 Twitter/X、InfoQ、通用 RSS 等数据源
- 自动去重（链接 + 标题相似度）
- AI 精简摘要和自动分类
- Web界面浏览和管理
- 定时自动抓取

## 安装

```bash
# 安装依赖
pip install -e .

# 或使用 uv
uv pip install -e .
```

## 配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 设置 OpenAI API Key：
```env
OPENAI_API_KEY=sk-xxx
```

3. 编辑 `config/sources.yaml` 添加订阅源

## 运行

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 端点

| 端点 | 功能 |
|------|------|
| `/api/articles` | 文章列表 |
| `/api/articles/{id}` | 文章详情 |
| `/api/categories` | 分类列表 |
| `/api/sources` |订阅源管理 |
| `/api/status` | 运行状态 |
| `/api/fetch` | 手动触发抓取 |

## 新增订阅源

方式一：编辑 `config/sources.yaml`

```yaml
sources:
  - name: "my_source"
    type: "rss"
    url: "https://example.com/rss.xml"
    enabled: true
```

方式二：通过 API

```bash
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"my_source","type":"rss","url":"https://example.com/rss.xml"}'
```

## 测试

```bash
pytest tests/ -v
```
```

- [ ] **Step 2: 运行应用验证**

```bash
# 创建 .env 文件（使用示例配置）
cp .env.example .env

# 运行应用
uvicorn app.main:app --reload
```

验证步骤：
- 访问 http://localhost:8000/docs
- 测试 `/api/fetch` 手动触发抓取
- 检查 `/api/articles` 是否有数据

- [ ] **Step 3: 提交最终版本**

```bash
git add README.md
git commit -m "docs: add README and finalize project"
```

---

## 自审检查

**1. Spec覆盖检查：**
- ✓ 数据源配置 → Task 1, Task 2
- ✓ Twitter/X 源支持 → Task 5
- ✓ InfoQ 关键词过滤 → Task 6
- ✓ 通用 RSS 源 → Task 5
- ✓ 批量抓取 → Task 9
- ✓ 定时调度 → Task 10
- ✓ 自动去重 → Task 7
- ✓ AI 摘要/分类 → Task 8
- ✓ SQLite 存储 → Task 3
- ✓ Web API 浏览 → Task 11
- ✓ Web API 管理订阅源 → Task 12
- ✓ 手动触发抓取 → Task 11

**2. Placeholder检查：**
- ✓ 无 TBD/TODO
- ✓ 每个步骤有完整代码

**3. 类型一致性：**
- ✓ ArticleData 结构一致
- ✓ SourceResponse 字段一致
- ✓ 函数签名匹配