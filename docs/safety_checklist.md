# 真实硬件安全核对清单

## 启动安全

- [ ] 默认 `config/devices.yaml` 中 `mode: mock`
- [ ] `motion.enabled: false` 且 `instrument.enabled: false`
- [ ] 启动商业版 UI **不会**自动连接运动平台或仪表
- [ ] 未设置 `NFS_SCANNER_REAL_DEVICES=1` 时，真实 I/O 被门控拦截

## 连接安全

- [ ] 设备中心进入 **不会**自动连接真实设备
- [ ] Mock 模式点击「连接」仅连接 Mock 设备服务
- [ ] Real 模式需 UI 安全确认 + 环境变量
- [ ] 缺少 `port` / `resource` 时显示 `[ERROR] Motion config missing: port` 等明确错误
- [ ] 连接失败时不显示误导性 Connected

## 运动安全

- [ ] 所有运动命令经 `SerialTransport` 锁串行执行
- [ ] `move_absolute` 前检查 soft limits，超限不发命令
- [ ] Home / Test Move / 真实扫描前需用户确认
- [ ] 脚本 `--motion-home` / `--motion-test-move` 必须输入 `YES`

## 扫描安全

- [ ] Real Scan 需：Real 模式 + 设备已连接 + 参数合法 + 最终确认
- [ ] 扫描在 QThread worker 中执行，不阻塞 UI
- [ ] 同时只允许一个 Real Scan 任务

## 停止 / 急停

- [ ] 工具栏 Stop → 设置 stop flag + motion.stop + instrument abort
- [ ] Emergency Stop → `motion.emergency_stop()` + abort
- [ ] UI 关闭时若 Real Scan 运行中，弹窗并请求停止

## 相机隐私

- [ ] `camera.safe_enumeration: true`（默认）
- [ ] 进入「相机 / 视觉」不自动打开摄像头
- [ ] 「刷新设备」不调用 `cv2.VideoCapture` 探测
- [ ] 仅用户点击「开始预览」才打开设备

## 配置风险

| 风险 | 缓解 |
|------|------|
| 误留 `enabled: true` | 示例文件默认 false；文档强调复制 example |
| 双配置文件不一致 | 优先 `config/devices.yaml`，json 仅 fallback |
| 环境变量误设 Real | UI 仍需 Real Hardware 确认 |

## 常见误操作

1. **只改 yaml 未设 REAL_DEVICES** → 连接失败（预期行为）
2. **Real 模式但未填 VISA 资源** → `[ERROR] Instrument config missing: resource`
3. **扫描区域 Y 超出 soft limits** → 扫描中断并记录 error 点
4. **关闭窗口时扫描仍在跑** → 弹窗确认后 stop

## 相关文档

- [real_hardware_mode.md](real_hardware_mode.md)
- [manual_acceptance_real_hardware.md](manual_acceptance_real_hardware.md)
- [config/README.md](../config/README.md)
