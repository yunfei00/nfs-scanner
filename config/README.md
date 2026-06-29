# 设备配置说明

## 主配置文件（唯一推荐入口）

```text
config/devices.yaml
```

首次使用请复制示例文件：

```powershell
copy config\devices.example.yaml config\devices.yaml
```

## 读取优先级

1. `config/devices.yaml`（优先）
2. `config/devices.json`（兼容旧版，仅当 yaml 不存在时）
3. 内置 Mock 默认（两者都不存在时）

## 安全默认值

- `mode: mock`
- `motion.enabled: false`
- `instrument.enabled: false`
- `camera.safe_enumeration: true`

真实硬件需手动启用上述项，并在 UI 中切换 **Real Hardware** 且设置 `NFS_SCANNER_REAL_DEVICES=1`。
