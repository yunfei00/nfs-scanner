# ZNA67 行式频谱存储方案（草案）

## 1. 目标

面向 R&S ZNA67 的近场扫描数据，提供一种**可持续追加、易调试、易导出**的存储方式。

核心要求：

1. 主数据文件按“**一次采样写一行**”方式落盘
2. 第一行保存频率轴，首列使用 `fre`
3. 第二行起保存每个扫描点的数据
4. 坐标 `x/y/z` 不放入主数据文件列中，改为写入元数据文件

---

## 2. 文件结构

建议每次扫描落到一个目录，例如：

```text
output/20260330_153000/
  scan_config.json
  frequencies.npy
  positions.npy
  spectrum.npy
  images.npy
  spectrum_rows.csv
  spectrum_rows_meta.jsonl
```

其中：

- `spectrum_rows.csv`：行式频谱主数据
- `spectrum_rows_meta.jsonl`：与每一行频谱对应的坐标元数据

---

## 3. 行式主数据格式（spectrum_rows.csv）

### 3.1 第一行：频率轴

第一行的格式：

```text
fre,f1,f2,f3,...,fN
```

说明：

- `fre` 为固定标记
- `f1..fN` 为当前测量设置对应的频率点（单位建议统一为 Hz）

### 3.2 第二行开始：每个点一行

每行格式：

```text
pt_000001,a1,a2,a3,...,aN
pt_000002,a1,a2,a3,...,aN
...
```

说明：

- 第一列 `pt_xxxxxx` 是行键（row_key）
- 后续 `a1..aN` 为该扫描点在各频点上的幅度值

---

## 4. 元数据格式（spectrum_rows_meta.jsonl）

按 JSON Lines 逐行写入，每行对应 `spectrum_rows.csv` 的一个 `row_key`：

```json
{"row_key":"pt_000001","x":0.0,"y":0.0,"z":5.0}
{"row_key":"pt_000002","x":1.0,"y":0.0,"z":5.0}
```

这样可以实现：

- 主数据文件保持纯频谱数值，便于快速载入/导出
- 坐标及后续扩展字段（时间戳、通道、功率、温度等）放在元数据中

---

## 5. 落盘流程建议

1. 首个测点到来时，写入 `fre` 头行
2. 每采一个点：
   - 向 `spectrum_rows.csv` 追加一行幅度数据
   - 向 `spectrum_rows_meta.jsonl` 追加一行坐标 JSON
3. 采集结束后再保留 `.npy` 文件作为高性能二进制缓存

---

## 6. 可实现性结论

该方案可直接实现，且已在当前代码中落地：

- 在数据集中新增频率轴缓存 `frequency_axis`
- 保存数据集时新增：
  - `frequencies.npy`
  - `spectrum_rows.csv`
  - `spectrum_rows_meta.jsonl`

与后续真实 ZNA67 接入时的适配关系：

- 只要驱动层能提供“频率数组 + 幅度数组”，即可复用该存储结构
- 若后续切换为复数数据（I/Q 或 Real/Imag），可在 `row_key` 后追加双列或拆分到并行文件，不影响当前框架

---

## 7. 下一步建议

1. 在 ZNA 实机采集时，确认频率单位与点数一致性
2. 增加导入器：从 `spectrum_rows.csv + meta.jsonl` 还原热力图输入
3. 为长任务增加“分段文件滚动”能力（例如每 5000 点切分一个数据块）
