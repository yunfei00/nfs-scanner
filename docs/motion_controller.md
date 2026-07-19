# 运动控制器（Serial GRBL/G-code）

## 配置

程序化运动适配器配置见 `%APPDATA%\NFSScanner\devices.local.yaml` → `motion`（示例见 `config/devices.example.yaml`）：

- `port`：如 `COM3`
- `baudrate`：默认 `115200`
- `timeout_s` / `command_delay_ms` / `settle_delay_ms`
- `soft_limits`：x/y/z 软限位（mm）
- `commands`：G-code 模板（home/stop/status/move）

## 指令

| 操作 | 默认命令 |
|------|----------|
| Home | `$H` |
| Stop | `!` |
| Unlock | `$X` |
| Status | `?` |
| 绝对移动 | `G90 G0 X{x} Y{y} Z{z}` |

## 安全

- 所有串口写入经 `SerialTransport` 锁串行化。
- `move_absolute` 前校验 soft limits，超限不发命令。
- 真实命令需 `NFS_SCANNER_REAL_DEVICES=1`。

## 调试

```powershell
$env:NFS_SCANNER_REAL_DEVICES="1"
python scripts/real_device_check.py --motion-position
python scripts/real_device_check.py --motion-idn
```

Home 与 smoke test 需脚本内二次确认。
