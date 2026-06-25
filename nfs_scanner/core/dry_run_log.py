"""Dry-run command recording (no hardware I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


DRY_RUN_BANNER = "DRY RUN - NO HARDWARE CONTROL"


@dataclass(slots=True, frozen=True)
class DryRunCommand:
    """One command that would be sent to hardware in a future real integration."""

    adapter: str
    command: str
    parameters: dict[str, str]
    timestamp: str
    note: str = DRY_RUN_BANNER

    def format_line(self) -> str:
        params = ", ".join(f"{key}={value}" for key, value in self.parameters.items())
        return f"[{self.note}] {self.adapter}.{self.command}({params}) @ {self.timestamp}"


@dataclass
class DryRunCommandLog:
    """In-memory append-only dry-run command history."""

    _entries: list[DryRunCommand] = field(default_factory=list)

    def append(self, command: DryRunCommand) -> None:
        self._entries.append(command)

    def record(
        self,
        adapter: str,
        command: str,
        parameters: dict[str, str] | None = None,
    ) -> DryRunCommand:
        entry = DryRunCommand(
            adapter=adapter,
            command=command,
            parameters=parameters or {},
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
        self.append(entry)
        return entry

    def entries(self) -> list[DryRunCommand]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def format_lines(self) -> list[str]:
        return [entry.format_line() for entry in self._entries]
