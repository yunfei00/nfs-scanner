from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

log = logging.getLogger(__name__)


def deep_merge(base: dict, override: dict) -> dict:
    """
    深合并：override 的值覆盖 base；若两边都是 dict，则递归合并。
    """
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping: {path}")
        return data


def save_yaml(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            dict(data),
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


@dataclass(frozen=True)
class ConfigPaths:
    default_config_path: Path
    user_config_path: Path


class ConfigManager:
    """
    配置加载优先级：
      1) default_config.yaml（内置默认）
      2) user_config.yaml（用户覆盖，缺省时为空）
    """

    def __init__(self, paths: ConfigPaths):
        self._paths = paths
        self._config: dict[str, Any] = {}

    @property
    def config(self) -> dict[str, Any]:
        return self._config

    @property
    def user_config_path(self) -> Path:
        return self._paths.user_config_path

    def load(self) -> dict[str, Any]:
        default_cfg = load_yaml(self._paths.default_config_path)
        user_cfg = load_yaml(self._paths.user_config_path)

        cfg = deep_merge(default_cfg, user_cfg)
        self._config = cfg

        log.info("Config loaded.")
        log.info("default_config=%s", self._paths.default_config_path)
        log.info("user_config=%s (exists=%s)", self._paths.user_config_path, self._paths.user_config_path.exists())
        return cfg

    def ensure_user_config_exists(self) -> None:
        """
        商业交付关键：第一次启动就把 user_config 写出来，客户可直接改。
        """
        if self._paths.user_config_path.exists():
            return
        default_cfg = load_yaml(self._paths.default_config_path)
        save_yaml(self._paths.user_config_path, default_cfg)
        log.info("User config created: %s", self._paths.user_config_path)
