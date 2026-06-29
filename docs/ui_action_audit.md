# 商业版 UI 按钮 / 动作审计

> 审计日期：2026-06-28  
> 范围：`nfs_scanner/ui/commercial/` 商业版 Mock Dry Run UI

## 摘要

| 类别 | 数量 | 说明 |
|------|------|------|
| Action Registry 动作 | 57 | 全部已注册 handler |
| 顶部工具栏按钮 | 14 | 含 overflow 次级按钮 |
| 工作区 Tab | 7 | 全部可切换 |
| 左侧流程步骤 | 7 | 可点击跳转 + 日志 |
| 右侧参数 Tab | 4 | 扫描/显示/仪表/设备 Mock |
| 底部日志 Tag | 6 | INFO/WARN/ERROR/SCAN/DATA + 清空 |

**原则**：Mock / Dry Run 模式下所有硬件动作为模拟；真实硬件需显式确认（当前未实现 Real Mode）。

---

## 1. 顶部工具栏

| 按钮 | Handler | 状态 | 成功日志 | 失败/警告日志 |
|------|---------|------|----------|---------------|
| 新建 | `project.new` → `_on_new_project` | WORKING | `[PROJECT] New project created` | 未保存确认对话框 |
| 打开 | `project.open` → `_on_open_project` | WORKING | `[PROJECT] Opened: <path>` | `[ERROR] Open project failed` |
| 保存 | `project.save` → `_on_save_project` | WORKING | `[PROJECT] Saved: <path>` | 请先新建/打开项目 |
| 连接 | `device.connect_all` | WORKING | `[DEVICE] Mock devices connected: ...` | — |
| 开始 | `scan.start` → Dry Run | WORKING | `[SCAN] Dry run scan started: N points` | `[WARN] 参数无效` |
| 暂停 | `_toggle_mock_scan_pause` | WORKING | pause/resume 日志 | toolbar pause 按钮已修复赋值 |
| 停止 | `scan.stop` | WORKING | `[SCAN] Dry run scan stopped by user` | `[WARN] No running scan task` |
| 导出 | `_on_export_data_menu` | WORKING | `[DATA] Exported CSV/PNG/JSON` | `[WARN] mock template only` |
| 报告 | `report.open_center` + HTML 生成 | WORKING | `[REPORT] Report generated` | 无项目时 WARN |
| 拍照 | `camera.capture` 截图 | WORKING (Mock) | `[EXPORT] 相机快照` | — |
| 对齐 | `region.align` | WORKING (Mock) | `[SCAN] 区域对齐` | — |
| 清除 | `region.clear` | WORKING | UI 日志 | — |
| 参数 | 跳转扫描参数 Tab | WORKING | `[PARAM]` | — |
| 帮助 | `DemoHelpDialog` | WORKING | `[INFO] Help opened` | — |

---

## 2. 工作区 Tab

| Tab | 视图类 | 状态 |
|-----|--------|------|
| 实时视图 | `RealtimeView` | WORKING — 图层/工具栏/底图 |
| 数据视图 | `DataView` | WORKING — Mock 任务/导出 |
| 3D 视图 | `ThreeDView` | WORKING — Mock 3D 占位 |
| 数据表格 | `DataTableView` | WORKING — 过滤/导出/排序 |
| 报告中心 | `ReportView` | WORKING — HTML/MD/PNG 导出 |
| 设备中心 | `DeviceCenterView` | WORKING — Mock 连接/刷新 |
| 相机/视觉 | `VisionView` | WORKING — 安全枚举 + 预览 |

---

## 3. 左侧扫描流程（可点击）

| 步骤 | 动作 | 日志 |
|------|------|------|
| 项目管理 | 跳转实时视图 | `[PROJECT] Project management opened` |
| 设备连接 | 跳转设备中心 | `[DEVICE] Device center opened` |
| 区域标定 | 跳转实时视图 | `[SCAN] Region calibration opened` |
| 扫描配置 | 聚焦右侧扫描参数 | `[PARAM] Scan configuration opened` |
| 扫描执行 | 跳转实时视图 + 提示开始 | `[SCAN] Execution step selected` |
| 数据分析 | 跳转数据视图 | `[DATA] Data analysis opened` |
| 报告导出 | 跳转报告中心 | `[REPORT] Report center opened` |

---

## 4. 右侧参数区

| 控件 | 状态 | 日志 |
|------|------|------|
| 扫描区域编辑 | WORKING — debounce 自动更新 | — |
| 应用参数 | WORKING — 新增按钮 | `[PARAM] Scan area applied` |
| 重置参数 | WORKING — 新增按钮 | `[PARAM] Scan parameters reset` |
| 参数模板 | WORKING | `[SCAN] 参数模板已应用` |
| 显示设置 LUT/透明度/图层 | WORKING | `[UI]` / `[DISPLAY]` |
| 仪表 Mock 配置保存 | WORKING | `[INSTR] Mock instrument settings applied` |
| 开始/停止/暂停扫描 | WORKING | `[SCAN]` |

---

## 5. 底部日志区

| 控件 | 状态 | 说明 |
|------|------|------|
| INFO/WARN/ERROR/SCAN/DATA | WORKING | 点击 Tag 单选过滤；再点恢复 |
| 清空 | WORKING | `[INFO] Log view cleared` |
| LogBus | WORKING | 内存最多 1000 条 |

---

## 6. 设备中心

| 按钮 | 状态 | 日志 |
|------|------|------|
| 全部刷新 | WORKING | DEVICE 刷新 |
| 连接/断开 | WORKING (Mock) | `[DEVICE] Mock device connected/disconnected` |
| 查看详情 | WORKING | Detail 对话框 |
| 应用 Mock 配置 | WORKING | CONFIG 保存 |

**安全**：刷新/连接 **不会** 打开 USB 相机。

---

## 7. 相机 / 视觉

| 按钮 | 状态 | 日志 |
|------|------|------|
| 刷新设备 | WORKING — 安全枚举 | `[CAMERA] Safe refresh completed` |
| 开始预览 | WORKING — 仅此时打开相机 | `[CAMERA] Preview started` |
| 停止预览 | WORKING | `[CAMERA] Preview stopped` |
| 拍照 | WORKING | `[CAMERA] Snapshot saved` |
| 设为扫描底图 | WORKING | `[BACKGROUND] Set scan background` |
| 清除底图 | WORKING（实时视图） | `[BACKGROUND] Background cleared` |

---

## 8. 仍为 Mock 的行为

- 运动平台移动、真实频谱采集、真实 VNA 控制
- Dry Run 扫描进度与幅度数据为模拟
- 3D 视图为 Mock surface
- PDF 报告为 placeholder
- Toolbar「拍照」为实时视图截图，非 USB 相机帧（USB 拍照在相机 Tab）

---

## 9. 真实硬件安全屏蔽

- 顶部「连接」仅 Mock connect_all
- 扫描开始/停止不发真实运动命令
- 相机枚举默认 `CAMERA_SAFE_ENUMERATION=True`
- 设备中心串口枚举 dead code（保持 Mock）
- Real Mode 切换：未实现，尝试时 WARN

---

## 10. 测试覆盖

见 `tests/test_ui_actions.py`、`test_export_manager.py`、`test_report_generator.py`、`test_project_manager.py`、`test_scan_simulator.py`、`test_background_image.py`、`test_camera_opencv.py`。
