# AI歌曲生成

用一句话灵感生成完整 AI 歌曲，支持中文流行歌、民谣、电子、品牌歌和创作者歌曲小样。

AI歌曲生成适合需要 AI song generator、AI歌曲生成、原创歌曲和中文AI写歌的创作者。输入主题、情绪、风格或一句创作想法后，AI 助手会生成完整歌曲，并返回试听、下载和项目链接；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `ai-song-generator`
- Package name: `ai-song-generator`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- AI写歌
- AI歌曲生成
- 生成歌曲
- 原创歌曲
- 一键写歌
- 中文AI写歌
- AI作曲
- 写一首歌
- AI song generator
- AI music generator
- generate song

## Use Cases

- 根据一句中文需求生成原创歌曲
- 为短视频、播客、品牌内容制作歌曲小样
- 探索副歌 hook、旋律方向和编曲风格
- 生成适合创作者内容发布的歌曲候选

## Examples

- 帮我写一首轻快的中文流行歌，主题是夏天旅行
- 写一首温暖的中文抒情歌，主题是想念
- 给一个生活方式品牌生成一首抓耳的主题歌

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "帮我写一首轻快的中文流行歌，主题是夏天旅行" --wait
node ./bin/aimv.js song create --brief "写一首温暖的中文抒情歌，主题是想念" --style mandopop --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
