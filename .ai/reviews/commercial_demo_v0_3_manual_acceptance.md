# Commercial Demo v0.3 — 手动验收清单

按顺序操作，每步核对「预期 UI 变化」与「通过标准」。

## 1. 启动商业 UI

**操作**：PowerShell 执行 `$env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main`

**预期**：Frameless 顶栏、Mock/Dry Run 标识、workflow 第 1–2 步已完成或第 3 步激活（非伪造 65% 扫描）

**通过标准**：窗口正常显示，无崩溃

---

## 2. 新建项目

**操作**：顶部「新建」

**预期**：状态栏项目名更新；日志 `[PROJECT] 新建项目`；workflow 第 1 步完成

**通过标准**：状态栏含项目名 + 「未保存」

---

## 3. 保存项目

**操作**：顶部「保存」

**预期**：日志显示 JSON 路径；状态栏「已保存」

**通过标准**：`~/.nfs_scanner/demo_projects/demo_project.json` 存在

---

## 4. 连接设备

**操作**：顶部「连接」或设备中心连接全部

**预期**：左侧设备卡片「已连接」；workflow 第 2 步完成

**通过标准**：motion/spectrum/camera 均为 connected

---

## 5. 打开设备中心

**操作**：Workflow 点击「设备连接」或切换 Tab

**预期**：Device Center 显示设备卡片与 mock 标识

**通过标准**：可 connect/disconnect/refresh，无真实硬件访问

---

## 6. 修改扫描参数

**操作**：右侧修改 X/Y 步长或区域

**预期**：中央路径刷新；右侧/底部统计更新

**通过标准**：点数/路径长度变化；无效输入红框无弹窗

---

## 7. 开始扫描

**操作**：顶部或右侧「开始」

**预期**：runtime running；workflow 第 5 步高亮；进度从 0 增加

**通过标准**：状态栏「扫描执行中 · N%」

---

## 8. 暂停

**操作**：右侧「暂停」

**预期**：状态 paused；按钮变「继续」

**通过标准**：进度停止增加

---

## 9. 继续

**操作**：点击「继续」

**预期**：runtime running；进度继续增加

**通过标准**：百分比大于暂停前

---

## 10. 停止

**操作**：顶部或右侧「停止」

**预期**：状态 stopped；workflow 显示「已停止」

**通过标准**：不自动生成 Data View completed 任务（本轮决策）

---

## 11. 再次开始直到完成

**操作**：再次「开始」，等待进度 100%

**预期**：自动切 Data View；新任务出现；workflow 第 6 步可用

**通过标准**：Data View 任务列表 ≥1 条新记录

---

## 12. 查看 Data View

**操作**：切换 Data View Tab

**预期**：任务列表、热力图/频谱预览、summary cards

**通过标准**：可选 trace/frequency；空状态仅在没有任务时显示

---

## 13. 查看 Report Center

**操作**：切换 Report Center Tab

**预期**：报告预览含项目、任务 ID、安全声明 MOCK/DRY RUN

**通过标准**：预览字段非 `--`

---

## 14. 导出报告

**操作**：Report Center「导出 MD」

**预期**：路径显示在 UI 与日志；workflow 第 7 步完成

**通过标准**：`~/.nfs_scanner/reports/report_*.md` 存在

---

## 15. 导出 mock data

**操作**：Data View「导出数据」或顶部「导出」

**预期**：JSON 路径写入日志

**通过标准**：`~/.nfs_scanner/mock_exports/data/*.json` 存在

---

## 16. Reset Demo

**操作**：Overflow「Reset Demo」

**预期**：runtime 停止；默认项目/设备/参数恢复；日志清空后一条重置提示

**通过标准**：可再次从步骤 2 开始演示

---

## 17. 旧 UI 仍可启动

**操作**：不设环境变量，`python -m nfs_scanner.main`

**预期**：Legacy MainWindow 启动

**通过标准**：非 commercial shell
