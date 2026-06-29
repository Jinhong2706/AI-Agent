# 中国财税 Excel 实战

针对中国会计准则、增值税、个税、社保、年终汇算的 Excel 工作流。覆盖小规模/一般纳税人计税、薪资表、社保公积金、季度报表等。

## 这是什么

`excel-finance-cn` 是一个针对**中国本地场景**原创设计的 OpenClaw / SkillHub Agent Skill。

不是任何已有项目的 fork 或翻译——从问题定义、框架设计、示例都是为中国用户从零写的。

## 触发场景

详见 `SKILL.md` 的 description 字段，AI 会自动判断何时调用。常见关键词：

- `增值税`
- `个税`
- `社保`
- `年终汇算`
- `薪资表`
- `财务报表`
- `Excel`

## 安装

### SkillHub（推荐）

```bash
# 通过 SkillHub Web 界面下载
# https://skillhub.cloud.tencent.com/skills/excel-finance-cn
```

### OpenClaw / Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R excel-finance-cn ~/.claude/skills/excel-finance-cn
```

### Cursor

把整个文件夹放到项目的 `.cursor/skills/excel-finance-cn/` 下，重启 Cursor 即可。

## 用法

直接用自然语言描述需求，AI 会自动加载本 skill。例如：

```
帮我用 中国财税 Excel 实战 来 ...
```

## License

MIT © 2026 ikun

## 反馈

- 觉得有用：在 SkillHub 给个 star
- 报 bug / 建议：在 SkillHub 评论区留言
