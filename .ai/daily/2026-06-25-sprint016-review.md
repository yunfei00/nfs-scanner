# Sprint 016 — Commercial UI Visual Completion

Date: 2026-06-25

## Summary

- 工具栏统一：新建/打开/保存/连接设备/开始/暂停/停止/导出/报告中心，Mock 优先始终可用。
- 工作流程支持 pending / active / completed 三态高亮。
- 底部 dock：Mock 频谱曲线（QPainter）、紧凑统计、可清空分类日志。
- 状态栏扩展：System Ready、Mock Runtime、项目/存储/进度。
- QSS：workflow completed 态、Demo banner 样式。
- 1366×768 / 1920×1080 布局：demo banner + 中央画布优先。

## Tests

- `python -m compileall nfs_scanner` — OK
- `python -m unittest discover -s tests -v` — OK (135)

## Constraints

- 无真实设备控制；旧 UI 默认启动不受影响。
