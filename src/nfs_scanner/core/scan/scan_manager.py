from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class ScanArea:
    x_min: float
    x_max: float
    y_min: float
    y_max: float

@dataclass(frozen=True)
class ScanConfig:
    step_mm: float
    z_height_mm: float
    area: ScanArea

class ScanManager:
    """
    阶段1：先做“假扫描”写入DB，跑通商业闭环。
    阶段2：再把 value 由真实设备采集替换。
    """
    def __init__(self, store):
        self.store = store

    def create_fake_task(self, cfg: dict) -> str:
        # 从配置读参数
        scan = (cfg.get("scan") or {})
        area = (scan.get("area") or {})
        step = float(scan.get("step_mm", 1.0))
        z = float(scan.get("z_height_mm", 1.0))

        area_obj = ScanArea(
            x_min=float(area.get("x_min", -5.0)),
            x_max=float(area.get("x_max", 5.0)),
            y_min=float(area.get("y_min", -5.0)),
            y_max=float(area.get("y_max", 5.0)),
        )
        scfg = ScanConfig(step_mm=step, z_height_mm=z, area=area_obj)

        task_id = str(uuid4())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        name = f"FakeScan {created_at}"

        self.store.create_task(
            task_id=task_id,
            name=name,
            created_at=created_at,
            status="done",
            config=cfg,
            note="auto-generated fake scan for pipeline validation",
        )

        # 生成点位并写入：value 用一个简单函数模拟（后续替换为真实采集值）
        points = []
        x = scfg.area.x_min
        while x <= scfg.area.x_max + 1e-9:
            y = scfg.area.y_min
            while y <= scfg.area.y_max + 1e-9:
                v = (x * x + y * y) ** 0.5  # 示例：半径
                points.append((x, y, scfg.z_height_mm, float(v)))
                y += scfg.step_mm
            x += scfg.step_mm

        self.store.insert_points(task_id, points)
        log.info("Fake scan task done: %s points=%d", task_id, len(points))
        return task_id
