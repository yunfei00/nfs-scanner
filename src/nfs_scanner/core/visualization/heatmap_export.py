from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

@dataclass(frozen=True)
class HeatmapImage:
    image: Image.Image
    vmin: float
    vmax: float
    width: int
    height: int

def build_grid(points: list[tuple[float, float, float, float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    根据点位构建规则网格：
    返回 xs(unique), ys(unique), grid[value] shape=(len(ys), len(xs))
    """
    xs = sorted({p[0] for p in points})
    ys = sorted({p[1] for p in points})

    x_index = {x: i for i, x in enumerate(xs)}
    y_index = {y: i for i, y in enumerate(ys)}

    grid = np.full((len(ys), len(xs)), np.nan, dtype=np.float32)

    for x, y, z, v in points:
        grid[y_index[y], x_index[x]] = v

    # 若有 nan，用最小值填充（也可用插值，后面再升级）
    nan_mask = np.isnan(grid)
    if nan_mask.any():
        valid = grid[~nan_mask]
        fill = float(valid.min()) if valid.size else 0.0
        grid[nan_mask] = fill

    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32), grid

def apply_lut_gray(grid: np.ndarray) -> HeatmapImage:
    """
    先用灰度 LUT（稳定、无外部色图依赖）：
    value -> [0,255]
    """
    vmin = float(grid.min())
    vmax = float(grid.max())
    if vmax - vmin < 1e-12:
        norm = np.zeros_like(grid, dtype=np.float32)
    else:
        norm = (grid - vmin) / (vmax - vmin)

    img8 = (norm * 255.0).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(img8, mode="L").convert("RGBA")
    return HeatmapImage(im, vmin=vmin, vmax=vmax, width=im.width, height=im.height)

def draw_colorbar(im: Image.Image, vmin: float, vmax: float, bar_width: int = 40) -> Image.Image:
    """
    右侧加一个灰度色条 + min/max 标注
    """
    w, h = im.size
    out = Image.new("RGBA", (w + bar_width + 120, h), (255, 255, 255, 255))
    out.paste(im, (0, 0))

    # colorbar
    bar_x0 = w + 20
    bar_x1 = bar_x0 + bar_width
    draw = ImageDraw.Draw(out)
    for y in range(h):
        t = 1.0 - (y / max(1, h - 1))
        g = int(t * 255)
        draw.line([(bar_x0, y), (bar_x1, y)], fill=(g, g, g, 255))

    # text
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((bar_x1 + 10, 5), f"max: {vmax:.6g}", fill=(0, 0, 0, 255), font=font)
    draw.text((bar_x1 + 10, h - 15), f"min: {vmin:.6g}", fill=(0, 0, 0, 255), font=font)
    return out

def export_heatmap_png(points: list[tuple[float, float, float, float]], out_png: Path) -> dict:
    """
    points -> heatmap.png (带色条)
    返回 meta 信息
    """
    out_png.parent.mkdir(parents=True, exist_ok=True)
    xs, ys, grid = build_grid(points)
    hm = apply_lut_gray(grid)
    out = draw_colorbar(hm.image, hm.vmin, hm.vmax)
    out.save(out_png, "PNG")
    return {
        "out": str(out_png),
        "nx": int(len(xs)),
        "ny": int(len(ys)),
        "vmin": hm.vmin,
        "vmax": hm.vmax,
    }
