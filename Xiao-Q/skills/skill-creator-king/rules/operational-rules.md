# 操作纪律 — SCK 创作准则

> 这五条是 skill 创作时必须遵守的内部纪律。前四条有 self-audit.py 自动验证；第五条是操作时的检查清单。

---

## 1. 不穷举 (No Exhaustion)

> 脚本扫描目录时用 `iterdir()` 还是手写的 `['a', 'b', 'c']`？手写列表一定会过时。

### 为什么重要

手写文件列表（如 `scripts = ['validate.py', 'init_skill.py']`）在文件增删后必然漂移。
新增文件不会被扫描，删除文件会导致运行时错误。这是「硬编码腐败」的典型形态。

### 检测方式

**自动检测 (self-audit check_5 纪律验证):**
- 扫描 `scripts/*.py`，检查是否有形如 `['*.py', '*.py']` 的硬编码文件列表
- 如果同一文件中不存在 `iterdir` 或 `os.walk` 调用 → 标记为「可能有硬编码列表」

**手动审查时自问:**
- 这个脚本如何发现要处理的文件？是动态扫描还是手写清单？
- 如果我新增一个文件，是否需要更新这个脚本？

### 正确做法

```python
# ❌ 手写列表
scripts = ['validate.py', 'init_skill.py', 'quality-audit.py']

# ✅ 动态扫描
scripts = list(Path('scripts').glob('*.py'))
```

### 例外

- 配置型文件列表（如 `__init__.py` 明确列出公开 API）不算违反
- 显式排除列表（如 `skip = {'__pycache__', '.DS_Store'}`）是必要的，不算违反

### 相关

- self-audit: check_5 纪律验证（自动）
- 反模式: D4 硬编码腐败

---

## 2. 不双写 (No Duplication)

> 同一份模板/配置是否有两份拷贝？双写必漂移。

### 为什么重要

当同一份内容以两种形式存在（如 init_skill.py 内联模板字符串 vs data/templates/*.md 文件），
修改其中一个时另一个必然遗忘。两份拷贝会在不知不觉中分化——第一次差一行，第十次是两个完全不同的东西。

### 检测方式

**自动检测 (self-audit check_5 纪律验证):**
- init_skill.py 中的 `_TMPL` 变量名 vs `data/templates/` 目录下的文件名
- 有变量无文件 → 孤儿变量
- 有文件无变量 → 孤儿文件
- 已知单源例外：`CONFIG_TMPL`（仅 init_skill.py）、`review-report`、`session-report`（仅 data/templates/）

**手动审查时自问:**
- 这段逻辑在别处也有吗？改动时需要改几个地方？
- 这份配置是从另一个文件复制的吗？为什么不能共享加载？

### 正确做法

```python
# ❌ 内联字符串 = 模板的拷贝
README_TMPL = """# {name}\n\n{desc}\n"""

# ✅ 从单一源文件加载
def _load_template(name: str) -> str:
    return (TEMPLATES_DIR / f"{name}.md").read_text()
```

### 例外

- 单源模板：内容极简单（<5行）且不太可能独立演变 → 可保留但不推荐
- `single_source` 白名单在 self-audit.py check_discipline_compliance() 中维护

### 相关

- self-audit: check_5 纪律验证（自动）
- 反模式: D2 内容漂移

---

## 3. 不窄检 (No Narrow Check)

> 验证工具的扫描范围是否小于被检查对象的文件范围？窄检 = 盲区。

### 为什么重要

如果 validate.py 只检查 SKILL.md 和 scripts/，但 skill 的 references/ 和 data/ 也有规范要求，
那么 references/ 中的数据漂移、data/ 中的死配置永远不会被发现。
验证工具必须覆盖它所声称要验证的全部范围。

### 检测方式

**自动检测 (self-audit check_5 纪律验证):**
- 检查 validate.py 是否使用 `iterdir()` 或 `os.walk()` 动态扫描
- 如果没有动态扫描 → 可能使用了硬编码的检查路径，范围可能过窄

**手动审查时自问:**
- validate.py 检查了哪些文件？skill 实际有哪些文件？
- 如果我在 references/ 新增一个文件，validate.py 会发现它吗？
- quality-audit.py 的扫描范围与 validate.py 覆盖互补吗？

### 正确做法

```python
# ❌ 只检查特定目录
for f in Path('scripts').glob('*.py'):
    check(f)

# ✅ 动态发现所有需检查的文件
for f in skill_dir.rglob('*.md'):
    if 'cache' not in f.parts:
        check(f)
```

### 审查清单

| 被检查对象 | validate.py 覆盖? | quality-audit.py 覆盖? |
|-----------|:---:|:---:|
| SKILL.md | ✅ | ✅ |
| scripts/*.py | ✅ | ✅ |
| references/*.md | ✅ | - |
| data/ | ✅ | ✅ |
| tests/ | ✅ | - |
| README.md | ✅ | ✅ |
| CHANGELOG.md | ✅ | - |

### 相关

- self-audit: check_5 纪律验证（自动）
- 反模式: D3 窄检

---

## 4. 改必扫 (Rename Must Scan)

> 重命名核心文件或术语后，必须扫描全仓库所有引用。改名不是只改一个文件，是改一个概念网络。

### 为什么重要

改一个文件名或术语名，如果只改了定义处而没改引用处，结果不是「部分过时」——是「引用全断」。
最经典的案例：PHILOSOPHY.md → PRINCIPLES.md 重命名后，多处引用仍指向旧路径，直到审查才发现。

### 检测方式

**自动检测 (self-audit check_6 名称一致性，需 --sck-mode):**
- 从术语表加载核心术语名单
- 全仓扫描 `.md` 和 `.yaml` 文件，检测是否有旧术语名残留
- 仅 SCK 自身审查时启用（其他 skill 没有 SCK 术语表）

**手动审查时自问:**
- 最近改过文件名吗？改了之后用 grep 扫过全仓吗？
- 改过 frontmatter 字段名吗（如 triggers → trigger_words）？
- CHANGELOG 记录的每次重命名，都确认过引用完整更新吗？

### 正确做法

```bash
# ❌ 只改文件名
mv PHILOSOPHY.md PRINCIPLES.md

# ✅ 改文件名 + 全仓扫描替换
mv PHILOSOPHY.md PRINCIPLES.md
grep -rl "PHILOSOPHY" --include="*.md" --include="*.yaml" . | xargs sed -i '' 's/PHILOSOPHY/PRINCIPLES/g'
# 然后逐文件确认替换正确（不是所有出现都应替换）
```

### 术语表机制 (SCK 专属)

SCK 在 `data/` 中维护术语表（当前在 self-audit.py check_name_consistency 中硬编码），
记录核心概念的标准名称。每次改名时更新术语表，self-audit --sck-mode 自动扫描残留。

### 相关

- self-audit: check_6 名称一致性（--sck-mode 专属）
- 反模式: D1 死引用、D2 内容漂移
- 审查历史: 过去 PHILOSOPHY→PRINCIPLES 重命名的教训

---

## 5. 不孤改 (Cascade Update)

> 新增一个资产类型或目录时，是否同步更新了所有依赖方？孤岛式修改必断裂。

### 为什么重要

Skill 的构件不是孤岛。当一个新资产类型被加入（如 `rules/` 目录），以下方必须感知到它的存在：
- L2 Token 扫描器（estimate-tokens.py）
- 完整性检查器（self-audit.py）
- 文件结构索引（SKILL.md / README.md）
- 架构文档（DESIGN.md ADR，同时承载需求规格 REQ）

历史上，`rules/` 引入时遗漏了 estimate-tokens.py 的扫描路径更新，导致 L2 预算误算——新目录的 Token 被静默排除了。

### 检测方式

**新增目录/资产类型时自问：**

| # | 检查项 | 具体操作 |
|---|--------|---------|
| 1 | Token 扫描 | `estimate-tokens.py` 的 L2 扫描路径是否包含新目录？ |
| 2 | 自审计覆盖 | `self-audit.py` 是否检查了新资产类型的完整性？ |
| 3 | 文件结构表 | `SKILL.md` / `README.md` 的文件结构清单是否列出了新条目？ |
| 4 | 架构追溯 | `DESIGN.md` 是否新增 ADR 记录此架构决策？ |
| 5 | 需求契约 | `DESIGN.md` 是否新增对应 REQ（如有功能需求）？ |
| 6 | 预算联动 | `token_budget` 的 `L2_deep` 和 `hard_cap` 是否已上调？ |

**手动审查时自问：**
- 我创建/修改了这个目录后，还有哪些文件引用了「旧结构」？
- 有没有 grep 能搜到的过时路径引用？
- 新增的资产类型是否在 anti-patterns.yaml 中需要新增检测规则？

### 正确做法

```
# ❌ 孤岛式：加了 rules/ 目录，只更新了 DESIGN.md
# ─ 结果：estimate-tokens 漏算 rules/ 的 Token
#        self-audit 不知道 rules/ 存在
#        SKILL.md 文件结构表缺少 rules/ 行

# ✅ 级联式：加了 rules/ 目录后
# 1. estimate-tokens.py: L2_DIRS.append("rules")
# 2. self-audit.py: check_5 追加 rules/ 覆盖率检查
# 3. SKILL.md / README.md: 文件结构表新增 rules/ 行
# 4. DESIGN.md: 新增 ADR 记录
# 5. DESIGN.md: 新增对应 REQ
# 6. token_budget: 上调 L2_deep + hard_cap
```

### 连锁更新清单模板

当新增资产类型 X 时，必查以下 7 项：

```markdown
## 新增 X → 连锁更新检查清单

- [ ] `scripts/estimate-tokens.py`：L2 扫描路径追加 X
- [ ] `scripts/self-audit.py`：完整性检查追加 X
- [ ] `SKILL.md`：文件结构表追加 X
- [ ] `README.md`：文件结构表追加 X
- [ ] `DESIGN.md`：新增 ADR 记录
- [ ] `DESIGN.md`：新增 REQ（如有功能需求）
- [ ] Token 预算联动：`token_budget.L2_deep` + `hard_cap` 上调
```

### 例外

- 纯文档文件（`.md`）加入已有目录不触发级联（加的是内容，不是类型）
- `data/` 下新增缓存/数据文件不触发（加的是实例，不是类型）
- `templates/` 下新增模板文件不触发（类型已存在）

### 相关

- 本条纪律由 `skill-design-framework.md` V2.0 的「连锁更新清单」抽象为独立 Rule
- 反模式: #13 级联断裂（框架附录）
- 反模式: D2 内容漂移（SCK self-audit）

---

## 6. 表先于盘 (Table Before Disk)

> 增删文件时，先改表、再动盘。表是承诺，盘是兑现。

### 为什么重要

每个 skill 的文件结构表（SKILL.md 和 README.md 中的 `## 文件结构` 节）和实际磁盘之间存在天然漂移风险。删了一个文件但忘了从表里移除 → SCK 报"表缺"假阳性。加了一个文件但表里没写 → SCK 检测不到，新资产成了幽灵文件。

根因：三处各有一份文件列表（SKILL.md 表、README 表、磁盘），但没有强制的一致性约束。

### 正确做法

增删文件必须按这个顺序：

```
1. 先改 SKILL.md 文件结构表  ← 承诺
2. 再操作磁盘（新建/删除）    ← 兑现
3. 最后同步 README.md 表     ← 镜像
4. 跑 SCK --no-cache 验证    ← 兜底
```

表先于盘。不是"做了什么事再去更新文档"——是"先把要做什么写进文档，再去做"。

### 为什么必须 `--no-cache`

SCK 默认缓存 24 小时。增删文件后跑 SCK 不加 `--no-cache`，读到的是旧结果——你会以为自己通过了检查，实际上只是看了昨天的自己。

### 适用范围

本规则适用于**所有由 SCK 创建或维护的 skill**，不限于 SCK 自身。

### 例外

- 在已有目录下新增纯内容文件（如 `references/` 下加一篇新文章）不触发——目录级结构没变
- 临时文件（`.DS_Store`、`__pycache__`）不计入
