# Real Device Integration — 安全边界

> 规划文档。当前代码库默认 **REAL_DEVICE_ENABLED=false**，商业 UI 不发送真实硬件命令。

## 1. 默认安全态

| 开关 | 默认值 | 说明 |
|------|--------|------|
| `REAL_DEVICE_ENABLED` | `false` | 代码内集成安全标志 |
| `NFS_SCANNER_REAL_DEVICES` | 未设置 | 环境变量显式启用 |
| Commercial UI → ScanManager | 未引用 | 商业 shell 不调用 |
| Motion G-code 发送 | 禁止 | DryRun 仅写日志 |

## 2. 真实设备启用条件

必须**同时**满足：

1. 安全评审 checklist 签字（见 Sprint R01）
2. 操作员显式设置 `NFS_SCANNER_REAL_DEVICES=1`
3. 应用内二次确认（UI 对话框，非静默启用）
4. 限位/急停策略文档化并测试
5. 回滚方案验证（一键恢复 Mock 模式）

## 3. 运动命令策略

| 命令类型 | Mock Demo v0.5 | Real Sprint 要求 |
|----------|----------------|------------------|
| home | DryRun 日志 only | dry-run preview → 二次确认 → 限位检查 → 发送 |
| jog | 禁止 | 速度/距离上限 + 急停 |
| move / G-code | 禁止 | SafetyGate 逐条校验 |
| 连续扫描联动 | MockScanRuntime | 必须经 ScanManager + 安全 gate |

**原则**：所有真实运动命令必须先经过 `SafetyGate`，UI 按钮不得直接调用 `MotionConnectionAdapter` 发送方法。

## 4. 频谱仪 / 相机

| 操作 | 要求 |
|------|------|
| VISA 连接 | connection-only Sprint 先验证 identity |
| SCPI 查询 | 超时 + 错误隔离，不阻塞 UI |
| 相机采集 | 帧缓冲上限，不写生产 CSV |

## 5. UI 层规则

1. 商业 UI 工具栏/属性面板 **不得** 在 Mock 模式下显示“已连接真实设备”
2. Real 模式必须有醒目 banner（区别于 Mock banner）
3. Reset Demo 必须断开真实连接并恢复 Mock 默认态
4. 日志必须标记 `[REAL]` vs `[MOCK]` vs `[DRY RUN]`

## 6. SafetyGate 职责（规划）

```
UI Action
   │
   ▼
SafetyGate.check(context)  ──► reject + log（默认）
   │
   ▼ (explicit real mode + confirmed)
DryRunAdapter.preview(command)  ──► 日志 + UI 确认
   │
   ▼
RealAdapter.execute(command)  ──► 限位/超时/急停监控
```

## 7. 回滚条件

任一情况立即回滚到 Mock 模式：

- 未预期 motion 命令
- 安全 gate 绕过
- 真实设备导致 UI 无响应 > 5s
- CSV 格式被真实路径污染
- QA safety 检查 FAIL

## 8. 评审清单（合并前）

- [ ] 默认 `REAL_DEVICE_ENABLED=false` 单测仍 PASS
- [ ] 未设置 env 时零真实连接尝试
- [ ] Commercial QA safety 段 PASS
- [ ] 旧 UI 启动不受影响
- [ ] decision_log 记录启用范围与评审人
