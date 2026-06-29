# Real Hardware 模式说明

## 与 Mock Dry Run 的区别

| | Mock Dry Run | Real Hardware |
|---|--------------|---------------|
| 运动 | 内存模拟 | 串口 GRBL/G-code |
| 频谱仪 | 合成 trace | VISA/SCPI 真实采集 |
| 默认 | **是** | 否，需 UI 确认 |
| 环境变量 | 无要求 | `NFS_SCANNER_REAL_DEVICES=1` |

## 启用方式

1. **UI**：设备中心 →「设备运行模式」→ Real Hardware → 确认对话框。
2. **配置**：复制 `config/devices.example.yaml` 为 `config/devices.yaml`，再设置 `motion.enabled` / `instrument.enabled` 为 `true`。
3. **环境变量**（可选）：
   - `NFS_SCANNER_DEVICE_MODE=real`（仅预选，仍需 UI 确认）
   - `NFS_SCANNER_REAL_DEVICES=1`（允许真实连接与运动）

## 安全注意事项

- 上电前确认急停可用、扫描区域无人无物。
- 首次使用先执行 Test IDN、查询位置、Single Sweep Test。
- Test Move 仅 +1mm X，且需确认。
- Home / 真实扫描开始前均有二次确认。

## Stop / Emergency Stop

- **停止扫描**：工具栏停止 → 设置 stop flag → motion.stop + instrument abort → 保存已采集数据。
- **Emergency Stop**：设备中心 Emergency Stop → `motion.emergency_stop()` + abort。

## 常见问题

**Q: 切换 Real 后连接失败？**  
A: 检查 `NFS_SCANNER_REAL_DEVICES=1`、`enabled=true`、串口/VISA 资源是否正确。

**Q: Mock Demo 是否受影响？**  
A: 默认仍为 Mock；不切换模式则行为与之前一致。
