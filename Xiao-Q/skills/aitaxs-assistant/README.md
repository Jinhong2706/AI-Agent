# AiTaxs 综合财税 AI 助手

<div align="center">

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-WorkBuddy%20%7C%20CodeBuddy-orange)
![Category](https://img.shields.io/badge/category-财税-red)

**面向个体工商户和小微企业主的一站式 AI 财税助手**

涵盖税务问答 · 精确计税 · 发票指导 · 申报提醒 · 节税建议

</div>

---

## 🚀 一键安装

### 方式一：通过仓库地址安装（推荐）

在 WorkBuddy / CodeBuddy 对话框输入：

```
/plugin marketplace add https://github.com/XHJ2AIDEVS/aitaxs-assistant.git
```

然后安装插件：

```
/plugin install aitaxs-assistant
```

### 方式二：本地 zip 安装

1. 下载 [aitaxs-assistant.zip](https://github.com/XHJ2AIDEVS/aitaxs-assistant/releases/latest)
2. 打开 WorkBuddy → 技能市场 → 从本地安装
3. 选择下载的 zip 文件

---

## ✨ 核心功能

| 功能模块 | 说明 | 触发关键词 |
|---|---|---|
| 🧮 **税额精确计算** | 工资个税 / 经营所得 / 增值税 / 企业所得税，含完整计算过程 | 帮我算个税、增值税多少、税负计算 |
| 📖 **税务知识问答** | 解读最新税率、优惠政策、申报规则 | 小规模纳税人、增值税率、税收优惠 |
| 🧾 **发票处理指导** | 增值税专票/普票/电子发票的开具、抵扣、报销合规操作 | 发票、抵扣、报销 |
| 📅 **申报提醒** | 各税种申报周期、操作步骤、逾期风险提示 | 什么时候报税、申报截止 |
| 💡 **节税建议** | 基于经营情况提供合法合规的税负优化方案 | 节税、降低税负、合理避税 |
| 🖥️ **H5 可视化界面** | 内置交互式计算页面，无需命令行操作 | 打开税务计算器、H5 界面 |

---

## 📊 支持税种

- **个人所得税**：工资薪金、经营所得（含 9 项专项附加扣除）
- **增值税**：小规模纳税人（3%/1%）、一般纳税人（6%/9%/13%）
- **企业所得税**：标准税率 25%、小微企业优惠（100万以内5%、300万以内10%）
- **印花税**：合同类、产权转移类

---

## 🎯 使用示例

**示例 1：工资个税计算**
```
我月薪 25000 元，有房贷 1000 元/月、子女教育 1000 元/月，请帮我算个税
```
> 应纳税所得额：25000 - 5000（起征点）- 1000（房贷）- 1000（子女）= 18000
> 税率：20%，速算扣除数：1410
> **应纳个税：18000 × 20% - 1410 = 2190 元/月**

---

**示例 2：小规模增值税**
```
我是个体户，季度含税销售额 28 万，增值税怎么算？
```
> 依据财政部、税务总局 2026 年第 10 号公告：2026-01-01 至 2027-12-31，小规模纳税人季度销售额 ≤ 30 万元免征增值税
> 你的季度销售额 28 万 < 30 万，**本季度增值税免征**

---

**示例 3：打开 H5 计算器**
```
打开税务计算器
```
> AI 自动打开内置 H5 界面，支持可视化输入计算

---

## 📁 仓库结构

```
aitaxs-assistant/
├── SKILL.md                    # AI 行为定义（核心）
├── plugin.json                 # 插件市场清单
├── marketplace.json            # 自定义市场索引
├── README.md                   # 本文件
├── .gitignore
├── .github/workflows/
│   └── validate.yml            # CI 自动校验
├── assets/
│   └── index.html              # H5 可视化交互界面
├── references/
│   └── tax-knowledge.md        # 税率表、政策文档
└── scripts/
    └── tax_calculator.py       # 税额计算脚本
```

---

## 🔧 计算脚本直接调用

```bash
# 工资个税
python scripts/tax_calculator.py --type salary --income 20000 --deductions 3000

# 经营所得个税（自动按 2023-2027 年个体户减半征税优惠测算）
python scripts/tax_calculator.py --type business --annual-profit 200000

# 增值税（小规模）
python scripts/tax_calculator.py --type vat --sales 280000

# 企业所得税
python scripts/tax_calculator.py --type corp --profit 1500000
```

---

## 📋 版本历史

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v1.2.0 | 2026-04-01 | 对齐 2026 年税收政策：更新小规模纳税人增值税优惠、个体工商户 200 万以内减半征税、小型微利企业统一 5% 实际税负、专项附加扣除与印花税税目；同步修正 CLI 示例 |
| v1.1.0 | 2026-03-13 | 新增 H5 可视化界面；完善企业所得税小微优惠计算；增加 plugin.json 市场规范 |
| v1.0.0 | 2026-03-01 | 初始版本，支持四大税种计算 |

---

## 📜 许可证

MIT License — 自由使用、修改、分发，保留作者署名即可。

---

## 💬 联系作者

- **QQ：** 1817694478
- **微信：** jacky_zhouxj

> ⚠️ 本工具仅供参考，税务计算结果请以国家税务总局官网及专业税务师意见为准。
