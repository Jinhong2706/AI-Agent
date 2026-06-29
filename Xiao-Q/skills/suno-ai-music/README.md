# Suno AI音乐生成

面向中文创作者的 Suno AI音乐生成工具，支持 AI写歌、歌词成曲、BGM 和参考音频改编。

Suno AI音乐生成适合想用中文完成 Suno AI音乐、Suno AI写歌、中文 Suno、Suno 替代和 AI音乐生成的创作者。音乐生成能力由 Suno 提供；你可以在 AI 助手中输入歌曲主题、歌词、风格、BGM 场景或参考音频，生成可试听、可下载的音乐作品。作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `suno-ai-music`
- Package name: `suno-ai-music`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- suno
- suno ai音乐
- Suno AI音乐
- suno ai写歌
- suno中文
- 中文suno
- suno替代
- suno音乐生成
- suno歌曲生成
- AI写歌
- AI音乐生成
- 歌词成曲

## Use Cases

- 用中文完成 Suno AI音乐风格的歌曲、歌词成曲或 BGM 创作
- 用中文 prompt 生成歌曲、歌词成曲或 BGM
- 为短视频、品牌内容和创作者内容生成音乐
- 基于参考音频或已有项目继续创作

## Examples

- 用 Suno AI音乐帮我写一首中文流行歌，主题是夏天旅行
- 我想找 Suno 替代，帮我把这段歌词生成歌曲
- 用类似 Suno 的方式生成一段适合短视频的 BGM

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "用 Suno AI音乐帮我写一首中文流行歌，主题是夏天旅行" --wait
node ./bin/aimv.js bgm create --brief "用类似 Suno 的方式生成一段适合短视频的 BGM" --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
