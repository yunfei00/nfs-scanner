# Component Library

本目录定义 NFS/FlyCloud Near Field Studio 商业版组件库的目标、职责和首批 Widget 范围。

组件库的目标是把可复用 UI 结构沉淀下来，让商业版 Shell、实时视图、属性面板和底部 Dock 共享一致的交互和视觉规则。

## Goals

- 复用通用 UI 组件，减少重复代码。
- 统一 objectName、动态属性和 QSS/theme 接口。
- 避免业务逻辑进入基础 Widget。
- 支持后续主题切换和布局适配。

## Boundaries

- 组件库只负责 UI 表现、状态展示和轻量交互。
- 不直接连接运动平台、频谱仪、相机或扫描任务。
- 不替代上层业务服务和设备适配器。
