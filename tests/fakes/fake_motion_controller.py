"""Fake motion controller for integration tests."""

from __future__ import annotations

from nfs_scanner.devices.motion.mock_motion import MockMotionController


class FakeMotionController(MockMotionController):
    """Record move commands and simulate idle waits instantly."""

    def __init__(self) -> None:
        super().__init__()
        self.move_calls: list[tuple[float, float, float]] = []
        self.stop_calls = 0
        self.emergency_stop_calls = 0

    def emergency_stop(self) -> None:
        self.emergency_stop_calls += 1
        super().emergency_stop()

    def move_absolute(self, x: float, y: float, z: float | None = None) -> None:
        if z is None:
            z = self.get_position()[2]
        self.move_calls.append((x, y, z))
        super().move_absolute(x, y, z)

    def stop(self) -> None:
        self.stop_calls += 1
        super().stop()

    def wait_until_idle(
        self,
        target: tuple[float, float, float] | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self._ensure_connected()
