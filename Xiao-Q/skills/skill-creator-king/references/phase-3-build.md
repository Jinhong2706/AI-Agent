# Phase 3 · 实施构建

## 入场条件

```bash
python3 scripts/phase-check.py <skill-dir> --phase 3
```
✅ DESIGN.md 有非占位 ADR + REQ 冻结 → 进入 Phase 3

## 目标
把设计变成文件。⚠️ 这是最容易踩坑的阶段。

> 📐 **施工规范**：`references/build-standards.md` 定义了 L2 文件结构、脚本错误处理模式、输出格式约定、自检清单。开始写代码前必读。

## 对话步骤

### Step 0：脚手架初始化（可选，v3.0新增）

**问用户**："要不要我先搭好目录骨架？"

```bash
python3 scripts/init_skill.py --name <skill-name> --template <basic|multi-scene|data-driven> --channel <lightweight|full>
```

一键生成：目录结构 + SKILL.md(模板) + README/CHANGELOG + 空 references/scripts/tests/data
完整通道额外生成：DESIGN

生成后 Phase 4 接着填充模板，不从头写空文件。

### Step 1：SKILL.md frontmatter — 过安全清单
**⚠️ Frontmatter 安全清单（逐项检查，不可跳过）：**
1. [ ] 没有用 `---` 做注释分隔符 → "上次 little-writer 因为这个注释导致 yaml_parser 提前截断，整个 skill 不可见"
2. [ ] 列表字段首行前无注释行 → "triggers 前如果有注释行，parser 可能看不到列表"
3. [ ] description 没用 `|` 块标量 → "用普通字符串！`|` 可能导致截断或重复"
4. [ ] 如果用 multi-scene，workflow 用短代码 → "W1/W2…，不要用文件路径！"
5. [ ] version 字段为唯一权威 → "这里定版本号，其他地方都跟它对齐"
6. [ ] name 字段是 skill 名不是 scene 名 → "整体名称，不是某个工作流名"

**用 validate.py 自动扫描。发现问题时用真实踩坑经历解释原因。**

### Step 2：SKILL.md L1 body
引导内容：路由表 + 核心原则 + 脚本索引 + 加载策略
Token 预算：≤1100 token（轻量可放宽到 1200）

### Step 3：L2 references
- 轻量：1 个文件
- 完整：按设计拆分的全部文件
- 写一个文件 → 回放给用户确认 → 写下一个

### Step 4-6（仅完整通道）
- scripts：含 _fallback_config() 降级
- tests：≥3 个测试

## Phase 3 收尾
用 validate.py 扫描 → 展示结果 → 如果 P0 未通过，必须修复后才进入 Phase 4。
