from __future__ import annotations

import json
import sqlite3
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class ScanTaskRow:
    id: str
    name: str
    created_at: str
    status: str
    note: str

class SQLiteStore:
    def __init__(self, db_path: Path, schema_path: Path):
        self.db_path = db_path
        self.schema_path = schema_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        sql = self.schema_path.read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.executescript(sql)
        log.info("SQLite initialized: %s", self.db_path)

    def create_task(self, task_id: str, name: str, created_at: str, status: str, config: dict[str, Any], note: str = "") -> None:
        cfg_json = json.dumps(config, ensure_ascii=False)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO scan_task (id, name, created_at, status, config_json, note) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, name, created_at, status, cfg_json, note),
            )
        log.info("ScanTask created: %s %s", task_id, name)

    def insert_points(self, task_id: str, points: list[tuple[float, float, float, float]]) -> None:
        # points: [(x,y,z,value), ...]
        with self.connect() as conn:
            conn.executemany(
                "INSERT INTO scan_point (task_id, x, y, z, value) VALUES (?, ?, ?, ?, ?)",
                [(task_id, x, y, z, v) for (x, y, z, v) in points],
            )
        log.info("ScanPoints inserted: task=%s count=%d", task_id, len(points))

    def list_tasks(self, limit: int = 20) -> list[ScanTaskRow]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at, status, COALESCE(note,'') FROM scan_task ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [ScanTaskRow(*r) for r in rows]
