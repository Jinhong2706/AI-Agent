# reverse-engineering-fusion v2.0

> 逆向工程融合技能 - ORRI方法论实现

## 🎯 概述

本技能提供一套系统化的逆向工程方法论,用于理解和融合外部系统的核心设计思想。

**核心原则**:逆向工程不是复制代码,而是理解原理后重新实现。

## ✨ 特性

- ✅ **ORRI方法论** - 观察→逆向→重建→创新四步法
- ✅ **融合四层次** - 功能层/协议层/架构层/原理层
- ✅ **完整实现** - 可运行的NES协议解析器和编辑引擎
- ✅ **多LLM支持** - MiniMax、火山方舟等适配器
- ✅ **详细文档** - 协议规范、参考实现、测试用例

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件,填写你的 API Key
```

### 3. 运行测试

```bash
npm test
```

### 4. 在 OpenClaw 中使用

当提到以下关键词时自动激活:
- "逆向工程融合"
- "ORRI方法"
- "提取协议格式"
- "NES协议解析"

## 📖 文档结构

```
reverse-engineering-fusion/
├── SKILL.md                    # 完整的方法论文档 (必读)
├── CLAUDE.md                   # OpenClaw激活规则
├── README.md                   # 本文件
├── package.json                # Node.js项目配置
├── tsconfig.json               # TypeScript配置
├── .env.example                # 环境变量示例
├── src/
│   └── nes-completion.ts      # 可运行的完整实现 ⭐
├── scripts/
│   └── test-nes.ts            # 集成测试脚本
└── references/
    ├── nes-protocol.md        # NES协议规范
    ├── parser-implementation.ts # 解析器参考实现
    └── engine-implementation.ts # 编辑引擎参考实现
```

## 💡 核心方法论:ORRI

### ① Observation(观察)
- 只看不改,记录输入输出
- 识别关键文件和边界条件
- 理解UI/UX交互流程

### ② Reverse(逆向)
- 提取通信协议格式
- 分析数据流和控制流
- 重建架构图和时序图

### ③ Reconstruct(重建)
- 先实现协议层(最稳定)
- 再实现数据转换层
- 最后实现业务逻辑层

### ④ Innovate(创新)
- 解决原系统的已知问题
- 扩展原系统未有的功能
- 与自有系统深度融合

## 🎯 典型案例:通义灵码 NES 系统融合

### 背景

- **目标**:提取通义灵码代码补全协议
- **约束**:不能直接用通义灵码API
- **资源**:使用自有AI模型(MiniMax/火山方舟)

### 协议格式

```xml
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>15</next_start_line>
    <next_end_line>15</next_end_line>
    <next_content>新代码</next_content>
  </next_edit>
</actions>
```

### 融合成果

| 组件 | 状态 | 说明 |
|------|------|------|
| 协议解析器 | ✅ | 完全自主实现 |
| 编辑引擎 | ✅ | 完全自主实现 |
| AI适配器 | ✅ | 接入火山方舟/MiniMax |
| 功能对齐 | ✅ | 与通义灵码兼容 |

## 📝 输出产物

完成逆向工程融合后,必须产出:

- [ ] **protocol.md** - 协议格式定义
- [ ] **architecture.md** - 架构设计文档
- [ ] **implementation.md** - 实施报告
- [ ] **maintenance.md** - 维护指南

## ⚠️ 常见错误

| 错误 | 规避方法 |
|------|----------|
| 陷入代码细节 | 先画架构图 |
| 迷信单一系统 | 保留自主核心 |
| 忽略边界条件 | 系统整理测试 |
| 缺乏文档 | 每步都要记录 |
| 硬编码敏感信息 | 使用环境变量 |

## 🔗 相关资源

- [SKILL.md](./SKILL.md) - 完整的方法论文档
- [CLAUDE.md](./CLAUDE.md) - OpenClaw激活规则
- [NES协议详解](./references/nes-protocol.md)
- [可运行实现](./src/nes-completion.ts)

---

**版本**:2.0.0  
**作者**:AI融合团队  
**更新**:2026-04-05  
**许可证**:MIT
