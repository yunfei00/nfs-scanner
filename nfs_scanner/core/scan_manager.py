"""Placeholder scan lifecycle manager."""

from __future__ import annotations

import logging


class ScanManager:
    """Manage the scan task lifecycle without executing real scans."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._is_scanning = False

    @property
    def is_scanning(self) -> bool:
        """Whether the placeholder scan task is marked as running."""

        return self._is_scanning

    def start_scan(self) -> bool:
        """Enter placeholder scan-running state."""

        if self._is_scanning:
            self._logger.warning("扫描任务已经处于运行状态。")
            return False

        self._is_scanning = True
        self._logger.info("扫描任务已进入占位运行状态。")
        return True

    def stop_scan(self) -> bool:
        """Leave placeholder scan-running state."""

        if not self._is_scanning:
            self._logger.warning("当前没有运行中的扫描任务。")
            return False

        self._is_scanning = False
        self._logger.info("扫描任务已停止。")
        return True
