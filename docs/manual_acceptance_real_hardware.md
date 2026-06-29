# 真实硬件人工验收步骤

> 照着做即可。建议先完成「无硬件验收」，再在有设备实验室做后续部分。

---

## 第一部分：无硬件验收

### 1. 启动商业版 UI

```powershell
cd d:\code_2026\nfs-scanner
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

### 2. 确认默认 Mock Dry Run

- 底部状态栏应显示：**模式: Mock Dry Run**
- 设备中心 → 设备运行模式应为 **Mock Dry Run**

### 3. 点击「连接」

- 应只连接 Mock 设备（motion / spectrum / camera 模拟服务）
- 日志类似：`Mock devices connected`
- **不应**出现串口或 VISA 连接尝试

### 4. 点击「开始」

- 应启动 Dry Run 扫描
- 进度、频谱视图、数据表格有 Mock 更新

### 5. 点击「停止」

- Dry Run 应停止
- 日志：`Dry run scan stopped by user`

### 6. 相机 / 视觉页

- 切换到「相机 / 视觉」
- **笔记本摄像头灯不应自动亮起**

### 7. 刷新设备

- 在设备中心点击「全部刷新」
- **摄像头仍不应自动亮起**

### 8. 导出 / 报告 / 项目

- 导出 CSV / PNG / JSON 有文件输出
- 报告中心可生成 HTML
- 新建 / 保存 / 打开项目正常

### 9. 自动化测试（可选）

```powershell
python -m unittest discover -s tests -v
```

---

## 第二部分：真实设备连接验收

### 1. 准备配置

```powershell
copy config\devices.example.yaml config\devices.yaml
```

编辑 `config/devices.yaml`：

- `motion.enabled: true`，填写实际 `port`（如 `COM3`）
- `instrument.enabled: true`，填写实际 `resource`

### 2. 启用真实设备门控

```powershell
$env:NFS_SCANNER_REAL_DEVICES="1"
```

### 3. 配置与状态检查（不移动）

```powershell
python scripts/real_device_check.py --config
python scripts/real_device_check.py --motion-status
python scripts/real_device_check.py --motion-position
python scripts/real_device_check.py --instrument-idn
```

预期：各命令打印连接结果或 IDN/位置，**不发送 Home / Move**。

### 4. 单次 sweep（可选）

```powershell
python scripts/real_device_check.py --instrument-single-sweep
```

预期：打印 trace 点数和幅度范围。

---

## 第三部分：真实运动验收

### 1. 安全检查

- [ ] 急停按钮可用
- [ ] 扫描区域无障碍物
- [ ] soft limits 与物理行程一致

### 2. 测试移动 +1mm

```powershell
python scripts/real_device_check.py --motion-test-move
```

提示：

```text
即将执行真实运动命令，请确认设备区域安全。
输入 YES 后继续：
```

输入 `YES` 后应仅 X 方向移动约 1mm，脚本打印 before/after 位置。

---

## 第四部分：真实扫描 Smoke Test

### 1. 扫描区域（固定 2×2）

```text
X: 0 -> 2, step 2
Y: 0 -> 2, step 2
Total: 4 points
```

### 2. 先 dry plan

```powershell
python scripts/real_scan_smoke_test.py --dry-plan
```

确认路径 4 点顺序正确，**无硬件命令**。

### 3. 执行扫描

```powershell
$env:NFS_SCANNER_REAL_DEVICES="1"
python scripts/real_scan_smoke_test.py --execute
```

输入 `YES` 后开始真实扫描。

### 4. 验收输出文件

```text
outputs/scans/smoke-test/<timestamp>/scan_points.csv
outputs/scans/smoke-test/<timestamp>/metadata.json
outputs/scans/smoke-test/<timestamp>/traces.npz
```

### 5. UI 内 Real Scan（可选）

1. 启动商业版 UI，设备中心切换 **Real Hardware** 并确认
2. 连接真实设备
3. 参数页设置相同 2×2 区域
4. 点击开始 → 最终确认
5. 观察底部统计、数据表格、实时视图路径更新
6. 点击停止或 Emergency Stop 验证安全停止

---

## 失败时怎么处理

| 现象 | 检查 |
|------|------|
| 连接被拒绝 | `NFS_SCANNER_REAL_DEVICES=1` 是否设置 |
| Motion missing port | `config/devices.yaml` → `motion.port` |
| Instrument missing resource | `instrument.resource` VISA 字符串 |
| 扫描立即 error | soft limits、Y 轴范围、仪表 timeout |
| 相机灯亮 | 是否误点「开始预览」；检查 `safe_enumeration: true` |

---

## 相关文档

- [safety_checklist.md](safety_checklist.md)
- [real_hardware_mode.md](real_hardware_mode.md)
- [real_scan_workflow.md](real_scan_workflow.md)
