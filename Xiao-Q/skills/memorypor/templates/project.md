# 项目：{project-name} — 模板

> 开始新项目时复制到 `~/self-improving/projects/{project-name}.md`。
> 项目特定模式覆盖全局和领域模式。

```markdown
# 项目：{project-name}

继承：global（全局）, domains/{relevant-domain}（相关领域）

## 项目信息
- 创建：YYYY-MM-DD
- 最后活动：YYYY-MM-DD
- 仓库：(URL 或路径)
- 状态：active（活动）| completed（完成）| archived（归档）

## 模式
<!-- 项目特定模式 -->
- 使用 {工具/框架}（项目标准）
- 不使用 {工具}（项目限制）
- 通过 {CI/CD 方法} 部署

## 覆盖
<!-- 与全局/领域不同的项目特定覆盖 -->
- {方面}：{值}（覆盖全局：{全局值}）

## 纠错
- 总数：N
- 最近：YYYY-MM-DD

## 历史
- YYYY-MM-DD：初始项目设置
- YYYY-MM-DD：{里程碑或重大变更}
```

## 覆盖语法

当项目模式与全局/领域不同时：

```markdown
## 覆盖
- 缩进：空格（覆盖全局Tab）
- 原因：项目ESLint配置要求空格
```

## 继承链

```
global（全局）(memory.md)
  └── domain（领域）(domains/{name}.md)
       └── project（项目）(本文件)
```

最具体的胜出。术语表参见 glossary.md。
