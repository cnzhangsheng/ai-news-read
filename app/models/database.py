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
                enabled BOOLEAN DEFAULT 1,
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


def get_db():
    """返回数据库连接的上下文管理器"""
    return aiosqlite.connect(env_config.database_path)


class SourceDB:
    @staticmethod
    async def create(name: str, type: str, url: str, enabled: bool = True,
                     filter_keywords: list[str] | None = None) -> int:
        async with get_db() as db:
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
        async with get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def get_by_id(id: int) -> dict[str, Any] | None:
        async with get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources WHERE id = ?", (id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_enabled() -> list[dict[str, Any]]:
        async with get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM sources WHERE enabled = 1")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    async def update(id: int, **kwargs: Any) -> bool:
        async with get_db() as db:
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
        async with get_db() as db:
            await db.execute("DELETE FROM sources WHERE id = ?", (id,))
            await db.commit()
            return True


class ArticleDB:
    @staticmethod
    async def create(source_id: int, title: str, link: str, summary: str | None = None,
                     content: str | None = None, published_at: datetime | None = None,
                     title_hash: str | None = None, is_duplicate: bool = False) -> int | None:
        async with get_db() as db:
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
        async with get_db() as db:
            await db.execute(
                "UPDATE articles SET ai_summary = ?, category = ? WHERE id = ?",
                (ai_summary, category, id)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_list(page: int = 1, page_size: int = 20, category: str | None = None,
                       source_id: int | None = None) -> tuple[list[dict[str, Any]], int]:
        async with get_db() as db:
            db.row_factory = aiosqlite.Row
            offset = (page - 1) * page_size

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
        async with get_db() as db:
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
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT DISTINCT category FROM articles WHERE category IS NOT NULL AND is_duplicate = 0"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    @staticmethod
    async def get_title_hashes(source_id: int, limit: int = 100) -> list[str]:
        async with get_db() as db:
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
        async with get_db() as db:
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
        async with get_db() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT l.*, s.name as source_name FROM fetch_logs l
                    JOIN sources s ON l.source_id = s.id
                    ORDER BY l.fetched_at DESC LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]