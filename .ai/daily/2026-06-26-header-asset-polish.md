# 2026-06-26 — Commercial Header Asset Polish

## 目标

仅收敛顶部 **NFS 品牌 Logo** 与 **工具栏图标** 质感，不改主体布局、不接真实设备。

## Task 01 — NFSLogoWidget

- 新增 `nfs_scanner/ui/commercial/widgets/brand_logo.py`
- `NFSLogoWidget`（44×44）纯 `QPainter` 绘制：
  - 圆角蓝色渐变 `#0EA5FF → #0284C7 → #1D4ED8`
  - 深色边框 `#075985`、高光、内阴影
  - 六边形科技感轮廓
  - 中央白色 **NFS** 字样（非 QLabel）
- 动态属性：`brandLogoWidget=true`、`brandLogoBlue=true`、`brandBlueBlock=true`
- `CommercialBrandArea` 接入；宽度 238px；保留中文标题 / 英文副标题 / v1.0.0 badge

## Task 02 — ToolIconFactory

- 新增 `nfs_scanner/ui/commercial/widgets/tool_icons.py`
- `ToolIconFactory` + `draw_tool_icon()`：22px `QPixmap` + `QPainter` 线性仪器风图标
- 覆盖：新建、打开、保存、连接、开始、停止、拍照、区域、清除、导出、报告、参数、帮助、overflow
- 色调：默认灰蓝、主操作蓝/绿、停止红、disabled 低透明
- `NFSIconToolButton` 通过 action 名映射内部图标；`customToolIcon=true`

## Task 03 — Toolbar Visual Polish

- 按钮保持 60×50、图标 22px、文字 11px
- 连接蓝 / 开始绿 / 停止红；disabled 降透明度
- >=1500px 无 overflow；分隔线克制（<=4）

## Task 04 — QA

新增/保持检查：`brand_logo_widget_used`、`brand_logo_not_plain_label`、`toolbar_custom_icons_used`、`toolbar_no_qt_default_icon_mode`、`top_header_screenshot_exists`、`overflow_hidden_at_default_width` 等。

修复：QA 查找 logo 时使用 `NFSLogoWidget` 而非 `QFrame`（此前误判为缺失）。

## Task 05 — 与目标图仍存在的差异

- 非设计师交付的最终品牌 SVG/PNG
- 图标为程序绘制占位，非最终矢量资产库
- 但已统一风格，明显优于 Qt 标准图标拼凑

## 测试

```powershell
python -m compileall nfs_scanner
python -m unittest discover -s tests -v
python tools/commercial_ui_visual_check.py
python tools/qa_run_commercial_demo.py
```

结果：148 tests OK；visual + QA **PASS**。
