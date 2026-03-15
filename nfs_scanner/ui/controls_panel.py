"""Left-side controls panel for the Near Field Scan System."""

from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core import ScanConfig


class ControlsPanel(QWidget):
    """Left-side structured panel for control-related parameters."""

    DEFAULT_X_VALUE = "0"
    DEFAULT_Y_VALUE = "0"
    DEFAULT_Z_VALUE = "5"
    DEFAULT_SCAN_START_X = "0"
    DEFAULT_SCAN_STOP_X = "4"
    DEFAULT_SCAN_STEP_X = "1"
    DEFAULT_SCAN_START_Y = "0"
    DEFAULT_SCAN_STOP_Y = "4"
    DEFAULT_SCAN_STEP_Y = "1"
    DEFAULT_SCAN_MODE = "snake"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.serial_port_combo: QComboBox
        self.baud_rate_combo: QComboBox
        self.serial_connect_button: QPushButton
        self.x_input: QLineEdit
        self.y_input: QLineEdit
        self.z_input: QLineEdit
        self.move_button: QPushButton
        self.home_button: QPushButton
        self.scan_start_x_input: QLineEdit
        self.scan_stop_x_input: QLineEdit
        self.scan_step_x_input: QLineEdit
        self.scan_start_y_input: QLineEdit
        self.scan_stop_y_input: QLineEdit
        self.scan_step_y_input: QLineEdit
        self.scan_mode_combo: QComboBox
        self.start_scan_button: QPushButton
        self.stop_scan_button: QPushButton
        self.reset_defaults_button: QPushButton
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel layout."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(self._create_serial_settings_group())
        layout.addWidget(self._create_motion_control_group())
        layout.addWidget(self._create_scan_parameters_group())
        layout.addStretch(1)

    def _create_serial_settings_group(self) -> QGroupBox:
        """Create the serial settings group."""

        group_box = QGroupBox("串口设置", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.serial_port_combo = QComboBox(group_box)
        self.serial_port_combo.addItem("端口列表（后续接入）")

        self.baud_rate_combo = QComboBox(group_box)
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_rate_combo.setCurrentText("115200")

        self.serial_connect_button = QPushButton("连接", group_box)

        layout.addRow("串口选择", self.serial_port_combo)
        layout.addRow("波特率", self.baud_rate_combo)
        layout.addRow("", self.serial_connect_button)

        return group_box

    def _create_motion_control_group(self) -> QGroupBox:
        """Create the motion control group."""

        group_box = QGroupBox("运动控制", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.x_input = self._create_axis_input(group_box)
        self.y_input = self._create_axis_input(group_box)
        self.z_input = self._create_axis_input(group_box)
        self.x_input.setText(self.DEFAULT_X_VALUE)
        self.y_input.setText(self.DEFAULT_Y_VALUE)
        self.z_input.setText(self.DEFAULT_Z_VALUE)

        self.move_button = QPushButton("移动", group_box)
        self.home_button = QPushButton("回零", group_box)

        button_container = QWidget(group_box)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.home_button)

        layout.addRow("X 输入", self.x_input)
        layout.addRow("Y 输入", self.y_input)
        layout.addRow("Z 输入", self.z_input)
        layout.addRow("", button_container)

        return group_box

    def _create_scan_parameters_group(self) -> QGroupBox:
        """Create the scan parameter group."""

        group_box = QGroupBox("扫描参数", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.scan_start_x_input = self._create_axis_input(group_box)
        self.scan_stop_x_input = self._create_axis_input(group_box)
        self.scan_step_x_input = self._create_axis_input(group_box)
        self.scan_start_y_input = self._create_axis_input(group_box)
        self.scan_stop_y_input = self._create_axis_input(group_box)
        self.scan_step_y_input = self._create_axis_input(group_box)
        self.scan_start_x_input.setText(self.DEFAULT_SCAN_START_X)
        self.scan_stop_x_input.setText(self.DEFAULT_SCAN_STOP_X)
        self.scan_step_x_input.setText(self.DEFAULT_SCAN_STEP_X)
        self.scan_start_y_input.setText(self.DEFAULT_SCAN_START_Y)
        self.scan_stop_y_input.setText(self.DEFAULT_SCAN_STOP_Y)
        self.scan_step_y_input.setText(self.DEFAULT_SCAN_STEP_Y)

        self.scan_mode_combo = QComboBox(group_box)
        self.scan_mode_combo.addItems(["raster", "snake"])
        self.scan_mode_combo.setCurrentText(self.DEFAULT_SCAN_MODE)

        self.start_scan_button = QPushButton("开始扫描", group_box)
        self.stop_scan_button = QPushButton("停止扫描", group_box)
        self.reset_defaults_button = QPushButton("恢复默认配置", group_box)

        button_container = QWidget(group_box)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addWidget(self.start_scan_button)
        button_layout.addWidget(self.stop_scan_button)

        layout.addRow("起始X", self.scan_start_x_input)
        layout.addRow("终止X", self.scan_stop_x_input)
        layout.addRow("步长X", self.scan_step_x_input)
        layout.addRow("起始Y", self.scan_start_y_input)
        layout.addRow("终止Y", self.scan_stop_y_input)
        layout.addRow("步长Y", self.scan_step_y_input)
        layout.addRow("扫描模式", self.scan_mode_combo)
        layout.addRow("", button_container)
        layout.addRow("", self.reset_defaults_button)

        return group_box

    def _create_axis_input(self, parent: QWidget) -> QLineEdit:
        """Create a numeric placeholder input."""

        line_edit = QLineEdit(parent)
        line_edit.setPlaceholderText("请输入数值")
        return line_edit

    def get_scan_config(self) -> ScanConfig:
        """Build a scan configuration from the current UI values."""

        defaults = ScanConfig(
            start_x=float(self.DEFAULT_SCAN_START_X),
            stop_x=float(self.DEFAULT_SCAN_STOP_X),
            step_x=float(self.DEFAULT_SCAN_STEP_X),
            start_y=float(self.DEFAULT_SCAN_START_Y),
            stop_y=float(self.DEFAULT_SCAN_STOP_Y),
            step_y=float(self.DEFAULT_SCAN_STEP_Y),
            z_height=float(self.DEFAULT_Z_VALUE),
            scan_mode=self.DEFAULT_SCAN_MODE,
        )
        return ScanConfig(
            start_x=self._read_float(self.scan_start_x_input, defaults.start_x),
            stop_x=self._read_float(self.scan_stop_x_input, defaults.stop_x),
            step_x=self._read_float(self.scan_step_x_input, defaults.step_x),
            start_y=self._read_float(self.scan_start_y_input, defaults.start_y),
            stop_y=self._read_float(self.scan_stop_y_input, defaults.stop_y),
            step_y=self._read_float(self.scan_step_y_input, defaults.step_y),
            z_height=self._read_float(self.z_input, defaults.z_height),
            scan_mode=self.scan_mode_combo.currentText().strip() or defaults.scan_mode,
        )

    def get_persistent_scan_settings(self) -> dict[str, str]:
        """Return scan settings that should persist across app runs."""

        return {
            "start_x": self._get_text_or_default(self.scan_start_x_input, self.DEFAULT_SCAN_START_X),
            "stop_x": self._get_text_or_default(self.scan_stop_x_input, self.DEFAULT_SCAN_STOP_X),
            "step_x": self._get_text_or_default(self.scan_step_x_input, self.DEFAULT_SCAN_STEP_X),
            "start_y": self._get_text_or_default(self.scan_start_y_input, self.DEFAULT_SCAN_START_Y),
            "stop_y": self._get_text_or_default(self.scan_stop_y_input, self.DEFAULT_SCAN_STOP_Y),
            "step_y": self._get_text_or_default(self.scan_step_y_input, self.DEFAULT_SCAN_STEP_Y),
            "scan_mode": self.scan_mode_combo.currentText().strip() or self.DEFAULT_SCAN_MODE,
        }

    def apply_persistent_scan_settings(self, settings: Mapping[str, Any]) -> None:
        """Apply persisted scan settings back into the panel."""

        self.scan_start_x_input.setText(
            self._coerce_setting(settings.get("start_x"), self.DEFAULT_SCAN_START_X)
        )
        self.scan_stop_x_input.setText(
            self._coerce_setting(settings.get("stop_x"), self.DEFAULT_SCAN_STOP_X)
        )
        self.scan_step_x_input.setText(
            self._coerce_setting(settings.get("step_x"), self.DEFAULT_SCAN_STEP_X)
        )
        self.scan_start_y_input.setText(
            self._coerce_setting(settings.get("start_y"), self.DEFAULT_SCAN_START_Y)
        )
        self.scan_stop_y_input.setText(
            self._coerce_setting(settings.get("stop_y"), self.DEFAULT_SCAN_STOP_Y)
        )
        self.scan_step_y_input.setText(
            self._coerce_setting(settings.get("step_y"), self.DEFAULT_SCAN_STEP_Y)
        )

        scan_mode = self._coerce_setting(settings.get("scan_mode"), self.DEFAULT_SCAN_MODE)
        if self.scan_mode_combo.findText(scan_mode) >= 0:
            self.scan_mode_combo.setCurrentText(scan_mode)

    def reset_scan_defaults(self) -> None:
        """Reset scan inputs and scan mode to their default values."""

        self.apply_persistent_scan_settings(self.get_default_scan_settings())

    def get_default_scan_settings(self) -> dict[str, str]:
        """Return the default scan settings."""

        return {
            "start_x": self.DEFAULT_SCAN_START_X,
            "stop_x": self.DEFAULT_SCAN_STOP_X,
            "step_x": self.DEFAULT_SCAN_STEP_X,
            "start_y": self.DEFAULT_SCAN_START_Y,
            "stop_y": self.DEFAULT_SCAN_STOP_Y,
            "step_y": self.DEFAULT_SCAN_STEP_Y,
            "scan_mode": self.DEFAULT_SCAN_MODE,
        }

    def _read_float(self, line_edit: QLineEdit, default_value: float) -> float:
        """Read a float from one line edit, or fall back to a default."""

        text = line_edit.text().strip()
        if not text:
            return default_value
        return float(text)

    def _get_text_or_default(self, line_edit: QLineEdit, default_value: str) -> str:
        """Return the current field text or a fallback default."""

        value = line_edit.text().strip()
        return value if value else default_value

    def _coerce_setting(self, value: Any, default_value: str) -> str:
        """Convert one persisted setting into a safe line-edit value."""

        if value is None:
            return default_value
        text = str(value).strip()
        return text if text else default_value
