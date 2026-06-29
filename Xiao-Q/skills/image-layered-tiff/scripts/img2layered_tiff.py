#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
img2layered_tiff.py - 将 JPG/PNG 图片转换为分层 TIFF / PSD 文件

支持的分层模式：
  rgb           - RGB 三通道分离 (R/G/B 三个灰度图层)
  cmyk          - CMYK 四通道分离 (C/M/Y/K 四个灰度图层)
  alpha         - 彩色图层 + Alpha 透明通道
  gray+color    - 灰度图层 + 彩色原图 (双图层)
  rgba          - RGBA 四通道分离 (R/G/B/A 四个灰度图层)
  hsl           - HSL 三通道分离 (色相/饱和度/亮度)
  lab           - CIE Lab 三通道分离
  edge-extract  - 边缘清晰图形提取 (多算法轮廓提取)

输出格式：
  tiff (默认)   - 多页 TIFF，每页一个图层，在 ImageJ/GIMP 中按页面查看
  psd           - Photoshop PSD，每个图层在 Photoshop 图层面板中独立显示

依赖：pip install Pillow numpy tifffile imagecodecs pytoshop

用法：
  python img2layered_tiff.py input.jpg --mode rgb --output output.tif
  python img2layered_tiff.py input.png --mode cmyk --compression lzw
  python img2layered_tiff.py input.png --mode alpha --dpi 300
  python img2layered_tiff.py input.jpg input2.png --mode rgb --dpi 300 --compression lzw
  python img2layered_tiff.py input.jpg --mode edge-extract --edge-threshold 50
  python img2layered_tiff.py input.jpg --mode rgb --format psd
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageCms
    import numpy as np
    import tifffile
    HAS_SCIPY = True
    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        HAS_SCIPY = False
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install Pillow numpy tifffile")
    sys.exit(1)

# pytoshop: 可选依赖，用于 PSD 输出
try:
    import pytoshop
    from pytoshop.layers import LayerRecord, LayerAndMaskInfo, LayerInfo, ChannelImageData
    from pytoshop.enums import ColorMode
    HAS_PYTOSHOP = True
except ImportError:
    HAS_PYTOSHOP = False


# ── 分层模式常量 ──────────────────────────────────────────
MODES = {
    "rgb":           {"desc": "RGB 三通道分离",       "layers": ["Red", "Green", "Blue"]},
    "rgba":          {"desc": "RGBA 四通道分离",      "layers": ["Red", "Green", "Blue", "Alpha"]},
    "cmyk":          {"desc": "CMYK 四通道分离",      "layers": ["Cyan", "Magenta", "Yellow", "Black"]},
    "alpha":         {"desc": "彩色 + Alpha 通道",    "layers": ["Composite", "Alpha"]},
    "gray+color":    {"desc": "灰度 + 彩色原图",     "layers": ["Grayscale", "Color"]},
    "hsl":           {"desc": "HSV 三通道分离",       "layers": ["Hue", "Saturation", "Lightness"]},
    "lab":           {"desc": "CIE Lab 三通道分离",   "layers": ["L*", "a*", "b*"]},
    "edge-extract":  {"desc": "边缘清晰图形提取",     "layers": ["Composite", "Canny-Edge", "Gradient-Mag", "Binary-Edge"]},
}

COMPRESSORS = {
    "none":  None,
    "lzw":   "lzw",
    "deflate": "zlib",
    "zip":   "zlib",
    "jpeg":  "jpeg",
    "jpeg2000": "jpeg2000",
}

# sRGB → CMYK 转换配置文件
SRGB_PROFILE = None  # 延迟初始化
CMYK_PROFILE = None


def _init_cmyk_profiles():
    """尝试初始化 ICC 配置文件，用于 RGB → CMYK 精确转换"""
    global SRGB_PROFILE, CMYK_PROFILE
    try:
        # PIL 内置 sRGB
        srgb_path = ImageCms.createProfile("sRGB")
        SRGB_PROFILE = ImageCms.ImageCmsProfile(srgb_path)

        # 尝试查找系统 CMYK 配置文件
        cmyk_paths = [
            # Windows 常见位置
            os.path.expandvars(r"%SystemRoot%\System32\spool\drivers\color\USWebCoatedSWOP.icc"),
            os.path.expandvars(r"%SystemRoot%\System32\spool\drivers\color\CoatedFOGRA39.icc"),
            os.path.expandvars(r"%SystemRoot%\System32\spool\drivers\color\JapanColor2001Coated.icc"),
            # macOS
            "/System/Library/ColorSync/Profiles/USWebCoatedSWOP.icc",
            "/Library/ColorSync/Profiles/USWebCoatedSWOP.icc",
        ]
        for p in cmyk_paths:
            if os.path.exists(p):
                CMYK_PROFILE = ImageCms.ImageCmsProfile(p)
                break

        if CMYK_PROFILE is None:
            # 创建一个简易 CMYK profile 用于基础转换
            CMYK_PROFILE = ImageCms.ImageCmsProfile(
                ImageCms.createProfile("CMYK")
            )
    except Exception:
        SRGB_PROFILE = None
        CMYK_PROFILE = None


def _rgb_to_cmyk(img: Image.Image) -> Image.Image:
    """RGB → CMYK 转换，优先使用 ICC profile，回退到 PIL 内置转换"""
    if img.mode != "RGB":
        img = img.convert("RGB")

    if SRGB_PROFILE and CMYK_PROFILE:
        try:
            transform = ImageCms.Transform(
                SRGB_PROFILE, "RGB",
                CMYK_PROFILE, "CMYK",
                renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
            )
            return transform.convert(img)
        except Exception:
            pass
    return img.convert("CMYK")


def _get_dpi(img: Image.Image, target_dpi: Optional[float]) -> Tuple[float, float]:
    """获取 DPI，优先使用图片自身 DPI，否则使用目标值"""
    if target_dpi:
        return (target_dpi, target_dpi)
    existing = img.info.get("dpi", img.info.get("resolution"))
    if existing:
        if isinstance(existing, tuple):
            return existing
        return (existing, existing)
    return (72.0, 72.0)


def _channel_to_uint8(arr: np.ndarray) -> np.ndarray:
    """确保通道数据为 uint8"""
    if arr.dtype == np.uint8:
        return arr
    if arr.dtype in (np.float32, np.float64):
        arr = np.clip(arr * 255, 0, 255)
    return arr.astype(np.uint8)


# ── 各模式分层函数 ────────────────────────────────────────

def split_rgb(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """RGB 三通道分离 → 三个灰度图层"""
    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    return [
        ("Red",   np.array(r)),
        ("Green", np.array(g)),
        ("Blue",  np.array(b)),
    ]


def split_rgba(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """RGBA 四通道分离 → 四个灰度图层"""
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    return [
        ("Red",   np.array(r)),
        ("Green", np.array(g)),
        ("Blue",  np.array(b)),
        ("Alpha", np.array(a)),
    ]


def split_cmyk(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """CMYK 四通道分离 → 四个灰度图层"""
    _init_cmyk_profiles()
    cmyk = _rgb_to_cmyk(img)
    c, m, y, k = cmyk.split()
    return [
        ("Cyan",    np.array(c)),
        ("Magenta", np.array(m)),
        ("Yellow",  np.array(y)),
        ("Black",   np.array(k)),
    ]


def split_alpha(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """彩色原图 + Alpha 透明通道 → 双图层"""
    rgba = img.convert("RGBA")
    rgb = rgba.convert("RGB")
    _, _, _, a = rgba.split()
    return [
        ("Composite", np.array(rgb)),
        ("Alpha",     np.array(a)),
    ]


def split_gray_color(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """灰度 + 彩色原图 → 双图层"""
    gray = img.convert("L")
    rgb = img.convert("RGB")
    return [
        ("Grayscale", np.array(gray)),
        ("Color",     np.array(rgb)),
    ]


def split_hsl(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """HSL 三通道分离 → 三个灰度图层"""
    hsl = img.convert("RGB").convert("HSV")
    h, s, v = hsl.split()
    # h = 色相 (0-255 映射自 0-360)
    # s = 饱和度 (0-255)
    # v = 明度 (0-255)
    return [
        ("Hue",        np.array(h)),
        ("Saturation", np.array(s)),
        ("Lightness",  np.array(v)),
    ]


def split_lab(img: Image.Image, dpi: Tuple[float, float]) -> List[Tuple[str, np.ndarray]]:
    """CIE Lab 三通道分离 → 三个灰度图层"""
    lab = img.convert("RGB").convert("LAB")
    l, a, b = lab.split()
    return [
        ("L*", np.array(l)),
        ("a*", np.array(a)),
        ("b*", np.array(b)),
    ]


# ── 边缘图形提取 ──────────────────────────────────────────

def _convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    2D 卷积（纯 numpy 向量化实现，通过滑动窗口切片加速）。
    支持 3x3 和 5x5 内核。
    """
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
    h, w = image.shape
    # 构建滑动窗口视图 (h, w, kh, kw)
    strides = padded.strides
    shape = (h, w, kh, kw)
    windows = np.lib.stride_tricks.as_strided(padded, shape=shape, strides=(strides[0], strides[1], strides[0], strides[1]))
    # 向量化点积求和
    return np.einsum('ijkl,kl->ij', windows, kernel)


def _sobel_operator(gray: np.ndarray) -> np.ndarray:
    """Sobel 算子计算梯度幅值（numpy 向量化实现）"""
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    gx = _convolve2d(gray.astype(np.float64), sobel_x)
    gy = _convolve2d(gray.astype(np.float64), sobel_y)
    return np.sqrt(gx ** 2 + gy ** 2)


def _canny_edge(gray: np.ndarray, threshold: int) -> np.ndarray:
    """
    Canny 边缘检测（numpy 向量化实现）

    步骤：高斯平滑 → Sobel 梯度 → 非极大值抑制 → 双阈值 + 滞后边缘跟踪
    """
    h, w = gray.shape
    f64 = gray.astype(np.float64)

    # 1. 高斯平滑
    if HAS_SCIPY:
        smoothed = gaussian_filter(f64, sigma=1.4)
    else:
        gauss_kernel = np.array([
            [2,  4,  5,  4,  2],
            [4,  9, 12,  9,  4],
            [5, 12, 15, 12,  5],
            [4,  9, 12,  9,  4],
            [2,  4,  5,  4,  2],
        ], dtype=np.float64) / 159.0
        smoothed = _convolve2d(f64, gauss_kernel)

    # 2. Sobel 梯度
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
    gx = _convolve2d(smoothed, sobel_x)
    gy = _convolve2d(smoothed, sobel_y)

    mag = np.sqrt(gx ** 2 + gy ** 2)
    angle = np.arctan2(gy, gx) * 180.0 / np.pi
    angle[angle < 0] += 180.0

    # 3. 非极大值抑制（向量化）
    # 将角度量化为 4 个方向 (0/45/90/135)
    angle_q = np.round(angle / 45.0) % 4

    nms = np.zeros((h, w), dtype=np.float64)
    for direction in range(4):
        if direction == 0:      # 0 deg: horizontal
            q1, q2 = mag[1:-1, 2:], mag[1:-1, :-2]
        elif direction == 1:    # 45 deg: diagonal
            q1, q2 = mag[:-2, 2:], mag[2:, :-2]
        elif direction == 2:    # 90 deg: vertical
            q1, q2 = mag[:-2, 1:-1], mag[2:, 1:-1]
        else:                   # 135 deg: anti-diagonal
            q1, q2 = mag[:-2, :-2], mag[2:, 2:]

        mask = (angle_q[1:-1, 1:-1] == direction)
        center = mag[1:-1, 1:-1]
        nms[1:-1, 1:-1] += np.where(mask & (center >= q1) & (center >= q2), center, 0)

    # 4. 双阈值
    high = threshold * 1.5
    low = threshold * 0.5
    strong = nms >= high
    weak = (nms >= low) & (~strong)

    # 5. 滞后边缘跟踪（向量化：用形态学膨胀检测强边缘邻域）
    from PIL import ImageFilter
    strong_img = Image.fromarray(strong.astype(np.uint8) * 255)
    # 3x3 膨胀：任何弱边缘在强边缘的 3x3 邻域内则提升为强边缘
    dilated = strong_img.filter(ImageFilter.MaxFilter(3))
    dilated_arr = np.array(dilated) > 0
    # 连续膨胀直到收敛
    prev_count = -1
    while True:
        connected = weak & dilated_arr
        count = connected.sum()
        if count == prev_count:
            break
        prev_count = count
        # 把新发现的边缘加入强边缘集
        strong |= connected
        strong_img = Image.fromarray(strong.astype(np.uint8) * 255)
        dilated = strong_img.filter(ImageFilter.MaxFilter(3))
        dilated_arr = np.array(dilated) > 0

    edge = strong.copy()
    return (edge.astype(np.uint8) * 255)


def _laplacian_edge(gray: np.ndarray) -> np.ndarray:
    """拉普拉斯算子边缘检测（对噪声敏感，适合边缘非常清晰的图形）"""
    kernel = np.array([
        [0,  1, 0],
        [1, -4, 1],
        [0,  1, 0],
    ], dtype=np.float64)

    f64 = gray.astype(np.float64)

    # 高斯预平滑
    if HAS_SCIPY:
        smoothed = gaussian_filter(f64, sigma=1.0)
    else:
        gauss_kernel = np.array([
            [1,  2,  1],
            [2,  4,  2],
            [1,  2,  1],
        ], dtype=np.float64) / 16.0
        smoothed = _convolve2d(f64, gauss_kernel)

    result = _convolve2d(smoothed, kernel)

    # 取绝对值并归一化到 0-255
    result = np.abs(result)
    max_val = result.max()
    if max_val > 0:
        result = (result / max_val * 255)
    return result.astype(np.uint8)


def split_edge_extract(img: Image.Image, dpi: Tuple[float, float], threshold: int = 30) -> List[Tuple[str, np.ndarray]]:
    """
    边缘清晰图形提取 → 四个图层

    图层说明：
      1. Composite    - 原图（彩色参考）
      2. Canny-Edge   - Canny 边缘检测结果（白色=边缘，黑色=无边缘）
      3. Gradient-Mag - Sobel 梯度幅值图（边缘越亮越强）
      4. Binary-Edge  - 拉普拉斯二值化边缘（对锐利轮廓最敏感）

    Args:
        img: PIL Image 对象
        dpi: DPI 分辨率元组
        threshold: 边缘检测阈值 1-255（默认 30）
    """

    # 原图彩色
    composite = np.array(img.convert("RGB"))

    # 灰度
    gray = np.array(img.convert("L"))

    # Canny 边缘
    canny = _canny_edge(gray, threshold)

    # Sobel 梯度幅值
    grad_mag = _sobel_operator(gray)
    grad_mag_uint8 = (grad_mag / grad_mag.max() * 255) if grad_mag.max() > 0 else grad_mag
    grad_mag_uint8 = grad_mag_uint8.astype(np.uint8)

    # 拉普拉斯二值化
    laplacian = _laplacian_edge(gray)
    # 二值化
    binary = ((laplacian > threshold * 0.8).astype(np.uint8)) * 255

    return [
        ("Composite",    composite),
        ("Canny-Edge",   canny),
        ("Gradient-Mag", grad_mag_uint8),
        ("Binary-Edge",  binary),
    ]


SPLITTERS = {
    "rgb":           split_rgb,
    "rgba":          split_rgba,
    "cmyk":          split_cmyk,
    "alpha":         split_alpha,
    "gray+color":    split_gray_color,
    "hsl":           split_hsl,
    "lab":           split_lab,
    "edge-extract":  split_edge_extract,
}


# ── TIFF 写入 ─────────────────────────────────────────────

def _build_description(img_path: str, mode: str, layers: List[Tuple[str, np.ndarray]]) -> str:
    """构建 TIFF 文件描述元数据（纯 ASCII，避免中文编码问题）"""
    stem = Path(img_path).stem
    lines = [
        f"Layered TIFF - Mode: {mode}",
        f"Source: {Path(img_path).name}",
        f"Size: {layers[0][1].shape[1]}x{layers[0][1].shape[0]}px",
        f"Layers ({len(layers)}):",
    ]
    for name, arr in layers:
        ch_desc = "RGB" if arr.ndim == 3 and arr.shape[2] == 3 else "Grayscale"
        lines.append(f"  [{ch_desc}] {name} ({arr.shape[1]}x{arr.shape[0]})")
    return "\n".join(lines)


def save_layered_tiff(
    layers: List[Tuple[str, np.ndarray]],
    output_path: str,
    compression: Optional[str] = None,
    dpi: Optional[Tuple[float, float]] = None,
    source_path: str = "",
    mode: str = "",
) -> str:
    """
    将多个图层写入分层 TIFF 文件

    Args:
        layers: [(图层名, numpy数组), ...] 列表
        output_path: 输出文件路径
        compression: 压缩方式 (None/lzw/zlib/jpeg)
        dpi: DPI 分辨率
        source_path: 源文件路径 (用于元数据)
        mode: 分层模式名称 (用于元数据)

    Returns:
        输出文件路径
    """
    description = _build_description(source_path, mode, layers)

    if dpi:
        x_res, y_res = dpi
    else:
        x_res = y_res = None

    with tifffile.TiffWriter(output_path, bigtiff=False) as tif:
        for i, (name, arr) in enumerate(layers):
            # 确保数据类型正确
            if arr.ndim == 2:
                # 灰度图层
                data = _channel_to_uint8(arr)
                photometric = "minisblack"
            elif arr.ndim == 3 and arr.shape[2] == 3:
                # RGB 彩色图层
                data = _channel_to_uint8(arr)
                photometric = "rgb"
            elif arr.ndim == 3 and arr.shape[2] == 4:
                # RGBA 彩色图层
                data = _channel_to_uint8(arr)
                photometric = "rgb"
            else:
                # 其他情况强制 uint8
                data = _channel_to_uint8(arr)
                photometric = "minisblack"

            # 构建 extratags 用于添加图层名称 (TIFF tag 269 = DocumentName)
            extratags = [(269, "s", 1, name, True)]  # DocumentName tag


            kwargs = {
                "photometric": photometric,
                "compression": compression,
                "extratags": extratags,
            }

            # 仅在第一页设置分辨率和描述
            if i == 0:
                if x_res is not None:
                    kwargs["resolution"] = (x_res, y_res)
                    kwargs["resolutionunit"] = "INCH"
                kwargs["description"] = description

            tif.write(data, **kwargs)

    return output_path


# ── PSD 写入 ─────────────────────────────────────────────

def save_layered_psd(
    layers: List[Tuple[str, np.ndarray]],
    output_path: str,
    source_path: str = "",
    mode: str = "",
) -> str:
    """
    将多个图层写入分层 PSD 文件（Photoshop 真正图层面板可见）

    Args:
        layers: [(图层名, numpy数组), ...] 列表
        output_path: 输出文件路径
        source_path: 源文件路径 (用于元数据)
        mode: 分层模式名称 (用于元数据)

    Returns:
        输出文件路径
    """
    if not HAS_PYTOSHOP:
        raise ImportError(
            "PSD 输出需要 pytoshop 库。请运行: pip install pytoshop"
        )

    if not layers:
        raise ValueError("图层列表不能为空")

    # 确定画布尺寸（以第一个图层为准）
    first_name, first_arr = layers[0]
    if first_arr.ndim == 3:
        h, w = first_arr.shape[0], first_arr.shape[1]
    else:
        h, w = first_arr.shape[0], first_arr.shape[1]

    # 判断是否全部为灰度图层
    all_grayscale = all(
        arr.ndim == 2 for _, arr in layers
    )

    # 构建 PSD 图层记录
    layer_records = []
    for name, arr in layers:
        arr = _channel_to_uint8(arr)
        # 确保尺寸一致
        if arr.ndim == 2:
            if arr.shape[0] != h or arr.shape[1] != w:
                img_temp = Image.fromarray(arr)
                arr = np.array(img_temp.resize((w, h), Image.LANCZOS))
            layer_records.append(LayerRecord(
                top=0, left=0, bottom=h, right=w,
                name=name,
                channels={0: ChannelImageData(image=arr, compression=0)},
            ))
        elif arr.ndim == 3 and arr.shape[2] == 3:
            if arr.shape[0] != h or arr.shape[1] != w:
                img_temp = Image.fromarray(arr)
                arr = np.array(img_temp.resize((w, h), Image.LANCZOS))
            layer_records.append(LayerRecord(
                top=0, left=0, bottom=h, right=w,
                name=name,
                channels={
                    0: ChannelImageData(image=arr[:, :, 0], compression=0),
                    1: ChannelImageData(image=arr[:, :, 1], compression=0),
                    2: ChannelImageData(image=arr[:, :, 2], compression=0),
                },
            ))
        elif arr.ndim == 3 and arr.shape[2] == 4:
            if arr.shape[0] != h or arr.shape[1] != w:
                img_temp = Image.fromarray(arr)
                arr = np.array(img_temp.resize((w, h), Image.LANCZOS))
            # RGBA -> RGB layer + transparency mask (channel -1)
            layer_records.append(LayerRecord(
                top=0, left=0, bottom=h, right=w,
                name=name,
                channels={
                    0: ChannelImageData(image=arr[:, :, 0], compression=0),
                    1: ChannelImageData(image=arr[:, :, 1], compression=0),
                    2: ChannelImageData(image=arr[:, :, 2], compression=0),
                    -1: ChannelImageData(image=arr[:, :, 3], compression=0),
                },
            ))

    layer_info = LayerInfo(layer_records=layer_records)
    layer_and_mask = LayerAndMaskInfo(layer_info=layer_info)

    # 创建 PSD
    psd = pytoshop.PsdFile(
        version=1,
        num_channels=3 if not all_grayscale else 1,
        height=h,
        width=w,
        depth=8,
        color_mode=ColorMode.rgb if not all_grayscale else ColorMode.grayscale,
        layer_and_mask_info=layer_and_mask,
    )

    with open(output_path, 'wb') as f:
        psd.write(f)

    return output_path


# ── 单文件转换 ────────────────────────────────────────────

def convert_single(
    input_path: str,
    mode: str = "rgb",
    output_path: Optional[str] = None,
    compression: Optional[str] = "lzw",
    dpi: Optional[float] = None,
    edge_threshold: int = 30,
    output_format: str = "tiff",
) -> str:
    """
    将单个 JPG/PNG 文件转换为分层 TIFF 或 PSD

    Args:
        input_path: 输入文件路径
        mode: 分层模式 (rgb/rgba/cmyk/alpha/gray+color/hsl/lab/edge-extract)
        output_path: 输出文件路径 (默认与输入同目录，后缀改为 .tif/.psd)
        compression: 压缩方式 (none/lzw/deflate/jpeg)，仅 tiff 格式
        dpi: 目标 DPI (None 表示保留原图 DPI)，仅 tiff 格式
        edge_threshold: 边缘检测阈值 1-255 (仅 edge-extract 模式)
        output_format: 输出格式 (tiff/psd，默认 tiff)

    Returns:
        输出文件路径
    """
    input_path = os.path.abspath(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 验证模式
    if mode not in SPLITTERS:
        raise ValueError(f"不支持的模式: {mode}，可选: {', '.join(SPLITTERS.keys())}")

    # 验证格式
    output_format = output_format.lower()
    if output_format not in ("tiff", "psd"):
        raise ValueError(f"不支持的格式: {output_format}，可选: tiff, psd")

    if output_format == "psd" and not HAS_PYTOSHOP:
        raise ImportError(
            "PSD 输出需要 pytoshop 库。请运行: pip install pytoshop"
        )

    # 确定输出路径
    ext = ".tif" if output_format == "tiff" else ".psd"
    if output_path is None:
        stem = Path(input_path).stem
        parent = Path(input_path).parent
        output_path = str(parent / f"{stem}_{mode}{ext}")

    output_path = os.path.abspath(output_path)

    # 打开图片
    img = Image.open(input_path)

    # 获取 DPI
    actual_dpi = _get_dpi(img, dpi)

    # 分层
    splitter = SPLITTERS[mode]
    if mode == "edge-extract":
        layers = splitter(img, actual_dpi, threshold=edge_threshold)
    else:
        layers = splitter(img, actual_dpi)

    # 写入文件
    if output_format == "psd":
        result = save_layered_psd(
            layers=layers,
            output_path=output_path,
            source_path=input_path,
            mode=mode,
        )
    else:
        comp = COMPRESSORS.get(compression, None)
        result = save_layered_tiff(
            layers=layers,
            output_path=output_path,
            compression=comp,
            dpi=actual_dpi,
            source_path=input_path,
            mode=mode,
        )

    return result


def convert_batch(
    input_paths: List[str],
    mode: str = "rgb",
    output_dir: Optional[str] = None,
    compression: Optional[str] = "lzw",
    dpi: Optional[float] = None,
    edge_threshold: int = 30,
    output_format: str = "tiff",
) -> List[str]:
    """
    批量转换多个 JPG/PNG 文件为分层 TIFF 或 PSD

    Args:
        input_paths: 输入文件路径列表
        mode: 分层模式
        output_dir: 输出目录 (默认为每个输入文件所在目录)
        compression: 压缩方式 (仅 tiff 格式)
        dpi: 目标 DPI (仅 tiff 格式)
        edge_threshold: 边缘检测阈值 1-255 (仅 edge-extract 模式)
        output_format: 输出格式 (tiff/psd，默认 tiff)

    Returns:
        输出文件路径列表
    """
    results = []
    ext = ".tif" if output_format == "tiff" else ".psd"
    for i, path in enumerate(input_paths):
        out_path = None
        if output_dir:
            stem = Path(path).stem
            out_path = str(Path(output_dir) / f"{stem}_{mode}{ext}")

        try:
            result = convert_single(
                input_path=path,
                mode=mode,
                output_path=out_path,
                compression=compression,
                dpi=dpi,
                edge_threshold=edge_threshold,
                output_format=output_format,
            )
            results.append(result)
            print(f"  [{i+1}/{len(input_paths)}] OK {Path(path).name} -> {Path(result).name}")
        except Exception as e:
            print(f"  [{i+1}/{len(input_paths)}] FAIL {Path(path).name}: {e}")
            results.append(None)

    return [r for r in results if r is not None]


# ── CLI 入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="将 JPG/PNG 图片转换为分层 TIFF / PSD 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
分层模式说明:
  rgb           RGB 三通道分离 (R/G/B 灰度图层)
  rgba          RGBA 四通道分离 (R/G/B/A 灰度图层)
  cmyk          CMYK 四通道分离 (C/M/Y/K 灰度图层)
  alpha         彩色原图 + Alpha 透明通道
  gray+color    灰度图层 + 彩色原图 (双图层)
  hsl           HSL 三通道分离 (色相/饱和度/明度)
  lab           CIE Lab 三通道分离 (L*/a*/b*)
  edge-extract  边缘清晰图形提取 (彩色原图 + Canny边缘 + 梯度幅值 + 二值轮廓)

输出格式:
  tiff (默认)   多页 TIFF，每页一个图层
  psd           Photoshop PSD，图层在 Photoshop 图层面板中独立显示

示例:
  python img2layered_tiff.py photo.jpg --mode rgb
  python img2layered_tiff.py photo.png --mode cmyk --dpi 300 --compression lzw
  python img2layered_tiff.py *.jpg --mode alpha --output-dir ./output
  python img2layered_tiff.py photo.jpg --mode gray+color -o combined.tif
  python img2layered_tiff.py logo.png --mode edge-extract --edge-threshold 50
  python img2layered_tiff.py photo.jpg --mode rgb --format psd
  python img2layered_tiff.py logo.png --mode rgba --format psd
        """,
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        help="输入图片文件路径 (支持多个文件，支持 *.jpg / *.png 通配符)",
    )
    parser.add_argument(
        "--mode", "-m",
        default="rgb",
        choices=list(MODES.keys()),
        help="分层模式 (默认: rgb)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出文件路径 (单文件时有效，默认: {原名}_{mode}.tif)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录 (批量处理时有效)",
    )
    parser.add_argument(
        "--compression", "-c",
        default="lzw",
        choices=list(COMPRESSORS.keys()),
        help="压缩方式 (默认: lzw)",
    )
    parser.add_argument(
        "--dpi",
        type=float,
        default=None,
        help="输出 DPI (默认保留原图 DPI)",
    )
    parser.add_argument(
        "--list-modes",
        action="store_true",
        help="列出所有支持的分层模式",
    )
    parser.add_argument(
        "--edge-threshold",
        type=int,
        default=30,
        help="边缘提取阈值 1-255，越高越只提取最清晰的边缘 (默认: 30，仅 edge-extract 模式)",
    )
    parser.add_argument(
        "--format", "-f",
        default="tiff",
        choices=["tiff", "psd"],
        help="输出格式 (默认: tiff; psd 需要安装 pytoshop)",
    )

    args = parser.parse_args()

    # 解析边缘提取阈值
    edge_threshold = max(1, min(255, args.edge_threshold))

    if args.list_modes:
        print("支持的分层模式:")
        print("-" * 50)
        for key, info in MODES.items():
            layers_str = ", ".join(info["layers"])
            print(f"  {key:<12} {info['desc']}")
            print(f"  {'':12} 图层: {layers_str}")
            print()
        return

    # 校验 inputs 非空
    if not args.inputs:
        parser.error("请指定输入图片文件路径")

    # 展开通配符
    expanded_inputs = []
    for p in args.inputs:
        if "*" in p or "?" in p:
            expanded_inputs.extend(sorted(Path(".").glob(p)))
        else:
            expanded_inputs.append(Path(p))

    # 过滤有效图片
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}
    input_files = [str(p) for p in expanded_inputs if p.suffix.lower() in valid_exts]

    if not input_files:
        print("未找到有效的图片文件")
        sys.exit(1)

    # 执行转换
    output_format = args.format
    if output_format == "psd" and not HAS_PYTOSHOP:
        print("PSD 输出需要 pytoshop 库。请运行: pip install pytoshop")
        sys.exit(1)

    if len(input_files) == 1:
        print(f"转换: {input_files[0]}")
        print(f"模式: {MODES[args.mode]['desc']}")
        print(f"格式: {output_format.upper()}")
        result = convert_single(
            input_path=input_files[0],
            mode=args.mode,
            output_path=args.output,
            compression=args.compression,
            dpi=args.dpi,
            edge_threshold=edge_threshold,
            output_format=output_format,
        )
        print(f"输出: {result}")

        # 显示文件大小
        size_kb = os.path.getsize(result) / 1024
        print(f"大小: {size_kb:.1f} KB")
    else:
        print(f"批量转换 {len(input_files)} 个文件")
        print(f"模式: {MODES[args.mode]['desc']}")
        print(f"格式: {output_format.upper()}")
        results = convert_batch(
            input_paths=input_files,
            mode=args.mode,
            output_dir=args.output_dir,
            compression=args.compression,
            dpi=args.dpi,
            edge_threshold=edge_threshold,
            output_format=output_format,
        )
        print(f"\n完成: {len(results)}/{len(input_files)} 个文件成功")
        if results:
            total_kb = sum(os.path.getsize(r) for r in results) / 1024
            print(f"总大小: {total_kb:.1f} KB")


if __name__ == "__main__":
    main()
