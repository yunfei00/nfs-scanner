"""Top-level exception reporting for the desktop process."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from types import TracebackType

from PySide6.QtWidgets import QApplication, QMessageBox


ExceptionHook = Callable[[type[BaseException], BaseException, TracebackType | None], None]


def install_exception_hook(logger: logging.Logger) -> ExceptionHook:
    """Log uncaught exceptions and show one concise operator-facing message."""

    previous_hook = sys.excepthook

    def handle_exception(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback: TracebackType | None,
    ) -> None:
        if issubclass(exception_type, KeyboardInterrupt):
            previous_hook(exception_type, exception, traceback)
            return
        logger.critical(
            "应用发生未处理异常",
            exc_info=(exception_type, exception, traceback),
        )
        if QApplication.instance() is not None:
            QMessageBox.critical(
                None,
                "应用错误",
                "程序发生未处理错误。设备任务将停止，请导出诊断包并联系技术支持。",
            )

    sys.excepthook = handle_exception
    return previous_hook
