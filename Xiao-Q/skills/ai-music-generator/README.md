# AI音乐生成器

AI音乐生成器，把中文创意、歌词、风格和场景描述生成歌曲、BGM 与可下载音频。

AI音乐生成器适合需要 AI music generator、音乐生成器、AI生成音乐和 BGM生成器的中文创作者。你可以输入一句创作想法、完整歌词、视频场景或品牌需求，在 AI 助手中生成歌曲、背景音乐、试听链接和音频下载；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `ai-music-generator`
- Package name: `ai-music-generator`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- AI音乐生成器
- ai音乐生成器
- AI music generator
- music generator
- 音乐生成器
- AI生成音乐
- AI音乐生成
- 生成音乐工具
- AI作曲生成器
- AI写歌生成器
- BGM生成器
- 背景音乐生成器

## Use Cases

- 把一句创意需求生成可试听音乐
- 根据歌词生成完整歌曲
- 为视频、广告、播客和游戏内容生成 BGM
- 快速生成多个音乐方向供创作者筛选

## Examples

- AI音乐生成器，帮我生成一首适合旅行 vlog 的中文歌
- 用音乐生成器把这段歌词做成完整歌曲
- 生成一段适合咖啡品牌广告的轻松 BGM

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "AI音乐生成器，帮我生成一首适合旅行 vlog 的中文歌" --wait
node ./bin/aimv.js bgm create --brief "生成一段适合咖啡品牌广告的轻松 BGM" --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
