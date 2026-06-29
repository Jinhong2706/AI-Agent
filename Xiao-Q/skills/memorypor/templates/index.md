# 记忆索引 — 模板

> 首次使用时将此模板复制到 `~/self-improving/index.md`。
> 跟踪所有命名空间及其大小，以便快速加载决策。

```markdown
# 记忆索引

## 热层（始终加载）
- memory.md：N 行 | 更新于 YYYY-MM-DD

## 温层（按需加载）
### 项目
- projects/{name}.md：N 行 | 更新于 YYYY-MM-DD

### 领域
- domains/{name}.md：N 行 | 更新于 YYYY-MM-DD

## 冷层（归档）
- archive/YYYY.md：N 行 | 归档于 YYYY-MM-DD

## 统计
最后更新：YYYY-MM-DD HH:MM
纠错总条目：N
热层总条目：N
历史晋升次数：N
历史降级次数：N
历史归档次数：N
```

## 使用

索引帮助代理决定：
1. 始终加载 memory.md（热层）
2. 按需加载匹配的项目/领域文件（温层）
3. 仅在明确查询时加载归档（冷层）

## 维护

更新 index.md：
- 每次晋升到热层后
- 创建/删除项目或领域文件后
- 归档条目后
- 通过心跳每周维护
