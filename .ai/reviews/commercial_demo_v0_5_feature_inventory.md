# Commercial Demo v0.5 — 功能入口清单

> 状态标记：`implemented` | `mock implemented` | `disabled` | `missing`  
> 本轮目标：missing = 0

## 1. 顶部工具栏

| 按钮 | 状态 | 行为 |
|------|------|------|
| 新建 | mock implemented | MockProjectService.new_project |
| 打开 | mock implemented | open_mock_project |
| 保存 | mock implemented | JSON → ~/.nfs_scanner/demo_projects/ |
| 连接 | mock implemented | 全连 mock 设备 + 设备中心 |
| 开始 | mock implemented | MockScanController.start（自动补齐项目/设备/参数） |
| 暂停 | mock implemented | 溢出菜单 + 右侧属性面板（running/paused） |
| 停止 | mock implemented | mock stop，不生成 completed task |
| 拍照 | mock implemented | 快照 PNG → ~/.nfs_scanner/screenshots/ |
| 区域对齐 | mock implemented | ROI/mock 控制点刷新 + workflow 第 3 步 |
| 清除 | mock implemented | 清除 annotation/marker 覆盖层 |
| 导出 | mock implemented | Data JSON 或 demo sample |
| 报告 | mock implemented | 切换 Report Center + 预览 |
| 参数 | mock implemented | 聚焦扫描参数 + 应用标准模板 |
| 帮助 | mock implemented | DemoHelpDialog（流程/安全/自检） |
| Reset Demo | mock implemented | 溢出菜单 → _reset_demo_session |

## 2. Workflow（7 步）

| 步骤 | 状态 |
|------|------|
| 1–7 导航 | mock implemented |
| 状态驱动 | DemoState 单一状态源 |

## 3. 右侧属性页

| Tab | 状态 |
|-----|------|
| 扫描参数 | mock implemented（区域模板 + 快速/标准/高密度参数模板） |
| 显示设置 | mock implemented（LUT/透明度/图层开关/Reset View） |
| 仪表设置 | mock implemented（频谱/相机/运动 mock 配置 + JSON 保存） |

## 4. Workspace Tabs

| Tab | 状态 |
|-----|------|
| 实时视图 | mock implemented |
| 数据视图 | mock implemented（深化统计/删除/清空历史） |
| 3D 视图 | mock implemented（QPainter 伪 3D） |
| 数据表格 | mock implemented（过滤/排序/CSV/JSON 导出） |
| 报告中心 | mock implemented（三模板 + demo 预览） |
| 设备中心 | mock implemented |

## 5. 底部 Dock

| 面板 | 状态 |
|------|------|
| 频谱 | mock implemented |
| 统计 | mock implemented |
| 日志 | mock implemented |

## 6. 导出体系

| 类型 | 路径 |
|------|------|
| project JSON | ~/.nfs_scanner/demo_projects/ |
| data JSON | ~/.nfs_scanner/mock_exports/data/ |
| table CSV/JSON | ~/.nfs_scanner/mock_exports/tables/ |
| report MD/HTML/PDF/PNG | ~/.nfs_scanner/reports/ |
| screenshot PNG | ~/.nfs_scanner/screenshots/ |
| device config JSON | ~/.nfs_scanner/mock_exports/config/ |
| self-check JSON/MD | .ai/qa/latest/ |

## 7. 自检 / QA

| 入口 | 状态 |
|------|------|
| 帮助 → Mock 自检 | mock implemented |
| _run_mock_self_check | mock implemented |
| tools/qa_run_commercial_demo.py | mock implemented（含 mock_features 检查） |

## missing 统计

**0** — 所有可见入口均有 mock 行为或 disabled+tooltip+日志说明。
