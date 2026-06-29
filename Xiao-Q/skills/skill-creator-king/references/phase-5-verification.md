# Phase 5 详细指引：交付

## 目标
最后一道质量控制，产出交付物，不为"过"而放水。

## 对话步骤

### Step 5.1：自检（v3.3 新增）

先跑 self-audit（嵌入 validate --strict），再跑评分。自检发现问题比评分低分更根本——链接都是断的，打分没有意义。

运行：`python3 scripts/validate.py <skill目录> --strict`
- 自动嵌入 5 项自检：引用完整性 / 配置活性 / 测试覆盖 / 保鲜度 / 纪律验证
- P0 未通过 → 阻塞交付
- P1/Medium → 列出改进建议但不阻塞

### Step 5.2：质量评分（v2.0 新增）

**⚠️ 踩坑提醒**："SCK 的 verify.py 能打出精准的 10 维度分，我们继承了它的思路。"

运行：`python3 scripts/quality-audit.py <skill目录> --channel <轻量|完整>`
- 自动维度（6个）：Frontmatter/Token/文件/版本/反模式/模板/数据源
- 手动维度（3个）：触发词/脚本边界/L2组织 — AI 人工裁定
- 轻量通道：满分85（不评SPEC/DESIGN/脚本相关）
- 完整通道：满分100
- 评分等级：🏆95+卓越 ✅85+良好 🔧70+需打磨 ⚠️<70需重构

评分嵌入交付报告，不作为独立文件。

### Step 5.3：交付前检查清单（v3.7 新增）

逐个确认，未通过需修改后才能交付：

1. [ ] README.md 是否存在？
2. [ ] README.md 是否包含「## 这是什么」或等价的介绍段落（说明技能解决什么问题、适合谁、不适合谁）？
3. [ ] SKILL.md frontmatter 的 name/version/description/triggers/token_budget 是否完整？
4. [ ] CHANGELOG.md 是否存在且有实质变更记录？
5. [ ] quality-audit 是否通过（无 P0 阻塞项）？
