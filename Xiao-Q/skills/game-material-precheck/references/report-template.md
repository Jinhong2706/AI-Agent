# HTML审核报告模板规范

生成游戏素材合规审核报告时，按以下结构组织。可自由调整样式，但必须保留核心信息。

## 文件命名

建议文件名：

```text
游戏素材合规审核报告_YYYYMMDD.html
```

若同日多次生成，可加版本号：

```text
游戏素材合规审核报告_YYYYMMDD_v2.html
```

## HTML结构

### 1. 头部信息

包含：

- 报告标题：游戏素材合规审核报告
- 审核日期
- 目标地区
- 素材数量
- 素材用途
- 发布日期：已定 / 未定
- 审核依据：乐享知识库 + 外部公开检索

### 2. 素材预览区

每个素材生成一个卡片：

- 素材编号
- 图片预览
- 用户原始文件名或截图名称
- 画面描述
- OCR/文案内容（如有）

图片嵌入方式优先级：

1. 将图片复制到报告同目录 `assets/` 下，并使用相对路径引用。
2. 或使用 base64 data URI 嵌入，适合单文件交付。
3. 若图片无法读取，则保留占位框并说明「图片未能嵌入，已基于用户描述审核」。

### 3. 风险总览表

字段：

| 素材 | 综合等级 | 结论 | 关键风险 | 必须动作 |
| --- | --- | --- | --- | --- |

结论枚举：

- 可上线
- 修改后上线
- 不建议上线
- 需法务/合规复核
- 信息不足，需补充材料

### 4. 单素材风险明细

字段：

| 风险维度 | 风险等级 | 问题描述 | 依据 | 修改建议 |
| --- | --- | --- | --- | --- |

维度建议：

- 内容合规
- 政策与社会秩序
- 知识产权
- 广告与运营
- 未成年人保护
- 文化/宗教/民族
- 战争/军事/国旗
- 舆情风险
- 敏感日期

### 5. 敏感日期排查

若发布日期已定：

- 核查当天、前后 3 天、同周是否有严肃纪念日或重大社会事件。
- 输出「是否建议发布」。

若发布日期未定：

- 输出通用避让清单。
- 对战争/军人/灾难/废墟/历史题材素材特别提醒避开严肃纪念日。

### 6. 外部舆情与平台规则参考

列出核心参考来源名称：

- 平台审核规范：华为、字节/抖音、支付宝、网易等。
- 舆情案例：近期游戏文案争议、IP侵权争议、AI生成争议、节日营销争议等。
- 敏感日期来源：国家公祭网、主流新闻媒体、公开百科等。

不要堆砌过多链接；保留 3-6 条关键依据即可。

### 7. 综合结论与下一步动作

输出：

- 总体结论
- 是否建议上线
- 必改项
- 建议项
- 需补充材料
- 是否建议二次复审

### 8. 免责声明

固定添加：

```text
本报告为素材发布前合规初筛意见，基于当前可见素材、乐享知识库内容及公开信息检索形成。最终上线结论请以法务/合规部门正式审核意见为准。
```

## 推荐CSS风格

```css
body {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f5f6fa;
  color: #222;
  margin: 0;
}
.container {
  max-width: 1080px;
  margin: 32px auto;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08);
  padding: 40px 44px 48px;
}
h1 {
  font-size: 28px;
  margin: 0 0 12px;
}
h2 {
  font-size: 20px;
  margin: 32px 0 16px;
  padding: 10px 14px;
  background: #f0f4ff;
  border-left: 5px solid #457bff;
  border-radius: 0 8px 8px 0;
}
.material-card {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
  margin: 16px 0;
  background: #ffffff;
}
.material-card img {
  width: 100%;
  max-height: 520px;
  object-fit: contain;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #111827;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 24px;
  font-size: 14px;
}
th {
  background: #111827;
  color: #fff;
  padding: 10px 12px;
  text-align: left;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #edf2f7;
  vertical-align: top;
}
.badge-p0 { background: #fee2e2; color: #991b1b; }
.badge-p1 { background: #ffedd5; color: #9a3412; }
.badge-p2 { background: #fef3c7; color: #92400e; }
.badge-p3 { background: #dbeafe; color: #1e40af; }
.badge-ok { background: #dcfce7; color: #166534; }
.badge {
  display: inline-block;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 700;
}
.note {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 10px;
  padding: 12px 14px;
  color: #7c2d12;
}
```

## 报告语气

保持专业、明确、可执行：

- 用「建议」「需」「必须」区分强度。
- 对不确定项标注「疑似」「需确认」「需授权证明」。
- 不要为了显得严厉而扩大风险。
- 不要使用空泛表述，修改建议必须能落地。
