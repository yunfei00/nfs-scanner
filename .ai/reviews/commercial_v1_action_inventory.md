# Commercial V1 Action Inventory

Generated: 2026-06-28

All actions registered in `nfs_scanner/ui/commercial/actions.py` via `CommercialActionRegistry`.

## Project
| action_id | text |
|-----------|------|
| project.new | 新建项目 |
| project.open | 打开项目 |
| project.save | 保存项目 |
| project.save_as | 另存为 |
| project.recent | 最近项目 |
| project.close | 关闭项目 |

## Device
| action_id | text |
|-----------|------|
| device.connect_all | 连接设备 |
| device.disconnect_all | 断开设备 |
| device.refresh_all | 刷新设备 |
| device.open_center | 设备中心 |
| device.configure | 配置设备 |
| device.test_connection | 测试连接 |

## Scan
| action_id | text |
|-----------|------|
| scan.start | 开始扫描 |
| scan.pause | 暂停扫描 |
| scan.resume | 继续扫描 |
| scan.stop | 停止扫描 |
| scan.reset | 重置扫描 |
| scan.apply_config | 应用配置 |
| scan.preview_path | 预览路径 |

## Camera / Region / View
| action_id | text |
|-----------|------|
| camera.capture | 拍照 |
| region.align | 区域对齐 |
| region.clear | 清除覆盖 |
| region.select / region.box_select / region.polygon_select | ROI 工具 |
| view.* | 实时视图工具（选择/平移/缩放/撤销/重做/标注/网格/路径/测量/LUT/透明度/适应/重置） |

## Data / Report / Settings / Help
| action_id | text |
|-----------|------|
| data.open_view / export_json / export_csv / export_table / clear_history | 数据视图 |
| report.open_center / preview / export_* | 报告中心 |
| settings.display / instrument / apply_template / save_device_config | 设置 |
| help.open / shortcuts / self_check / about | 帮助 |
| demo.reset | Reset Demo |

QA: `registry.validate()["all_actions_have_handlers"]` must PASS.
