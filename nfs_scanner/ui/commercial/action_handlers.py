"""Build CommercialActionRegistry with handlers bound to the main shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .actions import CommercialActionRegistry

if TYPE_CHECKING:
    from .main_shell import CommercialMainShell


def build_action_registry(shell: CommercialMainShell) -> CommercialActionRegistry:
    """Register all Commercial V1 actions with shell-bound handlers."""

    registry = CommercialActionRegistry()
    realtime = shell.workspace.realtime_view()
    data_view = shell.workspace.data_view()
    report_view = shell.workspace.report_view()
    device_center = shell.workspace.device_center_view()
    property_panel = shell.property_panel

    # --- Project ---
    registry.register_simple(
        "project.new",
        "新建项目",
        lambda: shell._on_new_project(interactive=True),
        category="project",
    )
    registry.register_simple(
        "project.open",
        "打开项目",
        lambda: shell._on_open_project(interactive=True),
        category="project",
    )
    registry.register_simple(
        "project.save", "保存项目", shell._on_save_project, category="project"
    )
    registry.register_simple(
        "project.save_as",
        "另存为",
        lambda: shell._on_save_project_as(interactive=True),
        category="project",
    )
    registry.register_simple(
        "project.recent", "最近项目", shell._on_recent_projects, category="project"
    )
    registry.register_simple(
        "project.close", "关闭项目", shell._on_close_project, category="project"
    )

    # --- Device ---
    registry.register_simple(
        "device.connect_all", "连接设备", shell._on_connect_device, category="device"
    )
    registry.register_simple(
        "device.disconnect_all", "断开设备", shell._on_disconnect_devices, category="device"
    )
    registry.register_simple(
        "device.refresh_all", "刷新设备", shell._on_refresh_devices, category="device"
    )
    registry.register_simple(
        "device.open_center", "设备中心", shell._on_open_device_center, category="device"
    )
    registry.register_simple(
        "device.configure",
        "配置设备",
        lambda: device_center.focus_config_tab(),
        category="device",
    )
    registry.register_simple(
        "device.test_connection",
        "测试连接",
        lambda: device_center.test_selected_connection(),
        category="device",
    )

    # --- Scan ---
    registry.register_simple(
        "scan.start", "开始扫描", shell._start_mock_scan, category="scan"
    )
    registry.register_simple(
        "scan.pause", "暂停扫描", shell._pause_mock_scan, category="scan"
    )
    registry.register_simple(
        "scan.resume", "继续扫描", shell._resume_mock_scan, category="scan"
    )
    registry.register_simple(
        "scan.stop", "停止扫描", shell._stop_mock_scan, category="scan"
    )
    registry.register_simple(
        "scan.reset", "重置扫描", shell._reset_scan_runtime, category="scan"
    )
    registry.register_simple(
        "scan.apply_config",
        "应用配置",
        lambda: property_panel.emit_current_scan_config(),
        category="scan",
    )
    registry.register_simple(
        "scan.preview_path",
        "预览路径",
        lambda: property_panel.emit_current_scan_config(),
        category="scan",
    )

    # --- Camera ---
    registry.register_simple(
        "camera.capture", "拍照", lambda: shell._trigger_action("camera.capture"), category="camera"
    )

    # --- Region ---
    registry.register_simple(
        "region.align", "区域对齐", lambda: shell._trigger_action("region.align"), category="region"
    )
    registry.register_simple(
        "region.clear", "清除覆盖", lambda: shell._trigger_action("region.clear"), category="region"
    )
    registry.register_simple(
        "region.select",
        "选择",
        lambda: realtime.activate_tool("选择"),
        category="region",
    )
    registry.register_simple(
        "region.box_select",
        "框选",
        lambda: realtime.activate_tool("框选"),
        category="region",
    )
    registry.register_simple(
        "region.polygon_select",
        "多边形",
        lambda: realtime.activate_tool("多边形"),
        category="region",
    )

    # --- View tools ---
    registry.register_simple("view.fit", "适应", realtime.fit_canvas, category="view")
    registry.register_simple("view.reset", "重置", realtime.reset_canvas, category="view")
    registry.register_simple(
        "view.pan", "平移", lambda: realtime.activate_tool("平移"), category="view"
    )
    registry.register_simple(
        "view.zoom", "缩放", lambda: realtime.activate_tool("缩放"), category="view"
    )
    registry.register_simple(
        "view.select", "选择", lambda: realtime.activate_tool("选择"), category="view"
    )
    registry.register_simple("view.undo", "撤销", realtime.undo_last_action, category="view")
    registry.register_simple("view.redo", "重做", realtime.redo_last_action, category="view")
    registry.register_simple(
        "view.annotate", "标注", lambda: realtime.activate_tool("标注"), category="view"
    )
    registry.register_simple("view.grid_toggle", "网格", realtime.toggle_grid, category="view")
    registry.register_simple("view.path_toggle", "路径", realtime.toggle_path, category="view")
    registry.register_simple(
        "view.measure", "测量", lambda: realtime.activate_tool("测量"), category="view"
    )
    registry.register_simple(
        "view.lut_change",
        "LUT",
        lambda: realtime.cycle_lut(),
        category="view",
    )
    registry.register_simple(
        "view.opacity_change",
        "透明度",
        lambda: realtime.adjust_opacity_step(5),
        category="view",
    )

    # --- Data ---
    registry.register_simple(
        "data.open_view", "数据视图", shell._on_open_data_view, category="data"
    )
    registry.register_simple(
        "data.export_json",
        "导出 JSON",
        lambda: data_view.export_selected_json(),
        category="data",
    )
    registry.register_simple(
        "data.export_csv",
        "导出 CSV",
        lambda: data_view.export_selected_csv(),
        category="data",
    )
    registry.register_simple(
        "data.export_table",
        "导出表格",
        lambda: shell.workspace.data_table_view().export_csv(),
        category="data",
    )
    registry.register_simple(
        "data.clear_history",
        "清空历史",
        lambda: data_view.clear_history(),
        category="data",
    )

    # --- Report ---
    registry.register_simple(
        "report.open_center", "报告中心", shell._on_report_center, category="report"
    )
    registry.register_simple(
        "report.preview",
        "报告预览",
        lambda: report_view.preview_current_report(),
        category="report",
    )
    registry.register_simple(
        "report.export_md",
        "导出 Markdown",
        lambda: report_view.export_markdown(),
        category="report",
    )
    registry.register_simple(
        "report.export_html",
        "导出 HTML",
        lambda: report_view.export_html(),
        category="report",
    )
    registry.register_simple(
        "report.export_png",
        "导出 PNG",
        lambda: report_view.export_png(),
        category="report",
    )
    registry.register_simple(
        "report.export_pdf_placeholder",
        "导出 PDF",
        lambda: report_view.export_pdf_placeholder(),
        category="report",
    )

    # --- Settings ---
    registry.register_simple(
        "settings.display",
        "显示设置",
        lambda: property_panel.focus_display_tab(),
        category="settings",
    )
    registry.register_simple(
        "settings.instrument",
        "仪表设置",
        lambda: property_panel.focus_instrument_tab(),
        category="settings",
    )
    registry.register_simple(
        "settings.apply_template",
        "参数模板",
        lambda: shell._trigger_action("settings.apply_template"),
        category="settings",
    )
    registry.register_simple(
        "settings.save_device_config",
        "保存设备配置",
        lambda: property_panel._save_instrument_mock_config(),
        category="settings",
    )

    # --- Help ---
    registry.register_simple("help.open", "帮助", shell._show_help_dialog, category="help")
    registry.register_simple(
        "help.shortcuts",
        "快捷键",
        lambda: shell._show_help_dialog(tab="shortcuts"),
        category="help",
    )
    registry.register_simple(
        "help.self_check", "自检", shell._run_commercial_self_check, category="help"
    )
    registry.register_simple(
        "help.about",
        "关于",
        lambda: shell._show_help_dialog(tab="about"),
        category="help",
    )

    # --- Demo reset ---
    registry.register_simple(
        "demo.reset", "Reset Demo", shell._reset_demo_session, category="demo"
    )

    return registry
