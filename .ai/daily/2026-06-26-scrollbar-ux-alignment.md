# Commercial Scrollbar / Slider UX Alignment

Date: 2026-06-26

## Summary

统一商业 UI 滚动条、滑块、进度条视觉与交互，解决“太细、不好拖、点一下就跳”的问题。

## Changes

| Area | Change |
|------|--------|
| QSS | QScrollBar 14px；handle min 48px；hover/pressed 高亮；隐藏 add/sub line |
| QSlider | handle 16px；groove 6px |
| QProgressBar | 只读进度样式，与滚动条区分 |
| scroll_helpers | 统一 singleStep/pageStep；configure scroll areas |
| scroll_metrics | 宽度、可滚动性、滚轮/handle 交互检查 |
| QA | interaction 分类 + Manual Behavior Verification |

## Results

- visual check: **PASS**
- QA pipeline: **PASS**
- 145 unittest: **PASS**
