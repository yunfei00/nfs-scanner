# 2026-06-26 — Commercial Demo v0.3 Functional Hardening

## 目标

功能稳定化与自检强化，不新增大功能，不微调 Header。

## v0.3 修复摘要

1. **状态一致性**：`demo_state_sync.py` 统一 workflow + status bar
2. **去除伪造进度**：启动不再 fake 65% workflow/状态栏
3. **日志节流**：Dry Run 每 10 点 flush；log 去重 + 400 行上限
4. **扫描前置检查**：项目 + mock 设备连接
5. **Data/Report 验收深化**：空状态、字段补全、安全声明
6. **QA 增强**：progress>5%、stop、二次 complete、reset_demo 截图

## QA 覆盖流程

新建 → 打开 → 保存 → 连接设备 → 改参数 → 开始 → 暂停 → 继续 → 停止 → 再开始完成 → Data View → Report → 导出 → Reset → 安全检查

## 手动验收

`.ai/reviews/commercial_demo_v0_3_manual_acceptance.md`

## 示例导出路径

- Mock 报告：`~/.nfs_scanner/reports/report_*.md`
- Mock 数据：`~/.nfs_scanner/mock_exports/data/mock_data_*.json`

## 安全边界

仍未进入真实设备控制；`REAL_DEVICE_ENABLED=false`

## 测试

compileall + unittest + visual + QA **PASS**

## 下一步

用户按 manual acceptance 做一次验收；真实设备 Sprint 需单独评审
