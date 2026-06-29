# 视频封面图生成器

[English](README.md) | 简体中文

自动生成适配各大主流视频平台的封面图。支持三种工作模式：

- **图片 + 描述**：同时提供原图与文字描述时，以原图为基础，描述内容指导 AI 扩图与装饰加工。
- **仅图片**：原图内容完整保留，因比例差异产生的留白区域由 AI 扩图技术（outpainting）自然补全。
- **仅描述**：未提供图片时，完全根据文字描述由 AI 直接生成封面图。

## 核心特性

- **多平台适配**：支持微信视频号、抖音、快手、B站、小红书等 5 大平台，共 11 种规格。
- **AI 扩图补全**：对留白区域进行内容延伸，主体完整居中保留，告别黑边与生硬裁切。
- **个性化加工**：支持通过 prompt 添加自定义文案（如标题）或装饰风格（如边框、滤镜），文案与装饰需具备社交媒体传播价值。
- **智能降级**：当 AI 扩图服务不可用时，自动降级为高斯模糊背景合成方案。

## 支持的平台与规格

| 平台 | 方向/用途 | 尺寸（宽×高）| 比例 | platform_key |
|------|----------|-------------|------|--------------|
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

> **平台说明：**
> - **微信视频号（横版）**：同时生成两种规格——3:4 个人主页卡片（`wechat_profile_card`，810×1080）、4:3 分享卡片（`wechat_share_card_horizontal`，1440×1080）。
> - **微信视频号（竖版）**：只需生成一种规格——3:4 个人主页卡片（`wechat_profile_card`，810×1080），同时用于个人主页和分享卡片。
> - **抖音**：竖版 3:4（810×1080）、横版 4:3（1440×1080）。
> - **快手**：推荐 9:16 竖版。
> - **B站**：同时生成两种尺寸——4:3 用于首页推荐封面，16:9 用于个人主页封面。
> - **小红书**：推荐比例在 3:4 至 2:1 之间。

## 使用方法

```bash
# 安装依赖
pip install pillow openai

# 生成全部平台封面
python scripts/generate_covers.py <输入图片> [输出目录]

# 微信视频号横版：个人主页卡片 + 分享卡片
python scripts/generate_covers.py <输入图片> [输出目录] \
    --platforms wechat_profile_card wechat_share_card_horizontal

# 微信视频号竖版：仅个人主页卡片（同时用于分享卡片）
python scripts/generate_covers.py <输入图片> [输出目录] \
    --platforms wechat_profile_card

# 仅生成指定平台（横版/竖版由 platform_key 区分）
python scripts/generate_covers.py <输入图片> [输出目录] \
    --platforms wechat_profile_card wechat_share_card_horizontal bilibili bilibili_profile

# 带文案和装饰描述（传递给 AI 扩图 prompt）
python scripts/generate_covers.py <输入图片> [输出目录] \
    --platforms douyin_vertical xiaohongshu_vertical \
    --text "在图片顶部添加白色标题文字'夏日旅行记'" \
    --style "添加简约白色边框装饰"

# 禁用 AI 扩图（使用模糊背景降级方案）
python scripts/generate_covers.py <输入图片> [输出目录] --no-ai
```

**参数说明：**
- `<输入图片>`：原始图片路径
- `[输出目录]`：封面图输出目录（默认为输入图片所在目录下的 `covers/` 子目录）
- `--platforms`：平台 key 列表（见上表），不填则生成全部 11 种规格
- `--text`：文案需求，描述要添加的文字内容和位置
- `--style`：装饰风格，描述边框、滤镜、氛围等视觉加工需求
- `--no-ai`：禁用 AI 扩图，改用模糊背景填充（速度更快，效果较差）

## 工作原理

1. **比例判断**：若原图与目标比例差异 ≤15%，直接等比裁剪；差异 >15% 时启用 AI 扩图。
2. **构建画布**：将原图等比缩放（contain 模式）居中放置在目标画布上，留白区域设为透明。
3. **AI 补全**：以透明区域为 mask，AI（`gpt-image-2`）根据原图风格自然延伸填充背景内容。
4. **降级处理**：API 调用失败时，以模糊处理后的原图作为背景进行合成。

## 依赖要求

- Python 3.x
- `Pillow`
- `openai`
- 配置 `OPENAI_API_KEY` 环境变量

## 目录结构

```
video-thumbnail-generator/
├── SKILL.md                  # 技能元数据与工作流指令
├── scripts/
│   └── generate_covers.py    # 核心处理脚本
├── README.md                 # 英文文档
└── README_CN.md              # 中文文档
```
