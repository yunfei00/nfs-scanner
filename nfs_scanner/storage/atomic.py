"""Durable filesystem primitives shared by configuration and scan storage."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_bytes(path: str | Path, payload: bytes) -> Path:
    """Replace one file atomically after flushing its temporary payload."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
        return target
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: str | Path, payload: Any) -> Path:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return atomic_write_text(path, serialized)


def append_text_durable(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Append one record and force it through the operating-system buffer."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding=encoding, newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    return target


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum_manifest(root: str | Path, *, filename: str = "checksums.sha256") -> Path:
    """Write deterministic SHA-256 entries for every regular result file."""

    root_path = Path(root)
    checksum_path = root_path / filename
    files = sorted(
        path
        for path in root_path.rglob("*")
        if path.is_file() and path != checksum_path and not path.name.endswith(".tmp")
    )
    lines = [f"{sha256_file(path)}  {path.relative_to(root_path).as_posix()}" for path in files]
    return atomic_write_text(checksum_path, "\n".join(lines) + ("\n" if lines else ""))
