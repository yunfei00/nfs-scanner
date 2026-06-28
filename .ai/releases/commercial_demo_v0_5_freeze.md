# Commercial Demo v0.5 — Release Freeze

- **版本名称**: Commercial Demo v0.5 Mock Feature Complete
- **冻结日期**: 2026-06-28
- **Git HEAD**: `56d466b`（冻结验证时 main 最新）
- **Git Tag**: `commercial-demo-v0.5`（见 Step 06）

---

## 1. 启动方式

### 旧 UI（默认入口）

```bash
python -m nfs_scanner.main
```

### 商业 UI（Mock Demo）

**PowerShell:**

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

**macOS / Linux:**

```bash
NFS_SCANNER_UI=commercial python -m nfs_scanner.main
```

启动后应看到 Mock / Dry Run / No Hardware Control 安全标识。

---

## 2. 已完成能力

| 能力 | 状态 |
|------|------|
| 商业 UI Shell（Frameless + 自定义顶栏） | ✅ |
| Header / Logo / Toolbar | ✅ 冻结，不再微调 |
| Project Mock Session（新建/打开/保存 JSON） | ✅ |
| Device Center Mock | ✅ |
| Scan Config / Path Preview | ✅ |
| Mock Scan Runtime（开始/暂停/继续/停止/完成） | ✅ |
| Realtime View（图层/工具/热力图/路径） | ✅ |
| 3D Mock View（QPainter 伪 3D） | ✅ |
| Data Table（过滤/排序/导出） | ✅ |
| Data View（任务/统计/导出/历史管理） | ✅ |
| Report Center（三模板/多格式导出） | ✅ |
| Mock Artifact Export（统一 ~/.nfs_scanner/） | ✅ |
| Self Check / Help Dialog | ✅ |
| Reset Demo（状态契约一致） | ✅ |
| QA Pipeline（functional + acceptance + mock_features） | ✅ |

功能入口清单 missing = **0**（见 `.ai/reviews/commercial_demo_v0_5_feature_inventory.md`）

---

## 3. QA 结果（冻结验证 2026-06-28）

| 门禁 | 结果 |
|------|------|
| `python -m compileall nfs_scanner` | **PASS** |
| `python -m unittest discover -s tests -v` | **PASS**（155 tests） |
| `python tools/commercial_ui_visual_check.py` | **PASS** |
| `python tools/qa_run_commercial_demo.py` | **PASS** |

**QA Report**: `.ai/qa/latest/qa_report.md`

关键 QA 项（全部 PASS）：

- `functional_mock_features`
- `all_visible_actions_have_feedback`
- `all_tabs_non_empty`
- `all_exports_created`
- `safety_no_real_hardware`
- `reset_state_consistent`

---

## 4. 产物路径

| 产物 | 路径 |
|------|------|
| QA report | `.ai/qa/latest/qa_report.md` |
| QA JSON | `.ai/qa/latest/qa_result.json` |
| 截图目录 | `.ai/qa/latest/screenshots/` |
| Visual report | `.ai/visual_check/commercial_ui_visual_report.md` |
| Mock report（示例） | `~/.nfs_scanner/reports/report_*.md` |
| Mock data JSON | `~/.nfs_scanner/mock_exports/data/mock_data_*.json` |
| Mock table CSV | `~/.nfs_scanner/mock_exports/tables/mock_table_*.csv` |
| Camera snapshot | `~/.nfs_scanner/screenshots/camera_snapshot_*.png` |
| Self-check JSON | `.ai/qa/latest/commercial_mock_self_check.json` |
| Self-check MD | `.ai/qa/latest/commercial_mock_self_check.md` |

---

## 5. 安全边界（冻结时确认）

| 项 | 状态 |
|----|------|
| `REAL_DEVICE_ENABLED` | **false**（默认） |
| `NFS_SCANNER_REAL_DEVICES=1` | **未启用** |
| 真实 ScanManager 调用 | **未接入商业 UI** |
| Motion / G-code 命令 | **未发送** |
| 真实频谱仪连接 | **未连接** |
| 真实相机连接 | **未连接** |
| 历史真实 CSV 格式 | **未修改** |
| 旧 UI 默认入口 | **保留** |

---

## 6. 未实现内容（非 v0.5 范围）

- 真实运动平台控制（home / jog / move / G-code）
- 真实频谱仪 / VNA 采集
- 真实相机帧采集
- 真实 ScanManager 与商业 UI 集成
- 历史 CSV 读写与生产数据格式
- 安装包 / 发布流水线
- License 加密
- 设计师最终 SVG / 图标资源库

---

## 7. 冻结结论

**Commercial Demo v0.5 正式冻结**，作为 Mock 演示阶段成果。

- 不再新增 Mock 功能
- 不再微调 Header
- 下一阶段：**Real Device Integration Planning**（仅规划，见 `docs/real-device-integration/`）
- 真实设备控制必须单独 Sprint + 安全评审，禁止从本冻结版本直接扩展

---

## 8. 相关文档

| 文档 | 路径 |
|------|------|
| v0.5 功能清单 | `.ai/reviews/commercial_demo_v0_5_feature_inventory.md` |
| v0.5 验收报告 | `.ai/reviews/commercial_demo_v0_5_full_mock_feature_acceptance.md` |
| v0.4 状态契约 | `.ai/reviews/commercial_demo_v0_4_state_contract.md` |
| 真实设备规划 | `docs/real-device-integration/README.md` |
