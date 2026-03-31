# app/main.py
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))