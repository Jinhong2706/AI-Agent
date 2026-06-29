# DESIGN 阶段 · 子步骤 1/2：需求定义

> 所属阶段：Phase 2 DESIGN（合并 WHAT+HOW，v3.14+）

## 入场条件

```bash
python3 scripts/phase-check.py <skill-dir> --phase 2
```
✅ Phase 1 DISCUSS 完成 → 进入 DESIGN 阶段

## ⚠️ 双文件兼容（旧架构）

如果目标 skill 同时存在 `SPEC.md` 和 `DESIGN.md`（v3.14 之前的旧架构），你有两个选择：

1. **建议合并**：将 SPEC.md 内容迁入 DESIGN.md（参考 DESIGN.template.md 结构），删除 SPEC.md。之后按合并架构操作。
2. **同步更新**：如果用户不想合并，更新 DESIGN.md 的 REQ 章节时，同步更新 SPEC.md 中对应的 REQ。两者必须保持版本一致。

> 不处理的后果：SPEC.md 变成僵尸文件，后续 phase-check 和 AP-013 会报版本不一致。

## 目标
把 Phase 1 的定位转化为可验证的需求。

## 对话步骤

### Step 1：数据源声明（v2.0 增强）
**Q: 这个 skill 需要访问外部数据吗？**

如果是数据驱动通道（📡），需要更详细的引导：
1. 确认数据源类型：📁本地文件 / 🌐网络API / 🔗WebSearch
2. 确认缓存策略：每次加载 / 按天缓存 / 按版本更新
3. 声明禁止项：不能搜索的内容（如"范文"）
4. 产出 data/sources.yaml：source定义 + 缓存策略 + 禁止项
5. 在 SKILL.md 中声明 data_sources_ref 或 allowed-tools
选项：
- 网络搜索（WebSearch）
- API 接口
- 本地文件
- 内置知识库（纯本地 references/）
- 不需要任何外部数据

如果需要，追问：
1. "具体是什么数据源？"
2. "🔒 严格限定只能用这些，还是 🌐 可以额外搜索补充？"
- **强制阻塞**：用户必须选一个

### Step 2：功能需求
**引导**："用户用这个 skill 能做哪几件事？排个优先级。"
- 轻量通道：3-5 个 REQ
- 完整通道：无上限，但要排序
- 追问："如果只能做对一件事，是哪件？"（帮用户聚焦）
- 每个 REQ 必须有验证标准："你怎么知道这个功能做好了？"

### Step 3：非功能需求
**引导**："除了能做什么，还有什么约束？比如 Token 预算、语言风格、安全边界……"
- 让用户排最重要的 3 个
- Token 预算：L0/L1/L2/hard_cap（给默认建议：L0:100/L1:800/L2:3500/hard_cap:5000）
- 如果用户不确定，反问："你的 skill 会被很多人用吗？还是你自己用？"（影响安全约束）

### Step 4：诚实标注
**引导**："哪些是 v1.0 一定要有的？哪些可以先放 v2.0？"
- ⚠️ 关键哲学："不承诺做不到的事"
- 如果用户提出跨会话能力（永久历史、用户档案），提醒："当前 skill 架构是无状态的，跨会话能力可能做不到。要不要标成 v2.0？"

## 子步骤收尾
小结 REQ 列表 + NFR 优先级 + 推迟项。完成后进入 → 子步骤 2/2 架构设计（`phase-2-design-architecture.md`）。

## 轻量 vs 完整差异
- 轻量：REQ 列表 + Token 预算，口头确认
- 完整：DESIGN.md（REQ+NFR+ADR 合并）+ data/sources.yaml
