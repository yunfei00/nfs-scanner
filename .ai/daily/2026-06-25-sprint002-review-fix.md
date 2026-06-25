Date: 2026-06-25

## Completed

- Sprint 002 Review Fix: 修复 Layer z-order 在 `build_mock()` 后 item 未设置 zValue 的问题。

## Changed Files

- `nfs_scanner/ui/commercial/graphics/layers.py`
- `nfs_scanner/ui/commercial/graphics/layer_manager.py`
- `nfs_scanner/ui/commercial/graphics/marker_items.py`
- `tests/test_layer_z_order.py`

## Fix Summary

- `BaseLayer` 增加 `z_value` / `set_z_value()`，`_register_item()` 注册时自动 `setZValue`。
- `LayerManager.ensure_layer()` 创建 layer 时分配固定 z：photo=0 … annotation=4。
- 移除仅在 ensure 时遍历旧 items 的 `_apply_z_order()`，改为 `verify_layer_z_values()` 供测试校验。
- `MarkerItem` 移除硬编码 `setZValue(10.0)`。
- `ScanPathLayer` 箭头改为沿路径方向绘制。

## Checks

- `python -m compileall nfs_scanner`
- `python -m unittest tests.test_layer_z_order -v`

## Issues

- 无

## Next

- 等待 Sprint 002 review 结论，不进入 Phase 3
