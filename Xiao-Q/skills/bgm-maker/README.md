# AI背景音乐生成

为视频、直播、播客、游戏和商业内容生成纯音乐 BGM 与背景配乐。

AI背景音乐生成适合需要 BGM生成、背景音乐生成器、纯音乐 BGM 和视频配乐的创作者。你可以描述场景、情绪、节奏和用途，为短视频、Vlog、游戏、播客、产品演示和商业内容生成可试听、可下载的背景音乐；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `bgm-maker`
- Package name: `bgm-maker`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- 背景音乐生成
- AI背景音乐
- BGM生成
- 配乐生成
- 纯音乐
- 视频BGM
- 游戏配乐
- 播客配乐
- BGM generator
- background music
- instrumental music
- AI BGM

## Use Cases

- 为视频生成纯音乐 BGM
- 为游戏、App 和产品演示制作背景音乐
- 生成播客片头、片尾和转场音乐
- 制作商业内容和演示文稿背景配乐

## Examples

- 生成一段适合城市夜景 vlog 的轻电子 BGM
- 给产品演示视频做一段干净、有科技感的背景音乐
- 为播客片头生成一段安静的钢琴背景音乐

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js bgm create --brief "给产品演示视频做一段干净、有科技感的背景音乐" --wait
node ./bin/aimv.js bgm create --brief "适合城市夜景 vlog 的轻电子背景音乐" --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
