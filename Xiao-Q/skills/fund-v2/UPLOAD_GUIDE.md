# 基金评价 Skill 上传到 KimiClaw 指南

## 已创建的文件

```
fund-evaluation/
├── SKILL.md                      # Skill 描述文件（必需）
└── scripts/
    └── fund_evaluator.py         # 基金评价脚本

fund-evaluation.skill             # 打包后的 skill 文件（zip格式）
```

## Skill 功能

- **获取基金季度持仓**：从天天基金网获取基金前十大重仓股数据
- **季度持仓对比**：对比两个季度的持仓变化（新增、清仓、仓位调整）
- **数据导出**：支持导出CSV格式
- **命令行支持**：可直接通过命令行使用

## 上传到 KimiClaw 的步骤

### 方法1：通过 KimiClaw Web 界面上传

1. 访问 KimiClaw 网站（https://claw.kimi.com）
2. 登录你的账号
3. 进入 **Skills** 或 **技能市场** 页面
4. 点击 **上传 Skill** 或 **发布 Skill**
5. 上传 `fund-evaluation.skill` 文件
6. 填写相关信息：
   - **名称**：基金评价
   - **描述**：中国公募基金评价分析工具，支持获取基金基本信息、季度持仓数据、持仓变动对比、业绩分析等功能
   - **标签**：基金、投资、数据分析、Python
   - **可见性**：选择公开或私有
7. 点击 **提交审核** 或 **发布**

### 方法2：通过 KimiClaw CLI 上传

```bash
# 安装 KimiClaw CLI（如果未安装）
pip install kimiclaw

# 登录
kimiclaw login

# 上传 skill
kimiclaw skill upload fund-evaluation.skill

# 或者指定详细信息
kimiclaw skill upload fund-evaluation.skill \
  --name "基金评价" \
  --description "中国公募基金评价分析工具" \
  --tags "基金,投资,数据分析"
```

### 方法3：通过 KimiClaw API 上传

```bash
# 使用 curl 上传
curl -X POST https://api.claw.kimi.com/v1/skills \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@fund-evaluation.skill" \
  -F "name=基金评价" \
  -F "description=中国公募基金评价分析工具"
```

## 使用方法

安装 skill 后，Kimi 会自动识别相关请求并加载 skill。

### 触发词示例

- "帮我分析一下基金 519702 的持仓"
- "获取交银趋势优先的季度持仓数据"
- "对比 519702 最近两个季度的持仓变化"
- "导出基金 519702 的持仓到 CSV"

### 代码中使用

```python
import sys
sys.path.insert(0, 'fund-evaluation/scripts')
from fund_evaluator import FundEvaluator

evaluator = FundEvaluator()

# 获取持仓
result = evaluator.get_holdings("519702")
evaluator.print_holdings(result)

# 季度对比
evaluator.compare_quarters("519702")

# 导出CSV
evaluator.export_to_csv(result, "output.csv")
```

## Skill 文件说明

| 文件 | 大小 | 说明 |
|------|------|------|
| fund-evaluation.skill | ~5KB | 打包后的 skill 文件 |

## 更新 Skill

如需更新 skill：

1. 修改 `SKILL.md` 或 `scripts/fund_evaluator.py`
2. 重新打包：`zip -r fund-evaluation.skill fund-evaluation`
3. 重新上传到 KimiClaw

## 支持的数据源

- **天天基金网** (fundf10.eastmoney.com)：主要数据来源
- **Wind API**（可选扩展）：可作为备用数据源

## 支持的基金类型

- 股票型基金
- 混合型基金
- 债券型基金（持仓以债券为主）
- QDII基金

## 注意事项

1. 数据来源于天天基金网公开数据，仅供研究参考
2. 季报数据有滞后性，最新持仓可能与当前实际情况有差异
3. 部分新成立基金可能数据不完整
