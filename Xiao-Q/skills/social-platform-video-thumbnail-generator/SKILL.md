---
name: video-thumbnail-generator
description: Generate video cover images for WeChat Video, Douyin, Kuaishou, Bilibili, and Xiaohongshu using AI
---

# 视频封面图生成

## 平台规格速查

| 平台 | 用途 | 尺寸（宽×高）| 比例 | platform_key |
|------|------|-------------|------|--------------|
| 微信视频号（横版）| 个人主页卡片 | 810×1080 | 3:4 | `wechat_profile_card` |
| 微信视频号（横版）| 分享卡片 | 1440×1080 | 4:3 | `wechat_share_card_horizontal` |
| 微信视频号（竖版）| 个人主页卡片 & 分享卡片 | 810×1080 | 3:4 | `wechat_profile_card` |
| 抖音 | 竖版 | 810×1080 | 3:4 | `douyin_vertical` |
| 抖音 | 横版 | 1440×1080 | 4:3 | `douyin_horizontal` |
| 快手 | 竖版 | 1080×1920 | 9:16 | `kuaishou_vertical` |
| 快手 | 横版 | 1920×1080 | 16:9 | `kuaishou_horizontal` |
| B站 | 首页推荐封面 | 1280×960 | 4:3 | `bilibili` |
| B站 | 个人主页封面 | 1920×1080 | 16:9 | `bilibili_profile` |
| 小红书 | 竖版 | 1080×1440 | 3:4 | `xiaohongshu_vertical` |
| 小红书 | 横版 | 1440×1080 | 4:3 | `xiaohongshu_horizontal` |

> 小红书官方推荐上传比例在 3:4 至 2:1 之间。

> **微信视频号横版**：默认同时生成个人主页卡片（3:4，`wechat_profile_card`）和分享卡片（4:3，`wechat_share_card_horizontal`）两张图片。

> **微信视频号竖版**：只需生成一张 3:4 的个人主页卡片（`wechat_profile_card`），同时用于个人主页和分享卡片。

> **B站**：选择B站平台时，默认同时生成首页推荐封面（4:3）和个人主页封面（16:9）两张图片。

## 工作流程

### 第一步：确认生成参数（必须）

收到图片后，**若用户未明确说明需要哪些平台或横/竖版方向**，须先向用户确认以下信息，再开始生成：

1. **目标平台**：需要哪些平台的封面？（微信视频号 / 抖音 / 快手 / B站 / 小红书，或全部）
2. **横版还是竖版**：每个平台需要横版还是竖版？（若平台只有一种方向则无需确认）
3. **文案/装饰**（可选）：是否需要在封面上添加文字、标题、装饰元素等？

示例确认问题：
> 请问您需要生成哪些平台的封面图？需要横版还是竖版？是否需要添加文案或装饰？

若用户已明确说明所有信息，可直接进入第二步。

**微信视频号特别说明**：
- **横版**：默认同时生成以下两种规格，无需额外确认：
  - 个人主页卡片（`wechat_profile_card`，810×1080，3:4）
  - 分享卡片（`wechat_share_card_horizontal`，1440×1080，4:3）
- **竖版**：只生成一种规格，同时用于个人主页和分享卡片：
  - 个人主页卡片（`wechat_profile_card`，810×1080，3:4）

**B站特别说明**：用户选择B站时，默认同时生成以下两种规格，无需额外确认：
- 首页推荐封面（`bilibili`，1280×960，4:3）
- 个人主页封面（`bilibili_profile`，1920×1080，16:9）

### 第二步：运行脚本

```bash
# 生成全部平台封面
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir>

# 仅生成指定平台（横版/竖版由 platform_key 区分）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> \
    --platforms wechat_profile_card douyin_vertical bilibili bilibili_profile

# 生成微信视频号横版全部两种规格（个人主页卡片+分享卡片）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> \
    --platforms wechat_profile_card wechat_share_card_horizontal

# 生成微信视频号竖版（个人主页卡片，同时用于分享卡片）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> \
    --platforms wechat_profile_card

# 生成B站全部两种规格（首页推荐封面+个人主页封面）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> \
    --platforms bilibili bilibili_profile

# 带文案和装饰描述（传递给 AI 扩图 prompt）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> \
    --platforms douyin_vertical xiaohongshu_vertical \
    --text "在图片顶部添加白色标题文字'夏日旅行记'" \
    --style "添加简约白色边框装饰"

# 禁用 AI 扩图（使用模糊背景降级方案）
python3 <skill_dir>/scripts/generate_covers.py \
    <input_image_path> <output_dir> --no-ai
```

**参数说明：**
- `<skill_dir>`：本技能所在目录的路径
- `<input_image_path>`：输入图片的路径
- `<output_dir>`：输出目录，建议使用 `<input_dir>/covers/`
- `--platforms`：平台 key 列表（见上表），不填则生成全部 11 种
- `--text`：文案需求，描述要添加的文字内容和位置
- `--style`：装饰风格，描述边框、滤镜、氛围等视觉加工需求
- `--no-ai`：禁用 AI 扩图，改用模糊背景填充（速度更快，效果较差）

### 第三步：交付结果

将生成的全部封面图作为附件发送给用户，并说明每张图对应的平台、方向和尺寸。

## AI 扩图策略

脚本采用 **OpenAI gpt-image-2 outpainting** 实现留白区域的 AI 补全：

1. **判断是否需要扩图**：若原图比例与目标比例差异 ≤15%，直接等比裁剪（无需扩图）；差异 >15% 时启用 AI 扩图。
2. **构建画布**：将原图等比缩放（contain 模式）居中放置在目标尺寸画布上，留白区域设为透明。
3. **AI 补全**：调用 `images.edit` API（模型：`gpt-image-2`），以透明区域为 mask，让 AI 根据原图风格自然延伸背景内容。
4. **降级方案**：若 AI 扩图失败（如网络错误、API 不可用），自动降级为模糊背景填充。

## 文案与装饰加工

通过 `--text` 和 `--style` 参数将加工需求传递给 AI 扩图 prompt：

- `--text`：描述文字内容、位置、颜色，如 `"在底部添加白色半透明标题'城市漫步'"`
- `--style`：描述视觉风格，如 `"添加电影感暗角效果"` 或 `"添加简约几何边框"`

**社交媒体传播价值要求**：添加文案或装饰时，须确保封面具备社交媒体传播价值，包括但不限于：
- 标题文案简洁有力、能引发点击欲望
- 视觉设计风格与平台调性匹配（如抖音偏动感、小红书偏精致生活）
- 色彩对比鲜明、主体突出，在信息流中具备视觉吸引力
- 避免过度堆砌文字或装饰，保持封面整洁易读

> 注意：文案和装饰由 AI 在扩图时一并生成，效果取决于 AI 理解能力，复杂排版建议后期用图像编辑工具精调。

## 注意事项

- 输出格式为 JPEG，quality=95，适合平台上传
- AI 扩图需要 `OPENAI_API_KEY` 环境变量
- 依赖：`Pillow`、`openai`（`pip install pillow openai`）
