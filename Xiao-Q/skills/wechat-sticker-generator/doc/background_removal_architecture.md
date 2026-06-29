# 背景去除技术架构文档

本文档详细说明本项目的背景去除系统架构、算法原理、参数配置及最佳实践。

---

## 一、技术方案概览

本项目实现了**三轨背景去除系统**，支持灵活切换：

| 方法 | 处理粒度 | 原理 | 适用场景 |
|------|---------|------|---------|
| `opencv` | 整图处理 | 漫水填充 + Soft Alpha | 纯白背景 + 深色前景 |
| `rembg` | 单格处理 | 深度学习语义分割 | 复杂背景兜底 |
| **`dual`** (推荐) | 双通道合并 | max(opencv, rembg) | 水墨/水彩/像素/Q版等浅色前景 |

---

## 二、算法原理详解

### 2.1 OpenCV 方案 (FloodFill + Soft Alpha Matte + Unblend)

**核心原理**：基于连通域颜色相似性与颜色距离计算。

1. **背景识别**：从图像边缘种子点出发，使用 `cv2.floodFill`（漫水填充）寻找与种子点颜色相似的连通区域。通过 `loDiff/upDiff`（颜色容差）确定背景像素。

2. **抗锯齿保留 (Soft Alpha)**：计算边缘像素到纯白色的"颜色距离"，距离纯白越近，Alpha 越低，实现平滑过渡。

3. **反向混合去白边 (Unblend)**：通过逆向 Alpha 混合公式剥离像素中的白雾：
   ```
   前景色 = (混合色 - (1 - alpha)) / alpha
   ```

4. **低透明度噪声过滤**：`Alpha < 10` 强制归零，消除不可见噪点。

**优势**：
- ✅ 极致的边缘质量（文字描边、毛发、半透明阴影无锯齿）
- ✅ 计算极快（CPU 秒级完成）
- ✅ 绝对稳定（无 AI 幻觉）

**劣势**：
- ❌ 强依赖纯白背景
- ❌ 浅色前景（水墨、淡彩、浅色皮肤）可能被误删
- ❌ 主体穿孔风险（纯白衣服贴边会被误删）

**参数**：
```python
lo_diff=10   # 下限颜色容差（越小越严格）
up_diff=10   # 上限颜色容差
```

---

### 2.2 Rembg 方案 (U-Net / ISNet 显著性目标检测)

**核心原理**：基于深度学习的语义分割 (Semantic Segmentation)。

- 使用 `isnet-anime` 或 `u2net` 等模型
- 通过理解画面"语义"生成概率图（Alpha 通道）
- 概率高的区域保留，概率低的区域丢弃

**优势**：
- ✅ 极高的鲁棒性（无视背景复杂度）
- ✅ 语义级保护（白色衣服不会被删）

**劣势**：
- ❌ 边缘硬伤（细小文字可能被切掉）
- ❌ 性能消耗大（依赖 GPU 加速）
- ❌ 可能误删表情包文字

**参数**：
```python
model_name="isnet-anime"  # 模型选择
alpha_matting=True        # 边缘后处理
```

**可选模型**：
| 模型 | 特点 |
|------|------|
| `isnet-anime` | 动漫风格（默认推荐） |
| `isnet-general-use` | 通用场景 |
| `u2net` | 高精度通用 |
| `u2netp` | 轻量级快速 |

---

### 2.3 Dual 方案 (双通道 Alpha 合并) ⭐ 推荐

**核心原理**：同时运行 OpenCV 和 Rembg，取两者 Alpha 的最大值。

```
final_alpha = max(alpha_opencv, alpha_rembg)
```

**工作流程**：
1. OpenCV 处理一遍（保护文字）
2. Rembg 处理一遍（保护浅色前景）
3. 取两者 Alpha 最大值
4. 任一失败时自动回退到另一个

**为什么有效**：

| 区域 | OpenCV Alpha | Rembg Alpha | 最终 Alpha |
|------|-------------|-------------|-----------|
| 水墨/淡彩 | ≈ 0 (误删) | ≈ 255 (保留) | **255** ✅ |
| 文字 | ≈ 255 (保留) | ≈ 0 (误删) | **255** ✅ |
| 纯白背景 | ≈ 0 | ≈ 0 | **0** ✅ |
| 深色主体 | ≈ 255 | ≈ 255 | **255** ✅ |

**优势**：
- ✅ 同时保护浅色前景和文字
- ✅ 自动容灾（单路失败不影响结果）
- ✅ 适用于水墨风、水彩风、像素风、Q版等

**劣势**：
- ⚠️ 性能消耗最大（运行两遍）
- ⚠️ 极端情况（白色角色+白色背景）仍需人工干预

---

## 三、处理粒度说明

### 3.1 OpenCV 模式：整图处理

对**完整的宫格大图**一次性处理。

**原因**：
- 保证所有表情的边缘裁剪规则完全一致
- 减少 GIF 边缘闪烁问题

**前置检测**：
```python
is_mostly_white_background(img, threshold=245)
```
检测四角 20×20 区域均值，低于阈值则判定非纯白背景。

### 3.2 Rembg 模式：单格处理

先切分为多张小图，再分别处理。

**原因**：
- Rembg 在单张小图上准确率最高
- 大图多目标会导致模型注意力分散

### 3.3 Dual 模式：单格处理

继承 Rembg 的单格处理粒度。

---

## 四、参数配置

### 4.1 完整参数结构

```json
{
  "background_type": "transparent",
  "enable_bg_removal": true,
  "bg_removal_method": "dual",
  "bg_removal_model": "isnet-anime",
  "bg_alpha_matting": true,
  "feather_edges": true,
  "feather_radius": 1.5,
  "sharpen_edges": false,
  "sharpen_threshold": 200
}
```

### 4.2 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `background_type` | string | `transparent` | 背景类型：`transparent` 或 `white` |
| `enable_bg_removal` | bool | `true` | 是否启用去背景 |
| `bg_removal_method` | string | `dual` | 算法：`opencv` / `rembg` / `dual` / `script` |
| `bg_removal_model` | string | `isnet-anime` | Rembg 模型 |
| `bg_alpha_matting` | bool | `true` | Rembg 边缘后处理 |
| `feather_edges` | bool | `true` | **边缘羽化**：平滑 Alpha 边缘，减少 GIF 锯齿 |
| `feather_radius` | float | `1.5` | 羽化半径（越大越柔和） |
| `sharpen_edges` | bool | `false` | 是否锐化边缘 |
| `sharpen_threshold` | int | `200` | 锐化阈值 |

### 4.3 方法选择指南

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 水墨风 (CHINESE_INK) | `dual` | 保护淡墨+文字 |
| 水彩风 (WATERCOLOR) | `dual` | 保护淡彩+文字 |
| 像素风 (PIXEL_ART) | `dual` | 保护浅色像素+文字 |
| Q版浅色皮肤 | `dual` | 保护浅色皮肤+文字 |
| 2D_KAWAII 深色角色 | `opencv` | 边缘质量最优 |
| MEME_STYLE | `opencv` | 文字保护最优 |
| 复杂背景 | `rembg` | 兜底方案 |

---

## 五、容灾与降级机制

### 5.1 OpenCV 降级

```
OpenCV 失败 (非纯白背景)
    ↓
自动回退到 Rembg 单格处理
```

### 5.2 Dual 容灾

```
OpenCV 失败 → 仅使用 Rembg 结果
Rembg 失败 → 仅使用 OpenCV 结果
两者都失败 → 保留原图
```

### 5.3 Alpha 清洗

所有处理完成后，强制 `Alpha < 10` 归零，防止 GIF 杂色噪点。

### 5.4 边缘羽化 (Edge Feathering)

**问题**：GIF 格式只支持 1-bit 透明度，半透明像素会被强制转为透明或不透明，导致边缘锯齿。

**解决方案**：对 Alpha 边缘做高斯模糊平滑过渡。

```
原始 Alpha:  0 | 50 | 128 | 200 | 255  (锯齿边缘)
羽化后:      0 | 30 | 100 | 180 | 255  (平滑过渡)
```

**参数**：
- `feather_edges`: 是否启用（默认 `true`）
- `feather_radius`: 羽化半径（默认 `1.5`，越大越柔和）

---

## 六、依赖安装

```bash
# 必需
pip install opencv-python numpy pillow

# Rembg 支持（推荐）
pip install rembg

# ONNX Runtime（如果报错）
pip install onnxruntime
```

---

## 七、最佳实践

1. **默认使用 `dual` 方法**：平衡质量与鲁棒性
2. **极端情况人工干预**：白色角色+白色背景请使用白底原图
3. **检查 `original_grid_nobg.png`**：预览去背景效果
4. **关注终端日志**：`[!]` 开头为警告，`[*]` 开头为信息

---

## 八、代码位置

| 文件 | 功能 |
|------|------|
| `modules/background.py` | 统一接口与 dual 实现 |
| `modules/bg_opencv.py` | OpenCV 算法实现 |
| `modules/postprocess.py` | 宫格切分与 GIF 合成 |

---

## 九、更新历史

- **2026-03-23**: 新增 `dual` 双通道方案，解决水墨/水彩浅色被删问题
- **2026-03-22**: 初始双轨架构（opencv + rembg）