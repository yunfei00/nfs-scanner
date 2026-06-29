# 真实扫描工作流

## 1. 连接设备

1. 复制 `config/devices.example.yaml` 为 `config/devices.yaml`，启用 motion/instrument。
2. 设置 `NFS_SCANNER_REAL_DEVICES=1`。
3. 启动商业版 UI，设备中心切换 **Real Hardware** 并确认。
4. 点击连接（顶部或设备中心）→ 确认对话框。

## 2. 配置扫描

- 右侧参数页设置 X/Y 区域、步长、Z 高度。
- 仪表频率/RBW 可在设备中心 Apply Settings 或 config 中预设。

## 3. 启动扫描

- 顶部「开始」→ 最终确认（区域、点数、设备 ID）→ Real Scan Worker 后台执行。

## 4. 数据保存

输出目录：

```text
outputs/scans/<project_id>/<timestamp>/
  scan_points.csv
  traces.npz
  metadata.json
  run.log
```

## 5. 停止与恢复

- 用户停止：已采集点写入 CSV/NPZ，日志 `[SCAN] Real scan stopped by user`。
- 异常（串口断开、超时、超限）：中断并保存已有数据。
- 恢复：修复设备后重新连接，可缩小区域做 smoke test（`scripts/real_scan_smoke_test.py`）。
