# 商业基线实施状态

> 最后更新：2026-07-19

## 验证结果

- 自动化测试：182 passed，4 skipped，4 subtests passed。
- Ruff、`compileall` 和唯一 UI 结构检查通过。
- 源码离屏启动并正常退出，退出码 0。
- 使用锁定的 PyInstaller 6.21.0 实际完成 Windows one-folder 打包。
- 打包后的 `NFSScanner.exe` 离屏启动并正常退出，退出码 0。
- 验证期间未连接或控制任何真实硬件。

## 唯一正式基线

- 唯一入口：`python -m nfs_scanner`。
- 唯一窗口：`nfs_scanner.ui.main_window.MainWindow`。
- 唯一主页面：`nfs_scanner.ui.widgets.ScanControlPage`。
- 唯一扫描执行器：`ScanWorker`；运行状态由 `ScanManager` 维护。
- 唯一设备入口：`DeviceManager` / `DeviceHub` 与现有 QSerialPort、ZNA67、N9020A、FSW 适配器。
- 已移除未接入主窗口的 RealScan/SimulationProvider/MockService 平行链路及其测试。

## 安全与生命周期

- 启动只发现串口和 VISA 资源，不自动连接真实设备。
- 运动串口需要操作员显式确认后手动打开。
- 掉线定时器只监测设备恢复，不自动重新打开串口。
- 普通停止与红色“软件急停”分别处理，并记录不同的扫描结果状态。
- Worker 在运动、等待、采集、存储检查点响应停止；关闭窗口会协作式等待线程并释放设备。
- 应用使用单实例锁和顶层异常日志。

## 数据与运维

- 配置、状态/日志和扫描数据使用独立的用户目录，不再依赖源码工作目录。
- 旧仓库相对配置首次复制到用户目录，已有用户配置不会被覆盖。
- 配置与结果元数据采用原子替换；追加数据同步到磁盘。
- 每次扫描保存可恢复清单，区分完成、失败、停止、急停和意外中断。
- 扫描结束生成 SHA-256 校验清单。
- 诊断 ZIP 包含版本、最近日志和脱敏配置，不包含测量数据。
- 历史扫描输出已从 Git 跟踪中移除，本机文件仍保留。

## 发布工程

- 运行、开发和构建依赖分别精确锁定。
- Windows CI 执行测试、静态检查、编译、唯一 UI 检查和启动冒烟测试。
- 发布工作流生成 one-folder、Inno Setup 安装器、portable ZIP、SPDX SBOM 和 SHA-256 校验。
- 标签发布强制要求 Authenticode 证书，并签名 EXE 与安装器。
- 应用版本统一来自 `nfs_scanner/version.py`；安装器读取 EXE 版本。
- 包含专有许可证、第三方依赖清单、用户手册和硬件验收矩阵。

## 发布前仍需外部确认

- 真实运动平台和各型号仪表的现场验收结果。
- 正式公司名称、版权主体、最终品牌图标与代码签名证书。
- Qt/PySide6 许可路线及第三方许可证的法务确认。
- 干净目标 Windows 设备上的安装、升级、卸载和驱动兼容性验证。
