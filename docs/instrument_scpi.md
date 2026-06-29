# 仪表 SCPI / VISA

## 支持类型

| 类型 | Adapter |
|------|---------|
| Mock | `MockSpectrumAnalyzer` |
| FSW | `fsw_adapter.py` |
| N9020A | `n9020a_adapter.py` |
| ZNA67 | `zna67_adapter.py` |
| Generic SCPI | `scpi_adapter.py` |

## 配置

`config/devices.yaml` → `instrument`：

```json
{
  "type": "fsw",
  "enabled": false,
  "transport": "visa",
  "resource": "TCPIP0::192.168.1.100::inst0::INSTR",
  "timeout_s": 10
}
```

## 单次扫描流程（FSW）

1. `*IDN?`
2. `*CLS` / preset
3. `INIT:CONT OFF`
4. 配置频率、RBW/VBW、点数
5. `INIT:IMM` → `*OPC?` → `TRAC:DATA? TRACE1`

## ASCII Trace 解析

使用 `devices/spectrum/utils.parse_ascii_float_values()`，支持逗号/分号/换行及 SCPI block header。

## 排查

- 连接超时：增大 `timeout_s`，检查 IP/VISA 资源字符串。
- 空 trace：确认 `INIT:CONT OFF` 与单次 trigger。
- 权限：需 `NFS_SCANNER_REAL_DEVICES=1`。
