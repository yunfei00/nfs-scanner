# NFS Scanner

> Near Field Scan System（近场扫描系统）
>
> 面向射频测试、近场扫描、EMC 调试与自动化测试场景的工业级扫描平台。当前仓库同时保留旧版 UI 和商业版 Demo UI。

---

## 当前状态

当前主线已经具备 **商业版 Mock Demo 闭环 v0.1**：

```text
项目流 → Mock 设备 → 扫描参数 → 路径预览 → Mock 扫描 → Data View → Report 导出
```

安全边界：

- 商业版当前默认是 `Mock / Dry Run / No Hardware Control`。
- 默认不控制真实运动平台。
- 默认不连接真实频谱仪。
- 默认不连接真实相机。
- 默认不调用真实 `ScanManager`。
- 默认不修改真实 CSV / 历史数据格式。
- 旧 UI 仍然保留，并且仍是默认入口。

---

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动旧版 UI（默认入口）

```bash
python -m nfs_scanner.main
```

### 3. 启动商业版 Demo UI（推荐验收入口）

#### Windows PowerShell

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

#### Windows CMD

```cmd
set NFS_SCANNER_UI=commercial
python -m nfs_scanner.main
```

#### macOS / Linux

```bash
NFS_SCANNER_UI=commercial python -m nfs_scanner.main
```

商业版 UI 启动后，顶部应显示类似：

```text
Mock / Dry Run / No Hardware Control / Real Device Disabled
```

这表示当前处于安全演示模式，不会控制真实硬件。

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
$env:NFS_SCANNER_AUTOCLOSE_MS="1500"
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

### macOS / Linux

```bash
NFS_SCANNER_AUTOCLOSE_MS=1500 NFS_SCANNER_UI=commercial python -m nfs_scanner.main
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
      ├── MockProjectService
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

1. 先读取 `.ai/constitution.md`。
2. 再读取 `.ai/cursor_workflow.md` 和 `.ai/project_status.md`。
3. 按当前 Sprint / Review Gate 执行。
4. 每个 task 小步提交。
5. 跑完整 QA：`python tools/qa_run_commercial_demo.py`。
6. 涉及真实设备、CSV、旧 UI 删除、真实扫描前必须停在 Major Review。

---

## Roadmap

### 当前

- 商业版 Mock Demo 闭环 v0.1；
- AI QA 自检闭环；
- 真实设备仍处于安全阻塞状态。

### 下一步候选

- 商业 UI 目标页面继续微调；
- 真实运动平台只读/连接层 review；
- 工具栏 overflow；
- Data View 图表增强；
- Report Center PDF 导出（需依赖评审）。

### Future

- Qt/C++ 高性能版本；
- 插件化设备生态；
- AI 辅助异常分析；
- 云端测试管理平台。

---

## License

For Research and Engineering Use.
