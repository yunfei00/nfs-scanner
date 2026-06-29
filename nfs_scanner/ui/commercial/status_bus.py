"""Lightweight status message bus for commercial UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class StatusMessage:
    text: str
    level: str = "INFO"


class StatusBus:
    """Broadcast short status messages to status bar or panels."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[StatusMessage], None]] = []
        self._last = StatusMessage("就绪")

    def emit(self, text: str, *, level: str = "INFO") -> None:
        message = StatusMessage(text=text, level=level.upper())
        self._last = message
        for listener in self._listeners:
            listener(message)

    def subscribe(self, callback: Callable[[StatusMessage], None]) -> None:
        self._listeners.append(callback)

    @property
    def last(self) -> StatusMessage:
        return self._last
