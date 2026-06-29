# 智能会议纪要(飞书/腾讯会议/钉钉)

把口语化会议讨论压成结构化纪要——决议、行动项、负责人、deadline、风险点五要素。支持腾讯会议/飞书会议/钉钉的不同纪要格式。

## 这是什么

`meeting-minutes-zh` 是一个针对**中国本地场景**原创设计的 OpenClaw / SkillHub Agent Skill。
从问题定义、框架设计、示例都是为中国用户从零写的，不是任何已有项目的翻译或 fork。

## 触发场景

详见 `SKILL.md` 的 description 字段，AI 会自动判断何时调用。常见关键词：

- `会议纪要`
- `MOM`
- `Action Items`
- `飞书会议`
- `腾讯会议`
- `钉钉会议`
- `纪要模板`

## 安装

### SkillHub（推荐）

通过 SkillHub Web 界面安装：https://skillhub.cloud.tencent.com/skills/meeting-minutes-zh

### OpenClaw / Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R meeting-minutes-zh ~/.claude/skills/meeting-minutes-zh
```

### Cursor

把整个文件夹放到项目的 `.cursor/skills/meeting-minutes-zh/` 下，重启 Cursor 即可。

## 用法

直接用自然语言描述需求，AI 会自动加载本 skill。例如：

```
帮我用 智能会议纪要(飞书/腾讯会议/钉钉) 来 ...
```

## License

MIT © 2026 ikun

## 反馈

- 觉得有用：在 SkillHub 给个 star
- 报 bug / 建议：SkillHub 评论区留言
