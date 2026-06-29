# 常见问题与故障排查

## 分析相关

**Q: 提示"数据不足"？**
A: 股票历史数据少于20个数据点。排查：
1. 检查股票代码是否正确（6位数字，沪市60开头，深市00/30开头）
2. 新股或停牌股数据不足，换只老股票试试
3. 使用 long 周期：`--period long`

**Q: 分析结果输出空白/没有任何内容？**
A: 通常是网络问题导致数据获取失败。排查：
1. 检查网络是否通畅
2. 换只股票代码重试
3. 如果所有股票都空白，可能是腾讯财经API临时不可用，稍后再试

**Q: 三维预测评分感觉像"掷骰子"？**
A: 评分基于"当前条件与历史相似案例的统计对比"，不是确定性预测。73分意味着"历史上73个类似条件中有上涨"，但市场随时可能打破历史规律。**请结合自己的判断使用**。

**Q: KDJ指标数值很奇怪？**
A: KDJ需要历史平滑值，如果数据点太少（<30天）结果会失真。建议用 `--period medium` 或 `--period long` 获取更多数据。

**Q: 雪球数据获取失败？**
A: 雪球需要登录cookie。如果不需要雪球数据，东方财富股吧的情绪分析可正常匿名使用。

## 网络/数据相关

**Q: 网络获取失败/超时？**
A: 最常见的问题。腾讯财经和东方财富API在国内通常可用，但偶有波动：
1. 稍后重试（等待1-2分钟）
2. 检查是否开了VPN/代理（可能干扰国内API访问）
3. 如果频繁失败，检查 DNS 设置

**Q: 实时行情和实际价格不一致？**
A: 腾讯财经行情有几秒到几分钟的延迟，属于正常现象。如需精确实时价格请查看券商软件。

**Q: 财务数据是上季度的？**
A: 财务数据在季报/年报披露后更新，存在4-8周延迟。这是所有公开数据源的共性。

## 导出/导入相关

**Q: PPT报告导出失败？**
A: 常见原因：
1. `ModuleNotFoundError: No module named 'pptx'` → `pip install python-pptx`
2. 文件写入权限问题 → 检查输出目录是否有写权限

**Q: PDF报告导出失败？**
A: 需要 reportlab 库：`pip install reportlab`

**Q: 截图OCR识别不准？**
A: OCR准确率取决于截图质量。技巧：高清截图、字体清晰、包含股票代码列、背景干净。

**Q: Excel导出打不开？**
A: 需要 openpyxl：`pip install openpyxl`

## 报错速查表

| 报错信息 | 原因 | 解决 |
|---------|------|------|
| `ModuleNotFoundError: No module named 'requests'` | 核心依赖未装 | `pip install requests beautifulsoup4 lxml` |
| `ModuleNotFoundError: No module named 'pptx'` | PPT依赖未装 | `pip install python-pptx` |
| `ModuleNotFoundError: No module named 'reportlab'` | PDF依赖未装 | `pip install reportlab` |
| `ModuleNotFoundError: No module named 'pytesseract'` | OCR依赖未装 | `pip install pytesseract pillow` + Tesseract系统包 |
| `ModuleNotFoundError: No module named 'akshare'` | 数据依赖未装 | `pip install akshare` |
| `数据不足` / `Insufficient data` | 历史数据点<20 | 换 `--period long` 或换只股票 |
| `ConnectionError` / `Timeout` | 网络不通 | 检查网络，稍后重试，关VPN |
| `JSONDecodeError` | API返回异常 | 接口临时故障，稍后重试 |
| `PermissionError` | 文件写入权限 | 检查输出目录权限 |
| 输出空白无报错 | 数据获取被吞 | 网络问题，换股票/换时间重试 |

## 容错机制

| 场景 | 工具行为 | 你需要做的 |
|------|---------|-----------|
| 单只股票网络失败 | 跳过该只，继续分析其他 | 重新执行命令 |
| 所有股票都失败 | 输出空白或简短错误 | 检查网络后重试 |
| 雪球需要登录 | 跳过雪球，只用东方财富 | 不影响核心功能 |
| API返回格式变了 | 可能解析出错 | 等待工具更新 |
