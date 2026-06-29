---
name: create-image-by-html
description: 当用户说"画一张图"、"生成配图"、"做个信息图"时，将 HTML 设计稿渲染成 PNG 图片输出。触发词：画图、生成图片、配图、信息图、设计图、HTML转PNG、导出图片。
---

# html-to-image

将精美的 HTML 设计稿通过 Playwright 浏览器截图，输出为 PNG 图片。

## 工作流程

用户说「画一张图」或类似表达时，激活此 Skill：

**Step 1 — 理解需求**
- 与用户确认图的类型（表格、架构图、流程图、对比表、封面等）
- 确认风格偏好（如果有的话）
- 确认输出尺寸

**Step 2 — 创建 HTML 文件**
- 根据需求设计 HTML + CSS，写入 `docs/` 或用户指定路径
- 使用精美现代的 CSS 样式
- 中文使用 `-apple-system, "PingFang SC", "Microsoft YaHei"` 字体栈
- 包含 `.container` 包裹层用于精确定位截图区域

**Step 3 — 渲染 PNG**
- 调用 `scripts/render.py` 脚本
- 使用 Playwright 打开 HTML 文件
- 截取 `.container` 区域，输出 PNG 到同目录下

**最佳实践 — 手动截图命令（当 render.py 不可用时）**
```bash
CHROME="~/Library/Caches/ms-playwright/chromium-1208/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
"$CHROME" --headless --disable-gpu \
  --screenshot=output.png \
  --window-size=1200,1500 \
  --hide-scrollbars \
  "file:///path/to/file.html"
```
- `--window-size`：视口大小，宽度建议 1200px，高度需根据内容动态调整
- **高度调优经验**：先预估内容高度（一般架构图 1400-1600px，流程图 1000-1200px），截完图检查底部是否完整，逐步微调
- `--hide-scrollbars`：确保无滚动条干扰

**Step 4 — 展示结果**
- 用 `open_result_view` 展示生成的 PNG
- 告知用户 HTML 源文件路径（便于后续调整）

**Step 5 — 迭代优化（如有反馈）**
常见问题快速修复：
| 问题 | 解决方案 |
|------|---------|
| 内容不居中 | `body { display: flex; justify-content: center; }` + `.container { margin: 0 auto; }` |
| 底部文字截断 | 调高 `--window-size` 高度（每次 +100px 试） |
| 底部留白太多 | 调低 `--window-size` 高度，或检查 HTML 内容实际占用空间 |
| 需要全页截图 | 使用 `--window-size` 配合内容实际高度，而非固定大数值 |

## 截图脚本用法

```bash
python3 scripts/render.py <html文件路径> [--output <输出PNG路径>] [--wait <等待ms>] [--scale <2>]
```

- `--output`：输出 PNG 路径，默认与 HTML 同名但扩展名为 `.png`
- `--wait`：等待渲染时间（毫秒），默认 300ms
- `--scale`：设备像素比，默认 2（Retina 高清）

## 设计规范

**风格**：蓝色科技风（浅蓝背景 #F0F4FF，白色卡片，圆角，柔和阴影）
**字体**：-apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial
**标题**：22px，#1E3A5F，深蓝色，bold
**正文**：13-14px，#2D4060
**辅助文字**：11-12px，#8CA0C0
**圆角卡片**：`border-radius: 14-20px; box-shadow: 0 4-8px rgba(59,130,246,0.10)`
**间距**：`padding: 40px 48px`，外边距 24px

## 常见图类型模板

### 表格图
- 浅色表头 `#EEF4FF`，蓝色文字
- 斑马纹行（hover 高亮 `#F8FAFF`）
- 高亮行（推荐项）用暖色背景 `#FFF9F0`
- 单元格标签用彩色徽章样式

### 架构图
- 节点用彩色渐变图标圆角卡片
- 箭头用 CSS 伪元素或 flex 布局
- 底部加图例说明

### 流程图
- 横向 5 列布局，每列一个步骤卡片
- 统一 `min-height` 确保对齐
- 连接线用渐变色箭头
- 底部加提示说明框

### 对比表
- 三栏并排对比
- ✅❌⚠️ 符号突出显示
- 优势项用绿色背景高亮整行
