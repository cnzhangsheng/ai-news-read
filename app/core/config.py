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