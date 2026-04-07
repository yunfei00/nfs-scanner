# nfs-scanner

Near Field Scan System（近场扫描系统）是一个基于 Python 3.11 与 PySide6 的桌面应用项目。

## 路线图文件
在开始任何实现前，请先阅读 `docs/ROADMAP.md`。
所有开发任务必须优先遵循路线图分阶段推进，不要跨阶段一次性实现过多内容。

当前仓库处于项目初始化阶段，目标是先建立清晰、可运行、便于后续迭代扩展的工程骨架。

## 环境要求

- Python 3.11
- PySide6

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方式

```bash
python -m nfs_scanner.main
```

## 当前目录结构

```text
nfs_scanner/
    __init__.py
    main.py
    app.py
    ui/
        __init__.py
        main_window.py
requirements.txt
README.md
```

## 当前实现

- 提供最小可运行的 PySide6 应用入口
- 创建标题为“近场扫描系统”的主窗口
- 主窗口默认大小为 `1600x900`
- 中央区域为占位组件，供后续功能模块扩展

## 扫描控制分层

- `nfs_scanner/core/scan_manager.py`
  负责扫描生命周期、运行/暂停/恢复/完成/失败/停止状态，以及 ETA、剩余时间、暂停累计时长等核心逻辑。
- `nfs_scanner/ui/widgets/scan_control_page.py`
  负责按钮交互、串口命令发送、路径点调度和状态栏展示；页面不再自行计算扫描计时。

## ETA 与暂停行为

- 开始扫描后会尽快显示 `剩余` 和 `预计完成`。
- 扫描运行中，状态栏会按当前 manager snapshot 动态刷新 ETA。
- 暂停时冻结剩余时间与预计完成时刻。
- 恢复后会基于暂停时保留的剩余时间重新锚定预计完成时刻。
- 完成后显示完成态与 `0` 秒剩余；失败或停止后会清空 ETA 展示。

## 测试命令

```bash
py -3.11 -m unittest tests.test_scan_manager_timing tests.test_scan_control_page_timing
py -3.11 -m compileall nfs_scanner tests
```

## 后续建议

- 增加主界面基础布局分区
- 预留运动控制、扫描任务和数据展示模块接口
- 引入基础日志与配置管理能力
