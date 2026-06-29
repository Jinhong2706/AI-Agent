---
name: OpenClaw自定义技能开发指南
description: 从零开发OpenClaw功能型Skill的完整实战指南。包含SKILL.md规范、目录结构、scripts/脚本开发、调试方法、代码模板。不是阅读文档，是可执行的脚手架工具——帮你一键生成Skill骨架、验证结构、本地调试。
version: "1.0.0"
updated_at: "2026-06-03"
category: ["开发工具", "OpenClaw"]
tags: ["Skill开发", "OpenClaw", "SKILL.md", "脚手架", "代码模板"]
trigger: ["开发技能", "创建Skill", "写SKILL.md", "技能开发指南", "OpenClaw开发"]
---

# OpenClaw自定义技能开发指南

> 不是阅读文档，是开发工具。帮你从零搭建一个可运行的OpenClaw Skill。

## 核心能力

1. **一键生成Skill骨架** — 输入技能名称和描述，自动生成完整目录结构+文件
2. **结构验证** — 检查Skill目录是否符合OpenClaw规范
3. **本地调试** — 模拟OpenClaw加载流程，本地测试Skill是否可运行
4. **代码模板库** — 常见功能（文件读写、HTTP请求、数据处理）的即用模板

---

## 快速开始

### 流程1：创建新Skill

用户说："帮我创建一个XX技能" 或 "我想开发一个Skill"

```bash
python scripts/scaffold.py --name "my-skill" --display-name "我的技能" --description "技能描述"
```

自动生成：
```
my-skill/
├── SKILL.md          # 技能定义文件
├── scripts/
│   └── main.py       # 主脚本（含模板代码）
└── references/
    └── README.md     # 参考文档说明
```

### 流程2：验证Skill结构

用户说："帮我检查这个Skill" 或 "验证一下结构"

```bash
python scripts/validate.py --path ./my-skill
```

检查项：
- ✅ SKILL.md 存在且格式正确（front matter必填字段）
- ✅ scripts/ 目录存在
- ✅ 脚本可执行（有shebang或可被python调用）
- ✅ 无敏感信息泄露（API Key硬编码检测）
- ✅ 文件大小合规（单文件≤50KB，总包≤5MB）

### 流程3：本地调试

用户说："测试一下这个Skill"

```bash
python scripts/debug.py --path ./my-skill --input '{"arg1": "value1"}'
```

模拟OpenClaw加载流程：
1. 解析SKILL.md → 提取脚本调用方式
2. 执行脚本 → 传入input
3. 返回输出结果

### 流程4：查看代码模板

用户说："给我一个XX功能的模板"

```bash
# 查看所有可用模板
python scripts/templates.py --list

# 生成特定模板
python scripts/templates.py --type file-io --output ./my-skill/scripts/file_utils.py
```

可用模板：
- `file-io` — 文件读写工具
- `http-request` — HTTP请求工具（web_fetch风格）
- `data-process` — 数据清洗/转换工具
- `report-gen` — 报告生成工具（Markdown输出）
- `cli-parser` — 命令行参数解析工具

---

## SKILL.md 完整规范

### Front Matter 必填字段

```yaml
---
name: skill-name          # 英文标识符，小写+短横线，唯一
description: 一句话描述     # 80字以内，说清干什么
version: "1.0.0"          # 语义化版本号
updated_at: "2026-06-03"  # 最后更新日期
---
```

### Front Matter 可选字段

```yaml
category: ["开发工具"]     # 分类标签数组
tags: ["模板", "脚手架"]   # 搜索标签
trigger: ["创建技能"]      # 触发词，Agent匹配用
```

### SKILL.md 正文结构

```markdown
# 技能名称

> 一句话定位，不是阅读文档是什么

## 核心能力
1. 能力1 — 输入什么 → 输出什么
2. 能力2 — ...

## 交互流程

### 流程1：XXX
1. 用户说/做什么
2. 调用哪个脚本
3. 输出什么

## 脚本说明

### scripts/xxx.py
- 输入：JSON格式参数
- 输出：JSON格式结果
- 逻辑：核心算法说明

## 设计原则
- 原则1
- 原则2
```

### 关键规则
1. **必须有脚本** — 纯SKILL.md无scripts/的Skill=阅读型=0分
2. **脚本必须可独立运行** — `python scripts/xxx.py --input '...'` 能直接跑
3. **输入输出用JSON** — 标准化，Agent好解析
4. **不依赖第三方包** — 纯Python标准库，零安装
5. **SKILL.md是入口** — Agent先读SKILL.md，再按流程调脚本

---

## 目录结构规范

```
skill-name/
├── SKILL.md              # 必填，技能定义+交互流程
├── scripts/              # 必填，至少1个可执行脚本
│   ├── main.py           # 主脚本
│   └── utils.py          # 工具函数（可选）
├── references/           # 可选，参考文档
│   └── api-spec.md       # API文档等
└── README.md             # 可选，给人看的说明
```

### 命名规则
- Skill名称：小写英文+短横线（如 `multi-search-engine`）
- 脚本文件：小写+下划线（如 `profit_calc.py`）
- 不要中文文件名，不要空格

---

## 脚本开发规范

### 标准模板

```python
#!/usr/bin/env python3
"""脚本功能一句话描述"""

import sys
import json
import argparse


def main(args):
    """主逻辑"""
    # 解析输入
    if args.input:
        data = json.loads(args.input)
    else:
        data = {}

    # 核心逻辑
    result = process(data)

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


def process(data):
    """核心处理逻辑，输入dict，输出dict"""
    # TODO: 实现你的逻辑
    return {"status": "ok", "data": data}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="脚本描述")
    parser.add_argument("--input", type=str, help="JSON格式输入参数")
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    args = parser.parse_args()
    main(args)
```

### 输入输出规范
- 输入：`--input` 接JSON字符串
- 输出：stdout打印JSON结果
- 可选：`--output` 写文件
- 错误：输出 `{"status": "error", "message": "错误描述"}`

### 禁止事项
- ❌ 不硬编码API Key（用环境变量或参数传入）
- ❌ 不依赖第三方包（只用标准库）
- ❌ 不写交互式输入（全部参数化）
- ❌ 不写绝对路径（用相对路径）

---

## 调试方法

### 1. 本地单脚本测试

```bash
python scripts/main.py --input '{"test": "hello"}'
```

### 2. 结构验证

```bash
python scripts/validate.py --path ./skill-name
```

### 3. 模拟完整流程

```bash
python scripts/debug.py --path ./skill-name --input '{"arg1": "value1"}'
```

### 4. 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 脚本报ModuleNotFoundError | 用了第三方包 | 换标准库实现 |
| 输出不是JSON | print了调试信息 | 只输出最终JSON |
| SKILL.md解析失败 | front matter格式错 | 检查---包围和YAML语法 |
| 脚本无执行权限 | 缺shebang | 加 `#!/usr/bin/env python3` |

---

## 打包发布

### 打包

```bash
cd skill-name
zip -r ../skill-name.zip . -x "*.pyc" "__pycache__/*" ".git/*"
```

### 发布到技能平台

```bash
curl -X POST https://skill-platform.example.com/api/skills \
  -H "Authorization: Bearer $PLATFORM_API_KEY" \
  -F "file=@skill-name.zip" \
  -F "name=skill-name" \
  -F "description=技能描述"
```

---

## 设计原则

1. **工具型>阅读型** — 有脚本、能运算、有输出，才是Skill
2. **输入→运算→输出** — 用户给数据，脚本算结果
3. **零依赖** — 纯标准库，拿到就能跑
4. **可独立运行** — 每个脚本都能单独 `python xxx.py` 执行
5. **JSON标准化** — 输入输出全用JSON，Agent好对接
