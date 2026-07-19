# 设备配置说明

## 推荐配置位置

正式安装后的可写配置位于当前用户目录：

```text
%APPDATA%\NFSScanner\devices.local.yaml
```

从源码运行时可复制安全示例：

```powershell
New-Item -ItemType Directory -Force "$env:APPDATA\NFSScanner"
Copy-Item config\devices.example.yaml "$env:APPDATA\NFSScanner\devices.local.yaml"
```

## 读取优先级

1. 用户目录 `devices.local.yaml`。
2. 用户目录 `devices.yaml`。
3. 用户目录 `devices.json`。
4. 仓库相对 `config/` 下的同名旧配置（只为兼容开发环境）。
5. 安全的 Mock 默认值。

## 安全默认值

- `mode: mock`
- `motion.enabled: false`
- `instrument.enabled: false`
- `camera.safe_enumeration: true`

统一界面的运动串口仍由操作员在界面中显式选择和确认后打开。配置文件不能绕过界面确认、软件急停或软限位。
