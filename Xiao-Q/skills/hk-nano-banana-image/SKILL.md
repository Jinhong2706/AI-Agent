---
name: hk-nano-banana-image
description: "Google nano-banana image generation via OpenAI-HK API. Use for: 生成图片, 画一张图, 文生图, 图生图, 以图生图, 编辑图片, 根据图片生成, image generation."
---

# Nano-Banana Image Generation (OpenAI-HK)

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
    "model": "nano-banana",
    "prompt": "your prompt in Chinese or English",
    "n": 1,
    "size": "16:9"
  }'

# Image-to-image (multipart form)
curl -X POST https://api.openai-hk.com/v1/images/edits \
  -H "Authorization: Bearer hk-$API_KEY" \
  -F "model=nano-banana" \
  -F "image[]=@input.png" \
  -F "prompt=your edit prompt"
```

## Available Models

| Model | Description | Quality |
|-------|-------------|---------|
| `nano-banana` | Standard | low/standard |
| `nano-banana-hd` | HD, 4K output | high |
| `nano-banana-2` | V2 model | standard |
| `nano-banana-2-2k` | V2 2K | high |
| `nano-banana-2-4k` | V2 4K | ultra |
| `gemini-3.1-flash-image-preview` | Gemini based | standard |
| `gemini-3.1-flash-image-preview-2k` | Gemini 2K | high |
| `gemini-3.1-flash-image-preview-4k` | Gemini 4K | ultra |

## Aspect Ratios

- `16:9` - Landscape (cinematic)
- `9:16` - Portrait (mobile/poster)
- `4:3` - Standard
- `3:4` - Portrait standard
- `2:3` - Portrait
- `3:2` - Landscape

## Image Generation Script

```bash
# Text-to-image
python3 /root/.openclaw/workspace/skills/hk-nano-banana-image/scripts/generate_image.py \
  --api-key "hk-xxx" \
  --prompt "一只橘猫在窗台上晒太阳" \
  --model nano-banana \
  --size 16:9 \
  --output "/root/.openclaw/media/images/$(date +%Y-%m-%d)-$RANDOM.png"

# Image-to-image
python3 /root/.openclaw/workspace/skills/hk-nano-banana-image/scripts/generate_image.py \
  --api-key "hk-xxx" \
  --prompt "把这只猫变成蓝色" \
  --input-image /path/to/cat.png \
  --output "/root/.openclaw/media/images/$(date +%Y-%m-%d)-$RANDOM.png"
```

## Workflows

### Text-to-Image (文生图)
1. User provides prompt
2. Choose model (default: `nano-banana`) and size (default: `16:9`)
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
- Max reference images for edit: 2
- For best quality, use `nano-banana-hd` or `nano-banana-2-4k`
