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

## 后续建议

- 增加主界面基础布局分区
- 预留运动控制、扫描任务和数据展示模块接口
- 引入基础日志与配置管理能力
