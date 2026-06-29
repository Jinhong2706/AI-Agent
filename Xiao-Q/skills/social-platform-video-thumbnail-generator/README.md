# Video Thumbnail Generator
English | [简体中文](README_CN.md)

Automatically generate video thumbnail images for major Chinese video platforms. Three working modes are supported:

- **Image + Description**: When a source image is provided along with a text description, the image is used as the base and the description guides AI outpainting and decoration.
- **Image only**: The source image is preserved in full; blank areas introduced by aspect ratio differences are seamlessly filled using AI outpainting.
- **Description only**: When no image is provided, thumbnails are generated entirely from the text description using AI image generation.

## Features

- **Multi-Platform Support**: Generates thumbnails for WeChat Video, Douyin, Kuaishou, Bilibili, and Xiaohongshu (RED) — 11 specifications across various orientations and usages.
- **AI Outpainting**: Naturally extends the background into blank areas, keeping the original subject intact and centered. No black bars, no awkward cropping.
- **Customization**: Pass text or decoration requirements as prompts (e.g., add a title, apply a border style) to be applied during AI generation. All text and decoration must serve social media engagement value.
- **Graceful Fallback**: If the AI service is unavailable, automatically falls back to a Gaussian blur background composite.

## Supported Platforms & Specifications

| Platform | Orientation / Usage | Size (W×H) | Ratio | `platform_key` |
|----------|---------------------|------------|-------|----------------|
| WeChat Video (Horizontal) | Profile Card | 810×1080 | 3:4 | `wechat_profile_card` |
| WeChat Video (Horizontal) | Share Card | 1440×1080 | 4:3 | `wechat_share_card_horizontal` |
| WeChat Video (Vertical) | Profile Card & Share Card | 810×1080 | 3:4 | `wechat_profile_card` |
| Douyin | Vertical | 810×1080 | 3:4 | `douyin_vertical` |
| Douyin | Horizontal | 1440×1080 | 4:3 | `douyin_horizontal` |
| Kuaishou | Vertical | 1080×1920 | 9:16 | `kuaishou_vertical` |
| Kuaishou | Horizontal | 1920×1080 | 16:9 | `kuaishou_horizontal` |
| Bilibili | Homepage Recommended Cover | 1280×960 | 4:3 | `bilibili` |
| Bilibili | Profile Page Cover | 1920×1080 | 16:9 | `bilibili_profile` |
| Xiaohongshu | Vertical | 1080×1440 | 3:4 | `xiaohongshu_vertical` |
| Xiaohongshu | Horizontal | 1440×1080 | 4:3 | `xiaohongshu_horizontal` |

> **Platform Notes:**
> - **WeChat Video (Horizontal)**: Two sizes generated simultaneously — 3:4 profile card (`wechat_profile_card`, 810×1080) and 4:3 share card (`wechat_share_card_horizontal`, 1440×1080).
> - **WeChat Video (Vertical)**: Only one size needed — 3:4 profile card (`wechat_profile_card`, 810×1080), used for both profile and share card.
> - **Douyin**: Vertical 3:4 (810×1080), Horizontal 4:3 (1440×1080).
> - **Kuaishou**: Recommended 9:16 vertical.
> - **Bilibili**: Two sizes generated simultaneously — 4:3 for homepage recommended cover, 16:9 for profile page cover.
> - **Xiaohongshu**: Recommended ratio between 3:4 and 2:1.

## Usage

```bash
# Install dependencies
pip install pillow openai

# Generate thumbnails for all platforms
python scripts/generate_covers.py <input_image> [output_dir]

# WeChat Video horizontal: profile card + share card
python scripts/generate_covers.py <input_image> [output_dir] \
    --platforms wechat_profile_card wechat_share_card_horizontal

# WeChat Video vertical: profile card only (also used as share card)
python scripts/generate_covers.py <input_image> [output_dir] \
    --platforms wechat_profile_card

# Generate thumbnails for specific platforms
python scripts/generate_covers.py <input_image> [output_dir] \
    --platforms wechat_profile_card wechat_share_card_horizontal bilibili bilibili_profile

# Add text and decoration via AI prompt
python scripts/generate_covers.py <input_image> [output_dir] \
    --platforms douyin_vertical xiaohongshu_vertical \
    --text "Add a white title 'Summer Travel' at the top" \
    --style "Add a minimal white border"

# Disable AI outpainting (use blur background fallback)
python scripts/generate_covers.py <input_image> [output_dir] --no-ai
```

**Arguments:**
- `<input_image>`: Path to the source image
- `[output_dir]`: Output directory (defaults to `covers/` next to the input file)
- `--platforms`: One or more `platform_key` values; omit to generate all 11
- `--text`: Text content and placement description for AI to render
- `--style`: Visual decoration description (border, filter, vignette, etc.)
- `--no-ai`: Skip AI outpainting; use Gaussian blur background instead

## How It Works

1. **Ratio check**: If the aspect ratio difference between source and target is ≤15%, the image is proportionally cropped. Otherwise, AI outpainting is used.
2. **Canvas build**: The source image is scaled to fit (contain) and centered on the target canvas; blank areas are set to transparent.
3. **AI fill**: The transparent areas are filled by AI (`gpt-image-2`) with contextually consistent content matching the original style.
4. **Fallback**: On API failure, a blurred and dimmed version of the source image is used as the background.

## Requirements

- Python 3.x
- `Pillow`
- `openai`
- Corresponding API key environment variable configured

## Directory Structure

```
video-thumbnail-generator/
├── SKILL.md                  # Skill metadata and workflow instructions
├── scripts/
│   └── generate_covers.py    # Core processing script
├── README.md                 # English documentation
└── README_CN.md              # Chinese documentation
```
