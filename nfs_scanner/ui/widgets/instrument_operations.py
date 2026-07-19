"""Instrument discovery, query, setting, and acquisition actions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread

from nfs_scanner.devices.spectrum import (
    InstrumentDiscoveryResult,
    SpectrumAnalyzerError,
    convert_zna_mmem_csv_to_row_text,
    save_fsw_trace_csv,
    save_n9020a_trace_csv,
    save_zna_trace_csv,
)
from nfs_scanner.core import SpectrumConfig
from nfs_scanner.infra.logging_config import get_logger

from .instrument_panel import InstrumentPanel

from .scan_workers import InstrumentSearchWorker


class InstrumentOperationsMixin:
    """Preserve the proven instrument handlers outside the page widget class."""

    def on_search_instruments(self) -> None:
        if self._instrument_search_thread is not None:
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("搜索中...")
        self.append_log("开始搜索仪表，请稍候...")
        self._write_instrument_search_log("开始搜索仪表（异步任务已启动）")

        self._instrument_search_thread = QThread(self)
        preferred_resources = self._load_cached_instrument_resources()
        if preferred_resources:
            self.append_log(f"读取到缓存设备 {len(preferred_resources)} 台，优先尝试直连识别")
        self._instrument_search_worker = InstrumentSearchWorker(preferred_resources=preferred_resources)
        self._instrument_search_worker.moveToThread(self._instrument_search_thread)
        self._instrument_search_thread.started.connect(self._instrument_search_worker.run)
        self._instrument_search_worker.finished.connect(self._on_instrument_search_finished)
        self._instrument_search_worker.finished.connect(self._instrument_search_thread.quit)
        self._instrument_search_worker.finished.connect(self._instrument_search_worker.deleteLater)
        self._instrument_search_thread.finished.connect(self._on_instrument_search_thread_finished)
        self._instrument_search_thread.finished.connect(self._instrument_search_thread.deleteLater)
        self._instrument_search_thread.start()

    def _on_instrument_search_finished(self, result: InstrumentDiscoveryResult) -> None:
        """处理异步仪表搜索结果，并同步更新 UI。"""

        if not result.pyvisa_available:
            for panel in self.instrument_panels:
                panel.set_discovered_message("未安装 pyvisa，无法通过 NI MAX 扫描 VISA 设备")
            self._write_instrument_search_log("仪表搜索失败：未安装 pyvisa，请先安装后重试")
            self.append_log("仪表搜索失败：未安装 pyvisa")
            return

        if not result.visa_backend_available:
            message = "VISA 后端不可用；请安装 NI-VISA，或安装 pyvisa-py 作为软件后端"
            for panel in self.instrument_panels:
                panel.set_discovered_message(message)
            self._write_instrument_search_log(f"仪表搜索已跳过：{message}；{result.visa_backend_error}")
            self.append_log(f"仪表搜索已跳过：{message}")
            return

        matched_resources: dict[str, list[str]] = {}
        first_matched_panel: InstrumentPanel | None = None

        for instrument_name in self.INSTRUMENT_ORDER:
            panel = self._find_instrument_panel(instrument_name)
            if panel is None:
                continue

            matched = result.matched_resources_for(instrument_name)
            matched_resources[instrument_name] = [item.resource_name for item in matched]
            if matched:
                summary = "；".join(f"{item.resource_name} -> {item.idn_text}" for item in matched[:2])
                if len(matched) > 2:
                    summary += f"；...共 {len(matched)} 台"
                panel.set_discovered_message(f"已匹配到 {instrument_name}: {summary}")
                if first_matched_panel is None:
                    first_matched_panel = panel
                for item in matched:
                    self.append_log(f"已找到 {instrument_name} 设备: {item.resource_name}")
            else:
                panel.set_discovered_message(f"未匹配到 {instrument_name}")

        self._save_cached_instrument_resources(matched_resources)

        if first_matched_panel is not None:
            self.instrument_tabs.setCurrentWidget(first_matched_panel)

        for instrument_name, resources in matched_resources.items():
            if resources:
                self._refresh_all_instrument_queries(instrument_name)

        self._write_instrument_search_log(f"仪表搜索完成：共扫描 {len(result.probes)} 个 VISA 资源")
        self.append_log(f"仪表搜索完成：共扫描 {len(result.probes)} 个 VISA 资源，详见 output/instrument_search.log")
        for probe in result.probes:
            if probe.error_message:
                self._write_instrument_search_log(f"VISA 资源探测失败: {probe.resource_name} | {probe.error_message}")
                continue
            match_text = probe.matched_instrument or "未识别"
            self._write_instrument_search_log(
                f"VISA 资源: {probe.resource_name} | *IDN?={probe.idn_text} | {match_text}"
            )

    def _find_instrument_panel(self, instrument_name: str) -> InstrumentPanel | None:
        """Return the panel instance for one instrument name."""

        return next((panel for panel in self.instrument_panels if panel.instrument_name == instrument_name), None)

    def on_instrument_query_requested(self, instrument_name: str, query_key: str) -> None:
        """处理仪表参数查询按钮，优先回填真实查询结果并写入日志。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return

        value, unit = self._query_instrument_value(instrument_name, query_key)
        panel.set_query_result(query_key, value, unit)
        label = self.QUERY_LABELS.get(query_key, query_key)
        suffix = f" {unit}" if unit else ""
        self.append_log(f"仪表查询: {instrument_name} - {label} = {value}{suffix}")

    def _refresh_all_instrument_queries(self, instrument_name: str) -> None:
        """发送该仪表支持的全部查询命令并同步刷新界面字段。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return

        query_keys = panel.get_supported_query_keys()
        if not query_keys:
            return

        self.append_log(f"仪表已连接，开始同步全部参数: {instrument_name}")
        for query_key in query_keys:
            value, unit = self._query_instrument_value(instrument_name, query_key)
            panel.set_query_result(query_key, value, unit)
            label = self.QUERY_LABELS.get(query_key, query_key)
            suffix = f" {unit}" if unit else ""
            self.append_log(f"仪表同步: {instrument_name} - {label} = {value}{suffix}")

    def _query_instrument_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """查询仪表参数：优先真实设备，失败后回退占位值。"""

        if instrument_name in self.INSTRUMENT_ORDER:
            return self._query_scpi_instrument_value(instrument_name, query_key)
        return self._mock_query_value(instrument_name, query_key)

    def _query_scpi_instrument_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """查询支持的 SCPI 仪表参数。优先走 VISA，ZNA67 再尝试串口回退。"""

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            return self._format_query_value(query_key, analyzer.query_setting(query_key))
        except SpectrumAnalyzerError as error:
            self.append_log(f"{instrument_name} 参数查询失败，已使用占位值: {error}")
            return self._mock_query_value(instrument_name, query_key)

    def _query_via_visa(
        self,
        command: str,
        *,
        instrument_name: str | None = None,
        timeout_ms: int = 1200,
    ) -> tuple[str | None, str]:
        """兼容旧入口，实际 VISA 访问已迁移到频谱适配器层。"""

        del command, instrument_name, timeout_ms
        return None, "仪表 VISA 查询已迁移到频谱适配器层"

    def _format_query_value(self, query_key: str, raw_value: str) -> tuple[str, str | None]:
        """格式化 SCPI 查询返回值，统一展示单位。"""

        cleaned_value = raw_value.strip()
        if query_key in {"start_freq", "center_freq", "stop_freq", "span"}:
            try:
                frequency_hz = float(cleaned_value)
                return self._to_preferred_frequency_unit(frequency_hz)
            except ValueError:
                return cleaned_value, None

        if query_key == "rbw":
            try:
                rbw_hz = float(cleaned_value)
                return self._to_preferred_frequency_unit(rbw_hz)
            except ValueError:
                return cleaned_value, None

        if query_key == "points":
            try:
                return str(int(float(cleaned_value))), None
            except ValueError:
                return cleaned_value, None

        if query_key == "scale":
            try:
                return f"{float(cleaned_value):.3f}", None
            except ValueError:
                return cleaned_value, None

        if query_key == "att":
            try:
                return f"{float(cleaned_value):.3f}", None
            except ValueError:
                return cleaned_value, None

        return cleaned_value, None

    def _to_preferred_frequency_unit(self, value_hz: float) -> tuple[str, str]:
        """把 Hz 值转换为更合适的人类可读单位。"""

        abs_value = abs(value_hz)
        if abs_value >= 1_000_000_000:
            return f"{value_hz / 1_000_000_000:.3f}", "GHz"
        if abs_value >= 1_000_000:
            return f"{value_hz / 1_000_000:.3f}", "MHz"
        if abs_value >= 1_000:
            return f"{value_hz / 1_000:.3f}", "kHz"
        return f"{value_hz:.3f}", "Hz"

    def on_instrument_set_requested(
        self,
        instrument_name: str,
        query_key: str,
        value_text: str,
        unit: str | None,
    ) -> None:
        """处理仪表参数设置请求。"""

        label = self.QUERY_LABELS.get(query_key, query_key)
        if not value_text:
            self.append_log(f"仪表设置失败: {instrument_name} - {label} 输入为空")
            return

        normalized_value = self._normalize_setting_value(query_key, value_text, unit)
        if normalized_value is None:
            self.append_log(f"仪表设置失败: {instrument_name} - {label} 数值格式无效")
            return

        success, reason = self._set_instrument_value(instrument_name, query_key, normalized_value)
        if success:
            suffix = f" {unit}" if unit else ""
            self.append_log(f"仪表设置成功: {instrument_name} - {label} = {value_text}{suffix}")
            self._refresh_all_instrument_queries(instrument_name)
            return

        self.append_log(f"仪表设置失败: {instrument_name} - {label}，原因: {reason}")

    def _normalize_setting_value(
        self,
        query_key: str,
        value_text: str,
        unit: str | None,
    ) -> str | float | int | None:
        """将界面输入转换成适配器可直接使用的设置值。"""

        if query_key in {"start_freq", "center_freq", "stop_freq", "span", "rbw"}:
            if unit is None or unit not in self.UNIT_SCALE:
                return None
            try:
                return float(value_text) * self.UNIT_SCALE[unit]
            except ValueError:
                return None

        if query_key == "points":
            try:
                return int(float(value_text))
            except ValueError:
                return None

        if query_key == "scale":
            try:
                return float(value_text)
            except ValueError:
                return None

        if query_key == "att":
            try:
                return float(value_text)
            except ValueError:
                return None

        if query_key == "preamp":
            normalized = value_text.strip().upper()
            if normalized in {"OFF", "15", "30"}:
                return normalized
            return None

        if query_key == "trace_mode":
            normalized = value_text.strip().upper()
            alias_map = {
                "CLEAR WRITE": "WRIT",
                "CLEARWRITE": "WRIT",
                "CLRW": "WRIT",
                "WRIT": "WRIT",
                "MAX HOLD": "MAXH",
                "MAXHOLD": "MAXH",
                "MAXH": "MAXH",
                "AVERAGE": "AVER",
                "AVER": "AVER",
                "MIN HOLD": "MINH",
                "MINHOLD": "MINH",
                "MINH": "MINH",
            }
            normalized = alias_map.get(normalized, normalized)
            if normalized in {"WRIT", "MAXH", "AVER", "MINH"}:
                return normalized
            return None

        return None

    def _set_instrument_value(
        self,
        instrument_name: str,
        query_key: str,
        normalized_value: str | float | int,
    ) -> tuple[bool, str]:
        """通过核心适配器设置一项仪表参数。"""

        if instrument_name not in self.INSTRUMENT_ORDER:
            return False, f"当前暂不支持 {instrument_name} 参数设置"

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            analyzer.set_setting(query_key, normalized_value)
            return True, ""
        except SpectrumAnalyzerError as error:
            return False, str(error)

    def on_instrument_action_requested(self, instrument_name: str, action_key: str) -> None:
        """处理仪表动作按钮，如 Preset 和保存数据。"""

        if action_key == "save_data":
            saved, message = self._save_instrument_snapshot(instrument_name)
            if saved:
                self.append_log(f"仪表参数快照已保存: {instrument_name} -> {message}")
            else:
                self.append_log(f"仪表参数快照保存失败: {instrument_name} - {message}")
            return

        if action_key == "save_param_demo":
            if instrument_name == "ZNA67":
                saved, message = self._save_zna67_demo_data(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    delay_time=100,
                    file_name=str(self.ZNA67_DEMO_FILE_PATH),
                )
                if saved:
                    self.append_log(f"ZNA67 存储数据测试成功: {message}")
                else:
                    self.append_log(f"ZNA67 存储数据测试失败: {message}")
                return

            if instrument_name == "FSW":
                saved, message = self._save_fsw_demo_data(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    file_name=str(self.FSW_DEMO_FILE_PATH),
                )
                if saved:
                    self.append_log(f"FSW 存储数据测试成功: {message}")
                else:
                    self.append_log(f"FSW 存储数据测试失败: {message}")
                return

            if instrument_name == "N9020A":
                saved, message = self._save_n9020a_demo_data(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    file_name=str(self.N9020A_DEMO_FILE_PATH),
                )
                if saved:
                    self.append_log(f"N9020A 存储数据测试成功: {message}")
                else:
                    self.append_log(f"N9020A 存储数据测试失败: {message}")
                return

            self.append_log(f"存储数据测试仅支持 ZNA67/N9020A/FSW，当前仪表: {instrument_name}")
            return

        if action_key != "preset":
            self.append_log(f"仪表动作失败: {instrument_name} - 不支持的动作 {action_key}")
            return

        try:
            analyzer = self._get_instrument_adapter(instrument_name)
            analyzer.preset()
        except SpectrumAnalyzerError as error:
            self.append_log(f"仪表动作失败: {instrument_name} - {action_key}，原因: {error}")
            return

        self.append_log(f"仪表动作成功: {instrument_name} - {action_key}")
        self._refresh_all_instrument_queries(instrument_name)

    def _save_instrument_snapshot(self, instrument_name: str) -> tuple[bool, str]:
        """保存当前仪表参数快照，便于后续调试和比对。"""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            return False, "未找到对应仪表面板"

        snapshot_values: dict[str, dict[str, str | None]] = {}
        query_keys = panel.get_supported_query_keys()
        for query_key in query_keys:
            value, unit = self._query_instrument_value(instrument_name, query_key)
            panel.set_query_result(query_key, value, unit)
            snapshot_values[query_key] = {"value": value, "unit": unit}

        timestamp = datetime.now()
        snapshot_path = self.SNAPSHOT_OUTPUT_DIR / f"{instrument_name.lower()}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        payload = {
            "instrument_name": instrument_name,
            "saved_at": timestamp.isoformat(timespec="seconds"),
            "resources": list(self._load_cached_instrument_resources(instrument_name)),
            "values": snapshot_values,
        }

        try:
            self.SNAPSHOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as error:
            return False, str(error)

        return True, str(snapshot_path)

    def _save_fsw_demo_data(
        self,
        *,
        x: float,
        y: float,
        z: float,
        file_name: str,
    ) -> tuple[bool, str]:
        """执行 FSW 行式 trace 存储（单条 trace）。"""

        target_path = Path(file_name)
        measurement = self._acquire_instrument_measurement("FSW")
        if not measurement.has_trace_data:
            return False, "FSW 采集结果不包含 trace 数据"

        frequencies, values = measurement.to_trace()
        try:
            point_count = save_fsw_trace_csv(
                frequencies=frequencies,
                values=values,
                x=x,
                y=y,
                z=z,
                file_path=target_path,
            )
        except (OSError, ValueError) as error:
            return False, str(error)

        return True, f"{target_path}（共 {point_count} 个频点）"

    def _save_zna67_demo_data(
        self,
        *,
        x: float,
        y: float,
        z: float,
        delay_time: int,
        file_name: str,
    ) -> tuple[bool, str]:
        """执行 ZNA67 行式 trace 存储。

        说明：
        - 当前为 demo 阶段，真实仪表采集接口由 `_acquire_zna67_raw_text` 预留。
        - 存储格式支持自动识别 trace 标签数量与名称。
        """

        del delay_time
        target_path = Path(file_name)
        raw_text = self._acquire_zna67_raw_text(x=x, y=y, z=z, delay_time=0)
        try:
            row_count, trace_names = save_zna_trace_csv(raw_text=raw_text, file_path=target_path)
        except (OSError, ValueError) as error:
            return False, str(error)

        trace_summary = "、".join(sorted(trace_names))
        return True, f"{target_path}（共 {row_count} 行，trace: {trace_summary}）"


    def _save_n9020a_demo_data(
        self,
        *,
        x: float,
        y: float,
        z: float,
        file_name: str,
    ) -> tuple[bool, str]:
        """执行 N9020A 行式 trace 存储（单条 trace）。"""

        target_path = Path(file_name)
        measurement = self._acquire_instrument_measurement("N9020A")
        if not measurement.has_trace_data:
            return False, "N9020A 采集结果不包含 trace 数据"

        frequencies, values = measurement.to_trace()
        try:
            point_count = save_n9020a_trace_csv(
                frequencies=frequencies,
                values=values,
                x=x,
                y=y,
                z=z,
                file_path=target_path,
            )
        except (OSError, ValueError) as error:
            return False, str(error)

        return True, f"{target_path}（共 {point_count} 个频点）"

    def _acquire_zna67_raw_text(self, *, x: float, y: float, z: float, delay_time: int) -> str:
        """采集 ZNA67 原始文本，并统一转换为行式文本。"""

        del delay_time
        measurement = self._acquire_instrument_measurement("ZNA67")
        mmem_text = measurement.metadata.get("mmem_csv_text")
        if not isinstance(mmem_text, str) or not mmem_text.strip():
            raise SpectrumAnalyzerError("ZNA67 未返回 MMEM CSV 文本。")
        return convert_zna_mmem_csv_to_row_text(raw_text=mmem_text, x=x, y=y, z=z)

    def _acquire_zna67_mmem_data(self, *, delay_time: int) -> str | None:
        """通过 ZNA67 的 MMEM 命令获取分号 CSV 文本。"""

        del delay_time
        measurement = self._acquire_instrument_measurement("ZNA67")
        mmem_text = measurement.metadata.get("mmem_csv_text")
        if isinstance(mmem_text, str) and mmem_text.strip():
            return mmem_text
        return None

    def _run_zna67_mmem_cycle_via_visa(
        self,
        *,
        store_command: str,
        read_command: str,
        delete_command: str,
    ) -> tuple[bool, str]:
        """兼容旧入口，实际 ZNA67 采集已迁移到统一适配器层。"""

        del store_command, read_command, delete_command
        return False, "ZNA67 MMEM 采集已迁移到统一适配器层"

    def _run_zna67_mmem_cycle_via_serial(
        self,
        *,
        store_command: str,
        read_command: str,
        delete_command: str,
    ) -> tuple[bool, str]:
        """兼容旧入口，真实设备访问已迁移到统一适配器层。"""

        del store_command, read_command, delete_command
        return False, "ZNA67 串口回退尚未迁入统一适配器层"

    def _write_via_visa(
        self,
        command: str,
        *,
        instrument_name: str | None = None,
        timeout_ms: int = 1200,
    ) -> tuple[bool, str]:
        """兼容旧入口，实际 VISA 写操作已迁移到频谱适配器层。"""

        del command, instrument_name, timeout_ms
        return False, "仪表 VISA 写操作已迁移到频谱适配器层"

    def _get_instrument_adapter(self, instrument_name: str):
        """Return a connected spectrum adapter for the given instrument tab."""

        if instrument_name not in self.INSTRUMENT_ORDER:
            raise SpectrumAnalyzerError(f"不支持的仪表类型: {instrument_name}")
        resources = self._load_cached_instrument_resources(instrument_name)
        return self.device_manager.ensure_spectrum_device(
            instrument_type=instrument_name,
            resource_names=resources,
        )

    def _build_instrument_measurement_config(
        self,
        panel: InstrumentPanel,
        *,
        fsw_clear_write_delay_seconds: float | None = None,
    ) -> SpectrumConfig:
        """Build one best-effort spectrum config from the current panel values."""

        displayed_values = panel.get_displayed_values()

        def read_field(setting_key: str) -> str | None:
            payload = displayed_values.get(setting_key, {})
            raw_value = str(payload.get("value", "")).strip()
            if not raw_value:
                return None
            raw_unit = payload.get("unit")
            if isinstance(raw_unit, str) and raw_unit.strip():
                return f"{raw_value}{raw_unit.strip()}"
            return raw_value

        if panel.instrument_name == "ZNA67":
            return SpectrumConfig(
                start_freq=read_field("start_freq"),
                stop_freq=read_field("stop_freq"),
                rbw=read_field("rbw"),
                acquisition_mode="trace",
            )

        return SpectrumConfig(
            start_freq=read_field("start_freq"),
            stop_freq=read_field("stop_freq"),
            center_freq=read_field("center_freq"),
            span=read_field("span"),
            rbw=read_field("rbw"),
            vbw=read_field("vbw"),
            ref_level=read_field("ref_level"),
            detector=read_field("detector"),
            trace_mode=read_field("trace_mode"),
            fsw_clear_write_delay_seconds=fsw_clear_write_delay_seconds if panel.instrument_name == "FSW" else None,
            acquisition_mode="trace",
        )

    def _acquire_instrument_measurement(self, instrument_name: str):
        """Acquire one normalized measurement through ``ScanManager``."""

        panel = self._find_instrument_panel(instrument_name)
        if panel is None:
            raise SpectrumAnalyzerError(f"未找到 {instrument_name} 面板。")

        analyzer = self._get_instrument_adapter(instrument_name)
        self.scan_manager.set_spectrum_analyzer(analyzer)
        self.scan_manager.set_spectrum_config(self._build_instrument_measurement_config(panel))
        return self.scan_manager.acquire_spectrum_measurement()

    def _on_instrument_search_thread_finished(self) -> None:
        """重置搜索按钮状态。"""

        self._instrument_search_thread = None
        self._instrument_search_worker = None
        self.search_button.setEnabled(True)
        self.search_button.setText("搜索仪表")

    def _write_instrument_search_log(self, message: str) -> None:
        """将仪表搜索日志写入文件，不在界面日志区域显示。"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.INSTRUMENT_SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self.INSTRUMENT_SEARCH_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
        get_logger(__name__).info("instrument-search | %s", message)

    def _mock_query_value(self, instrument_name: str, query_key: str) -> tuple[str, str | None]:
        """返回对应仪表的占位查询值。"""

        instrument_values = self.INSTRUMENT_PLACEHOLDER_VALUES.get(
            instrument_name,
            self.INSTRUMENT_PLACEHOLDER_VALUES["ZNA67"],
        )
        return instrument_values.get(query_key, ("-", None))

    def _read_serial_response_text(self, timeout_ms: int = 500) -> str:
        """读取一段串口响应文本，优先使用已累积的接收缓存。"""

        if self._serial_read_buffer.strip():
            text = self._serial_read_buffer
            self._serial_read_buffer = ""
            return text

        if not self._serial_port.waitForReadyRead(timeout_ms):
            return ""

        chunks = [bytes(self._serial_port.readAll()).decode("utf-8", errors="replace")]
        while self._serial_port.waitForReadyRead(80):
            chunks.append(bytes(self._serial_port.readAll()).decode("utf-8", errors="replace"))
        return "".join(chunks)

    def _load_cached_instrument_resources(self, instrument_name: str | None = None) -> tuple[str, ...]:
        """读取上一次保存的仪表资源缓存。"""

        if not self.INSTRUMENT_CACHE_PATH.exists():
            return ()
        try:
            payload = json.loads(self.INSTRUMENT_CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ()

        resources_by_instrument = payload.get("resources_by_instrument")
        if isinstance(resources_by_instrument, dict):
            normalized: dict[str, tuple[str, ...]] = {}
            for supported_name in self.INSTRUMENT_ORDER:
                raw_values = resources_by_instrument.get(supported_name, [])
                if not isinstance(raw_values, list):
                    normalized[supported_name] = ()
                    continue
                valid_values = [
                    item.strip()
                    for item in raw_values
                    if isinstance(item, str) and item.strip()
                ]
                normalized[supported_name] = tuple(valid_values)

            if instrument_name is not None:
                return normalized.get(instrument_name, ())

            deduplicated: list[str] = []
            seen: set[str] = set()
            for supported_name in self.INSTRUMENT_ORDER:
                for resource_name in normalized.get(supported_name, ()):
                    if resource_name in seen:
                        continue
                    seen.add(resource_name)
                    deduplicated.append(resource_name)
            return tuple(deduplicated)

        resources = payload.get("resources")
        if not isinstance(resources, list):
            return ()

        valid_resources = tuple(
            item.strip()
            for item in resources
            if isinstance(item, str) and item.strip()
        )
        if instrument_name is None or instrument_name == "ZNA67":
            return valid_resources
        return ()

    def _save_cached_instrument_resources(self, resources_by_instrument: dict[str, list[str]]) -> None:
        """保存本次识别到的仪表资源映射，供下次优先尝试。"""

        normalized_map: dict[str, list[str]] = {}
        all_resources: list[str] = []
        seen: set[str] = set()
        for instrument_name in self.INSTRUMENT_ORDER:
            raw_values = resources_by_instrument.get(instrument_name, [])
            deduplicated_for_instrument: list[str] = []
            instrument_seen: set[str] = set()
            for item in raw_values:
                cleaned = item.strip()
                if not cleaned or cleaned in instrument_seen:
                    continue
                instrument_seen.add(cleaned)
                deduplicated_for_instrument.append(cleaned)
                if cleaned not in seen:
                    seen.add(cleaned)
                    all_resources.append(cleaned)
            normalized_map[instrument_name] = deduplicated_for_instrument

        payload = {
            "resources_by_instrument": normalized_map,
            "resources": all_resources,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.INSTRUMENT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.INSTRUMENT_CACHE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
