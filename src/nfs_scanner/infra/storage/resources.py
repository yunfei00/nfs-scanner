from __future__ import annotations
from pathlib import Path
import importlib.resources as ir

def get_schema_path() -> Path:
    pkg = "nfs_scanner.infra.storage"
    with ir.as_file(ir.files(pkg) / "schema.sql") as p:
        return p
