# Phase 4 · 验证交付

## 入场条件

```bash
python3 scripts/phase-check.py <skill-dir> --phase 4
```
✅ scripts/ 有 .py 文件 + SKILL.md body 非骨架 → 进入 Phase 4

## 目标
最后一道质量控制，产出交付物，不为"过"而放水。

## 对话步骤

### Step 1：自检（v3.3 新增）

先跑 self-audit（嵌入 validate --strict），再跑评分。自检发现问题比评分低分更根本——链接都是断的，打分没有意义。

运行：`python3 scripts/validate.py <skill目录> --strict`
- 自动嵌入 5 项自检：引用完整性 / 配置活性 / 测试覆盖 / 保鲜度 / 纪律验证
- P0 未通过 → 阻塞交付
- P1/Medium → 列出改进建议但不阻塞

### Step 2：质量评分（v2.0 新增）

**⚠️ 踩坑提醒**："SCK 的 verify.py 能打出精准的 10 维度分，我们继承了它的思路。"

运行：`python3 scripts/quality-audit.py <skill目录> --channel <轻量|完整>`
- 自动维度（10个）：Frontmatter/Token/文件/版本/反模式/模板/数据源/声明一致性/README同步/CHANGELOG — 脚本评分
- 手动维度（4个）：触发覆盖/脚本LLM边界/L2组织/README质量 — AI 人工裁定
- 轻量通道：满分79（跳过4个手动维度+声明一致性）
- 完整通道：满分117
- 评分等级（百分比制）：🏆95%+卓越 ✅85%+良好 🔧70%+需打磨 ⚠️<70%需重构

评分嵌入交付报告，不作为独立文件。

### Step 3：交付前检查清单（v3.7 新增）

逐个确认，未通过需修改后才能交付：

1. [ ] README.md 是否存在？
2. [ ] README.md 是否包含「## 这是什么」或等价的介绍段落（说明技能解决什么问题、适合谁、不适合谁）？
3. [ ] SKILL.md frontmatter 的 name/version/description/triggers/token_budget 是否完整？
4. [ ] CHANGELOG.md 是否存在且有实质变更记录？
5. [ ] quality-audit 是否通过（无 P0 阻塞项）？
6. [ ] **若 skill 涉及文件产出**：SKILL.md 是否包含「## 输出文件约定」章节？实际产出路径是否与约定一致？
