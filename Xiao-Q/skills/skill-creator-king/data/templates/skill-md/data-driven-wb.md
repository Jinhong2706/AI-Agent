---
name: {name}
description: {desc}
version: "0.1.0"
triggers: []
token_budget:
  L0_trigger: 200
  L1_core: 1100
  L2_deep: 5000
  hard_cap: 10000
template: data-driven
sources:
  template: sources.template.yaml
scaffold: skill-creator-king
---

# {display_name}

{desc}

## 文件结构

详见 `README.md`

## 数据源

详见 `data/sources.yaml`

## 工作流

## 注意事项

- **🔒 修改纪律**：本 skill 由 skill-creator-king 创建。修改后必须加载 SCK 运行 `validate.py` + `phase-check.py`，修到 0 HIGH 为止。
