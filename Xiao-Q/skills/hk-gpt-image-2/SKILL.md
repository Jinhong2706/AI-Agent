---
name: hk-gpt-image-2
description: "HK gpt-image-2 image generation via OpenAI-HK API. Use for: hk生成图片, hk画图, hk文生图, hk图生图, gpt画图, GPT图片, or any hk image generation request."
---

# GPT-Image-2 Image Generation (OpenAI-HK)

## API Configuration

- **Base URL**: `https://api.openai-hk.com`
- **Auth**: `Bearer hk-{API_KEY}`
- **Endpoints**:
  - Text-to-image: `POST /v1/images/generations`
  - Image-to-image: `POST /v1/images/edits`

## Quick Start

```bash
# Text-to-image
curl https://api.openai-hk.com/v1/images/generations \
  -H "Authorization: Bearer hk-$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "your prompt",
    "n": 1,
    "size": "1024x1024",
    "quality": "low"
  }'
```

## Available Models

| Model | Description |
|-------|-------------|
| `gpt-image-2` | Latest GPT image generation v2 |
| `gpt-image-1.5` | Previous version |
| `gpt-image-1` | Original GPT image |

## Quality Options

| Quality | Description | Approx Cost |
|---------|-------------|--------------|
| `low` | Fast, ~800 credits (1024x1024) | 800 积分 |
| `medium` | Balanced, ~3000 credits | 3000 积分 |
| `high` | Maximum quality | Higher |
| `auto` | Model decides (default) | - |

## Size Options

### Square
- `1024x1024` (1K)
- `2048x2048` (2K)
- `2880x2880` (4K)

### Widescreen 16:9
- `1280x720` (1K)
- `2048x1152` (2K)
- `3840x2160` (4K)

### Story 9:16
- `720x1280` (1K)
- `1152x2048` (2K)
- `2160x3840` (4K)

### Other Ratios
- `5:4`, `4:5`, `4:3`, `3:4`, `3:2`, `2:3`, `21:9`

## Image Generation Script

```bash
# Text-to-image
python3 /root/.openclaw/workspace/skills/hk-gpt-image-2/scripts/generate_image.py \
  --api-key "hk-xxx" \
  --prompt "一只可爱的橘猫" \
  --model gpt-image-2 \
  --size 1024x1024 \
  --quality low \
  --output "/root/.openclaw/media/images/$(date +%Y-%m-%d)-$RANDOM.png"

# Image-to-image (edit)
python3 /root/.openclaw/workspace/skills/hk-gpt-image-2/scripts/generate_image.py \
  --api-key "hk-xxx" \
  --prompt "把这只猫变成蓝色" \
  --input-image /path/to/cat.png \
  --output "/root/.openclaw/media/images/$(date +%Y-%m-%d)-$RANDOM.png"
```

## Workflows

### Text-to-Image (文生图)
1. User provides prompt
2. Choose model (default: `gpt-image-2`), size (default: `1024x1024`), quality (default: `low`)
3. Call `/v1/images/generations`
4. Download and save image to `/root/.openclaw/media/images/`
5. Deliver to user

### Image-to-Image (图生图)
1. User provides reference image(s) and prompt
2. Call `/v1/images/edits` with multipart form
3. Download and save result
4. Deliver to user

## Notes

- Default output directory: `/root/.openclaw/media/images/`
- Filename format: `YYYY-MM-DD-RANDOM.png`
- Max reference images for edit: Multiple (no strict limit)
- For best quality, use `quality: high` but costs more credits
- Response format supports both `url` (default) and `b64_json`