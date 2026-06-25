# 04 Feature Specs

## 1. 项目管理

### 1.1 功能

- 新建项目
- 打开项目
- 保存项目
- 项目信息编辑
- 扫描任务列表
- 历史任务加载

### 1.2 项目元数据

- project_id
- project_name
- created_at
- updated_at
- operator
- comment
- default_output_dir

### 1.3 验收标准

- 新建项目后，所有扫描数据保存在项目目录下。
- 打开项目后，可看到历史扫描任务。
- 项目配置可保存并恢复。

---

## 2. 设备管理

### 2.1 运动平台

支持：

- 串口连接
- 复位 `$H`
- 位置查询 `?`
- 绝对移动 `G1 X.. Y.. Z.. F..`
- 版本查询 `$I`
- 帮助 `$`
- 状态解析
- 坐标范围保护

坐标范围：

- X：0~200
- Y：0~-300
- Z：0~10

### 2.2 频谱仪

通过统一 `ISpectrumAnalyzer` 管理：

- connect
- disconnect
- configure
- single_sweep
- query_idn
- get_marker_value

内置设备：

- ZNA67
- FSW
- N9020A
- Mock

扩展方式：

- Python 插件
- JSON SCPI 模板

### 2.3 相机

通过统一 `ICamera` 管理：

- connect
- disconnect
- get_frame
- capture_image
- save_image

V1 优先支持 USB Camera / OpenCV。

### 2.4 验收标准

- 主界面显示三类设备状态摘要。
- 设备中心能完成详细连接与诊断。
- 任一设备异常时，UI 显示明确错误，不崩溃。

---

## 3. 扫描流程

### 3.1 流程

1. 创建/打开项目。
2. 连接运动平台、频谱仪、相机。
3. 拍照或导入图片。
4. 标定扫描区域。
5. 设置扫描参数。
6. 生成扫描路径。
7. 开始扫描。
8. 每点执行：运动 → 等待稳定 → 采集频谱 → 保存数据 → 更新热力图。
9. 扫描完成后进入数据分析或报告导出。

### 3.2 扫描参数

- x_start
- x_stop
- x_step
- y_start
- y_stop
- y_step
- z_height
- feed_rate
- dwell_time
- average_count
- snake_mode
- return_home_after_scan
- marker_frequency
- trace_id

### 3.3 路径规划

- 支持普通行扫描。
- 支持蛇形扫描。
- 预估点数。
- 预估路径长度。
- 预估总时间。

### 3.4 扫描控制

- 开始
- 暂停
- 继续
- 停止
- 急停
- 扫描完成后回零

### 3.5 验收标准

- 扫描路径可视化。
- 点数、路径长度、预计时间实时计算。
- 暂停/继续不丢失当前状态。
- 停止扫描后数据已保存部分可追溯。

---

## 4. 相机对齐

### 4.1 对齐模式

- 矩形区域：适合板子与相机近似平行。
- 多点标定：3~4 个点，支持仿射/透视变换。

### 4.2 AlignmentConfig

字段：

- image_path
- mode
- world_points
- image_points
- transform_matrix
- x_range
- y_range
- created_at

### 4.3 UI 功能

- 拍照
- 导入图片
- 绘制矩形
- 拖动角点
- 调整扫描区域
- 显示比例尺
- 保存对齐配置
- 重置对齐

### 4.4 验收标准

- 对齐配置可保存到扫描任务。
- 重新打开任务后能恢复照片与区域。
- 扫描点能映射到图像坐标。

---

## 5. 热力图

### 5.1 数据来源

- 实时扫描数据。
- 离线频率文件。
- 历史任务数据库。

### 5.2 显示模式

- Magnitude
- Magnitude dB
- Phase
- Real
- Imag

### 5.3 LUT

内置：

- turbo
- jet
- viridis
- plasma
- inferno
- magma
- cividis
- rainbow
- hot
- cool
- gray
- blue-red
- iron
- thermal

### 5.4 关键要求

热力图必须作为整张图片绘制：

- 使用矩阵 H 生成 RGBA。
- 转为 QImage/QPixmap。
- 添加到 QGraphicsScene。
- 通过 opacity 控制透明度。

禁止按单元格绘制色块。

### 5.5 验收标准

- 放大后无格子缝隙。
- 透明度可调。
- LUT 切换立即生效。
- vmin/vmax 自动/手动生效。

---

## 6. 频谱视图

### 6.1 功能

- 实时显示当前扫描点频谱。
- 显示 Marker 频率。
- 支持频谱对比。
- 支持多 Trace。
- 支持保存频谱图。

### 6.2 坐标

- X：频率
- Y：幅度 dB 或其他模式

### 6.3 Marker

显示：

- marker_id
- frequency
- amplitude
- trace

### 6.4 验收标准

- 当前扫描点更新时，频谱图同步更新。
- Marker 与主画布联动。

---

## 7. 数据存储

### 7.1 目录结构

```text
project_dir/
  project.json
  scans/
    scan_YYYYMMDD_HHMMSS/
      scan_config.json
      alignment.json
      photo.png
      points.csv
      traces.csv
      heatmap_cache/
      report/
```

### 7.2 points.csv

字段：

- point_index
- x
- y
- z
- timestamp
- trace_id
- marker_frequency
- marker_value

### 7.3 traces.csv

兼容格式：

- `x_y_z_trace1_re/im`
- `x_y_z_Trc1_S21_re/im`

通用解析规则：

- 前 3 段为 x/y/z。
- 最后一段为 re/im。
- 中间所有字段连接为 trace_id。

### 7.4 验收标准

- 每次扫描都有独立任务目录。
- 即使扫描中断，也保留已采集数据。
- 离线分析能直接读取历史任务。

---

## 8. 报告导出

### 8.1 V1 报告内容

- 项目信息
- 设备信息
- 扫描参数
- 相机照片 + 热力图
- 频谱图
- Marker 表
- 扫描统计
- 日志摘要

### 8.2 导出格式

V1：PDF。

后续：Word / HTML / Markdown。

### 8.3 验收标准

- PDF 可离线生成。
- 报告图片与当前分析结果一致。
- 报告包含项目和设备信息。
