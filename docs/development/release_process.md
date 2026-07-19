# Windows 商业发布流程

## 发布输入

- Python 3.11。
- `requirements-windows.lock`：运行依赖精确版本。
- `requirements-dev.lock`：验证工具精确版本。
- `requirements-build.lock`：PyInstaller 构建依赖精确版本。
- `nfs_scanner/version.py`：应用版本唯一来源；PyInstaller 与安装器从它或 EXE 元数据取值。

## 本地发布前检查

```powershell
python -m pytest -q
python -m ruff check nfs_scanner tests tools scripts run.py
python -m compileall -q nfs_scanner tools scripts
python tools\unified_ui_check.py
```

必须使用无真实硬件的环境完成自动化检查。随后依据
[`hardware_acceptance_matrix.md`](../hardware_acceptance_matrix.md) 在隔离的现场环境执行硬件验收。

## 自动构建

`.github/workflows/release.yml` 执行以下步骤：

1. 安装三份锁定依赖并执行完整验证。
2. 通过 `NFSScanner.spec` 生成 Windows one-folder 程序。
3. 生成只包含运行依赖的 SPDX 2.3 SBOM。
4. 离屏启动打包后的 EXE，确认可正常启动并退出。
5. 使用 Inno Setup 生成按用户安装的 x64 安装包。
6. 生成 portable ZIP 和 SHA-256 校验文件。
7. 标签发布必须存在代码签名证书，否则构建失败。

## 签名配置

仓库不保存私钥。发布仓库需要配置：

- `WINDOWS_CERTIFICATE_BASE64`
- `WINDOWS_CERTIFICATE_PASSWORD`

标签构建会对 EXE 和安装器执行 SHA-256 Authenticode 签名与可信时间戳。手动工作流在没有证书时可用于内部未签名验证，但不能作为客户交付物。

## 客户交付检查

- 安装包、portable ZIP 与 `SHA256SUMS.txt` 一致。
- EXE 和安装器数字签名有效。
- 包内包含 `LICENSE`、`THIRD_PARTY_NOTICES.md`、用户手册、硬件验收矩阵和 SBOM。
- 在干净的目标 Windows 设备上完成安装、启动、卸载、日志与用户数据目录检查。
- 发布说明列出硬件/驱动兼容性、已知限制、升级与回滚方式。
