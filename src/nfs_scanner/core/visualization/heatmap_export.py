from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from nfs_scanner.core.visualization.lut_manager import get_lut


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

def export_heatmap_png(
    points: list[tuple[float, float, float, float]],
    out_png: Path,
    *,
    lut_name: str = "viridis",
    opacity: float = 1.0,
    autoscale: bool = True,
    vmin: float | None = None,
    vmax: float | None = None,
    min_size: int = 600,
    scale: int = 20,
    smooth: bool = True,
) -> dict:
    """
    points -> heatmap.png (带色条)
    - min_size: 最小可读尺寸（热力图主体最短边至少达到该像素）
    - scale: 基础放大倍数（每个网格点对应多少像素）
    - smooth: True 用双线性插值，False 用最近邻像素块
    """
    out_png.parent.mkdir(parents=True, exist_ok=True)

    xs, ys, grid = build_grid(points)
    hm = apply_lut(
        grid,
        lut_name=lut_name,
        opacity=opacity,
        autoscale=autoscale,
        vmin=vmin,
        vmax=vmax,
    )

    # 计算目标尺寸：优先让最短边 >= min_size
    w0, h0 = hm.image.size  # 网格像素（nx, ny）
    if w0 <= 0 or h0 <= 0:
        raise ValueError("Empty heatmap grid")

    # 基础放大
    target_w = w0 * max(1, int(scale))
    target_h = h0 * max(1, int(scale))

    # 兜底：如果还太小，再提高倍数
    shortest = min(target_w, target_h)
    if shortest < min_size:
        k = int(np.ceil(min_size / max(1, shortest)))
        target_w *= k
        target_h *= k

    resample = Image.Resampling.BILINEAR if smooth else Image.Resampling.NEAREST
    hm_big = hm.image.resize((target_w, target_h), resample=resample)

    # 加色条
    out = draw_colorbar(hm_big, hm.vmin, hm.vmax)
    out.save(out_png, "PNG")

    return {
        "out": str(out_png),
        "nx": int(len(xs)),
        "ny": int(len(ys)),
        "render_w": int(target_w),
        "render_h": int(target_h),
        "vmin": hm.vmin,
        "vmax": hm.vmax,
        "smooth": bool(smooth),
        "lut": lut_name,
        "opacity": float(opacity),
        "autoscale": bool(autoscale),
    }

def render_heatmap_image(
    points,
    *,
    lut_name: str = "viridis",
    opacity: float = 1.0,
    autoscale: bool = True,
    vmin: float | None = None,
    vmax: float | None = None,
    min_size: int = 600,
    scale: int = 20,
    smooth: bool = True,
    with_colorbar: bool = True,
) -> Image.Image:
    xs, ys, grid = build_grid(points)
    hm = apply_lut(
        grid,
        lut_name=lut_name,
        opacity=opacity,
        autoscale=autoscale,
        vmin=vmin,
        vmax=vmax,
    )

    w0, h0 = hm.image.size
    target_w = w0 * max(1, int(scale))
    target_h = h0 * max(1, int(scale))
    shortest = min(target_w, target_h)
    if shortest < min_size:
        k = int(np.ceil(min_size / max(1, shortest)))
        target_w *= k
        target_h *= k

    resample = Image.Resampling.BILINEAR if smooth else Image.Resampling.NEAREST
    hm_big = hm.image.resize((target_w, target_h), resample=resample)

    if with_colorbar:
        return draw_colorbar(hm_big, hm.vmin, hm.vmax)
    return hm_big


def apply_lut(grid: np.ndarray, *, lut_name: str = "viridis", opacity: float = 1.0,
              autoscale: bool = True, vmin: float | None = None, vmax: float | None = None) -> HeatmapImage:
    if autoscale or vmin is None or vmax is None:
        vmin = float(grid.min())
        vmax = float(grid.max())
    else:
        vmin = float(vmin)
        vmax = float(vmax)

    if vmax - vmin < 1e-12:
        norm = np.zeros_like(grid, dtype=np.float32)
    else:
        norm = (grid - vmin) / (vmax - vmin)
    norm = norm.clip(0.0, 1.0)

    lut = get_lut(lut_name).table  # (256,3)
    idx = (norm * 255.0).round().astype(np.uint8)  # (H,W)

    rgb = lut[idx]  # (H,W,3)
    a = int(max(0.0, min(1.0, float(opacity))) * 255)
    alpha = np.full((rgb.shape[0], rgb.shape[1], 1), a, dtype=np.uint8)
    rgba = np.concatenate([rgb.astype(np.uint8), alpha], axis=2)

    im = Image.fromarray(rgba, mode="RGBA")
    return HeatmapImage(im, vmin=vmin, vmax=vmax, width=im.width, height=im.height)

def render_heatmap_for_ui(
    points,
    *,
    lut_name: str = "viridis",
    opacity: float = 1.0,
    autoscale: bool = True,
    vmin: float | None = None,
    vmax: float | None = None,
    min_size: int = 600,
    scale: int = 20,
    smooth: bool = True,
    with_colorbar: bool = True,
):
    xs, ys, grid = build_grid(points)
    hm = apply_lut(
        grid,
        lut_name=lut_name,
        opacity=opacity,
        autoscale=autoscale,
        vmin=vmin,
        vmax=vmax,
    )

    w0, h0 = hm.image.size
    target_w = w0 * max(1, int(scale))
    target_h = h0 * max(1, int(scale))
    shortest = min(target_w, target_h)
    if shortest < min_size:
        k = int(np.ceil(min_size / max(1, shortest)))
        target_w *= k
        target_h *= k

    resample = Image.Resampling.BILINEAR if smooth else Image.Resampling.NEAREST
    hm_big = hm.image.resize((target_w, target_h), resample=resample)

    out_img = draw_colorbar(hm_big, hm.vmin, hm.vmax) if with_colorbar else hm_big
    return xs, ys, grid, out_img, hm.vmin, hm.vmax


