# 01 目录与职责

```text
nfs_scanner/
  app.py
  main.py
  version.py

  application/
    context.py                 # 管理器组合根

  ui/
    main_window.py             # 唯一窗口
    theme.py                   # 唯一主题加载
    serial_ports.py
    widgets/
      app_header.py
      scan_control_page.py     # 页面状态和核心交互
      scan_control_layout.py   # 控件与布局
      scan_workers.py          # 后台 Worker
      instrument_operations.py # 仪表动作
      scan_control_support.py  # 串口/配置/存储辅助
      instrument_panel.py
      collapsible_section.py

  core/                        # 扫描、状态、项目和业务规则
  devices/                     # 设备适配及传输实现
  storage/                     # 数据集持久化
  infra/                       # 日志等基础设施
  config/                      # 配置加载
  analysis/                    # 数据分析

resources/styles/
  engineering_dark.qss        # 唯一全局主题

tests/
tools/unified_ui_check.py
```

## 放置规则

| 内容 | 位置 |
|---|---|
| 窗口骨架 | `ui/main_window.py` |
| 页面控件和布局 | `ui/widgets/scan_control_layout.py` |
| 页面交互和状态 | `ui/widgets/scan_control_page.py` |
| 扫描/仪表后台任务 | `ui/widgets/scan_workers.py` |
| 仪表操作 | `ui/widgets/instrument_operations.py` |
| 串口、配置和存储辅助 | `ui/widgets/scan_control_support.py` |
| 扫描业务规则 | `core/` |
| 设备协议及厂商差异 | `devices/` |

不得创建 `ui/commercial`、`ui/legacy` 或其他平行 UI 目录。
