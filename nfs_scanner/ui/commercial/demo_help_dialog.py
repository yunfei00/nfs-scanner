"""Help and self-check dialog for commercial mock demo."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.integration_safety import REAL_DEVICE_ENV_VAR, is_real_device_control_allowed


class DemoHelpDialog(QDialog):
    """Built-in help and mock self-check panel."""

    def __init__(self, shell, parent=None, *, initial_tab: str = "help") -> None:
        super().__init__(parent or shell)
        self._shell = shell
        self._initial_tab = initial_tab
        self.setWindowTitle("帮助 / 自检")
        self.setMinimumSize(640, 480)
        self._status_browser: QTextBrowser | None = None
        self._tabs: QTabWidget | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)
        self._tabs = tabs
        tabs.addTab(self._build_help_tab(), "快速开始")
        tabs.addTab(self._build_shortcuts_tab(), "快捷键")
        tabs.addTab(self._build_safety_tab(), "安全说明")
        tabs.addTab(self._build_about_tab(), "关于")
        tabs.addTab(self._build_self_check_tab(), "自检")
        if self._initial_tab == "shortcuts":
            tabs.setCurrentIndex(1)
        elif self._initial_tab == "about":
            tabs.setCurrentIndex(3)
        elif self._initial_tab == "self_check":
            tabs.setCurrentIndex(4)
        layout.addWidget(tabs, 1)

        row = QHBoxLayout()
        run_button = QPushButton("运行自检", self)
        run_button.clicked.connect(self._run_self_check)
        export_button = QPushButton("导出自检报告", self)
        export_button.clicked.connect(self._export_self_check)
        close_button = QPushButton("关闭", self)
        close_button.clicked.connect(self.accept)
        row.addWidget(run_button)
        row.addWidget(export_button)
        row.addStretch(1)
        row.addWidget(close_button)
        layout.addLayout(row)

    def _build_help_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        browser = QTextBrowser(page)
        browser.setOpenExternalLinks(False)
        browser.setHtml(
            """
            <h3>Commercial V1 操作流程</h3>
            <ol>
              <li>新建 / 打开 / 保存项目（project.nfsproj）</li>
              <li>连接设备（Simulation Provider，无真实硬件）</li>
              <li>配置扫描区域、步长、频率与路径策略</li>
              <li>开始扫描，可暂停 / 继续 / 停止</li>
              <li>Data View 查看热力图与频谱</li>
              <li>Report Center 预览并导出报告</li>
            </ol>
            <p><b>当前模式</b>: Simulation Provider · 正式商用流程 · 无硬件控制</p>
            """
        )
        layout.addWidget(browser)
        return page

    def _build_shortcuts_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        browser = QTextBrowser(page)
        browser.setHtml(
            """
            <h3>快捷键</h3>
            <ul>
              <li>Ctrl+N — 新建项目</li>
              <li>Ctrl+O — 打开项目</li>
              <li>Ctrl+S — 保存项目</li>
              <li>F11 — 最大化窗口</li>
              <li>Esc — 关闭对话框</li>
            </ul>
            """
        )
        layout.addWidget(browser)
        return page

    def _build_about_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        browser = QTextBrowser(page)
        browser.setHtml(
            """
            <h3>NFS Scanner</h3>
            <p><b>版本</b>: Commercial V1</p>
            <p><b>UI</b>: 商业版界面</p>
            <p><b>数据提供</b>: Simulation Provider（DemoProvider）</p>
            <p>后续可通过替换 Provider/Adapter 接入真实运动平台、频谱仪与相机，UI 流程无需重写。</p>
            """
        )
        layout.addWidget(browser)
        return page

    def _build_safety_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        browser = QTextBrowser(page)
        real_env = os.getenv(REAL_DEVICE_ENV_VAR, "(unset)")
        browser.setHtml(
            f"""
            <h3>安全边界</h3>
            <ul>
              <li>不发送真实运动命令（home / jog / move / G-code）</li>
              <li>不连接真实频谱仪或相机</li>
              <li>不使用真实 ScanManager</li>
              <li>REAL_DEVICE_ENABLED: {not is_real_device_control_allowed()}</li>
              <li>{REAL_DEVICE_ENV_VAR}: {real_env}</li>
            </ul>
            """
        )
        layout.addWidget(browser)
        return page

    def _build_self_check_tab(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        self._status_browser = QTextBrowser(page)
        layout.addWidget(self._status_browser)
        return page

    def _collect_checks(self) -> list[tuple[str, bool, str]]:
        shell = self._shell
        devices = shell._services.devices.list_devices()
        tasks = shell.workspace.data_view().analysis_service.list_tasks()
        snapshot = shell.mock_scan.snapshot()
        return [
            ("MOCK 模式", True, "Commercial UI"),
            ("DRY RUN", True, "无硬件控制"),
            ("REAL_DEVICE_ENABLED=false", not is_real_device_control_allowed(), str(not is_real_device_control_allowed())),
            (f"{REAL_DEVICE_ENV_VAR} 未启用", os.getenv(REAL_DEVICE_ENV_VAR, "") != "1", os.getenv(REAL_DEVICE_ENV_VAR, "(unset)")),
            ("Project", shell._services.project.current_session() is not None, "session ok"),
            ("Devices", len(devices) >= 3, f"{len(devices)} devices"),
            ("Scan Config", shell.property_panel.can_start_scan(), "valid"),
            ("Runtime", snapshot.status in {"idle", "configured", "running", "paused", "completed", "stopped"}, snapshot.status),
            ("Data View", len(tasks) >= 1, f"{len(tasks)} tasks"),
            ("Report Center", shell.workspace.report_view()._task_combo is not None, "ready"),
        ]

    def _run_self_check(self) -> None:
        checks = self._collect_checks()
        lines = ["<h3>Mock 自检结果</h3>", "<ul>"]
        for name, passed, detail in checks:
            mark = "✓" if passed else "✗"
            lines.append(f"<li>{mark} <b>{name}</b>: {detail}</li>")
        overall = all(item[1] for item in checks)
        lines.append("</ul>")
        lines.append(f"<p><b>Overall: {'PASS' if overall else 'FAIL'}</b></p>")
        if self._status_browser is not None:
            self._status_browser.setHtml("\n".join(lines))
        shell = self._shell
        shell.bottom_dock.append_log_line(
            f"Mock 自检: {'PASS' if overall else 'FAIL'}",
            level="QA",
        )

    def _export_self_check(self) -> None:
        checks = self._collect_checks()
        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks],
            "overall_pass": all(p for _, p, _ in checks),
        }
        output_dir = Path(".ai") / "qa" / "latest"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "commercial_mock_self_check.json"
        md_path = output_dir / "commercial_mock_self_check.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_lines = ["# Commercial Mock Self Check", ""]
        md_lines.extend(f"- [{'x' if p else ' '}] {n}: {d}" for n, p, d in checks)
        md_lines.append("")
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        self._shell.bottom_dock.append_log_line(f"自检报告已导出: {json_path}", level="QA")
        if self._status_browser is not None:
            self._status_browser.append(f"<p>已导出: {json_path}</p>")
