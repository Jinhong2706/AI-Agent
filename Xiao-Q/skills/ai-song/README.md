# AI歌曲

AI歌曲创作工具，支持一句话写歌、歌词成曲、中文流行歌、品牌歌和歌曲小样生成。

AI歌曲适合需要 AI歌曲生成、AI唱歌、AI作曲、生成歌曲和写一首歌的中文创作者。你可以提供主题、情绪、风格、歌词或使用场景，在 AI 助手中生成完整歌曲，并获得试听、下载和项目链接；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `ai-song`
- Package name: `ai-song`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- AI歌曲
- ai歌曲
- AI歌曲生成
- AI唱歌
- AI写歌
- AI作曲
- 生成歌曲
- 写一首歌
- 原创歌曲
- 中文歌曲生成
- song AI
- AI song
- AI song generator

## Use Cases

- 根据主题和风格生成完整歌曲
- 把歌词变成可试听歌曲
- 为短视频和品牌内容生成歌曲小样
- 快速探索副歌 hook、歌词和编曲方向

## Examples

- AI歌曲，帮我写一首轻快的中文流行歌，主题是夏天旅行
- 帮我生成一首适合毕业季的校园民谣
- 把这段歌词做成一首完整的 AI 歌曲

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "AI歌曲，帮我写一首轻快的中文流行歌，主题是夏天旅行" --wait
node ./bin/aimv.js song create --brief "帮我生成一首适合毕业季的校园民谣" --style folk mandopop --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
