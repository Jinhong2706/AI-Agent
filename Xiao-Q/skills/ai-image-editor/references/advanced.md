# 高级用法参考

## 依赖安装

```bash
# 基础依赖
pip install Pillow opencv-python numpy

# 智能抠图（换背景推荐）
pip install rembg
# rembg 首次运行会自动下载模型 (~150MB)

# 高质量去水印（OpenCV inpaint）
pip install opencv-python
```

## OpenCV 去水印（比简单版效果好）

```python
import cv2
import numpy as np

def opencv_inpaint(img_path, mask_path, output_path):
    img = cv2.imread(img_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    # 膨胀 mask 让边缘更自然
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    cv2.imwrite(output_path, result)
    print(f"OpenCV inpaint 完成: {output_path}")
```

在 `scripts/inpaint.py` 中可加入此函数作为可选路径：
- 检测到 `cv2` 可用时优先用 `cv2.inpaint`
- 否则回退到简单中值模糊方案

## rembg 智能抠图（换背景推荐）

```python
from rembg import remove
from PIL import Image

def smart_remove_bg(input_path, output_path):
    img = Image.open(input_path)
    result = remove(img)  # 自动生成 RGBA 带透明通道
    result.save(output_path)
    print(f"rembg 抠图完成: {output_path}")
```

`scripts/change_bg.py` 已集成此逻辑，安装 `rembg` 后自动启用。

## Stable Diffusion AI 扩图（真实 AI 效果）

需要本地运行或 API 调用 Stable Diffusion + Inpainting 模型：

```python
# 伪代码示例，实际需要 diffusers 库 + GPU
from diffusers import StableDiffusionInpaintPipeline
import torch

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-inpainting",
    torch_dtype=torch.float16
).to("cuda")

# 将扩展区域作为 mask，原图作为 init_image
result = pipe(
    prompt="high quality, seamless background extension",
    image=init_image,
    mask_image=mask_image,
).images[0]
```

当前 `scripts/outpaint.py` 为轻量镜像填充实现，
如需真实 AI 效果，可接入上述方案或调用在线 API。

## 批量处理

```bash
# 批量调亮所有 jpg
for f in *.jpg; do
  python scripts/adjust_basic.py \
    --input "$f" \
    --output "bright_$f" \
    --brightness 25
done
```

## 常见图片格式支持

Pillow 支持：JPG / PNG / WEBP / BMP / GIF
输出统一保存为 JPG（quality=95），如需透明背景请改为 PNG。
