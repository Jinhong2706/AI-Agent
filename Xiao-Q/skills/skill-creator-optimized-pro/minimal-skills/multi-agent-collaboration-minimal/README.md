# 多 Agent 协作最小 Skill 包

这是一个最小可安装 Skill 包模板，可复制到用户技能目录后继续扩展。

## 文件结构

```text
multi-agent-collaboration-minimal/
├── SKILL.md
├── README.md
└── references/
    └── checklist.md
```

## 使用方式

1. 复制整个目录。
2. 修改 `SKILL.md` 的 `name`、`description` 和业务流程。
3. 按需补充 `references/`、`templates/`、`examples/`、`scripts/`。
4. 运行主包中的 `scripts/validate-skill.py` 和 `scripts/score-skill.py` 做发布前检查。
