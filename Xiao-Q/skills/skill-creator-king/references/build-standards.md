# BUILD 阶段 · 施工规范

> 适用：Phase 3 BUILD。确保所有 skill 共享一致的施工标准，减少质量方差。

## 1. L2 文件结构约定

L2（深度指令文件）存放在 `references/` 目录下。

### 命名规范

| 文件类型 | 命名格式 | 示例 |
|----------|---------|------|
| 工作流指南 | `workflow-{场景}.md` | `workflow-create.md`, `workflow-review.md` |
| 配置说明 | `config-{主题}.md` | `config-oauth.md` |
| 领域知识 | `domain-{领域}.md` | `domain-hk-stock.md` |
| 命令速查 | `commands-{工具}.md` | `commands-git.md` |

### 拆分原则

- **单一职责**：一个文件只讲一件事。如果能在 30 秒内向别人说清「这个文件干什么」→ 拆对了
- **Token 预算**：每个 L2 文件 ≤ 3500 token（运行 `estimate-tokens.py` 实测，别猜）
- **懒加载**：不常触发的场景 → 标记为按需加载，不在 SKILL.md 中直接引用
- **避免循环引用**：L2 文件之间不互相引用（skill-creator-king 自身的 reference 可以例外）

## 2. L1 Body 撰写规范

L1（SKILL.md body）是 skill 的「驾驶舱」——AI 加载时最先看到的段。

### 必须包含

1. **路由逻辑**：用户输入 → 场景判断 → 工作流选择
2. **核心原则**：3-5 条不可妥协的底线（用 🔒 标记）
3. **脚本索引**：如果 `scripts/` 有 .py 文件，必须有对应的调用说明
4. **加载策略**：哪些 L2 文件总是加载 / 哪些按需加载

### 禁止

- ❌ 在 L1 body 中写超过 3 行的代码示例（代码放 scripts/）
- ❌ 用 `{placeholder}` 不填就直接用——
- ❌ 多个 `## Notes` 段落——合并成一个
- ❌ 超过 1200 token（轻量通道 1000 token）

## 3. 脚本错误处理模式

所有 `scripts/` 下的 Python 文件必须遵循三段式：

```python
def main():
    try:
        # 1. 正常路径
        result = do_work()
        return {"ok": True, "data": result}
    except TimeoutError:
        # 2. 已知失败 → 降级
        print("⚠️ 操作超时，使用缓存数据", file=sys.stderr)
        return {"ok": True, "data": fallback_data, "degraded": True}
    except Exception as e:
        # 3. 未知失败 → 透传（不要吞异常）
        print(f"❌ 不可恢复的错误: {e}", file=sys.stderr)
        return {"ok": False, "error": str(e)}
```

**强制性规则**：
- 🔒 不能把 API 错误当「未找到」返回空结果——必须区分「没有结果」和「获取失败」
- 🔒 不能 `exit(1)` 裸露退出——上层 caller 无法处理，必须 return 结构化错误
- 🔒 必须有 `_fallback_config()` 或等价的降级函数（至少一个空壳）

## 4. 输出格式约定

### Markdown 输出

- 用 `##` 作为顶级标题（`#` 留给 SKILL.md）
- 代码块必须标注语言：` ```python `
- 表格必须对齐列宽

### JSON 输出

- 顶层必须是 `{"ok": bool, ...}` 结构
- 字段名用 snake_case
- 不要裸返回 list / str —— 上层调用方无法判断成功/失败

### 文件路径约定

当 skill 涉及文件产出（生成/导出/保存/输出/写入），必须声明：

1. **输出目录**：明确路径是当前工作目录、固定子目录、用户指定、还是系统临时目录
2. **文件命名规则**：固定名称、时间戳、UUID、或用户指定
3. **目录创建**：若输出目录不存在，代码中应有 `os.makedirs(dir, exist_ok=True)` 逻辑
4. **覆盖策略**：同名文件是覆盖还是追加？是否警告用户？

## 5. 自检清单（进入 Phase 4 VERIFY 前必过）

- [ ] 所有 `{placeholder}` 已替换为实际内容
- [ ] Token 预算已实测（`estimate-tokens.py`），不在 hard_cap 以上
- [ ] 错误处理三段式已覆盖所有脚本
- [ ] L2 文件没有循环引用
- [ ] 如果引用了外部脚本/MCP 工具，已在 SKILL.md 或 DESIGN.md 中声明
- [ ] `version` 字段已从 `0.1.0` 升级为正式版本号
- [ ] **若涉及文件产出**：SKILL.md 已包含「## 输出文件约定」章节，明确四要素（目录/命名/格式/错误输出），且实际脚本与约定一致

---

_此文件为 Phase 3 BUILD 的强制参考，但不替代 validate.py 的自动检查。_
