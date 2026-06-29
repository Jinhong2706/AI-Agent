# auto-test.md — 自动生成并运行定制测试

> Phase 4 VERIFY 的第三步。在 `validate.py` + `quality-audit.py` 之后执行。

> 本工作流不替代 validate/audit，而是**补充它们检测不到的 bug**：名称不一致、路由遗漏、领域特定的完整性约束。

## 适用场景

- 新建 skill 完成后
- 修改 skill 后（升级迭代）
- 手动触发："帮我测一下这个 skill"

## 工作流

### 步骤 1：分析 skill 结构

扫描目标 skill 目录，提取以下特征：

```
目标 skill 结构分析：
- 核心文件: SKILL.md, README.md, CHANGELOG.md ...
- L2 文件: references/{a,b,c}.md
- 数据文件: 类型 + 数量（如星体档案 42 个、模板 1 个）
- 路由表: 是否在 SKILL.md 中有场景路由定义
- 特殊约束: 从 SKILL.md / references 中提取的领域规则
  （如"六层结构""最多 5 个批次""命名规范 a-z+连字符"）
```

### 步骤 2：生成测试脚本

基于步骤 1 的结构分析，**用 Python 编写** `tests/test.py`，写入目标 skill 目录。

**必须包含的测试类别**（按通用程度降序）：

#### T1. 文件完整性（通用）
- 所有 SKILL.md 文件索引表中列出的文件必须存在
- 如有委托（README.md 树形结构），验证 README.md 存在且含 `├──`
- 实际文件数与声明数一致

#### T2. Frontmatter 质量（通用）
- SKILL.md frontmatter 含 `name`, `description`, `version`, `triggers`
- 数据文件的 frontmatter 含业务必需字段（从实际数据反推）

#### T3. 路由一致性（有路由表时）
- 路由表引用的所有 L2 文件必须存在
- 所有 L2 文件必须在路由表中有对应条目
- 所有 L2 文件必须包含路由引用声明（`路由规则见 SKILL.md`）

#### T4. 路径引用（通用）
- 全局搜索 `references/xxx/` 模式，比对实际目录结构
- 排除 CHANGELOG.md（历史记录中可能描述路径修复）

#### T5. 领域特定完整性（每个 skill 不同）
- 数据文件与 SKILL.md 中的引用表一一对应（如 42 个星体档案 = SKILL.md 表中的 42 个名字）
- 映射表覆盖率（如 thinking-tools 模型数 = 数据文件数）
- 命名规范（如 `a-z0-9-` 格式）

#### T6. 边界用例（从 L2 文件提取）
- 读取各 L2 workflow，提取"上限""最多""不存在""未匹配"等边界处理逻辑
- 生成对应的存在性断言

#### T7. 模板有效性（有模板时）
- 验证模板文件存在且包含关键占位符/章节

### 步骤 3：运行测试

```bash
python3 <skill>/tests/test.py
```

**首次运行预期会有失败**——这正是测试的价值：在交付前发现问题。

### 步骤 4：修复失败

对每个失败项，按优先级处理：

| 优先级 | 失败类型 | 行动 |
|:---:|------|------|
| P0 | 文件缺失 / 路径错误 | 立即修复源文件 |
| P1 | 名称不一致 / 数量不对 | 检查源→测试哪边更权威，修复另一端 |
| P2 | 测试脚本 bug | 修正测试断言 |

**修复后立即重新运行**，直到 100% 通过。

### 步骤 5：报告

在 VERIFY 阶段输出中追加：

```
🧪 自动测试: <N>/<M> 通过 (100%)
   - T1 文件完整性: ✅
   - T2 Frontmatter: ✅
   - T3 路由一致性: ✅
   - T4 路径引用: ✅
   - T5 领域完整性: ✅
   - T6 边界用例: ✅
   - T7 模板有效性: ✅
```

如有失败，列出待修复项。

---

## 测试脚本模板

生成的 `tests/test.py` 应遵循以下约定：

```python
#!/usr/bin/env python3
"""<skill-name> 自动生成测试"""

import re, os, yaml, sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
passed = 0; failed = 0; warnings = 0

def ok(msg):
    global passed; passed += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global failed; failed += 1
    print(f"  ❌ {msg}")

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# --- Tests below ---
# (LLM 根据 skill 结构定制生成)

# --- Summary ---
section("SUMMARY")
total = passed + failed
print(f"  Score: {passed}/{total} ({passed/total*100:.0f}%)")
sys.exit(0 if failed == 0 else 1)
```

---

## 与现有工具的分工

| 检查维度 | validate.py | quality-audit.py | auto-test |
|---------|:-----------:|:----------------:|:---------:|
| 文件存在性 | ✅ | ✅ | ✅ (扩展) |
| Frontmatter 格式 | ✅ | ✅ | ✅ (领域字段) |
| Token 预算 | ❌ | ✅ | ❌ |
| 反模式 | ✅ | ✅ | ❌ |
| 名称一致性 | ❌ | ❌ | ✅ |
| 路由完整性 | ❌ | ❌ | ✅ |
| 领域约束 | ❌ | ❌ | ✅ |
| 边界用例 | ❌ | ❌ | ✅ |

auto-test 不是 validate/audit 的替代品——是**互补层**，覆盖它们检测不到的语义和领域特定问题。
