"""Right property panel — target-style compact instrument parameters."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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

from .preview_stats_display import update_preview_stat_labels
from .scroll_helpers import configure_scroll_area
from .widgets import NFSDangerButton, NFSNumericField, NFSPrimaryButton, NFSSecondaryButton


class CommercialPropertyPanel(QScrollArea):
    """Tabbed compact property panel matching the target screenshot."""

    scan_config_changed = Signal(ScanRegion, ScanPathConfig)
    scan_preview_updated = Signal(ScanPreviewStats)
    scan_start_requested = Signal()
    scan_stop_requested = Signal()
    scan_pause_toggle_requested = Signal()

    _DEBOUNCE_MS = 250
    _COMPACT_FIELD_WIDTH = 92

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commercialPropertyPanel")
        self.setProperty("compactMode", "true")
        self.setProperty("targetStyleMode", "true")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
        self._action_button_row: QWidget | None = None
        self._target_presentation_active = False
        self._tabs: QTabWidget | None = None
        self._setup_ui()
        QTimer.singleShot(0, self._emit_scan_config)

    def _setup_ui(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget(container)
        tabs.setObjectName("commercialPropertyTabs")
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(self._wrap_scroll_page(self._build_scan_tab(tabs), tabs), "扫描参数")
        tabs.addTab(self._wrap_scroll_page(self._build_display_tab(tabs), tabs), "显示设置")
        tabs.addTab(self._wrap_scroll_page(self._build_instrument_tab(tabs), tabs), "仪表设置")
        layout.addWidget(tabs, 1)
        self._tabs = tabs
        self.setWidget(container)
        configure_scroll_area(self, vertical=False, horizontal=False)

    def _wrap_scroll_page(self, content: QWidget, parent: QWidget) -> QScrollArea:
        """Wrap one tab page so the tab bar stays fixed while content scrolls."""

        scroll = QScrollArea(parent)
        scroll.setObjectName("commercialPropertyTabScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content)
        configure_scroll_area(scroll, vertical=True, horizontal=False)
        return scroll

    def _build_scan_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 16, 8)
        layout.setSpacing(8)

        layout.addWidget(self._build_region_section(page))
        layout.addWidget(self._build_stats_grid(page))
        layout.addWidget(self._build_scan_settings_section(page))
        layout.addWidget(self._build_action_buttons(page))
        layout.addWidget(self._build_frequency_section(page))

        self._validation_label = QLabel("", page)
        self._validation_label.setObjectName("nfsMutedLabel")
        self._validation_label.setWordWrap(True)
        layout.addWidget(self._validation_label)
        layout.addStretch(1)
        return page

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

    def _compact_field(self, parent: QWidget, key: str, default: float, unit: str = "mm") -> NFSNumericField:
        field = NFSNumericField(unit, parent)
        field.setText(f"{default:g}")
        field.setMinimumWidth(self._COMPACT_FIELD_WIDTH)
        field.setMaximumWidth(self._COMPACT_FIELD_WIDTH)
        field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map[key] = field
        return field

    def _build_xyz_row(
        self,
        parent: QWidget,
        row_label: str,
        specs: tuple[tuple[str, float], ...],
    ) -> QWidget:
        row = QWidget(parent)
        row.setObjectName("commercialPropertyGridRow")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        caption = QLabel(row_label, row)
        caption.setObjectName("nfsMutedLabel")
        layout.addWidget(caption)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        axis_names = {
            "x_start": "X",
            "y_start": "Y",
            "z_height": "Z",
            "x_stop": "X",
            "y_stop": "Y",
            "z_stop": "Z",
            "x_step": "X",
            "y_step": "Y",
            "z_step": "Z",
        }
        for column, (key, default) in enumerate(specs):
            axis = QLabel(axis_names[key], row)
            axis.setObjectName("nfsMutedLabel")
            axis.setAlignment(Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(axis, 0, column)
            grid.addWidget(self._compact_field(row, key, default), 1, column)
            grid.setColumnStretch(column, 1)
        layout.addLayout(grid)
        return row

    def _build_region_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "扫描区域")
        region_combo = QComboBox(frame)
        region_combo.addItems(["矩形区域", "全板区域", "自定义 ROI"])
        frame_layout.addWidget(region_combo)
        frame_layout.addWidget(
            self._build_xyz_row(
                frame,
                "起点",
                (("x_start", DEFAULT_X_START), ("y_start", DEFAULT_Y_START), ("z_height", DEFAULT_Z_HEIGHT)),
            )
        )
        frame_layout.addWidget(
            self._build_xyz_row(
                frame,
                "终点",
                (("x_stop", DEFAULT_X_STOP), ("y_stop", DEFAULT_Y_STOP)),
            )
        )
        frame_layout.addWidget(
            self._build_xyz_row(
                frame,
                "步长",
                (("x_step", DEFAULT_X_STEP), ("y_step", DEFAULT_Y_STEP)),
            )
        )
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
            card_layout.addWidget(QLabel(caption, card))
            value = QLabel("--", card)
            value.setObjectName("nfsPreviewStatValue")
            card_layout.addWidget(value)
            grid.addWidget(card, index // 2, index % 2)
            self._preview_stat_labels[key] = value
        return grid_host

    def _build_scan_settings_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "扫描设置")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self._mode_combo = QComboBox(frame)
        self._mode_combo.addItem("蛇形", "snake")
        self._mode_combo.addItem("光栅", "raster")
        self._mode_combo.currentIndexChanged.connect(self._on_scan_mode_changed)

        dwell_field = NFSNumericField("ms", frame)
        dwell_field.setText(str(DEFAULT_DWELL_MS))
        dwell_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["dwell_ms"] = dwell_field

        avg_field = NFSNumericField("次", frame)
        avg_field.setText("4")

        speed_field = NFSNumericField("mm/min", frame)
        speed_field.setText(f"{DEFAULT_SPEED_MM_MIN:g}")
        speed_field.valueChanged.connect(self._schedule_emit_scan_config)
        self._field_map["speed_mm_min"] = speed_field

        grid.addWidget(QLabel("扫描模式", frame), 0, 0)
        grid.addWidget(self._mode_combo, 0, 1)
        grid.addWidget(QLabel("驻留时间", frame), 0, 2)
        grid.addWidget(dwell_field, 0, 3)
        grid.addWidget(QLabel("平均次数", frame), 1, 0)
        grid.addWidget(avg_field, 1, 1)
        grid.addWidget(QLabel("速度", frame), 1, 2)
        grid.addWidget(speed_field, 1, 3)
        frame_layout.addLayout(grid)

        heatmap_checkbox = QCheckBox("实时显示热力图", frame)
        heatmap_checkbox.setChecked(True)
        home_checkbox = QCheckBox("扫描完成回零 (Mock)", frame)
        frame_layout.addWidget(heatmap_checkbox)
        frame_layout.addWidget(home_checkbox)
        return frame

    def _build_frequency_section(self, parent: QWidget) -> QWidget:
        frame, frame_layout = self._section_frame(parent, "频率设置")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        source_combo = QComboBox(frame)
        source_combo.addItems(["内部源", "外部源"])
        trace_combo = QComboBox(frame)
        trace_combo.addItems(["Trace 1", "Trace 2"])
        mode_combo = QComboBox(frame)
        mode_combo.addItems(["扫频", "FFT", "Max Hold"])
        start_field = NFSNumericField("MHz", frame)
        start_field.setText("100")
        stop_field = NFSNumericField("MHz", frame)
        stop_field.setText("6000")
        points_field = NFSNumericField("pts", frame)
        points_field.setText("1001")

        rows = (
            ("源", source_combo),
            ("Trace", trace_combo),
            ("模式", mode_combo),
            ("起始频率", start_field),
            ("终止频率", stop_field),
            ("点数", points_field),
        )
        for row_index, (caption, widget) in enumerate(rows):
            grid.addWidget(QLabel(caption, frame), row_index, 0)
            grid.addWidget(widget, row_index, 1)
        frame_layout.addLayout(grid)

        apply_button = QPushButton("应用", frame)
        apply_button.setObjectName("nfsSecondaryButton")
        apply_button.setEnabled(False)
        apply_button.setToolTip("Mock 占位")
        frame_layout.addWidget(apply_button)
        return frame

    def _build_action_buttons(self, parent: QWidget) -> QWidget:
        row = QWidget(parent)
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._action_button_row = row
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._start_scan_button = NFSPrimaryButton("开始扫描", row)
        self._stop_scan_button = NFSDangerButton("停止扫描", row)
        self._start_scan_button.clicked.connect(self.scan_start_requested.emit)
        self._stop_scan_button.clicked.connect(self.scan_stop_requested.emit)
        self._pause_scan_button = NFSSecondaryButton("暂停", row)
        self._pause_scan_button.clicked.connect(self.scan_pause_toggle_requested.emit)
        self._pause_scan_button.setVisible(False)
        for button in (self._start_scan_button, self._pause_scan_button, self._stop_scan_button):
            button.setMinimumWidth(72)
            button.setMinimumHeight(32)
        layout.addWidget(self._start_scan_button, 1)
        layout.addWidget(self._pause_scan_button, 1)
        layout.addWidget(self._stop_scan_button, 1)
        return row

    def _build_display_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 16, 8)
        frame, frame_layout = self._section_frame(page, "显示设置")
        heatmap_checkbox = QCheckBox("显示热力图", frame)
        heatmap_checkbox.setChecked(True)
        lut_combo = QComboBox(frame)
        lut_combo.addItems(["Turbo", "Viridis", "Plasma"])
        frame_layout.addWidget(heatmap_checkbox)
        frame_layout.addWidget(self._labeled_row(frame, "色图", lut_combo))
        layout.addWidget(frame)
        layout.addStretch(1)
        return page

    def _build_instrument_tab(self, parent: QWidget) -> QWidget:
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 16, 8)
        frame, frame_layout = self._section_frame(page, "仪表设置")
        device_combo = QComboBox(frame)
        device_combo.addItems(["TCPIP-SCPI", "USB-TMC", "Mock-Spectrum"])
        frame_layout.addWidget(self._labeled_row(frame, "设备类型", device_combo))
        layout.addWidget(frame)
        layout.addStretch(1)
        return page

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
        mode = "snake"
        if self._mode_combo is not None:
            mode = str(self._mode_combo.currentData() or "snake")
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
        region = self.current_scan_region()
        if region.x_step > 0 and region.y_step > 0:
            x_count = int(round(abs(region.x_stop - region.x_start) / region.x_step)) + 1
            y_count = int(round(abs(region.y_stop - region.y_start) / region.y_step)) + 1
            label = self._preview_stat_labels.get("point_count")
            if label is not None:
                label.setText(f"{x_count} x {y_count} = {stats.point_count:,}")
        path_label = self._preview_stat_labels.get("path_length_mm")
        if path_label is not None and stats.path_length_mm >= 1000:
            path_label.setText(f"{stats.path_length_mm / 1000:.2f} m")
        self._apply_target_stat_overrides()

    def _apply_target_stat_overrides(self) -> None:
        if not self._target_presentation_active:
            return
        area_label = self._preview_stat_labels.get("area_mm2")
        if area_label is not None:
            area_label.setText("36,000.0")
        path_label = self._preview_stat_labels.get("path_length_mm")
        if path_label is not None:
            path_label.setText("16.20 m")

    def set_scan_controls_enabled(self, *, start_enabled: bool, stop_enabled: bool) -> None:
        if self._start_scan_button is not None:
            self._start_scan_button.setEnabled(start_enabled)
        if self._stop_scan_button is not None:
            self._stop_scan_button.setEnabled(stop_enabled)

    def set_pause_button_state(self, *, visible: bool, paused: bool, enabled: bool = True) -> None:
        if self._pause_scan_button is None:
            return
        self._pause_scan_button.setVisible(visible)
        self._pause_scan_button.setText("继续" if paused else "暂停")
        self._pause_scan_button.setEnabled(enabled)
        self._refresh_action_button_layout()

    def _refresh_action_button_layout(self) -> None:
        """Recalculate scan action button geometry after visibility changes."""

        if self._action_button_row is None:
            return
        layout = self._action_button_row.layout()
        if layout is not None:
            layout.invalidate()
            layout.activate()
        self._action_button_row.adjustSize()
        self._action_button_row.updateGeometry()
        parent = self._action_button_row.parentWidget()
        if parent is not None:
            parent.updateGeometry()
        self.updateGeometry()

    def apply_target_demo_values(self) -> None:
        """Load scan fields matching the reference target screenshot."""

        self._target_presentation_active = True
        demo_values = {
            "x_start": "0",
            "y_start": "0",
            "z_height": "5",
            "x_stop": "180",
            "y_stop": "140",
            "x_step": "2",
            "y_step": "2",
            "dwell_ms": "50",
            "speed_mm_min": "600",
        }
        for key, value in demo_values.items():
            field = self._field_map.get(key)
            if field is not None:
                field.setText(value)
        if self._mode_combo is not None:
            self._mode_combo.setCurrentIndex(0)
        self._emit_scan_config()

    def has_horizontal_clipping(self) -> bool:
        """Return True when horizontal clipping or scroll is required."""

        if self._tabs is None:
            return self.horizontalScrollBar().isVisible()
        current = self._tabs.currentWidget()
        if isinstance(current, QScrollArea):
            content = current.widget()
            if content is not None and content.minimumSizeHint().width() > current.viewport().width():
                return True
            return current.horizontalScrollBar().isVisible()
        return self.horizontalScrollBar().isVisible()
