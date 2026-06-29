# Excel 公式翻译官(人话→公式)

你描述需求(人话),它给你 Excel/WPS 公式 + 解释 + 不踩坑的边界条件。专攻 VLOOKUP/INDEX-MATCH/SUMIFS/数组公式/动态数组等高频但易错的场景。

## 这是什么

`xlsx-formula-master` 是一个针对**中国本地场景**原创设计的 OpenClaw / SkillHub Agent Skill。
从问题定义、框架设计、示例都是为中国用户从零写的，不是任何已有项目的翻译或 fork。

## 触发场景

详见 `SKILL.md` 的 description 字段，AI 会自动判断何时调用。常见关键词：

- `Excel 公式`
- `WPS 公式`
- `VLOOKUP`
- `INDEX MATCH`
- `SUMIFS`
- `数组公式`
- `动态数组`
- `Excel 翻译`

## 安装

### SkillHub（推荐）

通过 SkillHub Web 界面安装：https://skillhub.cloud.tencent.com/skills/xlsx-formula-master

### OpenClaw / Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R xlsx-formula-master ~/.claude/skills/xlsx-formula-master
```

### Cursor

把整个文件夹放到项目的 `.cursor/skills/xlsx-formula-master/` 下，重启 Cursor 即可。

## 用法

直接用自然语言描述需求，AI 会自动加载本 skill。例如：

```
帮我用 Excel 公式翻译官(人话→公式) 来 ...
```

## License

MIT © 2026 ikun

## 反馈

- 觉得有用：在 SkillHub 给个 star
- 报 bug / 建议：SkillHub 评论区留言
