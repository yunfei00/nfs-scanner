"""Right-side spectrum settings panel."""

from __future__ import annotations

from typing import Any, Mapping

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from nfs_scanner.core import SpectrumConfig


class SpectrumPanel(QWidget):
    """Right-side structured panel for spectrum-related settings."""

    DEFAULT_DEVICE_TYPE = "TCPIP-SCPI"
    DEVICE_TYPE_OPTIONS = ("FSW", "N9020A", "ZNA67", "TCPIP-SCPI", "USB-TMC", "Mock-Spectrum")
    DEFAULT_START_FREQ = "100MHz"
    DEFAULT_STOP_FREQ = "3GHz"
    DEFAULT_RBW = "100kHz"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.device_type_combo: QComboBox
        self.device_connect_button: QPushButton
        self.start_freq_input: QLineEdit
        self.stop_freq_input: QLineEdit
        self.rbw_input: QLineEdit
        self.lut_combo: QComboBox
        self.auto_range_checkbox: QCheckBox
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel layout."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        layout.addWidget(self._create_device_group())
        layout.addWidget(self._create_frequency_group())
        layout.addWidget(self._create_display_group())
        layout.addStretch(1)

    def _create_device_group(self) -> QGroupBox:
        """Create the device connection group."""

        group_box = QGroupBox("设备连接", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.device_type_combo = QComboBox(group_box)
        self.device_type_combo.addItems(list(self.DEVICE_TYPE_OPTIONS))
        self.device_type_combo.setCurrentText(self.DEFAULT_DEVICE_TYPE)

        self.device_connect_button = QPushButton("连接", group_box)

        layout.addRow("设备类型", self.device_type_combo)
        layout.addRow("", self.device_connect_button)

        return group_box

    def _create_frequency_group(self) -> QGroupBox:
        """Create the frequency settings group."""

        group_box = QGroupBox("频率设置", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.start_freq_input = self._create_input(self.DEFAULT_START_FREQ, group_box)
        self.stop_freq_input = self._create_input(self.DEFAULT_STOP_FREQ, group_box)
        self.rbw_input = self._create_input(self.DEFAULT_RBW, group_box)

        layout.addRow("Start Freq", self.start_freq_input)
        layout.addRow("Stop Freq", self.stop_freq_input)
        layout.addRow("RBW", self.rbw_input)

        return group_box

    def _create_display_group(self) -> QGroupBox:
        """Create the display settings group."""

        group_box = QGroupBox("显示设置", self)
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QFormLayout(group_box)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        self.lut_combo = QComboBox(group_box)
        self.lut_combo.addItems(["viridis", "jet", "gray", "hot"])

        self.auto_range_checkbox = QCheckBox("启用自动范围", group_box)
        self.auto_range_checkbox.setChecked(True)

        layout.addRow("LUT", self.lut_combo)
        layout.addRow("自动范围", self.auto_range_checkbox)

        return group_box

    def get_selected_device_type(self) -> str:
        """Return the selected placeholder spectrum-device type."""

        return self.device_type_combo.currentText().strip()

    def set_selected_device_type(self, device_type: str) -> None:
        """Apply the last persisted spectrum-device selection."""

        normalized = device_type.strip() or self.DEFAULT_DEVICE_TYPE
        index = self.device_type_combo.findText(normalized)
        if index >= 0:
            self.device_type_combo.setCurrentIndex(index)

    def get_persistent_settings(self) -> dict[str, str]:
        """Return spectrum settings that should persist across app runs."""

        return {
            "spectrum_start_freq": self._get_text_or_default(
                self.start_freq_input, self.DEFAULT_START_FREQ
            ),
            "spectrum_stop_freq": self._get_text_or_default(
                self.stop_freq_input, self.DEFAULT_STOP_FREQ
            ),
            "spectrum_rbw": self._get_text_or_default(self.rbw_input, self.DEFAULT_RBW),
            "spectrum_device_type": self.get_selected_device_type() or self.DEFAULT_DEVICE_TYPE,
        }

    def apply_persistent_settings(self, settings: Mapping[str, Any]) -> None:
        """Apply persisted spectrum settings back into the panel."""

        self.start_freq_input.setText(
            self._coerce_setting(settings.get("spectrum_start_freq"), self.DEFAULT_START_FREQ)
        )
        self.stop_freq_input.setText(
            self._coerce_setting(settings.get("spectrum_stop_freq"), self.DEFAULT_STOP_FREQ)
        )
        self.rbw_input.setText(self._coerce_setting(settings.get("spectrum_rbw"), self.DEFAULT_RBW))
        self.set_selected_device_type(
            self._coerce_setting(settings.get("spectrum_device_type"), self.DEFAULT_DEVICE_TYPE)
        )

    def get_spectrum_config(self) -> SpectrumConfig:
        """Return the current spectrum parameter snapshot."""

        return SpectrumConfig(
            start_freq=self._get_text_or_default(self.start_freq_input, self.DEFAULT_START_FREQ),
            stop_freq=self._get_text_or_default(self.stop_freq_input, self.DEFAULT_STOP_FREQ),
            rbw=self._get_text_or_default(self.rbw_input, self.DEFAULT_RBW),
            lut_name=self.lut_combo.currentText().strip(),
            auto_range=self.auto_range_checkbox.isChecked(),
        )

    def _create_input(self, default_value: str, parent: QWidget) -> QLineEdit:
        """Create a line edit with a default placeholder value."""

        line_edit = QLineEdit(parent)
        line_edit.setText(default_value)
        return line_edit

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
