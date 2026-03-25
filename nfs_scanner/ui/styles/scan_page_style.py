"""Stylesheet definitions for the scan control page."""

from __future__ import annotations


def build_scan_page_stylesheet() -> str:
    """Return a dark industrial stylesheet for scan-control related widgets."""

    return """
QWidget#scanControlRoot {
    background-color: #1f232a;
    color: #d9e1ea;
}

QGroupBox {
    border: 1px solid #3b4450;
    border-radius: 8px;
    margin-top: 14px;
    font-weight: 600;
    color: #dce3eb;
    background-color: #262b33;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 2px;
    padding: 0 6px;
    color: #9fc5ff;
}

QFrame#sectionBody,
QFrame#summaryBar,
QFrame#statusBarFrame {
    background-color: #262b33;
    border: 1px solid #3b4450;
    border-radius: 8px;
}

QPushButton {
    background-color: #3a434f;
    color: #e4ebf3;
    border: 1px solid #4c5766;
    border-radius: 6px;
    padding: 6px 10px;
}

QPushButton:hover {
    background-color: #465260;
}

QPushButton:pressed {
    background-color: #313a45;
}

QPushButton#primaryButton {
    background-color: #1d6fd3;
    border-color: #2f87ef;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background-color: #2a7ce2;
}

QPushButton#dangerButton {
    background-color: #844046;
    border-color: #a24f58;
}

QPushButton#dangerButton:hover {
    background-color: #9a4d56;
}

QLineEdit,
QComboBox,
QPlainTextEdit,
QTextEdit,
QTableWidget,
QTabWidget::pane {
    background-color: #20252d;
    border: 1px solid #44505e;
    border-radius: 6px;
    color: #d8e2ed;
    selection-background-color: #2f87ef;
}

QLineEdit {
    padding: 5px 8px;
}

QHeaderView::section {
    background-color: #303744;
    color: #ecf2f9;
    border: 1px solid #465362;
    font-weight: 700;
    padding: 6px;
}

QTableWidget {
    gridline-color: #3f4a57;
}

QTabBar::tab {
    background-color: #323a45;
    border: 1px solid #4a5666;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #1f6fd0;
    color: #f2f7fd;
}

QLabel#sectionSummary {
    color: #9db0c7;
}

QToolButton#toggleButton {
    border: none;
    font-size: 14px;
    font-weight: 700;
    color: #a9c8f8;
    padding: 2px 6px;
}

QToolButton#toggleButton:hover {
    color: #d2e6ff;
}

QPlainTextEdit {
    font-family: "Consolas", "Courier New", monospace;
}
"""
