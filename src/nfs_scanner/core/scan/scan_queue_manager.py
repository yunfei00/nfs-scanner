from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class QueueItem:
    id: str
    created_at: str
    status: str  # queued/running/done/failed/skipped/canceled
    params: dict[str, Any]
    trace_list: list[dict[str, Any]]
    task_id: str | None = None
    message: str = ""


class ScanQueueManager:
    """
    SQLite 持久化扫描队列（串行执行）。
    - 自动建表（不会要求你手动改 schema.sql）
    - 只依赖 SQLiteStore.connect()
    """

    def __init__(self, store) -> None:
        self.store = store
        self.ensure_table()

    def ensure_table(self) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_queue_item (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  status TEXT NOT NULL,
                  params_json TEXT NOT NULL,
                  trace_list_json TEXT NOT NULL,
                  task_id TEXT,
                  message TEXT DEFAULT ''
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_queue_status ON scan_queue_item(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_queue_created ON scan_queue_item(created_at);")

    def add(self, *, item_id: str, params: dict[str, Any], trace_list: list[dict[str, Any]]) -> None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.store.connect() as conn:
            conn.execute(
                "INSERT INTO scan_queue_item (id, created_at, status, params_json, trace_list_json) VALUES (?,?,?,?,?)",
                (
                    item_id,
                    created_at,
                    "queued",
                    json.dumps(params, ensure_ascii=False),
                    json.dumps(trace_list, ensure_ascii=False),
                ),
            )

    def list(self, limit: int = 300) -> list[QueueItem]:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, status, params_json, trace_list_json, task_id, message "
                "FROM scan_queue_item ORDER BY created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()

        out: list[QueueItem] = []
        for r in rows:
            out.append(
                QueueItem(
                    id=r[0],
                    created_at=r[1],
                    status=r[2],
                    params=json.loads(r[3]),
                    trace_list=json.loads(r[4]),
                    task_id=r[5],
                    message=r[6] or "",
                )
            )
        return out

    def next_queued(self) -> Optional[QueueItem]:
        with self.store.connect() as conn:
            r = conn.execute(
                "SELECT id, created_at, status, params_json, trace_list_json, task_id, message "
                "FROM scan_queue_item WHERE status='queued' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
        if not r:
            return None
        return QueueItem(
            id=r[0],
            created_at=r[1],
            status=r[2],
            params=json.loads(r[3]),
            trace_list=json.loads(r[4]),
            task_id=r[5],
            message=r[6] or "",
        )

    def update_status(self, item_id: str, status: str, message: str = "") -> None:
        with self.store.connect() as conn:
            conn.execute(
                "UPDATE scan_queue_item SET status=?, message=? WHERE id=?",
                (status, message, item_id),
            )

    def bind_task(self, item_id: str, task_id: str) -> None:
        with self.store.connect() as conn:
            conn.execute("UPDATE scan_queue_item SET task_id=? WHERE id=?", (task_id, item_id))

    def delete(self, item_id: str) -> None:
        with self.store.connect() as conn:
            conn.execute("DELETE FROM scan_queue_item WHERE id=?", (item_id,))

    def bulk_update(self, ids: list[str], status: str, message: str = "") -> None:
        if not ids:
            return
        with self.store.connect() as conn:
            for item_id in ids:
                conn.execute(
                    "UPDATE scan_queue_item SET status=?, message=? WHERE id=?",
                    (status, message, item_id),
                )
