# Commercial V1 Manual Acceptance

## 启动

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

## 验收清单

### 项目
- [ ] 新建项目 → 目录 `~/.nfs_scanner/projects/` 下出现 `project.nfsproj`
- [ ] 打开 Demo 项目
- [ ] 保存 → 状态栏显示「已保存」
- [ ] 另存为 → 新目录副本

### 设备
- [ ] 连接全部设备（Simulation，无硬件 I/O）
- [ ] 设备中心卡片状态同步
- [ ] Dry Run 命令日志有输出
- [ ] 断开 / 刷新

### 扫描
- [ ] 参数修改 → 路径预览更新
- [ ] 开始 / 暂停 / 继续 / 停止
- [ ] 停止不生成 completed 任务
- [ ] 完整扫描 → Data View 新任务

### 视图
- [ ] 实时工具：选择/平移/缩放/框选/多边形/撤销/重做/标注/网格/路径/测量
- [ ] 3D / 数据表格 / 报告中心 Tab 非空
- [ ] 导出 JSON/CSV/MD/HTML/PNG/PDF placeholder

### 帮助
- [ ] 帮助对话框：快速开始 / 快捷键 / 安全 / 关于 / 自检

## 安全确认
- [ ] `NFS_SCANNER_REAL_DEVICES` 未设置
- [ ] 无真实 motion / SCPI / 相机控制
