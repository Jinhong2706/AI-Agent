---
name: futures-monitor
description: >
  期货实时数据监测系统，覆盖国内全部 6 大期货交易所 90+ 主力合约品种。
  当用户提到期货监测、期货行情、期货看板、期货仪表盘、主力合约、期货实时数据、
  启动期货系统、期货监控、期货数据看板、commodity monitoring、futures dashboard 时使用此技能。
  可一键启动本地 Web 服务，提供市场概览、涨跌排行、品种详情（日线/分钟线/持仓排名/仓单/结算参数）等功能。
metadata:
  copyright: 版权所有 天津创锐丰科技有限公司
  author: 黄军雷
  version: "2.1.0"
  website: https://www.crf.net.cn
---

# 期货实时监测系统

**版权所有 © 天津创锐丰科技有限公司 | 作者：黄军雷 | 官网：www.crf.net.cn**

一句话启动本地期货监测仪表盘——覆盖 6 大交易所、90+ 主力合约、零外部依赖。

---

## 工作流程

```
用户请求 → 部署模板文件 → 启动 Python 服务 → 打开浏览器
```

### 步骤 1：部署模板文件

将 `assets/server.py` 和 `assets/index.html` 复制到工作目录：

```
{workspace}/futures-monitor/
├── server.py          # 后端服务（从 assets/server.py 复制）
└── static/
    └── index.html     # 前端仪表盘（从 assets/index.html 复制到 static/）
```

**具体操作**：
1. 在工作目录下创建 `futures-monitor/static/` 目录
2. 将 `assets/server.py` 复制为 `futures-monitor/server.py`
3. 将 `assets/index.html` 复制为 `futures-monitor/static/index.html`

### 步骤 2：启动服务

```bash
cd {workspace}/futures-monitor
python server.py
```

服务默认在 `http://127.0.0.1:8765` 启动，会自动打开浏览器。

**可选参数**：
- `-p 9000` — 自定义端口
- `--no-browser` — 不自动打开浏览器

### 步骤 3：确认启动

启动后向用户报告：
- 本机访问地址
- 跟踪品种数量（90+）
- 可用功能：市场概览、涨跌排行、品种详情（日线/分钟线/持仓/仓单/结算/预警/盈亏）

---

## 系统功能

| 功能 | 说明 |
|------|------|
| 🔔 价格预警 | 设定涨破/跌破规则，触发时弹窗+Toast通知，自动持久化到文件 |
| 💰 盈亏计算 | 输入开仓价/手数，自动拉当前价，秒出盈亏/收益率/保证金占用 |
| 市场概览 | 涨跌统计、涨幅榜/跌幅榜 TOP5 |
| 行情表格 | 主力合约最新行情，按交易所/类别筛选，列排序 |
| 品种详情 | 30天日线走势图、分钟分时图（切换tab自动加载） |
| 持仓排名 | 前20名期货公司多空持仓，新增席位汇总行 |
| 仓单数据 | 各仓库仓单变化 |
| 结算参数 | 保证金率、手续费率 |
| 自动刷新 | 30秒/1分钟/5分钟可选 |

## 技术说明

- **后端**：纯 Python 标准库（http.server），无需 pip install
- **前端**：HTML/CSS/JS + ECharts 5.5 交互图表，深色主题
- **数据源**：通过 WorkBuddy finance-data API 获取
- **性能**：LRU 缓存（1000 条上限）+ ThreadPoolExecutor（10 并发）+ 指数退避重试（3 次）
- **图表**：ECharts K 线图（candlestick + 成交量 + 持仓线）、分时图（折线 + 标记线），支持 tooltip、缩放、legend
- **快捷键**：R 刷新、Esc 关闭弹窗

## 启动参数

- `-p 9000` — 自定义端口
- `--no-browser` — 不自动打开浏览器
- `--workers 10` — 并发线程数（默认 10）
- `--cache-size 1000` — 缓存上限（默认 1000）

## API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/daily` | 全部主力合约最新日线 |
| `GET /api/daily?exchange=SHFE` | 按交易所筛选 |
| `GET /api/summary` | 市场概览统计 |
| `GET /api/detail?ts_code=CU.SHF` | 合约详情（30天） |
| `GET /api/minute?ts_code=CU.SHF&freq=5MIN` | 实时分钟线 |
| `GET /api/holding?symbol=CU&exchange=SHFE` | 持仓排名 |
| `GET /api/warehouse?symbol=CU&exchange=SHFE` | 仓单数据 |
| `GET /api/settle?ts_code=CU.SHF` | 结算参数 |
| `GET /api/limit?ts_code=CU.SHF` | 涨跌停价格 |
| `GET /api/contracts` | 主力合约列表 |
| `GET /api/alerts` | 获取全部预警规则 |
| `GET /api/alerts/check` | 检查预警触发状态 |
| `POST /api/alerts/add` | 新增预警规则 |
| `POST /api/alerts/delete` | 删除预警规则 |
| `POST /api/alerts/toggle` | 启用/禁用预警规则 |
| `POST /api/pnl` | 盈亏计算 |

---

## Resources

### assets/
- `server.py` — 后端服务模板（复制到目标目录即可运行）
- `index.html` — 前端仪表盘模板（需放入 static/ 子目录）

---

## 变更日志

### v2.1.0（2026-04-12）

**新增功能：**
- 🔔 **价格预警**：支持涨破/跌破两种预警类型，触发时弹窗+Toast通知，自动持久化到 `alert_rules.json`，支持暂停/恢复/删除
- 💰 **盈亏计算**：选择品种→填入开仓价，自动拉取当前价，一键计算盈亏/收益率/保证金占用，支持"我的持仓"本地保存
- 📊 **持仓排名汇总**：新增多头大户合计/空头合计/总成交量三个汇总卡片，便于快速判断多空力量对比
- ⏱ **分钟线自动加载**：打开品种详情后切换到分钟线 tab，自动加载 5 分钟 K 线，无需手动触发

**API 新增：**
- `GET /api/alerts` — 获取全部预警规则
- `GET /api/alerts/check` — 检查预警触发状态
- `POST /api/alerts/add` — 新增预警规则
- `POST /api/alerts/delete` — 删除预警规则
- `POST /api/alerts/toggle` — 启用/禁用预警规则
- `POST /api/pnl` — 盈亏计算

---

### v2.0.0（2026-04-09）

- 初始版本，覆盖 6 大期货交易所 90+ 主力合约
- 市场概览、行情表格、涨跌排行
- 品种详情：30天日线、分钟分时图
- 持仓排名、仓单数据、结算参数
- 自动刷新（30秒/1分钟/5分钟）
