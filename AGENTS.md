# AGENTS.md

## 项目

Near Field Scan System（nfs-scanner），Python 3.11 + PySide6 近场扫描桌面系统。

## 当前唯一基线

项目只允许一套正式界面：`nfs_scanner.ui.main_window.MainWindow` + `ScanControlPage`。商业版双界面已经移除，不得重新增加 `ui/commercial`、UI 模式环境变量或第二套启动入口。

唯一界面建立在已调试的原有接口上：

- `DeviceManager`
- `ScanManager`
- `QSerialPort` 运动控制链路
- 现有 ZNA67 / N9020A / FSW 适配与数据保存接口

重构界面时不得擅自改变设备命令、扫描顺序、数据格式、软限位和安全门禁。

## 分层

- `application/`：创建长生命周期管理器，不依赖 UI。
- `ui/main_window.py`：唯一窗口骨架。
- `ui/widgets/scan_control_page.py`：页面状态、扫描生命周期和稳定公开操作方法。
- `ui/widgets/scan_control_layout.py`：只构建布局和控件。
- `ui/widgets/scan_workers.py`：后台线程 Worker。
- `ui/widgets/instrument_operations.py`：仪表搜索、查询、设置和采集动作。
- `ui/widgets/scan_control_support.py`：串口发现、配置、存储和路径辅助。
- `core/`：领域状态、扫描和项目规则。
- `devices/`：设备适配及传输细节。
- `infra/`、`storage/`、`config/`：日志、持久化和配置。

## 开发规则

1. 只在唯一界面上增加功能，不创建平行页面或演示壳。
2. 保持 `ScanControlPage` 的构造参数和已有操作方法兼容。
3. UI 布局与设备行为分离；耗时操作必须使用现有 Worker/线程边界。
4. 使用类型注解和清晰 docstring，单文件尽量控制在 800 行以内。
5. 界面文案优先使用中文，使用统一 QSS 主题，不在控件中堆叠零散样式。
6. 默认不连接真实设备；测试不得绕过硬件安全开关。
7. 不引入数据库、授权、云服务或新的重量级依赖。
8. 保留用户已有改动，不修改无关生成产物。

## 验证

```powershell
python -m pytest -q
python -m ruff check nfs_scanner tests tools scripts run.py
python -m compileall -q nfs_scanner tools scripts
python tools\unified_ui_check.py
```

完成任务后说明修改文件、实现内容、验证结果和仍存在的限制。
