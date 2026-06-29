# Mock / Dry Run 模式

## 含义

商业版 UI 默认运行在 **Mock / Dry Run** 模式：

- 不发送真实运动平台命令
- 不连接真实频谱仪 / VNA
- USB 相机仅在用户点击「开始预览」时打开
- 扫描进度、幅度、热力图为模拟数据

顶部安全标识：

```text
Mock / Dry Run / No Hardware Control / Real Device Disabled
```

## 模拟扫描流程

1. 新建或打开项目
2. 点击 **连接**（Mock 设备 connected）
3. 在右侧 **扫描参数** 配置区域与步长
4. 点击 **应用参数** 或等待 debounce 自动更新
5. 点击 **开始** 启动 Dry Run
6. 观察底部扫描统计、频谱视图、数据表格更新
7. 点击 **停止** 结束

日志示例：

```text
[SCAN] Dry run scan started: 6461 points
[SCAN] Dry run scan stopped by user
```

## 导出与报告

- 导出菜单：CSV / PNG / JSON → `outputs/exports/`
- 报告按钮：跳转报告中心并生成 HTML → `outputs/reports/`

## Real Mode

当前 **未实现** Real Mode。若未来启用，连接真实硬件前必须弹出确认对话框。
