# NFS Scanner

> Near Field Scan System（近场扫描系统）
>
> 一个面向射频测试与近场扫描场景的工业级自动化测试平台，集成运动控制、频谱采集、数据管理、热力图分析与自动化扫描能力。

## 项目背景

在 EMC、天线调试、射频性能分析等场景中，工程师通常需要：

- 控制扫描平台进行二维运动
- 调用频谱仪完成自动采样
- 管理大量测试数据
- 生成热力图进行问题定位

传统流程依赖人工操作，效率低且重复性差。

NFS Scanner 旨在构建统一的软件平台，实现扫描、采集、分析全流程自动化。

---

## Product Specification

商业版 UI、功能路线、Codex 连续开发任务已经整理到：

- `docs/product-spec/README.md`：产品规格总入口
- `docs/product-spec/06_codex_tasks.md`：Codex 任务清单
- `docs/product-spec/07_acceptance_checklist.md`：任务验收清单
- `.ai/codex.md`：Codex/AI Agent 开发规则
- `.ai/backlog/`：可逐项执行的任务队列
- `.ai/prompts/`：远程控制 Codex 时可复制的提示词
- `.ai/reviews/`：代码审查模板

推荐开发流程：

1. 先读取 `.ai/codex.md`。
2. 再读取 `docs/product-spec/README.md`。
3. 从 `.ai/backlog/` 选择第一个未完成任务。
4. 每次只实现一个任务。
5. 使用 `docs/product-spec/07_acceptance_checklist.md` 验收。

---

## 核心功能

### 自动扫描控制

- 二维扫描路径生成
- 自动运行与暂停恢复
- ETA预计完成时间计算
- 扫描状态管理

### 多设备统一接入

当前支持：

- Rohde & Schwarz FSW
- Keysight N9020A
- Rohde & Schwarz ZNA67
- Mock Simulator

统一采用 Adapter 架构屏蔽设备差异。

### 数据采集与存储

- 单点采集
- Trace采集
- CSV导出
- JSON结果存储

### 热力图分析

- 扫描结果可视化
- 热力图生成
- 多频点分析
- 后处理扩展

---

## 系统架构

```text
PySide6 UI
      │
      ▼
 ScanManager
      │
      ▼
 DeviceManager
      │
      ▼
 Spectrum Adapter Layer
      │
 ┌────┼────┬─────┐
 ▼    ▼    ▼     ▼
FSW N9020A ZNA67 MOCK
```

---

## 技术亮点

### 1. 统一频谱仪抽象层

采用 Adapter + Factory 模式实现多厂商设备统一接入。

新增设备时无需修改上层扫描逻辑。

### 2. 扫描生命周期统一管理

ScanManager 负责：

- 运行控制
- ETA计算
- 暂停恢复
- 采样调度

实现业务逻辑与界面解耦。

### 3. 工业级可扩展架构

支持后续扩展：

- VNA
- 示波器
- GNSS测试设备
- 自定义SCPI设备

### 4. 自动化测试平台化设计

不仅是单一工具，而是面向自动化测试平台演进的基础框架。

---

## 项目成果

- 完成统一频谱仪适配层
- 完成扫描任务管理框架
- 完成 FSW/N9020A/ZNA67 接入
- 完成自动化数据采集流程
- 支持热力图分析扩展

---

## 安装运行

```bash
pip install -r requirements.txt
python -m nfs_scanner.main
```

---

## Roadmap

### V0.1

- 扫描控制
- 数据采集
- 热力图展示

### V0.5

- 多设备管理
- 数据管理中心
- 项目管理功能

### V1.0

- 企业级测试平台
- 自动报告生成
- 插件化设备生态

### Future

- Qt/C++ 高性能版本
- AI辅助异常分析
- 云端测试管理平台

---

## 技术栈

- Python 3.11
- PySide6
- VISA / SCPI
- NumPy
- Matplotlib
- Qt Graphics View

---

## AI Development Workflow

本项目使用文档驱动的 AI 开发流程。开始任务前应优先阅读以下入口：

- `.ai/cursor_workflow.md`：Cursor 固定执行流程。
- `.ai/cursor_night_run.md`：长会话夜间执行指南。
- `docs/product-spec/`：产品规格与验收口径。
- `docs/architecture/`：系统架构与模块边界。
- `docs/design-system/`：商业版 UI 设计系统。
- `docs/ui-spec/`：商业版 UI 布局与视图规格。
- `docs/component-library/`：组件库目标与首批 Widget 范围。

每次 AI 任务应保持小步提交，遵守 `.ai/commit_rules.md`，并在 `.ai/review_gate.md` 定义的检查点暂停 review。

---

## License

For Research and Engineering Use.
