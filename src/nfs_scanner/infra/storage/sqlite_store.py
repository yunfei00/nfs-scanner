from __future__ import annotations

import csv
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


    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, name, created_at, status, config_json, COALESCE(note,'') "
                "FROM scan_task WHERE id=?",
                (task_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "created_at": row[2],
            "status": row[3],
            "config_json": row[4],
            "note": row[5],
        }

    def count_points(self, task_id: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(1) FROM scan_point WHERE task_id=?",
                (task_id,),
            ).fetchone()
        return int(row[0] if row else 0)

    def export_points_csv(self, task_id: str, out_path: Path) -> int:
        """
        导出点位到 CSV：x,y,z,value
        返回导出行数
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT x, y, z, value FROM scan_point WHERE task_id=? ORDER BY id ASC",
                (task_id,),
            )
            with out_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["x", "y", "z", "value"])
                n = 0
                for r in rows:
                    w.writerow(r)
                    n += 1
        return n

    def fetch_points(self, task_id: str) -> list[tuple[float, float, float, float]]:
        """
        返回 [(x,y,z,value), ...]
        """
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT x, y, z, value FROM scan_point WHERE task_id=? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
        return [(float(x), float(y), float(z), float(v) if v is not None else 0.0) for (x, y, z, v) in rows]

def queue_add(self, *, item_id: str, created_at: str, params: dict, trace_list: list, status: str = "queued") -> None:
    import json
    with self.connect() as conn:
        conn.execute(
            "INSERT INTO scan_queue_item (id, created_at, status, params_json, trace_list_json) VALUES (?,?,?,?,?)",
            (item_id, created_at, status, json.dumps(params, ensure_ascii=False), json.dumps(trace_list, ensure_ascii=False)),
        )

def queue_list(self, *, limit: int = 200) -> list[dict]:
    import json
    with self.connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, status, params_json, trace_list_json, task_id, message FROM scan_queue_item ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "created_at": r[1],
            "status": r[2],
            "params": json.loads(r[3]),
            "trace_list": json.loads(r[4]),
            "task_id": r[5],
            "message": r[6] or "",
        })
    return out

def queue_update_status(self, item_id: str, status: str, message: str = "") -> None:
    with self.connect() as conn:
        conn.execute("UPDATE scan_queue_item SET status=?, message=? WHERE id=?", (status, message, item_id))

def queue_bind_task(self, item_id: str, task_id: str) -> None:
    with self.connect() as conn:
        conn.execute("UPDATE scan_queue_item SET task_id=? WHERE id=?", (task_id, item_id))

def queue_delete(self, item_id: str) -> None:
    with self.connect() as conn:
        conn.execute("DELETE FROM scan_queue_item WHERE id=?", (item_id,))


def queue_next_queued(self) -> dict | None:
    import json
    with self.connect() as conn:
        r = conn.execute(
            "SELECT id, created_at, status, params_json, trace_list_json, task_id, message "
            "FROM scan_queue_item WHERE status='queued' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
    if not r:
        return None
    return {
        "id": r[0],
        "created_at": r[1],
        "status": r[2],
        "params": json.loads(r[3]),
        "trace_list": json.loads(r[4]),
        "task_id": r[5],
        "message": r[6] or "",
    }

