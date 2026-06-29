# Excel 自动化 Skill 示例包

这是一个最小可安装 Skill 包示例，用于演示 Excel 自动化类技能的注册信息、触发条件、执行流程、异常处理与交付契约。

## 文件结构

- `SKILL.md`：技能主体说明，包含可解析 YAML front matter。
- `package.json`：最小包元数据。
- `README.md`：安装包说明。

## 使用建议

将本目录作为独立技能包复制或发布到目标 SkillHub/技能加载目录后，由运行环境读取 `SKILL.md` 的 front matter 与正文规则。
