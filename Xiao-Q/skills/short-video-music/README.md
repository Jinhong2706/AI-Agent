# 短视频配乐AI

为抖音、小红书、Vlog、Reels 和创作者内容生成抓耳歌曲、hook 与 BGM。

短视频配乐AI适合抖音、小红书、Vlog、Reels、产品种草和品牌社媒内容，用于生成短视频配乐、抓耳歌曲、hook、背景音乐和纯音乐 BGM。描述视频主题、情绪和节奏后，AI 助手会生成可试听、可下载的音乐结果；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `short-video-music`
- Package name: `short-video-music`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- 短视频配乐
- 视频BGM
- 小红书配乐
- 抖音配乐
- Vlog配乐
- 短视频BGM
- 内容创作者音乐
- 种草视频配乐
- short video music
- TikTok music
- reels music
- vlog BGM

## Use Cases

- 为短视频生成抓耳 hook
- 为 Vlog、小红书和 Reels 生成 BGM
- 为产品种草和社媒活动制作配乐
- 把创作者 brief 变成歌曲或背景音乐候选

## Examples

- 给美妆短视频生成一段精致、有节奏感的 BGM
- 为旅行短视频生成一首抓耳的 30 秒歌曲
- 给产品开箱视频做一段轻快背景音乐

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --brief "为旅行短视频生成一首抓耳的 30 秒歌曲" --wait
node ./bin/aimv.js bgm create --brief "精致、有节奏感的美妆短视频 BGM" --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
