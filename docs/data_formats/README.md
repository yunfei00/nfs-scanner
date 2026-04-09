# 数据格式版本文档

本目录用于维护 nfs-scanner 的**扫描数据格式规范**，目标是让历史数据可追溯、可排查、可迁移。

## 目录说明

- `v1.0.md`：当前已落地的数据格式说明（CSV + sidecar meta.json）。
- `CHANGELOG.md`：数据格式版本演进记录。

## 维护规则

1. 每次 `DATA_FORMAT_VERSION` 变更，都必须新增对应版本说明文件。
2. `CHANGELOG.md` 需记录：变更内容、兼容策略、迁移建议。
3. 代码中的写入/读取逻辑、测试样例、文档三者必须同步更新。
4. 不允许只改代码不更新文档，避免现场无法判断旧数据来源。

## 快速排查建议

1. 先看 `xxx.meta.json` 的 `data_format_version` / `generator_version`。
2. 再核对当前程序 `nfs_scanner/version.py` 中的版本常量。
3. 若版本不一致，参考 `CHANGELOG.md` 与对应 `vX.Y.md`。
