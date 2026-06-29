---
name: research-pro
version: 1.4.5
description: 你的商业情报顾问。支持 Tavily 引擎搜索，提供 S/A/B/C 四级信源分级与情感化报告生成。适用于市场调研、竞品分析及企业信用查询。
tags: [market-research, business-intelligence, search-engine]
author: Mobius (Beijing Yuding Technology Co., Ltd.)
license: MIT
---

# ResearchPro - 你的商业情报顾问 (v1.4.5)

ResearchPro 是一款专为商业决策者设计的深度调研工具。它集成了 Tavily AI 搜索引擎，通过智能信源分级体系（S/A/B/C），为你提供精准、可靠的市场洞察。

## 🛡️ v1.4.5 安全增强特性

本次更新专注于修复安全扫描发现的问题：

*   **移除硬编码密钥**：PostHog API Key 强制从环境变量读取，禁止默认值 fallback。
*   **清理过期签名**：OSS 资源链接移除临时签名参数，使用公开读权限的永久链接。
*   **依赖漏洞修复**：升级 `requests>=2.32.3`，修复 CVE-2023-32681、CVE-2024-35195 等已知漏洞。
*   **原子写入机制**：配置文件与配额文件采用临时文件重命名策略，防止崩溃导致数据损坏。
*   **代码精简**：禁用未完成的腾讯云引擎调用，避免不完整签名逻辑带来的安全风险。
*   **输入验证增强**：`sanitize_input` 函数过滤危险字符并限制长度，防止命令注入与路径遍历。

## ✨ 核心功能

*   **Tavily 引擎集成**：全球实时搜索，覆盖科技、金融、政策等多领域信息源。
*   **信源分级**：自动识别并标注信息来源可信度（S/A/B/C 四级），让决策更有底气。
*   **情感化交互**：告别冷冰冰的代码报错，提供温暖、建设性的引导建议。
*   **多模板支持**：涵盖学术研究、商业调研、快速验证及微信生态专项模板。
*   **离线缓存**：支持搜索结果本地缓存，减少重复查询的 API 消耗。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key（可选）
v1.4.5 版本已预置平台 Tavily Key，开箱即用。如需更高额度，可配置自有 Key：
```bash
python main.py --setup
```
或通过环境变量设置：
```bash
set TAVILY_API_KEY=your_api_key_here
```

### 3. 启动调研
```bash
# 交互向导模式（推荐新手）
python main.py --wizard

# 命令行直达模式
python main.py --query "2026 年智能家居行业趋势"
```

## 📊 商业化说明

*   **免费额度**：每个设备终身享有 **2 次** 免费深度调研额度。
*   **身份识别**：基于硬件指纹（Machine ID SHA-256）进行唯一标识。
*   **技术支持**：如需获取更多额度或定制方案，请添加微信：**Mobius_Lee**。

## 🔒 安全合规

*   **零隐私泄露**：埋点数据仅上报设备哈希值与查询长度，不采集个人身份信息。
*   **本地配额管理**：所有配额数据存储于本地加密目录，不上传云端。
*   **开源审计**：核心代码完全开放，欢迎安全社区提交 PR 或 Issue。

---
*© 2026 Beijing Yuding Technology Co., Ltd. All rights reserved.*
