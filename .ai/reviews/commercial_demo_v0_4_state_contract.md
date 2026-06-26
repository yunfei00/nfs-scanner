# Commercial Demo v0.4 — State Contract

## 单一状态源：DemoState

所有 Workflow、状态栏、工具栏按钮状态必须从 `DemoState` 派生，禁止各面板自行推断步骤。

### 字段

| 字段 | 含义 |
|------|------|
| `project_open` | 是否有活动项目 |
| `devices_connected` | motion/spectrum/camera 已连接 |
| `scan_config_valid` | 扫描参数校验通过 |
| `scan_state` | runtime 状态 |
| `progress_percent` | 扫描进度 0–100 |
| `current_task_id` | **当前会话**完成的扫描任务（stop 后仍为 None） |
| `selected_history_task_id` | 用户在 Data View 选中的历史任务 |
| `report_exported` | 本会话是否导出过报告 |
| `report_exported_for_task_id` | 导出报告对应的 task_id |
| `has_history_tasks` | Data View 是否有历史任务（**不驱动** idle workflow） |

### Workflow 映射（0-based index）

| 步骤 | 名称 | idle/reset（有设备+有效配置） | running | completed + current_task | report exported |
|------|------|------------------------------|---------|--------------------------|-----------------|
| 0 | 项目管理 | completed | completed | completed | completed |
| 1 | 设备连接 | completed | completed | completed | completed |
| 2 | 区域标定 | completed | completed | completed | completed |
| 3 | 扫描配置 | completed | completed | completed | completed |
| 4 | 扫描执行 | **active** (待开始) | **active** | completed | completed |
| 5 | 数据分析 | pending | pending | **active** | completed |
| 6 | 报告导出 | pending | pending | pending | **completed** |

### Reset Demo 契约

Reset 后必须满足：

- `scan_state` ∈ {idle, configured}
- `progress_percent` = 0
- `current_task_id` = None
- `report_exported` = false
- Workflow 步骤 6/7（index 5/6）**不得** active 或 completed
- 状态栏任务：**未开始**
- 底部统计：已配置 / 0%
- 历史任务可保留，但 `has_history_tasks` **不得**提升 workflow 到第 6/7 步

### Stop vs Complete

| 事件 | current_task_id | Workflow 6/7 | Data View 新任务 |
|------|-----------------|--------------|------------------|
| **Stop** | None | 不进入 | 不注册 |
| **Complete** | 设置 task_id | 第 6 步可用 | 注册新任务 |
| **Export report** | 不变 | 第 7 步完成（仅对应 task） | 不变 |

### 历史任务与当前任务

- 查看 Data View 历史任务：可高亮第 6 步，但不改变 `scan_state` / progress
- Report Center 打开预览：**不**设置 `report_exported`
- 仅 **Export** 操作设置 `report_exported_for_task_id`
