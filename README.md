# nfs-scanner

Near Field Scan System（近场扫描系统）是一个基于 Python 3.11 与 PySide6 的桌面工程应用，用于承载运动控制、扫描任务、频谱采集、数据落盘与后续热力图分析流程。

## 当前分层

- `nfs_scanner/core/scan_manager.py`
  负责扫描生命周期、ETA、暂停/恢复计时，以及扫描过程中统一的频谱采样调用入口。
- `nfs_scanner/core/device_manager.py`
  负责设备连接状态与频谱仪适配器复用，避免 UI 直接管理底层设备实例。
- `nfs_scanner/devices/spectrum/`
  统一的频谱仪适配层。
  - `base_spectrum.py`：上层统一接口
  - `scpi_transport.py`：VISA/SCPI 传输层
  - `scpi_adapter.py`：通用 SCPI 适配基础类
  - `factory.py`：按 instrument type 创建具体适配器
  - `zna67_adapter.py` / `fsw_adapter.py` / `n9020a_adapter.py`：设备独立适配器
- `nfs_scanner/ui/widgets/scan_control_page.py`
  负责界面交互、状态展示、扫描页联动与调用 manager，不再直接拼装扫描计时或设备命令。

## 当前支持的频谱仪接入方式

- `ZNA67`
  已整理进统一适配框架，当前仍通过既有 MMEM 数据导出链路读取 trace。
- `FSW`
  已接入统一 SCPI 适配层，本轮优先打通单次连接、参数下发、触发、读取 trace 的最小闭环。
- `N9020A`
  已纳入统一适配框架，命令入口与结果结构与 FSW 对齐，便于后续真机联调。
- `MOCK`
  用于无硬件环境下的开发与测试。

## 统一采样结果

所有适配器都向上层返回 `SpectrumAcquisitionResult`，至少包含：

- `instrument_type`
- `timestamp`
- `acquisition_mode`
- `frequency_settings`
- `rbw_hz` / `vbw_hz` / `ref_level_dbm`
- `point_value` 或完整 `trace`
- `metadata`

这样扫描流程、实时落盘、后续 CSV/热力图逻辑不需要感知底层设备差异。

## 扫描控制行为

- 扫描生命周期、ETA、暂停/恢复逻辑统一由 `ScanManager` 管理。
- 页面层只读取 `ScanRuntimeSnapshot` 刷新“运行时间 / 剩余 / 预计完成”。
- 扫描过程中的频谱采集统一通过 `ScanManager` 调用当前频谱适配器。

## 安装与运行

```bash
pip install -r requirements.txt
python -m nfs_scanner.main
```

如果需要真实 VISA 设备联调，还需要本机安装 `pyvisa` 与对应厂商 VISA Runtime。

## 联调脚本

本轮新增通用联调脚本：

```bash
py -3.11 scripts\test_spectrum_analyzer.py --help
```

FSW 最小闭环示例：

```bash
py -3.11 scripts\test_spectrum_analyzer.py ^
  --instrument FSW ^
  --resource TCPIP0::192.168.0.20::inst0::INSTR ^
  --start-freq 2.4GHz ^
  --stop-freq 2.5GHz ^
  --rbw 100kHz ^
  --vbw 300kHz ^
  --ref-level 10 ^
  --detector RMS ^
  --trace-mode WRIT ^
  --save-json output\fsw_debug.json
```

N9020A 示例：

```bash
py -3.11 scripts\test_spectrum_analyzer.py ^
  --instrument N9020A ^
  --resource TCPIP0::192.168.0.30::inst0::INSTR ^
  --center-freq 2.45GHz ^
  --span 100MHz ^
  --rbw 100kHz
```

## 推荐测试命令

```bash
py -3.11 -m unittest discover -s tests
py -3.11 -m compileall nfs_scanner tests scripts
py -3.11 scripts\test_spectrum_analyzer.py --help
```

## 当前已打通范围

- 扫描生命周期与 ETA 已下沉到 `ScanManager`
- 频谱仪统一适配层已建立
- `FSW / N9020A / ZNA67 / Mock` 已可通过统一工厂创建
- 扫描结果已支持携带统一的 `SpectrumAcquisitionResult`
- 扫描页保存点位数据时，非 ZNA67 仪器会直接保存归一化结果 JSON

## 本轮未展开的现场项

- FSW 真机下各命令在具体固件版本上的逐项确认
- N9020A 真机参数映射与 trace 查询的逐项核对
- 多设备切换时的 UI 参数面板进一步细化
- 将扫描页里剩余的仪表面板参数项继续补齐到 `vbw / ref level / detector / trace mode`
