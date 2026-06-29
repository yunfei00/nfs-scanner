"""In-memory log bus for commercial UI bottom dock filtering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable


@dataclass(slots=True)
class LogEntry:
    level: str
    message: str
    timestamp: str

    def formatted(self) -> str:
        return f"[{self.level}] {self.message}"


class LogBus:
    """Store recent UI log lines and support level filtering."""

    MAX_ENTRIES = 1000

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []
        self._listeners: list[Callable[[], None]] = []

    def append(self, message: str, *, level: str = "INFO") -> LogEntry:
        entry = LogEntry(
            level=level.upper(),
            message=message.strip(),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self._entries.append(entry)
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[-self.MAX_ENTRIES :]
        for listener in self._listeners:
            listener()
        return entry

    def entries(self, *, levels: Iterable[str] | None = None) -> list[LogEntry]:
        if levels is None:
            return list(self._entries)
        allowed = {level.upper() for level in levels}
        return [entry for entry in self._entries if entry.level in allowed]

    def clear(self) -> None:
        self._entries.clear()
        for listener in self._listeners:
            listener()

    def subscribe(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)
