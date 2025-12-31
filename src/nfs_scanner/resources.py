from __future__ import annotations

from pathlib import Path
import importlib.resources as ir


def get_default_config_path() -> Path:
    """
    返回包内 default_config.yaml 的可访问路径。
    开发态：就是源文件路径；
    打包态：importlib.resources 会提供可读的临时路径/句柄。
    """
    pkg = "nfs_scanner.infra.config"
    with ir.as_file(ir.files(pkg) / "default_config.yaml") as p:
        return p
