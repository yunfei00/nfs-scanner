from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from PySide6.QtCore import QObject, Signal

from nfs_scanner.core.drivers.motion.base import MotionDriver
from nfs_scanner.core.drivers.spectrum.base import SpectrumDriver, TraceInfo
from nfs_scanner.core.scan.task_files import make_task_dir, write_meta
from nfs_scanner.core.scan.trace_store import TraceStore, TraceGrid


@dataclass(frozen=True)
class ScanParams:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    step_mm: float
    z_height_mm: float
    feed: float
    freq_hz: float


class ScanRunner(QObject):
    progress = Signal(int, int)        # done, total
    status = Signal(str)               # text
    finished = Signal(str, bool, str)  # task_id, ok, message

    def __init__(
        self,
        *,
        task_id: str,
        task_name: str,
        scans_dir: Path,
        params: ScanParams,
        traces: List[TraceInfo],
        motion: MotionDriver,
        spectrum: SpectrumDriver,
    ) -> None:
        super().__init__()
        self.task_id = task_id
        self.task_name = task_name
        self.scans_dir = scans_dir
        self.params = params
        self.traces = traces
        self.motion = motion
        self.spectrum = spectrum

        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.clear()

    def request_stop(self) -> None:
        self._stop.set()

    def request_pause(self, on: bool) -> None:
        if on:
            self._pause.set()
        else:
            self._pause.clear()

    def run(self) -> None:
        try:
            task_dir = make_task_dir(self.scans_dir, self.task_id)
            store = TraceStore(task_dir)

            xs = np.arange(self.params.x_min, self.params.x_max + 1e-9, self.params.step_mm, dtype=np.float32)
            ys = np.arange(self.params.y_min, self.params.y_max + 1e-9, self.params.step_mm, dtype=np.float32)
            nx, ny = len(xs), len(ys)

            freqs = np.array([self.params.freq_hz], dtype=np.float32)  # nf=1

            # 每个 trace 一个 values 网格 (ny,nx,1)
            grids = {}
            for t in self.traces:
                grids[t.name] = np.zeros((ny, nx, 1), dtype=np.float32)

            total = nx * ny
            done = 0

            self.status.emit("Connecting drivers...")
            self.motion.connect()
            self.spectrum.connect()
            self.spectrum.set_frequency(self.params.freq_hz)

            self.status.emit("Homing...")
            self.motion.home()

            # 扫描：按 y 行扫描（你后续要蛇形也可以）
            self.status.emit("Scanning...")
            for iy, y in enumerate(ys):
                for ix, x in enumerate(xs):
                    if self._stop.is_set():
                        raise RuntimeError("User stopped")

                    while self._pause.is_set() and not self._stop.is_set():
                        self.status.emit("Paused")
                        threading.Event().wait(0.05)

                    self.motion.move_to(float(x), float(y), float(self.params.z_height_mm), float(self.params.feed))

                    for tr in self.traces:
                        v = self.spectrum.measure_trace_point(tr.name)
                        grids[tr.name][iy, ix, 0] = float(v)

                    done += 1
                    if done % 5 == 0 or done == total:
                        self.progress.emit(done, total)

            # 落盘
            self.status.emit("Saving...")
            trace_list = []
            for tr in self.traces:
                grid = TraceGrid(
                    trace_name=tr.name,
                    unit=tr.unit or "dB",
                    xs=xs,
                    ys=ys,
                    freqs=freqs,
                    values=grids[tr.name],
                )
                store.save_grid(grid)
                trace_list.append({"name": tr.name, "kind": tr.kind, "unit": tr.unit})

            meta = {
                "task_id": self.task_id,
                "task_name": self.task_name,
                "params": {
                    "x_min": self.params.x_min,
                    "x_max": self.params.x_max,
                    "y_min": self.params.y_min,
                    "y_max": self.params.y_max,
                    "step_mm": self.params.step_mm,
                    "z_height_mm": self.params.z_height_mm,
                    "feed": self.params.feed,
                    "freq_hz": self.params.freq_hz,
                },
                "trace_list": trace_list,
            }
            write_meta(task_dir, meta)

            self.finished.emit(self.task_id, True, "OK")
        except Exception as e:
            self.finished.emit(self.task_id, False, str(e))
        finally:
            try:
                self.motion.disconnect()
            except Exception:
                pass
            try:
                self.spectrum.disconnect()
            except Exception:
                pass
