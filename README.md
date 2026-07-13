# NFS Scanner

## 启动与本地设备配置（第一阶段）

默认启动商业版 UI：

```powershell
python -m nfs_scanner
```

如需调试保留的旧版 UI，请显式设置兼容环境变量：

```powershell
$env:NFS_SCANNER_UI="legacy"; python -m nfs_scanner
```

本地设备配置不提交到 Git。首次配置时执行：

```powershell
copy config\devices.example.yaml config\devices.local.yaml
```

配置读取优先级为：显式传入路径、`config/devices.local.yaml`、兼容的
`config/devices.yaml`、内置 Mock 默认配置。默认模式始终为 Mock；真实硬件仍需
满足现有的环境变量和 UI 确认安全门禁。

> Near Field Scan System（近场扫描系统）
>
> 面向射频测试、近场扫描、EMC 调试与自动化测试场景的工业级扫描平台。当前仓库同时保留旧版 UI 和商业版 Demo UI。

---

## 先看这里：如何启动商业版 UI

**商业版 UI 不是默认入口。** 直接运行 `python -m nfs_scanner.main` 会启动旧版 UI。

商业版 Demo UI 必须显式设置：

```text
NFS_SCANNER_UI=commercial
```

### Windows PowerShell（推荐）

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main
```

### Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
set NFS_SCANNER_UI=commercial && python -m nfs_scanner.main
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
NFS_SCANNER_UI=commercial python -m nfs_scanner.main
```

商业版 UI 启动后，顶部应显示类似安全标识：

```text
Mock / Dry Run / No Hardware Control / Real Device Disabled
```

这表示当前处于安全演示模式，不会控制真实硬件。

---

## Real Hardware Mode（真实设备，可选）

商业版 UI 已支持 **Mock Dry Run** 与 **Real Hardware** 双模式并存：

- **默认**：Mock Dry Run（与之前 Demo 行为一致）
- **Real**：需在设备中心切换模式并确认，且设置 `NFS_SCANNER_REAL_DEVICES=1`

### 配置

编辑 `config/devices.yaml`（从 `config/devices.example.yaml` 复制）：

- `mode`: `mock`（默认）| `real`
- `motion.enabled` / `instrument.enabled`: 默认 `false`

读取优先级：`config/devices.yaml` → `config/devices.json`（兼容）→ 内置 Mock 默认。

### 启动（仍为 Mock）

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

### 启用真实设备

```powershell
$env:NFS_SCANNER_REAL_DEVICES="1"
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

在 **设备中心** 切换 **Real Hardware** → 连接 → Test IDN / 查询位置 → 配置小范围扫描 → 开始（有最终确认）。

扫描数据输出：`outputs/scans/<project_id>/<timestamp>/`

详细说明：

- [docs/real_hardware_mode.md](docs/real_hardware_mode.md)
- [docs/real_device_integration_audit.md](docs/real_device_integration_audit.md)
- [docs/real_scan_workflow.md](docs/real_scan_workflow.md)

手工检查脚本：

```powershell
python scripts/real_device_check.py --instrument-idn
python scripts/real_device_check.py --motion-position
```

---

## Camera / Vision（商业版可选功能）

商业版 UI 提供 **相机 / 视觉** 工作区，用于 USB UVC 相机预览与拍照。这是 **可选功能**：

- 启动时 **不会** 自动连接相机
- **不会** 影响 Mock Demo、Dry Run、Mock 扫描闭环
- 仅在用户手动点击「开始预览」后才打开设备

### 启动方式

```powershell
pip install -r requirements.txt
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

启动后切换到 **相机 / 视觉** 标签页。

### 默认相机参数

| 参数 | 默认值 |
|------|--------|
| 设备名 | `LRCP  F1080P`（双空格） |
| 编码 | MJPEG |
| 分辨率 | 1920x1080 |
| 帧率 | 30 fps |

拍照保存目录：`outputs/camera/camera_YYYYMMDD_HHMMSS.jpg`

详细说明见 [docs/camera.md](docs/camera.md) 与 [docs/camera_ffmpeg_check.md](docs/camera_ffmpeg_check.md)。

### 相机测试

```bash
python -m unittest tests.test_camera_opencv -v
```

真实 USB 联调（Windows）：

```powershell
$env:NFS_SCANNER_CAMERA_TEST="1"
python -m unittest tests.test_camera_opencv.CameraHardwareTestCase -v
```

### Camera background / Scan background（v0.2）

相机拍照后可设为 **实时视图** 的扫描底图：

1. **相机 / 视觉** → 开始预览 → 拍照
2. 点击 **设为扫描底图**
3. 切换到 **实时视图** 查看底图与 overlay 叠加
4. 工具栏 **清除底图** 恢复 mock 演示样式

详见 [docs/background_image.md](docs/background_image.md)。

### 商业版操作流程（Mock Dry Run）

1. **新建项目** → 配置扫描参数 → **应用参数**
2. **连接** Mock 设备
3. **开始** Dry Run 扫描 → **停止**
4. **导出** CSV / PNG / JSON（`outputs/exports/`）
5. **报告** 生成 HTML（`outputs/reports/`）
6. 可选：相机拍照 → **设为扫描底图** → 实时视图查看

文档：[docs/ui_actions.md](docs/ui_actions.md) · [docs/mock_dry_run.md](docs/mock_dry_run.md) · [docs/ui_action_audit.md](docs/ui_action_audit.md)

---

## 默认旧版 UI

旧版 UI 仍然保留，并且仍是默认入口：

```bash
python -m nfs_scanner.main
```

如果你看到的是旧界面，不是商业版界面，通常是因为没有设置：

```text
NFS_SCANNER_UI=commercial
```

---

## 当前状态

**Commercial V1 项目生命周期完成**（正式商用流程 + Simulation Provider）。

- 文档：`.ai/reviews/commercial_v1_functional_completion.md`
- 项目生命周期：`.ai/reviews/commercial_v1_project_lifecycle.md`
- 项目生命周期验收：`.ai/reviews/commercial_v1_project_lifecycle_acceptance.md`
- Action 清单：`.ai/reviews/commercial_v1_action_inventory.md`
- 手动验收：`.ai/reviews/commercial_v1_manual_acceptance.md`
- v0.5 冻结 tag：`commercial-demo-v0.5`（历史基线）

底层仍为 Simulation / Dry Run，**未接入真实运动平台、频谱仪、相机**。

```text
全部工具栏/Tab/属性页/导出/自检 → Mock 行为完整 → QA PASS → 已冻结
```

项目生命周期已正式落盘：

- 默认项目根目录：`~/.nfs_scanner/projects/`
- 项目文件：`<ProjectName>/project.nfsproj`
- 最近项目：`~/.nfs_scanner/recent_projects.json`
- 支持新建、打开、保存、另存为、recent、dirty 状态与多处 UI 项目上下文显示。

v0.4 功能验收（Reset 状态一致、Stop 不生成 task）仍然有效。

下一阶段为 **Real Device Integration Planning**（仅文档，未启用真实设备）：  
`docs/real-device-integration/README.md`

**Mock Demo 安全声明：**

- 商业版当前默认是 `Mock / Dry Run / No Hardware Control`。
- 默认不控制真实运动平台。
- 默认不连接真实频谱仪。
- 默认不连接真实相机。
- 默认不调用真实 `ScanManager`。
- 默认不修改真实 CSV / 历史数据格式。
- 旧 UI 仍然保留，并且仍是默认入口。

---

## 商业版 Demo 验收流程

启动商业版 UI 后，可以按下面流程验收：

1. 新建项目 / 打开项目 / 保存项目。
2. 进入设备中心，执行 Mock 设备连接。
3. 回到实时视图，修改扫描区域、步长、扫描模式等参数。
4. 查看中央画布中的路径预览、热力图、ROI、色标和 MiniMap。
5. 点击开始扫描，观察路径进度、状态栏和运行日志。
6. 测试暂停、继续、停止。
7. 扫描完成后进入 Data View，查看 Mock 任务结果。
8. 进入 Report Center，预览并导出 Mock Markdown 报告。
9. 使用 Reset Demo 恢复初始演示状态。

---

## AI QA / 自检命令

商业版 UI 已经配置了自动 QA 闭环，可以用下面命令让 AI/脚本自动检查启动、截图、布局、功能流和安全边界。

```bash
python -m compileall nfs_scanner
python -m unittest discover -s tests -v
python tools/commercial_ui_visual_check.py
python tools/qa_run_commercial_demo.py
```

QA 结果输出位置：

```text
.ai/qa/latest/qa_report.md
.ai/qa/latest/qa_result.json
.ai/qa/latest/screenshots/commercial_default.png
.ai/qa/latest/screenshots/commercial_maximized.png
```

截图文件通常作为本地 QA 产物使用，是否提交以 `.gitignore` 当前规则为准。

---

## 自动关闭启动检查

如果只是验证启动，不想手动关闭窗口，可以使用：

### Windows PowerShell

```powershell
$env:NFS_SCANNER_AUTOCLOSE_MS="1500"; $env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main
```

### Windows CMD

```cmd
set NFS_SCANNER_AUTOCLOSE_MS=1500 && set NFS_SCANNER_UI=commercial && python -m nfs_scanner.main
```

### macOS / Linux

```bash
NFS_SCANNER_AUTOCLOSE_MS=1500 NFS_SCANNER_UI=commercial python -m nfs_scanner.main
```

---

## 常见启动问题

### 1. 启动后还是旧 UI

原因：没有设置商业版环境变量。

解决：

```powershell
$env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main
```

### 2. PowerShell 提示无法运行脚本

如果激活虚拟环境时报执行策略问题，可以临时使用：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. 缺少 PySide6 / numpy 等依赖

确认已经在虚拟环境中执行：

```bash
pip install -r requirements.txt
```

### 4. 只想快速验证商业 UI 能否启动

```powershell
$env:NFS_SCANNER_AUTOCLOSE_MS="1500"; $env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main
```

---

## 真实设备安全说明

默认情况下，真实设备控制是关闭的。

不要在无人值守或未完成安全 review 前设置：

```bash
NFS_SCANNER_REAL_DEVICES=1
```

真实运动控制、真实频谱仪采集、真实相机采集、完整真实扫描都需要单独 Major Review 批准后再进入对应 Sprint。

---

## 项目背景

在 EMC、天线调试、射频性能分析等场景中，工程师通常需要：

- 控制扫描平台进行二维/三维运动；
- 调用频谱仪完成自动采样；
- 管理大量测试数据；
- 生成热力图进行问题定位；
- 输出可交付的分析报告。

传统流程依赖人工操作，效率低且重复性差。NFS Scanner 旨在构建统一的软件平台，实现扫描、采集、分析和报告的全流程自动化。

---

## 核心功能

### 商业版 Demo UI

- 自定义深色商业界面；
- 扫描流程侧栏；
- 设备中心；
- 实时画布、Mock PCB、热力图、ROI、路径预览；
- 右侧扫描参数与统计；
- 底部频谱、扫描统计和日志；
- Mock 扫描运行；
- Data View Mock 分析；
- Report Center Mock 报告导出；
- AI QA 自动截图与自检。

### 自动扫描控制

- 扫描区域配置；
- Raster / Snake 路径预览；
- 点数、面积、路径长度、预计时间计算；
- Mock 扫描生命周期：start / pause / resume / stop / complete。

### 多设备统一接入

当前代码保留或规划的设备方向：

- Rohde & Schwarz FSW；
- Keysight N9020A；
- Rohde & Schwarz ZNA67；
- Motion Platform；
- Camera；
- **Camera / Vision（USB 预览，商业版可选）**；
- Mock / Dry Run Simulator。

当前商业版默认使用 Mock / Dry Run，不访问真实硬件。

### 数据与报告

- Mock 任务注册；
- Data View Mock 任务列表；
- Mock 频谱与热力图；
- Report Center Markdown 导出。

---

## 系统架构

当前目标架构强调 UI 与真实设备解耦：

```text
Commercial UI
      │
      ▼
CommercialServiceBundle
      │
      ├── ScanRuntimeServiceProtocol
      │       └── MockScanRuntimeService / Future RealScanRuntimeService
      │
      ├── DeviceServiceProtocol
      │       └── MockDeviceService / Future RealDeviceService
      │
      ├── ProjectService（project.nfsproj）
      ├── SimulationDeviceProvider → MockDeviceService
      ├── ScanRuntimeController → MockScanRuntimeService
      ├── MockAnalysisService
      └── MockReportService
```

真实设备路径必须经过安全开关和 Major Review，不允许 UI 直接操作硬件。

---

## 技术栈

- Python 3.11+
- PySide6
- Qt Graphics View
- NumPy
- VISA / SCPI（真实设备方向）
- unittest

---

## Product Specification

商业版 UI、功能路线、Codex / Cursor 连续开发任务已经整理到：

- `docs/product-spec/README.md`：产品规格总入口；
- `docs/master-roadmap/`：V1.0 总路线、里程碑、依赖关系；
- `docs/design-system/`：商业版 UI 设计系统；
- `docs/ui-spec/`：商业版 UI 布局与视图规格；
- `docs/component-library/`：商业组件库；
- `docs/development/project_coding_standard.md`：项目编码与分层标准；
- `.ai/constitution.md`：AI 自动开发最高规则；
- `.ai/assumptions.md`：默认实现假设；
- `.ai/night_mode.md`：夜间无人值守规则；
- `.ai/cursor_workflow.md`：Cursor 固定执行流程；
- `.ai/review_gate.md`：Review Gate / Major Review 规则；
- `.ai/qa/`：商业版 Demo QA 报告与截图输出。

推荐 AI 开发流程：

```text
Product Spec → Architecture → Design System → Sprint Backlog → Cursor/Codex → QA Pipeline → Review Gate
```
