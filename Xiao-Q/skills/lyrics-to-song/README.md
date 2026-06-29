# 歌词成曲AI

把中文或英文歌词生成完整歌曲，支持标题、风格、演唱方向、试听链接和音频下载。

歌词成曲AI适合需要 lyrics to song、歌词生成歌曲、填词成曲和中文歌词成曲的词作者、音乐人和内容创作者。提供歌词、标题和风格方向后，AI 助手会生成可试听、可下载的完整歌曲；作品会同步到海绵音乐账号，可在「海绵音乐AI写歌」小程序和 lexuan.club 网页继续管理。

Powered by 海绵音乐。账号、积分、会员和作品库与海绵音乐小程序 / lexuan.club 互通。

## Package Identity

- Skill slug: `lyrics-to-song`
- Package name: `lyrics-to-song`
- Agent tool name: `aimv`
- Node entrypoint: `bin/aimv.js`
- Runtime bundle: `dist/aimv.cjs`

## Keywords

- 歌词成曲
- 歌词生成歌曲
- 歌词作曲
- AI歌词成曲
- 中文歌词成曲
- AI作曲
- 把歌词做成歌
- lyrics to song
- turn lyrics into song
- AI lyrics music
- song from lyrics

## Use Cases

- 把完整歌词生成一首歌
- 为歌词草稿探索旋律和编曲方向
- 给词作者制作 demo 小样
- 从中文或英文歌词生成多首候选歌曲

## Examples

- 把这段歌词做成一首温暖的中文民谣
- 把我的歌词生成一首中文流行歌
- 把这段英文歌词做成一首情绪化的 indie pop

## Run

```bash
node ./bin/aimv.js init
node ./bin/aimv.js song create --lyrics "..." --title "海风里" --style mandopop warm --wait
node ./bin/aimv.js song create --lyrics-file ./lyrics.txt --title "海风里" --style mandopop warm --wait
```

The package does not include an opaque native binary or an extensionless Unix executable. It runs through Node.js >=18.
