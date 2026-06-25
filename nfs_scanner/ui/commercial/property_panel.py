"""Right property panel with parameter tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core.path_planner import calculate_preview_stats, generate_preview_points
from nfs_scanner.core.scan_config import (
    DEFAULT_DWELL_MS,
    DEFAULT_SPEED_MM_MIN,
    DEFAULT_X_START,
    DEFAULT_X_STOP,
    DEFAULT_X_STEP,
    DEFAULT_Y_START,
    DEFAULT_Y_STEP,
    DEFAULT_Y_STOP,
    DEFAULT_Z_HEIGHT,
    ScanPathConfig,
    ScanPreviewStats,
    ScanRegion,
)

from .preview_stats_display import update_density_badge, update_mode_badge, update_preview_stat_labels
from .widgets import NFSCard, NFSDangerButton, NFSNumericField, NFSParameterGroup, NFSPrimaryButton, NFSStatusBadge


class CommercialPropertyPanel(QScrollArea):
    """Scrollable property panel with scan, display and instrument tabs."""

    scan_config_changed = Signal(ScanRegion, ScanPathConfig)
    scan_preview_updated = Signal(ScanPreviewStats)

    _DEBOUNCE_MS = 250

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_scan_config)
        self._field_map: dict[str, NFSNumericField] = {}
        self._mode_combo: QComboBox | None = None
        self._validation_label: QLabel | None = None
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._mode_badge: NFSStatusBadge | None = None
        self._density_badge: NFSStatusBadge | None = None
        self._setup_ui()
        QTimer.singleShot(0, self._emit_scan_config)

    def _setup_ui(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(container)
        tabs.setObjectName("commercialPropertyTabs")
        tabs.addTab(self._build_scan_tab(tabs), "扫描参数")
        tabs.addTab(self._build_display_tab(tabs), "显示设置")
        tabs.addTab(self._build_instrument_tab(tabs), "仪表设置")
        layout.addWidget(tabs)
        self.setWidget(container)

    def _build_scan_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        preview_card = NFSCard("预览统计", page)
        preview_card.setProperty("cardRole", "previewStats")
        preview_form = QFormLayout()
        preview_form.setContentsMargins(0, 0, 0, 0)
        preview_form.setVerticalSpacing(8)

        header_row = QWidget(preview_card.body)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        self._mode_badge = NFSStatusBadge("Snake", "running", header_row)
        self._density_badge = NFSStatusBadge("高密度预览", "warning", header_row)
        self._density_badge.setVisible(False)
        header_layout.addWidget(self._mode_badge)
        header_layout.addWidget(self._density_badge)
        header_layout.addStretch(1)
        preview_form.addRow(header_row)

        for key, label in (
            ("point_count", "点数"),
            ("area_mm2", "区域面积"),
            ("path_length_mm", "路径长度"),
            ("estimated_seconds", "预计时间"),
        ):
            value_label = QLabel("--", preview_card.body)
            value_label.setObjectName("nfsPreviewStatValue")
            label_widget = QLabel(label, preview_card.body)
            label_widget.setObjectName("nfsMutedLabel")
            preview_form.addRow(label_widget, value_label)
            self._preview_stat_labels[key] = value_label

        preview_card.body_layout.addLayout(preview_form)
        layout.addWidget(preview_card)

        self._validation_label = QLabel("", page)
        self._validation_label.setObjectName("nfsMutedLabel")
        self._validation_label.setWordWrap(True)
        layout.addWidget(self._validation_label)

        area_card = NFSCard("扫描区域", page)
        area_form = NFSParameterGroup(parent=area_card.body)
        self._register_numeric_field(area_form, "x_start", "起始 X", f"{DEFAULT_X_START:g}", "mm")
        self._register_numeric_field(area_form, "x_stop", "终止 X", f"{DEFAULT_X_STOP:g}", "mm")
        self._register_numeric_field(area_form, "y_start", "起始 Y", f"{DEFAULT_Y_START:g}", "mm")
        self._register_numeric_field(area_form, "y_stop", "终止 Y", f"{DEFAULT_Y_STOP:g}", "mm")
        self._register_numeric_field(area_form, "z_height", "Z 高度", f"{DEFAULT_Z_HEIGHT:g}", "mm")
        self._register_numeric_field(area_form, "x_step", "步长 X", f"{DEFAULT_X_STEP:g}", "mm")
        self._register_numeric_field(area_form, "y_step", "步长 Y", f"{DEFAULT_Y_STEP:g}", "mm")
        area_card.body_layout.addWidget(area_form)
        layout.addWidget(area_card)

        path_card = NFSCard("路径策略", page)
        path_form = QFormLayout()
        path_form.setContentsMargins(0, 0, 0, 0)
        path_form.setVerticalSpacing(8)

        self._mode_combo = QComboBox(path_card.body)
        self._mode_combo.addItems(["snake", "raster"])
        self._mode_combo.currentTextChanged.connect(self._on_scan_mode_changed)
        path_form.addRow(QLabel("扫描模式", path_card.body), self._mode_combo)

        dwell_field = NFSNumericField("ms", path_card.body)
        dwell_field.setText(str(DEFAULT_DWELL_MS))
        dwell_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["dwell_ms"] = dwell_field
        path_form.addRow(QLabel("驻留时间", path_card.body), dwell_field)

        speed_field = NFSNumericField("mm/min", path_card.body)
        speed_field.setText(f"{DEFAULT_SPEED_MM_MIN:g}")
        speed_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["speed_mm_min"] = speed_field
        path_form.addRow(QLabel("移动速度", path_card.body), speed_field)

        path_card.body_layout.addLayout(path_form)
        layout.addWidget(path_card)

        freq_card = NFSCard("频率设置", page)
        freq_form = NFSParameterGroup(parent=freq_card.body)
        freq_form.add_row("Start Freq", "100 MHz")
        freq_form.add_row("Stop Freq", "3 GHz")
        freq_form.add_row("RBW", "100 kHz")
        freq_card.body_layout.addWidget(freq_form)
        layout.addWidget(freq_card)

        button_row = QWidget(page)
        button_layout = QVBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(NFSPrimaryButton("开始扫描", button_row))
        button_layout.addWidget(NFSDangerButton("停止扫描", button_row))
        layout.addWidget(button_row)
        layout.addStretch(1)
        return page

    def _register_numeric_field(
        self,
        form: NFSParameterGroup,
        key: str,
        label: str,
        value: str,
        unit: str,
    ) -> None:
        field = form.add_numeric_row(label, value, unit=unit)
        field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map[key] = field

    def _on_scan_mode_changed(self) -> None:
        self._emit_scan_config()

    def _schedule_emit_scan_config(self) -> None:
        self._debounce_timer.start(self._DEBOUNCE_MS)

    def _parse_float(self, key: str, default: float) -> float:
        field = self._field_map[key]
        text = field.text().strip()
        try:
            value = float(text)
            field.set_valid(True)
            return value
        except ValueError:
            field.set_valid(False)
            return default

    def _parse_int(self, key: str, default: int) -> int:
        field = self._field_map[key]
        text = field.text().strip()
        try:
            value = int(float(text))
            field.set_valid(True)
            return value
        except ValueError:
            field.set_valid(False)
            return default

    def current_scan_region(self) -> ScanRegion:
        return ScanRegion(
            x_start=self._parse_float("x_start", DEFAULT_X_START),
            x_stop=self._parse_float("x_stop", DEFAULT_X_STOP),
            y_start=self._parse_float("y_start", DEFAULT_Y_START),
            y_stop=self._parse_float("y_stop", DEFAULT_Y_STOP),
            z_height=self._parse_float("z_height", DEFAULT_Z_HEIGHT),
            x_step=self._parse_float("x_step", DEFAULT_X_STEP),
            y_step=self._parse_float("y_step", DEFAULT_Y_STEP),
        )

    def current_scan_path_config(self) -> ScanPathConfig:
        mode = self._mode_combo.currentText() if self._mode_combo is not None else "snake"
        return ScanPathConfig(
            scan_mode=mode if mode in ("snake", "raster") else "snake",
            dwell_ms=self._parse_int("dwell_ms", DEFAULT_DWELL_MS),
            speed_mm_min=self._parse_float("speed_mm_min", DEFAULT_SPEED_MM_MIN),
        )

    def _emit_scan_config(self) -> None:
        region = self.current_scan_region()
        path_config = self.current_scan_path_config()
        parse_errors = self._collect_parse_errors()
        errors = parse_errors + region.validate() + path_config.validate()

        if errors:
            if self._validation_label is not None:
                self._validation_label.setText("参数无效，已使用安全默认值预览：" + "；".join(errors))
            region = region.clamped()
            path_config = path_config.clamped()
        elif self._validation_label is not None:
            self._validation_label.setText("")

        points = generate_preview_points(region, path_config)
        stats = calculate_preview_stats(points, region, path_config)
        self._update_preview_stats_display(stats)
        self.scan_config_changed.emit(region, path_config)
        self.scan_preview_updated.emit(stats)

    def _collect_parse_errors(self) -> list[str]:
        errors: list[str] = []
        for key, field in self._field_map.items():
            text = field.text().strip()
            if not text:
                field.set_valid(False)
                errors.append(f"{key} 不能为空")
                continue
            try:
                if key == "dwell_ms":
                    int(float(text))
                else:
                    float(text)
                field.set_valid(True)
            except ValueError:
                field.set_valid(False)
                errors.append(f"{key} 格式无效")
        return errors

    def _update_preview_stats_display(self, stats: ScanPreviewStats) -> None:
        update_mode_badge(self._mode_badge, stats)
        update_density_badge(self._density_badge, stats)
        update_preview_stat_labels(self._preview_stat_labels, stats)

    def _build_display_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("显示设置", page)
        form = NFSParameterGroup(parent=card.body)
        form.add_row("vmin", "0.0")
        form.add_row("vmax", "1.0")

        heatmap_checkbox = QCheckBox("显示热力图", card.body)
        auto_range_checkbox = QCheckBox("自动范围", card.body)
        auto_range_checkbox.setChecked(True)

        lut_combo = QComboBox(card.body)
        lut_combo.addItems(["viridis", "plasma", "inferno", "magma", "gray"])

        card.body_layout.addWidget(form)
        card.body_layout.addWidget(heatmap_checkbox)
        card.body_layout.addWidget(auto_range_checkbox)
        card.body_layout.addWidget(lut_combo)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_instrument_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)

        card = NFSCard("仪表设置", page)
        form = NFSParameterGroup(parent=card.body)
        form.add_row("设备类型", "TCPIP-SCPI")
        form.add_row("Center", "1.5 GHz")
        form.add_row("Span", "2 GHz")
        form.add_row("Points", "1001")
        form.add_row("Detector", "Peak")

        device_combo = QComboBox(card.body)
        device_combo.addItems(["TCPIP-SCPI", "USB-TMC", "Mock-Spectrum"])

        card.body_layout.addWidget(form)
        card.body_layout.addWidget(device_combo)
        layout.addWidget(card)
        layout.addStretch(1)
        return page
