"""
任务持久化存储 - SQLite 实现

替代内存字典，保证重启后任务数据不丢失。
"""

import json
import sqlite3
import time
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("circuitai.task_store")

# 数据库文件路径（容器中可挂载 volume）
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


class TaskStore:
    """线程安全的 SQLite 任务存储。
    
    兼容原 dict 接口：store[task_id] = {...}, task_id in store, store[task_id], del store[task_id]
    """

    def __init__(self, db_path: str = str(DB_PATH)):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        # 用主线程连接建表
        self._init_table(self._get_conn())
        logger.info("TaskStore 初始化完成: %s", db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """每个线程一个连接（SQLite 线程限制）。"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, timeout=10)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    @staticmethod
    def _init_table(conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id   TEXT PRIMARY KEY,
                status    TEXT NOT NULL DEFAULT 'processing',
                data      TEXT NOT NULL DEFAULT '{}',
                created   REAL NOT NULL,
                updated   REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created)")
        conn.commit()

    # ---- dict-like 接口 ----

    def __setitem__(self, task_id: str, value: dict):
        conn = self._get_conn()
        created = value.get("created", time.time())
        conn.execute(
            """INSERT INTO tasks (task_id, status, data, created, updated)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(task_id) DO UPDATE SET
                 status=excluded.status, data=excluded.data, updated=excluded.updated""",
            (task_id, value.get("status", "processing"), json.dumps(value, ensure_ascii=False), created, time.time()),
        )
        conn.commit()

    def __getitem__(self, task_id: str) -> dict:
        conn = self._get_conn()
        row = conn.execute("SELECT data FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return json.loads(row[0])

    def __contains__(self, task_id: str) -> bool:
        conn = self._get_conn()
        row = conn.execute("SELECT 1 FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        return row is not None

    def __delitem__(self, task_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
        conn.commit()

    def get(self, task_id: str, default=None):
        try:
            return self[task_id]
        except KeyError:
            return default

    def items(self):
        """遍历所有任务（用于过期清理）。"""
        conn = self._get_conn()
        rows = conn.execute("SELECT task_id, data FROM tasks").fetchall()
        for task_id, data in rows:
            yield task_id, json.loads(data)

    def list_completed(self, limit: int = 20, offset: int = 0) -> list[dict]:
        """返回已完成的任务列表（最新在前），不含完整result以节省带宽。"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT task_id, status, data, created FROM tasks WHERE status='done' ORDER BY created DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        results = []
        for task_id, status, data, created in rows:
            parsed = json.loads(data)
            # 只返回摘要，不返回完整result
            summary = {
                "task_id": task_id,
                "status": status,
                "created": created,
                "circuit_type": None,
                "component_count": 0,
                "error_count": 0,
            }
            result = parsed.get("result") or {}
            func = result.get("function")
            if isinstance(func, dict):
                summary["circuit_type"] = func.get("circuit_type")
            elif isinstance(func, str):
                summary["circuit_type"] = func[:60]
            summary["component_count"] = len(result.get("components") or [])
            summary["error_count"] = len(result.get("errors") or [])
            results.append(summary)
        return results

    def count_completed(self) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()
        return row[0] if row else 0

    # ---- 清理 ----

    def cleanup_expired(self, max_age_seconds: int = 600):
        """删除超龄任务。"""
        cutoff = time.time() - max_age_seconds
        conn = self._get_conn()
        cur = conn.execute("DELETE FROM tasks WHERE created < ?", (cutoff,))
        if cur.rowcount:
            logger.info("清理 %d 个过期任务", cur.rowcount)
        conn.commit()


# 全局单例
task_store = TaskStore()
