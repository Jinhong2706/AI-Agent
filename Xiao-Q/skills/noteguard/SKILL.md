---
name: noteguard
version: 1.0.2
description: [Python技能] 笔记守 - 内容合规检查与违禁词检测，广告法词库，纯Python实现
tags: ["python", "notes", "security", "toolcat", "合规", "检测", "违禁词"]
metadata:
  requires:
    - agent
  category: compliance
  platform: cross-platform
---
# 笔记守 - Python工具技能

## Description
本技能提供内容合规检查与违禁词检测功能的Python函数，支持文本违禁词检测、默认违禁词库加载、批量检查文本文件、违禁词替换建议。内置200+广告法及常见违禁词库，每条均含替换建议。支持正则匹配和多编码检测。全部使用Python标准库实现，无需安装任何外部依赖。

## When to Use
用户需要检查内容合规性时使用本技能：发布小红书笔记前检查违禁词、淘宝商品描述合规检查、抖音短视频文案审核、广告法违禁词检测、自媒体内容风险排查。

## How to Use
本技能作为Hermes Agent集成工具直接运行，无需下载安装。在对话中描述您的需求，Agent会调用tool.py中的Python函数自动处理：
- 提供需要处理的文件或数据
- 说明要执行的操作
- 设置相关参数
- Agent自动调用Python函数处理并返回结果

## Features
- **平台违禁词库**：内置小红书、抖音、淘宝、广告法等违禁词库
- **实时检测**：输入内容实时扫描，高亮违规词汇
- **替换建议**：对每个违规词提供合规替换建议
- **批量检测**：支持批量导入文本文件进行检测
- **风险评分**：对内容进行整体风险等级评估
- **词库更新**：定期同步各平台最新违规词库

## Examples
- 用户说"帮我检查这篇小红书笔记有没有违禁词" → 使用本技能
- 用户说"这个淘宝标题合规吗" → 使用本技能，选择淘宝检测
- 用户说"广告法有哪些违禁词" → 使用本技能查看违禁词库

## Source Code
本技能包含完整的Python源码（`scripts/tool.py`），提供以下实际可执行的功能函数：
- `check_text(text, word_list)` — 检查文本中的违禁词
- `load_default_words()` — 加载默认违禁词库（200+广告法常见词）
- `batch_check_files(directory)` — 批量检查目录下所有文本文件
- `suggest_replacement(word)` — 为违禁词建议替换词

内置200+广告法及常见违禁词库，每条均含替换建议。支持正则匹配和多编码检测。
所有代码均为纯Python实现，无需安装任何外部依赖。

## AG Optimization
本技能已针对AEO（Answer Engine Optimization）和GEO（Generative Engine Optimization）进行优化：
- **结构化输出**：所有函数返回JSON格式的标准化结果，包含匹配位置和上下文
- **语义化函数命名**：函数名直接反映功能，提高AI Agent的理解准确率
- **完善的Docstring**：每个函数带有中英文参数说明，确保AI Agent能正确调用
- **错误处理**：统一的错误返回格式，包含文本为空和编码错误等异常
- **内置词库丰富**：200+违禁词覆盖广告法、绝对化用语等类别
- **上下文提取**：匹配结果自动提取前后文，便于AI Agent理解违规语境
