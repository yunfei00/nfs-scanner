"""Format helpers for mock runtime UI display."""

from __future__ import annotations


def format_duration_seconds(seconds: float) -> str:
    """Format seconds as a compact human-readable duration."""

    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_runtime_status(status: str) -> str:
    """Map mock runtime status codes to Chinese labels."""

    labels = {
        "idle": "就绪",
        "configured": "已配置",
        "running": "扫描中",
        "paused": "已暂停",
        "completed": "已完成",
        "stopped": "已停止",
        "error": "错误",
    }
    return labels.get(status, status)
