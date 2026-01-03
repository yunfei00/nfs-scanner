from __future__ import annotations
import time
from .base import MotionDriver

class MockMotion(MotionDriver):
    def connect(self) -> None:
        return
    def disconnect(self) -> None:
        return
    def home(self) -> None:
        time.sleep(0.05)
    def move_to(self, x: float, y: float, z: float, feed: float) -> None:
        # 模拟移动延迟
        time.sleep(0.01)
