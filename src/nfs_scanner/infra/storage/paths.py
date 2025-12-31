from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "NFSScanner"

def get_app_home() -> Path:
    # 1) 支持环境变量强制指定（商业现场最常用）
    env = os.getenv("NFS_APP_HOME")
    if env:
        return Path(env).expanduser().resolve()

    # 2) 默认路径：Windows 用 APPDATA；Linux 用 ~/.local/share
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return (base / APP_NAME).resolve()

    # linux/mac
    return (Path.home() / ".local" / "share" / APP_NAME).resolve()

def ensure_dirs(app_home: Path) -> dict[str, Path]:
    paths = {
        "home": app_home,
        "config": app_home / "config",
        "logs": app_home / "logs",
        "data": app_home / "data",
        "exports": app_home / "exports",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths
