# NFS Scanner

Near Field Scan System（近场扫描系统）是基于 Python 3.11 与 PySide6 的桌面工程工具，用于运动平台控制、扫描任务执行、频谱仪参数配置、数据采集和结果输出。

代码库现在只保留一套正式界面：以原有稳定设备和扫描接口为基础重构的统一工程控制台。不再支持商业版/旧版双界面切换，也不再读取 `NFS_SCANNER_UI`。

## 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m nfs_scanner
```

等价入口：

```powershell
python run.py
nfs-scanner
```

仅安装运行依赖时可使用：

```powershell
python -m pip install -r requirements.txt
```

## 唯一界面

统一界面保留已经调试的原始操作接口：

- 串口枚举、打开、关闭和自动重连；
- X/Y/Z 点动、绝对坐标、复位、位置与版本查询；
- 扫描起点、终点、步距、等待时间和执行控制；
- ZNA67、N9020A、FSW 搜索、参数查询/设置和数据保存；
- 结果路径、热力图入口、运行日志和坐标/时间/状态显示。

界面使用左右双滚动工作区，可在常见屏幕高度下访问全部控件。内部扫描字段保持不变，表头改为中文用户文案。

## 架构

```text
app.py
  └─ ApplicationContext
       ├─ DeviceManager（原有设备接口）
       └─ ScanManager（原有扫描接口）
            ↓
        MainWindow（唯一窗口）
            ↓
        ScanControlPage（稳定公开页面 API）
            ├─ scan_control_layout.py      布局构建
            ├─ scan_workers.py             后台扫描/搜索 Worker
            ├─ instrument_operations.py    仪表操作
            └─ scan_control_support.py     串口、配置、存储和路径辅助
```

主要目录：

```text
nfs_scanner/
  application/   # 应用上下文和依赖装配
  core/          # 扫描、项目、状态和业务模型
  devices/       # 运动、频谱仪、相机适配器
  ui/            # 唯一 PySide6 界面
  storage/       # 数据集持久化
  infra/         # 日志等基础设施
  config/        # 配置加载
tests/           # 自动化回归测试
tools/           # 结构验收工具
```

详细规则见 [架构总览](docs/architecture/00_overview.md) 和 [目录职责](docs/architecture/01_directory_structure.md)。

## 硬件安全

- 不修改已调试的串口、运动和频谱仪命令接口。
- 真实设备操作仍受现有配置、软限位和安全检查保护。
- 未连接设备时，界面只展示状态和诊断信息。
- 真实运动联调前必须阅读 [安全检查清单](docs/safety_checklist.md)。
- 自动化测试默认不连接或操作真实硬件。

本地设备配置可从示例创建：

```powershell
Copy-Item config\devices.example.yaml config\devices.local.yaml
```

## 验证

```powershell
python -m pytest -q
python -m ruff check nfs_scanner tests tools scripts run.py
python -m compileall -q nfs_scanner tools scripts
python tools\unified_ui_check.py
python tools\unified_ui_check.py --screenshot output\unified-ui.png
```

自动关闭启动检查：

```powershell
$env:NFS_SCANNER_AUTOCLOSE_MS="1000"
python -m nfs_scanner
```

## 文档

- [实施状态](docs/implementation_status.md)
- [架构设计](docs/architecture/README.md)
- [开发与测试](docs/development/README.md)
- [运动控制](docs/motion_controller.md)
- [频谱仪 SCPI](docs/instrument_scpi.md)
- [真实扫描流程](docs/real_scan_workflow.md)
- [数据格式](docs/data_formats/README.md)
