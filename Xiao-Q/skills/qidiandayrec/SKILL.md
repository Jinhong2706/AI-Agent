---
name: qidian-sanjiang-picker
description: >
  起点中文网好书推荐，支持两种模式：
  1）三江榜新书推荐——每天从起点三江榜单中精选3本优质新书；
  2）经典网文推荐——从起点万订/十万均订经典作品中随机推荐，附IP衍生品（电视剧/动漫/手办）和海外出圈信息。
  内置去重机制，支持按 SBTI 性格筛选。
  触发场景：推荐好书、三江榜、起点推荐、小说推荐、今天看什么书、书荒、找书看、每日推书、起点新书推荐、网文推荐、三江推荐、按性格推荐、SBTI推书、经典网文、万订推荐、十万均订、神作推荐、看经典、经典好书。
  当用户提到"推荐几本好书"、"三江榜有什么书"、"书荒了推荐一下"、"每日推书"等意图时触发三江模式。
  当用户提到"推荐经典"、"有没有经典网文"、"万订好书"、"十万均订"、"神作推荐"、"看看经典"等意图时触发经典模式。
  当用户描述自己的性格或 SBTI 类型并请求推荐书时，也应使用此skill。
allowed-tools: 
disable: true
---

# 起点三江好书推荐

从起点中文网三江榜单中精选优质小说，整理成推荐报告。每次推荐与上一次不重复。
每本书附带 SBTI 人格鉴定和诙谐必看理由。
**支持按用户性格筛选推荐**——告诉我你的 SBTI 或描述你的性格，推荐最对味的书。

## 工作流程

### Step 0: 环境预检与自动安装（agent 负责，脚本运行前完成）

**重要：在调用任何 Python 脚本之前，必须先执行以下预检流程。**

小白用户可能没有安装 Python，agent 必须自动检测并帮用户安装好一切。

#### 0.1 检测 Python3 是否可用

```bash
which python3 2>/dev/null && python3 --version 2>/dev/null || which python 2>/dev/null && python --version 2>/dev/null
```

- 如果 `python3` 可用且版本 ≥ 3.6 → ✅ 直接进入 Step 1，使用 `python3`
- 如果只有 `python` 且版本 ≥ 3.6 → ✅ 直接进入 Step 1，使用 `python`
- 如果都没有或版本 < 3.6 → ❌ 进入 0.2 自动安装

#### 0.2 按操作系统自动安装 Python3

根据当前系统自动执行安装命令（**默认自动执行，无需用户确认**）：

**macOS：**
```bash
which brew >/dev/null 2>&1 && brew install python3 || {
    echo "正在下载 Python3 安装包..."
    curl -fsSL -o /tmp/python3-installer.pkg "https://www.python.org/ftp/python/3.12.4/python-3.12.4-macos11.pkg"
    echo "⚠️ 需要管理员权限安装 Python3"
    sudo installer -pkg /tmp/python3-installer.pkg -target /
    rm -f /tmp/python3-installer.pkg
}
```

**Windows（PowerShell）：**
```powershell
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements
```

**Linux（Debian/Ubuntu）：**
```bash
sudo apt update && sudo apt install -y python3 python3-pip
```

**Linux（CentOS/RHEL/Fedora）：**
```bash
sudo dnf install -y python3 python3-pip 2>/dev/null || sudo yum install -y python3 python3-pip
```

#### 0.3 安装失败的兜底方案

如果自动安装失败，向用户展示手动安装指引：

> **Python3 自动安装未成功，请手动安装：**
> - macOS: 访问 https://www.python.org/downloads/ 下载安装包，双击安装
> - Windows: 访问 https://www.python.org/downloads/ 下载安装包，**安装时务必勾选 "Add Python to PATH"**
> - Linux: 运行 `sudo apt install python3 python3-pip`（Ubuntu）或 `sudo dnf install python3`（Fedora）

#### 0.4 pip 依赖（脚本自动处理）

脚本内置了 pip 依赖自动安装：首次运行时自动检测 `beautifulsoup4` 和 `lxml`，缺失则自动 `pip install`，无需 agent 干预。

### Step 1: 运行推荐脚本

#### 基础推荐（默认3本）

**推荐使用 JSON 输出**（确保链接完整，不丢 `_trace` 参数）：

```bash
python3 scripts/sanjiang_picker.py --count 3 --output json
```

然后 agent 从 JSON 结果的每本书的 `qidian_url` 字段取链接，自行格式化为 Markdown 展示。

也可以用 Markdown 输出（但 agent 整理时必须保留原始链接不得修改）：

```bash
python3 scripts/sanjiang_picker.py --count 3 --output markdown
```

#### 按性格推荐 🎭（新功能！）

如果用户描述了自己的性格或 SBTI 类型，使用 `--sbti` 参数：

```bash
# 用户说"我是吗喽"
python3 scripts/sanjiang_picker.py --sbti MALO --output json

# 用户说"我比较躺平"
python3 scripts/sanjiang_picker.py --sbti 躺平 --output json

# 用户说"我是社恐独行侠"
python3 scripts/sanjiang_picker.py --sbti 社恐独行侠 --output json

# 用户说"我看啥都不顺眼"
python3 scripts/sanjiang_picker.py --sbti 看啥都不顺眼 --output json
```

**agent 解析用户意图的指引：**

| 用户说的 | --sbti 参数 |
|---------|------------|
| "我是吗喽/MALO" | `MALO` |
| "我比较躺平/摆烂/咸鱼" | `躺平` |
| "我是草者/暴躁" | `FUCK` |
| "社恐/独来独往/一个人待着" | `社恐独行侠` |
| "佛系/无所谓/随便" | `佛系` |
| "内耗/焦虑/纠结" | `内耗焦虑` |
| "搞笑/逗比/气氛组" | `JOKE-R` |
| "逃避/装死/鸵鸟" | `ZZZZ` |
| "老好人/心软/讨好型" | `ATM` |
| "自信/有魅力" | `SEXY` |
| "控场/拿捏/大局观" | `CTRL` |
| "愤世嫉俗/看不惯一切" | `SHIT` |

脚本内置了模糊匹配，**直接把用户原话传给 --sbti 即可**，不需要 agent 精确翻译成 code。

#### 查看所有 SBTI 人格

```bash
python3 scripts/sanjiang_picker.py --list-sbti
```

#### 强制刷新缓存

```bash
python3 scripts/sanjiang_picker.py --refresh --output markdown
```

#### 输出完整候选池（调试用）

```bash
python3 scripts/sanjiang_picker.py --dump-cache
```

**参数说明：**
- `--count N`: 推荐书籍数量，默认3本
- `--date YYYY-MM-DD`: 指定榜单日期（默认自动获取最新）
- `--output json|markdown|text`: 输出格式，默认markdown
- `--sbti TEXT`: 按 SBTI 人格筛选（支持代号/中文名/自由描述）
- `--list-sbti`: 列出所有 SBTI 人格类型
- `--refresh`: 强制刷新缓存（忽略已有缓存重新抓取）
- `--dump-cache`: 输出当天完整缓存数据
- `--no-save`: 不保存本次推荐到历史（用于测试）
- `--setup`: 仅检测环境并安装依赖

### Step 2: 整理推荐报告

脚本执行后，对输出结果进行整理：

1. **检查数据完整性**：确保每本书都有书名、作者、分类、简介
2. **如果用户指定了 SBTI**：在报告开头标注"已按你的性格 XXX 筛选推荐"
3. **格式化输出**：使用Markdown格式，清晰展示

⚠️ **【强制规则】链接必须原样使用，严禁自行拼接！**

脚本输出的每本书都包含 `qidian_url` 字段，格式形如：
```
https://www.qidian.com/book/{book_id}/?_trace=qidiandayrec_skill
```

**agent 在生成推荐报告时，必须严格使用脚本返回的 `qidian_url` 原始值，不得自行拼接或简化链接。**

❌ 错误示范（丢失 `_trace` 参数）：
```
[点击阅读](https://www.qidian.com/book/1047379865/)
```

✅ 正确示范（保留完整 `_trace` 参数）：
```
[点击阅读](https://www.qidian.com/book/1047379865/?_trace=qidiandayrec_skill)
```

`_trace=qidiandayrec_skill` 是推荐来源追踪参数，用于标记流量来自本 skill 的推荐。丢掉它等于丢失推荐归因数据，这是业务硬性要求。

**最佳实践**：使用 `--output json` 获取结构化数据，然后直接读取每本书的 `qidian_url` 字段填入链接，确保万无一失。

### Step 3: 交付推荐结果

将整理好的推荐报告直接展示给用户。如果用户需要，可以：
- 保存为Markdown文件
- 推送到企业微信（使用markdown_v2格式）

## 本地缓存机制（保护源站）

**设计原则：同一天的数据只抓一次，后续全部读缓存。**

### 工作方式

```
用户请求推荐
    │
    ├─ 检查本地缓存 (.cache/sanjiang_YYYY-MM-DD.json)
    │    │
    │    ├─ ✅ 缓存命中 → 直接读取，零网络请求
    │    │
    │    └─ ❌ 缓存未命中 → 全量抓取
    │         │
    │         ├─ 1. 获取三江榜单列表
    │         ├─ 2. 逐本获取详情（全部书，不是只抓3本）
    │         ├─ 3. 每本书预打 SBTI 人格标签
    │         ├─ 4. 写入缓存文件
    │         └─ 5. 清理7天前的旧缓存
    │
    └─ 从缓存数据中筛选推荐
         ├─ SBTI 性格筛选（如有）
         ├─ 去重（排除上次推荐）
         ├─ 随机轮换
         └─ 分类多样性
```

### 缓存效果

- **首次请求**：全量抓取（约20-30本书），耗时约30-60秒
- **后续请求**：直接读缓存，**耗时 < 1秒，零网络请求**
- **多人共用**：同一台机器上所有用户共享同一份缓存
- **源站压力**：每天最多1次全量抓取，无论推荐多少次
- **缓存大小**：每日约 50-100 KB
- **自动清理**：保留最近7天缓存，过期自动删除

### 预标注 SBTI

缓存中的每本书都已打上 SBTI 人格标签：
- 抓取阶段就完成人格分配，而非推荐时才打标
- 好处：后续按性格筛选时可以直接过滤，不需要重新计算
- 每本书的人格是确定性的（基于 book_id hash），不会每次变化

## SBTI 人格筛选机制

### 三层匹配策略

1. **精确匹配**：用户直接说了 SBTI 代号（如 MALO）或中文名（如 吗喽）→ 直接命中
2. **关键词匹配**：用户描述了性格特征（如"躺平""摆烂"）→ 通过内置关键词表映射到人格
3. **模糊匹配**：用户自由描述（如"不想上班只想看书"）→ 按 trait/keywords 相似度排序，取 top3

### 筛选流程

```
用户输入 --sbti "躺平"
    │
    ├─ 1. 精确匹配 → 查 SBTI_INDEX["躺平"] → 未命中
    ├─ 2. 关键词匹配 → 查 trait_map["躺平"] → 命中 MALO（吗喽）
    └─ 3. 从缓存中筛选 sbti_code == "MALO" 的所有书
         └─ 从匹配结果中挑选 3 本推荐
```

### 15种 SBTI 人格

| 代号 | 人格名 | 适配类型 |
|------|--------|---------|
| SOLO | 孤儿 | 武侠、仙侠、灵异 |
| MALO | 吗喽 | 都市、轻小说、日常 |
| FUCK | 草者 | 玄幻、奇幻、战争 |
| OJBK | 无所谓人 | 历史、二次元 |
| FAKE | 伪人 | 悬疑、灵异、权谋 |
| IMSB | 自我攻击者 | 都市、科幻、现实 |
| JOKE-R | 小丑 | 轻小说、游戏 |
| ZZZZ | 装死者 | 奇幻、仙侠、游戏 |
| ATM | ATM-er | 都市、历史、现实 |
| DRUNK | 酒鬼 | 武侠、历史、仙侠 |
| WOC! | 握草人 | 玄幻、科幻、悬疑 |
| MUM | 妈妈 | 轻小说、都市、游戏 |
| SEXY | 尤物 | 都市、历史、武侠 |
| CTRL | 拿捏者 | 历史、悬疑、科幻 |
| SHIT | 狗屎人 | 现实、末世、科幻 |

## 去重与轮换机制

- **历史记录文件**：`scripts/.sanjiang_history.json`，记录每次推荐的书籍ID
- **排除规则**：每次推荐自动排除上一次推荐的书
- **随机轮换**：候选书籍先随机打乱，再按分类多样性挑选
- **兜底策略**：如果去重后候选不足，回退到全量选择
- **历史清理**：仅保留最近30天的推荐记录

## 数据源说明

数据通过起点图（qidiantu.com）获取，该网站提供起点的公开数据分析：

- 三江榜单列表：`https://www.qidiantu.com/bang/1/6/{date}`
- 书籍详情页：`https://www.qidiantu.com/info/{book_id}`

## 自动化任务

可设置每天早上10点自动推荐，使用 automation_update 创建定时任务：

- 任务名称：起点三江每日推荐
- 执行时间：每天10:00
- 任务内容：运行脚本获取推荐 → 格式化报告 → 展示给用户

## 依赖

### Python3（agent 预检安装）

脚本需要 Python 3.6+。agent 在调用脚本前会自动检测，如未安装则按操作系统自动安装（见 Step 0）。

### pip 依赖（脚本自动安装）

以下库由脚本首次运行时自动安装，**无需手动操作**：

- `beautifulsoup4` — HTML 页面解析
- `lxml` — 高性能 XML/HTML 解析器

手动安装（仅在自动安装失败时使用）：

```bash
pip3 install beautifulsoup4 lxml
```

环境检测命令：

```bash
python3 scripts/sanjiang_picker.py --setup
```

## 注意事项

- **缓存优先**：同一天的数据只从起点图抓取一次，后续全部读本地缓存
- **请求间隔**：全量抓取时每本书间隔1.5秒，善待源站
- **缓存自动清理**：保留最近7天，过期自动删除
- 三江榜单通常每周五更新，周末获取的是最新一期
- 如果指定日期无数据，脚本会自动回退查找最近7天的榜单
- 起点图数据比起点官网延迟1-2天，属正常现象

---

# 📖 经典网文推荐模式（万订/十万均订）

从起点万订（1600+本）和十万均订（33本）经典作品中随机推荐，
附带 IP 衍生品（电视剧/动漫/手办）和海外出圈信息。

## 触发条件

当用户意图是看**经典网文**而非三江新书时，使用经典模式：

| 用户说的 | 使用模式 |
|---------|---------|
| "推荐经典网文" | 经典模式 ✅ |
| "有没有万订好书" | 经典模式 ✅ |
| "十万均订推荐" | 经典模式 ✅ |
| "推荐神作" | 经典模式 ✅ |
| "看看经典" | 经典模式 ✅ |
| "三江榜有什么" | 三江模式 |
| "最近有什么新书" | 三江模式 |

## 经典模式工作流程

### Step 1: 运行经典推荐脚本

**推荐使用 JSON 输出**（确保链接完整）：

```bash
python3 scripts/classic_picker.py --count 3 --output json
```

#### 按层级筛选

```bash
# 只推荐十万均订（33本顶级经典）
python3 scripts/classic_picker.py --tier 100k --output json

# 只推荐万订
python3 scripts/classic_picker.py --tier 10k --output json
```

#### 按 SBTI 人格推荐

```bash
python3 scripts/classic_picker.py --sbti MALO --output json
python3 scripts/classic_picker.py --sbti 躺平 --output json
```

#### 增量检查新增书（推荐）

```bash
python3 scripts/classic_picker.py --check-update --output json
```

#### 强制全量重新抓取（慎用）

```bash
python3 scripts/classic_picker.py --refresh
```

#### 从 Excel 导入全量万订数据

用户可以从起点图（微信公众号"起点数据图"）免费领取万订全量 Excel，然后导入：

```bash
python3 scripts/classic_picker.py --import-excel /path/to/万订名单.xlsx
```

导入后数据会与在线爬取的数据合并缓存，后续推荐范围更广。

### Step 2: 整理推荐报告

⚠️ **【强制规则】与三江模式相同：链接必须原样使用脚本返回的 `qidian_url`，严禁自行拼接！**

整理报告时，必须着重体现以下特色信息：

1. **层级标签必须醒目**：
   - 十万均订的书标注 `🏆十万均订`
   - 万订的书标注 `📈万订`
   - 让用户一眼区分

2. **IP 衍生品信息（中国IP希望之星）**：
   - 如果推荐的书有电视剧、电影、动漫、手办等衍生品 → **着重介绍**
   - 使用"🎬 中国IP希望之星"标题突出
   - 列出衍生品类型、名称、年份、平台、亮点

3. **海外出圈信息**：
   - 如果书在海外有知名度（如诡秘之主、大奉打更人）→ **强调海外影响力**
   - 附带海外论坛/社区链接（WebNovel、Reddit、NovelUpdates、Fandom Wiki 等）
   - 国内书地址仍指向起点（带 `_trace` 参数）

### Step 3: 交付推荐结果

展示给用户。如果用户还想看更多，可以再次运行（自动去重不重复）。

## 经典书库数据架构

### 预置数据 + 增量更新（零等待设计）

脚本内置134本经典书库预置数据（`data/preset_classics.json`），用户首次使用**零网络请求、毫秒级加载**。
后续每周自动增量检查起点图新增书目（仅抓列表页，秒级完成），无需全量重刷。

```
用户请求经典推荐
    │
    ├─ 1. 检查用户缓存 (.cache/classic_books.json)
    │    │
    │    ├─ ✅ 缓存命中且 ≤7天 → 直接读取（0.1秒）
    │    │
    │    └─ ✅ 缓存命中但 >7天 → 先用旧数据，后台增量检查
    │
    ├─ 2. 无缓存 → 降级到预置数据 (data/preset_classics.json)
    │    │
    │    └─ ✅ 预置命中 → 写入缓存 + 增量检查新增（~2秒）
    │
    ├─ 3. 增量更新（过期或首次预置触发）
    │    │
    │    ├─ 抓列表页 ×2（十万均订 + 万订，~1.5秒）
    │    ├─ 对比已有 book_id，仅新增书补详情
    │    ├─ Tier 升级检查（万订→十万均订自动升级）
    │    └─ 合并 + 更新缓存
    │
    └─ 4.（兜底）全量抓取：仅在无预置+无缓存时触发
```

**性能对比：**

| 场景 | 旧方案 | 新方案 |
|------|--------|--------|
| 首次使用 | 全量抓取134本详情（~3分钟） | 预置数据加载（<0.2秒） |
| 缓存命中 | 0.1秒 | 0.1秒 |
| 缓存过期 | 全量重新抓取（~3分钟） | 增量检查（~2秒） |
| 有新增书 | N/A | 仅补新书详情（每本~2秒） |

## 数据源

| 数据 | URL | 说明 |
|------|-----|------|
| 十万均订 | `qidiantu.com/badge/shiwanjunding` | 完整33本 |
| 万订 | `qidiantu.com/badge/wanrenzhuipeng` | 最新100本 |
| Excel全量 | 微信加 `qidiantu` 领取（免费） | 1600+本全量 |
| 书籍详情 | `qidiantu.com/info/{book_id}` | 作者/分类/简介 |

## 参数说明

| 参数 | 说明 |
|------|------|
| `--count N` | 推荐数量，默认3本 |
| `--output json\|markdown` | 输出格式，默认json |
| `--sbti TEXT` | 按 SBTI 人格筛选 |
| `--tier 100k\|10k` | 层级筛选 |
| `--check-update` | 增量检查新增书（秒级，推荐日常使用） |
| `--refresh` | 全量重新抓取（耗时较长，慎用） |
| `--import-excel FILE` | 从 Excel 导入 |
| `--dump-cache` | 输出完整缓存 |
| `--no-save` | 不保存历史 |
| `--setup` | 环境检测（含预置数据+缓存状态） |
