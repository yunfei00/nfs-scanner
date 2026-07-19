# 02 UI 架构

## 唯一窗口

`MainWindow` 负责窗口尺寸、产品标题区和 `ScanControlPage` 装配。它不包含设备操作实现。

## 主页面

`ScanControlPage` 是唯一主工作区和兼容 API。已有槽函数和构造参数必须保持稳定。

页面由左右 QScrollArea 和水平 QSplitter 构成：

- 左侧：串口、运动、扫描参数、测试信息、执行动作；
- 右侧：扫描区域、仪表参数、结果路径和日志；
- 底部：位置、时间、剩余时间和系统状态。

## 代码边界

- `scan_control_layout.py` 只负责控件创建、排列和信号连接。
- `scan_workers.py` 包含耗时扫描和仪表搜索 Worker。
- `instrument_operations.py` 包含仪表查询/设置/采集操作。
- `scan_control_support.py` 包含串口发现、配置文件和扫描输出辅助。
- `engineering_dark.qss` 是唯一视觉事实源。

禁止在业务处理方法中拼接大段 QSS，禁止新增第二套窗口组件体系。
