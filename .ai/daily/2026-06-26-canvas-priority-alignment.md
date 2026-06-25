# Commercial Target Page Alignment — Canvas Priority

Date: 2026-06-26

## Summary

压缩左右侧栏与 bottom dock 占比，提升中央 RealtimeCanvas 视觉优先级。

## Layout Changes

| Region | Before | After |
|--------|--------|-------|
| Left panel | 280px | 240px |
| Right panel | 380px | 320px |
| Bottom dock ratio (default) | 28% | 24% |
| Bottom dock ratio (maximized) | 22% | 20% |
| Center splitter stretch | 7:3 | 8:2 |
| Device scroll max height | 240px | 180px |

## New Visual Metric

`center_canvas_priority`:
- canvas width >= right panel × 1.6
- canvas width >= left panel × 2.0
- canvas area >= 50% of realtime view

## Results (1280×720)

- Canvas: **636×307** (was 536×307)
- Ratios: right **1.99x**, left **2.65x**, area **81%**
- visual check: **PASS**
- QA pipeline: **PASS**
- 143 unittest: **PASS**
