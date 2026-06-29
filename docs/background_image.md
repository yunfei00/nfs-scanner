# 扫描背景底图（Background Image）

本文档说明 NFS Scanner 商业版 UI 中「相机拍照图作为实时视图底图」功能（Background v0.2）。

## 背景底图用途

1. 使用 USB 相机拍摄被测物或扫描区域
2. 将照片设为 **实时视图** 的参考底图
3. 在底图上方叠加扫描矩形、路径点、热力图等 overlay

当前底图仅作为 **视觉参考**，不提供像素到毫米的精确映射。

## 使用流程

1. 启动商业版 UI：`$env:NFS_SCANNER_UI="commercial"; python -m nfs_scanner.main`
2. 打开 **相机 / 视觉** 标签页
3. 点击 **开始预览**（只有此时才会打开相机）
4. 点击 **拍照**，图片保存至 `outputs/camera/camera_YYYYMMDD_HHMMSS.jpg`
5. 点击 **设为扫描底图**
6. 切换到 **实时视图**，即可看到刚才拍摄的图片作为底层背景
7. 扫描矩形、路径、热力图等 overlay 显示在底图上方
8. 在实时视图工具栏点击 **清除底图** 可恢复默认 mock 演示样式

## 实时视图行为

- 底图通过 `PhotoLayer`（`QGraphicsPixmapItem`，z=0）显示
- 视图缩放使用 `KeepAspectRatio`（contain），完整显示、居中、不拉伸变形
- 无底图时保持原有 mock PCB 演示背景
- 底图透明度可在实时视图工具栏选择：100% / 70% / 50% / 30%

## 项目状态

运行时由 `BackgroundManager`（`nfs_scanner/core/background/`）管理：

| 字段 | 说明 |
|------|------|
| `background_image_path` | 底图文件路径 |
| `background_width` / `background_height` | 图像尺寸 |
| `background_opacity` | 透明度（0.0–1.0） |
| `background_fit_mode` | 默认 `contain` |
| `background_visible` | 是否可见 |

保存项目时，上述字段写入 `display_config`，便于后续完整持久化。重启软件后若未打开已保存项目，底图不会自动恢复（v0.2 不要求跨会话持久化）。

## 当前限制

- 暂不做相机标定
- 暂不做像素坐标到扫描坐标的精确映射
- 暂不做畸变校正、透视矫正
- 暂不支持从文件对话框加载任意图片（可后续扩展）
- 热力图 mock 仍按 scene 坐标绘制，可能与真实照片比例不完全一致

## 后续计划

- 两点 / 四点标定
- 像素坐标到扫描坐标映射
- 从项目目录加载 / 导出背景图
- 热力图与底图对齐导出

## 相关模块

| 模块 | 路径 |
|------|------|
| BackgroundManager | `nfs_scanner/core/background/manager.py` |
| RealtimeView | `nfs_scanner/ui/commercial/views/realtime_view.py` |
| VisionView | `nfs_scanner/ui/commercial/views/vision_view.py` |
| PhotoLayer | `nfs_scanner/ui/commercial/graphics/layers.py` |
