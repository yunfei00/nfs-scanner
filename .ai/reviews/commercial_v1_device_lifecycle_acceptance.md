# Commercial V1 Device Lifecycle Acceptance

## 验收日期

2026-06-28

## 通过项

1. 连接设备（Simulation connect_all，三类核心设备 connected）
2. 断开设备（单设备 / 全部，Workflow 第 2 步同步）
3. 刷新设备（last_updated / last_message 更新）
4. 设备配置（Device Center + 仪表设置 Tab）
5. 测试连接（Simulation test OK）
6. Device Center 完整卡片与 Dry Run Log
7. 左侧 DeviceStatusPanel 与 Device Center 状态一致
8. device_config 写入 / 恢复 project.nfsproj
9. device actions 均有 handler
10. QA device lifecycle checks PASS
11. compileall / unittest / visual check / qa_run_commercial_demo

## 未进入

- 真实运动平台 / 频谱仪 / 相机
- NFS_SCANNER_REAL_DEVICES=1
- 真实 ScanManager 扫描

## QA 报告

`.ai/qa/latest/qa_report.md`
