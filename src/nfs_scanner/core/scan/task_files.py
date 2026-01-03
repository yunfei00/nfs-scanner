from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Any

def make_task_dir(scans_dir: Path, task_id: str) -> Path:
    d = scans_dir / task_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "traces").mkdir(parents=True, exist_ok=True)
    (d / "exports").mkdir(parents=True, exist_ok=True)
    return d

def write_meta(task_dir: Path, meta: dict[str, Any]) -> Path:
    meta = dict(meta)
    meta.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    p = task_dir / "meta.json"
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
