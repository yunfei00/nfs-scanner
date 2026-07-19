# Mock / Dry Run

统一界面保留“模拟频谱仪（仅运动平台真实运行）”选项，用于在不连接真实频谱仪时验证运动扫描链路。

完整自动化测试还使用 `MockSpectrumAnalyzer`、模拟设备 provider 和 fake transport，以覆盖扫描、存储和安全门禁。Mock 测试不得发送串口运动或 VISA 命令。

```powershell
python -m pytest -q tests\test_dry_run.py tests\test_scan_manager_spectrum_integration.py
```

真实运动仍要求串口已经显式打开，并受平台软限位保护。
