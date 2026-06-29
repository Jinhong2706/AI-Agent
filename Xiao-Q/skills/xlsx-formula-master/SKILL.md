---
name: xlsx-formula-master
displayName: Excel 公式翻译官(人话→公式)
slug: xlsx-formula-master
version: 1.0.0
author: ikun
license: MIT
language: zh-CN
description: |
  你描述需求(人话)，它给你 Excel / WPS 公式 + 解释 + 不踩坑的边界条件。
  专攻 VLOOKUP / XLOOKUP / INDEX-MATCH / SUMIFS / 数组公式 / 动态数组 / Power Query 等高频但易错场景。
  自动适配你的 Excel 版本（2019 / 365 / WPS）——版本不同公式可能不能用。
  触发：用户说 "Excel 公式"、"VLOOKUP"、"怎么算"、"WPS 公式"、"求和怎么写"、"匹配数据"、"数据透视"。
keywords: ["Excel 公式", "WPS 公式", "VLOOKUP", "XLOOKUP", "INDEX MATCH", "SUMIFS", "COUNTIFS", "数组公式", "动态数组", "Power Query", "Excel 翻译"]
---

# Excel 公式翻译官

## 这个 skill 解决什么

Excel 用户的两大痛点：
1. **知道想要什么，不知道用哪个公式** —— "我想要 A 列每个值在 B 列出现几次" 不知道是 COUNTIF
2. **公式是 ChatGPT 给的，但用了报错** —— 因为 Excel 版本 / 中英文 / 区域差异

这个 skill 干 3 件事：
1. **翻译**：自然语言需求 → 可执行的 Excel / WPS 公式
2. **解释**：每个参数是什么意思，为什么这么写
3. **避坑**：边界条件（空值 / 错误值 / 大小写 / 文本数字混排），不同版本兼容性

**不做的事**：不做 VBA 宏（那是 `xlsx-vba-zh` 的活，本 skill 只覆盖公式）；不做数据透视表的可视化设计。

---

## 公式知识地图（按使用频率排）

```
查找匹配类（用得最多）
├─ VLOOKUP（兼容性好，但只能从左往右）
├─ XLOOKUP（2021/365 才有，最强）
├─ INDEX + MATCH（VLOOKUP 不够时的万能替代）
└─ HLOOKUP（横向查找，用得少）

条件聚合类
├─ SUMIF / SUMIFS（按条件求和）
├─ COUNTIF / COUNTIFS（按条件计数）
├─ AVERAGEIF / AVERAGEIFS（按条件平均）
└─ MAXIFS / MINIFS（条件最值，2019+）

文本处理类
├─ LEFT / RIGHT / MID（截取）
├─ FIND / SEARCH（查找位置）
├─ SUBSTITUTE / REPLACE（替换）
├─ TEXTJOIN（连接，2019+）
└─ TEXTSPLIT（拆分，365 才有）

日期时间类
├─ TODAY / NOW（当前）
├─ DATEDIF（日期差，隐藏函数）
├─ EOMONTH / EDATE（月末 / N 月后）
└─ NETWORKDAYS（工作日，要排除节假日）

数组 / 动态数组（365 / 2021+ 才有）
├─ FILTER（条件筛选）
├─ UNIQUE（去重）
├─ SORT / SORTBY（排序）
└─ LET / LAMBDA（自定义命名 / 函数，超强但少有人用）

逻辑判断类
├─ IF / IFS（条件分支）
├─ AND / OR / NOT
├─ IFERROR / IFNA（错误兜底）
└─ SWITCH（多分支）
```

---

## 6 个最常踩的坑

### 坑 1：VLOOKUP 只能从左往右

```
❌ 错的：=VLOOKUP(A2, D:F, -1, FALSE)   --- 左查找 VLOOKUP 不行
✓ 对的：=INDEX(C:C, MATCH(A2, D:D, 0))   --- INDEX+MATCH 万能
✓ 365：=XLOOKUP(A2, D:D, C:C)             --- 最简单
```

### 坑 2：精确匹配第 4 参数必须 FALSE / 0

```
❌ 错的：=VLOOKUP(A2, D:F, 2)             --- 默认 TRUE 是模糊匹配
✓ 对的：=VLOOKUP(A2, D:F, 2, FALSE)
       =VLOOKUP(A2, D:F, 2, 0)
```

模糊匹配会按 D 列的"接近值"匹配，结果完全错。

### 坑 3：单元格里看着是数字其实是文本

现象：SUM 出来是 0，VLOOKUP 找不到。

诊断：=ISTEXT(A2) 看是否返回 TRUE。

修：=VALUE(A2) 或选中列 → 数据 → 分列 → 完成（强制转数字）。

### 坑 4：SUMIFS 条件区域和求和区域行数不一致

```
❌ =SUMIFS(B2:B100, A:A, "苹果")   --- B 是 99 行，A 是整列，报错
✓ =SUMIFS(B:B, A:A, "苹果")       --- 都用整列
✓ =SUMIFS(B2:B100, A2:A100, "苹果") --- 都精确范围
```

### 坑 5：日期被识别成数字（比如 45000）

现象：单元格显示日期，但参与计算变成 5 位数字。

修：单元格格式 → 日期。**或者公式里包一层** `TEXT(A2, "yyyy-mm-dd")`。

### 坑 6：中英文 Excel 公式名不同（罕见但坑）

中文 Excel 默认中文公式名（如 `求和` 而非 `SUM`），跨电脑复制会报错。

修：统一用英文公式名（在选项里把"使用 R1C1 引用样式"关掉，公式还是英文）。

---

## 高频场景模板

### 场景 1：两表匹配查找

> "Sheet1 的 A 列是订单号，要从 Sheet2 里把对应的客户名匹配过来"

```
Excel 2021 / 365：
=XLOOKUP(A2, Sheet2!A:A, Sheet2!B:B, "未找到")

Excel 2019 / WPS：
=IFERROR(VLOOKUP(A2, Sheet2!A:B, 2, 0), "未找到")
```

### 场景 2：按条件求和

> "把 A 列是『一般纳税人』且 B 列日期在 2024 年的 C 列金额加起来"

```
=SUMIFS(C:C, A:A, "一般纳税人",
        B:B, ">="&DATE(2024,1,1),
        B:B, "<="&DATE(2024,12,31))
```

### 场景 3：文本拆分（中文姓名分姓和名）

```
单字姓（如 "张三"）：
姓=LEFT(A2,1)
名=MID(A2,2,LEN(A2)-1)

复姓（如 "欧阳锋"）—— 需先建复姓清单 D:D：
姓=IF(COUNTIF(D:D, LEFT(A2,2))>0, LEFT(A2,2), LEFT(A2,1))
名=MID(A2, LEN(姓)+1, 99)
```

### 场景 4：去重计数

> "A 列有重复的订单号，统计有多少个不重复订单"

```
Excel 365：
=COUNTA(UNIQUE(A:A))-1   --- 减 1 是去掉表头

Excel 2019 / WPS：
=SUMPRODUCT(1/COUNTIF(A2:A1000, A2:A1000))
```

### 场景 5：条件最大值（多条件）

> "找出 A 列是『北区』且 B 列大于 0 的 C 列最大值"

```
2019+ 直接：
=MAXIFS(C:C, A:A, "北区", B:B, ">0")

旧版 ：
{=MAX(IF((A:A="北区")*(B:B>0), C:C))}   --- 数组公式 Ctrl+Shift+Enter
```

### 场景 6：日期工龄计算

```
=DATEDIF(B2, TODAY(), "Y") & "年" &
 DATEDIF(B2, TODAY(), "YM") & "个月"
```

DATEDIF 是隐藏函数，输入时不会自动提示但能用。

---

## AI 执行流程

### 第一步：摸需求

如果用户没说清楚，问：
1. **你用的是 Excel 几版 / WPS？**（决定能不能用 XLOOKUP / FILTER 等）
2. **数据大概长什么样？**（行数、列、有没有表头、空值情况）
3. **你想要的结果是什么样？**（具体例子最好）
4. **这个公式是只算 1 次还是要拖填整列？**（影响 $ 锁定方式）

### 第二步：选公式

- 优先 XLOOKUP > VLOOKUP（如果版本支持）
- 优先内置函数 > 数组公式（数组公式难维护）
- 多条件 → SUMIFS / COUNTIFS（不要 SUM(IF) 数组）
- 文本处理 → 优先 TEXTJOIN / TEXTSPLIT（如果版本支持）

### 第三步：写公式 + 解释

输出 3 部分：
```
【公式】
=...

【参数解释】
- 参数 1：XX，含义是 XX
- 参数 2：XX，含义是 XX
...

【边界条件】
- 如果 XX 情况会怎样？→ 用 IFERROR 兜底：=IFERROR(原公式, "默认值")
- 如果 XX 数据类型问题 → 用 VALUE / TEXT 转换
- 如果跨版本 → 兼容写法是 XX

【拖填注意】
- 列锁定 / 行锁定（$A$1 vs $A1 vs A$1 vs A1）的选择
```

### 第四步：自检 checklist

- [ ] 公式在用户说的版本（2019 / 365 / WPS）能用？
- [ ] 边界异常处理了？（找不到值、除以 0、文本数字混排）
- [ ] 拖填时引用方式对？（要不要 $）
- [ ] 没用到隐藏函数 / 罕见函数？用了的话提示用户
- [ ] 中英文公式名一致？

---

## 输出格式

```markdown
## 你的需求
（用一句话复述用户的需求，确认理解一致）

## 推荐公式（你的版本：Excel 2019）

```
=IFERROR(VLOOKUP(A2, Sheet2!A:B, 2, 0), "未找到")
```

## 怎么用
1. 在 Sheet1 的 C2 输入此公式
2. 双击 C2 右下角小方块，自动拖填到底
3. C 列就是匹配到的客户名

## 参数解释
- A2：要查找的订单号
- Sheet2!A:B：在 Sheet2 的 A-B 列里找
- 2：返回 B 列（匹配区域第 2 列）
- 0：精确匹配（一定要写）
- IFERROR：兜底，找不到时返回"未找到"而不是 #N/A

## 注意事项
- 如果 A2 是数字但显示是文本（左上角有绿三角），先选中列 → 分列 → 完成
- 如果你升级到 365 / 2021，可以换成更简单的 XLOOKUP

## 备选方案（如果上面不行）
（XLOOKUP 写法 + INDEX/MATCH 写法）
```

---

## 终止条件

- 用户拿到了能跑的公式
- 解释 + 边界条件 + 拖填说明都给了
- 用户没追问"为什么不行" / "还能怎么写"

不主动写 VBA / 数据透视表 / Power Query（除非用户要求）。
