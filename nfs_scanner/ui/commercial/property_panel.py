"""Right property panel — compact instrument-style scan parameters."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
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

from .preview_stats_display import update_preview_stat_labels
from .scroll_helpers import configure_scroll_area
from .widgets import NFSDangerButton, NFSNumericField, NFSPrimaryButton, NFSSecondaryButton


class CommercialPropertyPanel(QScrollArea):
    """Compact scrollable property panel for scan and instrument parameters."""

    scan_config_changed = Signal(ScanRegion, ScanPathConfig)
    scan_preview_updated = Signal(ScanPreviewStats)
    scan_start_requested = Signal()
    scan_stop_requested = Signal()
    scan_pause_toggle_requested = Signal()

    _DEBOUNCE_MS = 250

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        self.setProperty("compactMode", "true")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_scan_config)
        self._field_map: dict[str, NFSNumericField] = {}
        self._mode_combo: QComboBox | None = None
        self._validation_label: QLabel | None = None
        self._preview_stat_labels: dict[str, QLabel] = {}
        self._start_scan_button: NFSPrimaryButton | None = None
        self._stop_scan_button: NFSDangerButton | None = None
        self._pause_scan_button: NFSSecondaryButton | None = None
        self._setup_ui()
        QTimer.singleShot(0, self._emit_scan_config)

    def _setup_ui(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("扫描参数", container)
        title.setObjectName("nfsSectionTitle")
        layout.addWidget(title)

        layout.addWidget(self._build_region_section(container))
        layout.addWidget(self._build_stats_grid(container))
        layout.addWidget(self._build_scan_settings_section(container))
        layout.addWidget(self._build_frequency_section(container))
        layout.addWidget(self._build_action_buttons(container))

        self._validation_label = QLabel("", container)
        self._validation_label.setObjectName("nfsMutedLabel")
        self._validation_label.setWordWrap(True)
        layout.addWidget(self._validation_label)
        layout.addStretch(1)

        self.setWidget(container)
        configure_scroll_area(self, vertical=True, horizontal=False)

    def _section_frame(self, parent: QWidget, caption: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(parent)
        frame.setObjectName("nfsCompactSection")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)
        frame_layout.setSpacing(6)
        label = QLabel(caption, frame)
        label.setObjectName("nfsMutedLabel")
        frame_layout.addWidget(label)
        return frame, frame_layout

    def _build_region_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "扫描区域")

        region_combo = QComboBox(frame)
        region_combo.addItems(["矩形区域", "全板区域", "自定义 ROI"])
        frame_layout.addWidget(region_combo)

        for row_label, field_specs in (
            (
                "起点",
                (
                    ("x_start", DEFAULT_X_START),
                    ("y_start", DEFAULT_Y_START),
                    ("z_height", DEFAULT_Z_HEIGHT),
                ),
            ),
            (
                "终点",
                (
                    ("x_stop", DEFAULT_X_STOP),
                    ("y_stop", DEFAULT_Y_STOP),
                ),
            ),
            (
                "步长",
                (
                    ("x_step", DEFAULT_X_STEP),
                    ("y_step", DEFAULT_Y_STEP),
                ),
            ),
        ):
            row = QWidget(frame)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            row_layout.addWidget(QLabel(row_label, row))
            axis_names = {"x_start": "X", "y_start": "Y", "z_height": "Z", "x_stop": "X", "y_stop": "Y", "x_step": "X", "y_step": "Y"}
            for key, default in field_specs:
                field = NFSNumericField("mm", row)
                field.setText(f"{default:g}")
                field.valueChanged.connect(self._schedule_emit_scan_config)
                self._field_map[key] = field
                row_layout.addWidget(QLabel(axis_names[key], row))
                row_layout.addWidget(field, 1)
            frame_layout.addWidget(row)

        return frame

    def _build_stats_grid(self, parent: QWidget) -> QWidget:
        grid_host = QFrame(parent)
        grid_host.setObjectName("nfsPreviewStatsGrid")
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        for index, (key, caption) in enumerate(
            (
                ("point_count", "点数"),
                ("area_mm2", "区域面积"),
                ("path_length_mm", "路径长度"),
                ("estimated_seconds", "预计时间"),
            )
        ):
            card = QFrame(grid_host)
            card.setObjectName("nfsPreviewStatCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 4, 6, 4)
            card_layout.setSpacing(2)
            name = QLabel(caption, card)
            name.setObjectName("nfsMutedLabel")
            value = QLabel("--", card)
            value.setObjectName("nfsPreviewStatValue")
            card_layout.addWidget(name)
            card_layout.addWidget(value)
            grid.addWidget(card, index // 2, index % 2)
            self._preview_stat_labels[key] = value
        return grid_host

    def _build_scan_settings_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "扫描设置")

        self._mode_combo = QComboBox(frame)
        self._mode_combo.addItems(["snake", "raster"])
        self._mode_combo.currentTextChanged.connect(self._on_scan_mode_changed)
        frame_layout.addWidget(self._labeled_row(frame, "扫描模式", self._mode_combo))

        dwell_field = NFSNumericField("ms", frame)
        dwell_field.setText(str(DEFAULT_DWELL_MS))
        dwell_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["dwell_ms"] = dwell_field
        frame_layout.addWidget(self._labeled_row(frame, "驻留时间", dwell_field))

        avg_field = NFSNumericField("次", frame)
        avg_field.setText("4")
        frame_layout.addWidget(self._labeled_row(frame, "平均次数", avg_field))

        speed_field = NFSNumericField("mm/min", frame)
        speed_field.setText(f"{DEFAULT_SPEED_MM_MIN:g}")
        speed_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["speed_mm_min"] = speed_field
        frame_layout.addWidget(self._labeled_row(frame, "速度", speed_field))

        heatmap_checkbox = QCheckBox("实时热力图", frame)
        heatmap_checkbox.setChecked(True)
        home_checkbox = QCheckBox("扫描完成回零 (Mock)", frame)
        frame_layout.addWidget(heatmap_checkbox)
        frame_layout.addWidget(home_checkbox)
        return frame

    def _build_frequency_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "频率设置")

        source_combo = QComboBox(frame)
        source_combo.addItems(["内部源", "外部源"])
        trace_combo = QComboBox(frame)
        trace_combo.addItems(["Trace 1", "Trace 2"])
        mode_combo = QComboBox(frame)
        mode_combo.addItems(["扫频", "FFT", "Max Hold"])

        for caption, widget in (
            ("源", source_combo),
            ("Trace", trace_combo),
            ("模式", mode_combo),
        ):
            frame_layout.addWidget(self._labeled_row(frame, caption, widget))

        start_field = NFSNumericField("MHz", frame)
        start_field.setText("100")
        stop_field = NFSNumericField("MHz", frame)
        stop_field.setText("3000")
        points_field = NFSNumericField("pts", frame)
        points_field.setText("1001")
        frame_layout.addWidget(self._labeled_row(frame, "起始频率", start_field))
        frame_layout.addWidget(self._labeled_row(frame, "终止频率", stop_field))
        frame_layout.addWidget(self._labeled_row(frame, "点数", points_field))
        return frame

    def _build_action_buttons(self, parent: QWidget) -> QWidget:
        row = QWidget(parent)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._start_scan_button = NFSPrimaryButton("开始扫描", row)
        self._stop_scan_button = NFSDangerButton("停止扫描", row)
        self._start_scan_button.clicked.connect(self.scan_start_requested.emit)
        self._stop_scan_button.clicked.connect(self.scan_stop_requested.emit)
        self._pause_scan_button = NFSSecondaryButton("暂停扫描", row)
        self._pause_scan_button.clicked.connect(self.scan_pause_toggle_requested.emit)
        self._pause_scan_button.setVisible(False)
        layout.addWidget(self._start_scan_button)
        layout.addWidget(self._pause_scan_button)
        layout.addWidget(self._stop_scan_button)
        return row

    @staticmethod
    def _labeled_row(parent: QWidget, caption: str, widget: QWidget) -> QWidget:
        row = QWidget(parent)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(caption, row)
        label.setObjectName("nfsMutedLabel")
        label.setMinimumWidth(56)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return row

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
        update_preview_stat_labels(self._preview_stat_labels, stats)

    def set_scan_controls_enabled(self, *, start_enabled: bool, stop_enabled: bool) -> None:
        if self._start_scan_button is not None:
            self._start_scan_button.setEnabled(start_enabled)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_pause_button_state(self, *, visible: bool, paused: bool, enabled: bool = True) -> None:
        if self._pause_scan_button is None:
            return
        self._pause_scan_button.setVisible(visible)
        self._pause_scan_button.setText("继续扫描" if paused else "暂停扫描")
        self._pause_scan_button.setEnabled(enabled)
