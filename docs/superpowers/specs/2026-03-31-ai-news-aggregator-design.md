# AI 新闻订阅聚合工具设计文档

## 项目概述

一个可扩展、配置友好的 AI 新闻订阅聚合工具，使用 Python + FastAPI 实现。支持 Twitter/X、InfoQ、通用 RSS 等数据源，通过 OpenAI API 进行摘要精简和自动分类。

## 背景

用户需要一个自动化的新闻聚合工具，能够：
- 从多个 RSS 源抓取 AI 相关新闻
- 自动过滤（InfoQ）和去重（链接 + 标题相似度）
- 通过 AI 精简摘要并分类
- 通过 Web 界面管理和浏览

## 技术选型

| 项目 | 选择 | 原因 |
|------|------|------|
| Web 框架 | FastAPI | 异步优先，自动生成 API 文档 |
| 数据库 | SQLite | 轻量、无需额外服务、适合个人工具 |
| AI 服务 | OpenAI API | 稳定可靠、API 成熟 |
| 调度器 | APScheduler | 内置后台调度、简单易用 |
| 配置格式 | YAML | 人类可读、方便手动编辑 |

## 架构设计

采用单体应用架构：

```
┌─────────────────────────────────────────┐
│              FastAPI App                 │
├─────────────┬───────────────────────────┤
│  Web API    │   Background Scheduler    │
│  (routes)   │   (APScheduler)           │
├─────────────┴───────────────────────────┤
│              Core Services               │
│  (fetcher, parser, dedup, ai, db)       │
├─────────────────────────────────────────┤
│              SQLite + YAML               │
└─────────────────────────────────────────┘
```

## 项目结构

```
ai_news_read/
├── app/
│   ├── api/              # Web API 路由
│   │   ├── __init__.py
│   │   ├── routes.py     # 主路由
│   │   └── sources.py    #订阅源管理路由
│   ├── core/             # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py     # 配置加载
│   │   └── scheduler.py  # 定时调度器
│   ├── models/           # 数据模型
│   │   ├── __init__.py
│   │   ├── schema.py     # Pydantic 模型
│   │   └── database.py   # SQLite 表定义
│   ├── services/         # 业务逻辑
│   │   ├── __init__.py
│   │   ├── fetcher.py    # RSS 抓取
│   │   ├── parser.py     # 内容解析
│   │   ├── dedup.py      # 去重处理
│   │   ├── ai.py         # AI 处理
│   │   └── filter.py     # InfoQ 关键词过滤
│   ├── utils/            # 工具函数
│   │   ├── __init__.py
│   │   └── similarity.py # 标题相似度计算
│   └── main.py           # 应用入口
├── config/
│   └── sources.yaml      #订阅源配置
├── data/
│   └── news.db           # SQLite 数据库
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## 配置文件设计

### config/sources.yaml

```yaml
# 全局设置
settings:
  fetch_interval: 60      # 抓取间隔（分钟）
  ai_model: "gpt-4o-mini" # OpenAI 模型
  max_articles_per_fetch: 50  # 每次抓取上限

#订阅源列表
sources:
  # Twitter/X 用户（通过 RSSHub）
  - name: "elon_musk"
    type: "twitter"
    url: "https://rsshub.app/twitter/user/elonmusk"
    enabled: true
    
  - name: "karpathy"
    type: "twitter"
    url: "https://rsshub.app/twitter/user/karpathy"
    enabled: true

  # InfoQ 技术新闻（AI 过滤）
  - name: "infoq_ai"
    type: "infoq"
    url: "https://feed.infoq.com/"
    enabled: true
    filter_keywords:
      - "AI"
      - "大模型"
      - "机器学习"
      - "深度学习"
      - "生成式AI"
      - "AIGC"
      - "LLM"
      - "人工智能"

  # 通用 RSS 源
  - name: "openai_blog"
    type: "rss"
    url: "https://openai.com/blog/rss.xml"
    enabled: true
```

### 新增订阅源方式

1. 编辑 `config/sources.yaml`，添加新条目
2. 或通过 Web API `POST /api/sources` 添加
3. 无需修改代码

## 数据模型

### SQLite 表结构

```sql
--订阅源表
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    filter_keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文章表
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
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
);

-- 抓取日志表
CREATE TABLE fetch_logs (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    status TEXT,
    articles_count INTEGER,
    error_message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 核心流程

```
1. 读取 sources.yaml
   ↓
2. 遍历 enabled=true 的源
   ↓
3. 抓取 RSS → parser.parse()
   ↓
4. infoq 类型 → filter.apply_keywords()
   ↓
5. 去重检查 → dedup.check(link + title_similarity)
   ↓
6. 新文章 → ai.process(summary + category)
   ↓
7. 存入 SQLite
   ↓
8. 记录 fetch_logs
```

### 去重策略

- **链接唯一性**：数据库中 link 字段 UNIQUE
- **标题相似度**：TF-IDF 向量 + 余弦相似度，阈值 0.85

### AI 处理

- 模型：gpt-4o-mini（默认）
- 输入：标题 +原始摘要 + 内容（前 1000 字）
- 输出：精简摘要（≤ 200字）+ 分类标签
- 分类类别：技术动态、产品发布、研究进展、行业资讯、其他

## Web API

### 端点列表

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 文章列表 | `/api/articles` | GET | 分页、按分类/来源筛选 |
| 文章详情 | `/api/articles/{id}` | GET | 单篇文章详情 |
| 分类列表 | `/api/categories` | GET | 所有分类及文章数 |
|订阅源列表 | `/api/sources` | GET | 所有订阅源 |
| 新增订阅源 | `/api/sources` | POST | 添加新订阅源 |
| 更新订阅源 | `/api/sources/{id}` | PUT | 更新配置 |
| 删除订阅源 | `/api/sources/{id}` | DELETE | 删除订阅源 |
| 运行状态 | `/api/status` | GET | 当前调度状态 |
| 抓取日志 | `/api/logs` | GET | 最近抓取记录 |
| 立即抓取 | `/api/fetch` | POST | 抓取所有启用的源 |
| 抓取指定源 | `/api/fetch/{source_id}` | POST | 抓取单个源 |

### Pydantic 模型

```python
# app/models/schema.py

class SourceCreate(BaseModel):
    name: str
    type: str  # twitter | infoq | rss
    url: str
    enabled: bool = True
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
    source_name: str
    title: str
    summary: str | None
    ai_summary: str | None
    category: str | None
    link: str
    published_at: datetime | None
    fetched_at: datetime

class FetchLogResponse(BaseModel):
    id: int
    source_name: str
    status: str
    articles_count: int
    error_message: str | None
    fetched_at: datetime
```

## 环境变量

### .env.example

```env
OPENAI_API_KEY=sk-xxx
DATABASE_PATH=data/news.db
CONFIG_PATH=config/sources.yaml
```

## 依赖

### pyproject.toml

```toml
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
    "scikit-learn>=1.3.0",  # TF-IDF
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
]
```

## 验证方案

1. **单元测试**：测试 parser、filter、dedup、ai 各模块
2. **集成测试**：测试完整抓取流程
3. **手动验证**：
   - 运行 `uvicorn app.main:app --reload`
   - 访问 `/docs` 查看 API 文档
   - 手动触发抓取 `/api/fetch`
   - 检查数据库内容

## 扩展性

- **新增数据源类型**：在 `app/services/parser.py` 添加新解析器
- **新增 AI 分类**：修改 `app/services/ai.py` 的分类列表
- **更换 AI 服务**：修改 `app/services/ai.py` 的 API 调用逻辑
- **更换数据库**：修改 `app/models/database.py` 的连接逻辑