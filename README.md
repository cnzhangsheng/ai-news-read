# AI新闻订阅聚合工具

一个可扩展、配置友好的 AI 新闻订阅聚合 Web 应用。

## 功能

- 支持 Twitter/X、InfoQ、通用 RSS 等数据源
- 自动去重（链接 + 标题相似度）
- AI 精简摘要和自动分类（OpenAI）
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
| `/api/articles` | 文章列表（分页、筛选） |
| `/api/articles/{id}` | 文章详情 |
| `/api/categories` | 分类列表 |
| `/api/sources` |订阅源管理（CRUD） |
| `/api/status` | 运行状态 |
| `/api/fetch` | 手动触发抓取 |
| `/api/logs` | 抓取日志 |

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

## 数据源类型

| 类型 | 说明 |
|------|------|
| `twitter` | Twitter/X 用户（通过 RSSHub） |
| `infoq` | InfoQ 技术新闻（自动 AI 过滤） |
| `rss` | 通用 RSS 源 |

## 项目结构

```
ai_news_read/
├── app/
│   ├── api/          # Web API 路由
│   ├── core/         # 配置与调度器
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── config/           # 配置文件
├── data/             # SQLite 数据库
└── tests/            # 测试目录
```

## 测试

```bash
pytest tests/ -v
```