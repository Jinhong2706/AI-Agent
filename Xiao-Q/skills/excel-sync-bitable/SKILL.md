---
name: excel-sync-bitable
label: Excel与飞书表格互转
version: 4.8.0
description: "Excel/CSV与飞书表格（多维表格/电子表格）双向转换工具。支持：1. 导入Excel到多维表格（创建新表或同步到现有表）；2. 从多维表格/电子表格导出数据为CSV或Excel格式。自动识别URL类型，智能推断字段类型。"
---

# Excel与飞书表格互转技能使用指南

## 核心功能
- ✅ **导入功能**：将Excel/XLSX/CSV文件导入或同步到飞书多维表格
- ✅ **导出功能**：从飞书多维表格/电子表格导出数据为CSV或Excel格式
- ✅ **智能类型推断**：自动识别字段类型（文本/数字/日期）
- ✅ **多表导出**：支持一次性导出多个数据表/工作表
- ✅ **格式转换**：CSV与Excel格式互转
- ✅ **自动识别URL**：自动识别 wiki/base/sheets 链接类型
- ✅ **富文本解析**：电子表格富文本单元格自动提取纯文本

---

## 快速开始
使用脚本 `scripts/excel_sync_bitable.py` 执行操作。

---

## 功能一：创建新的多维表格
适用于需要将Excel数据导入到新的多维表格的场景。

### 命令示例
```bash
python scripts/excel_sync_bitable.py \
  --input /path/to/your/file.xlsx \
  --mode create \
  --app-name "员工信息表" \
  --table-name "员工列表"
```

### 参数说明
| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | Excel文件路径 |
| `--mode create` | 是 | 指定为创建新表模式 |
| `--app-name` | 是 | 新建多维表格的应用名称 |
| `--table-name` | 是 | 新建数据表的名称 |

---

## 功能二：同步到现有多维表格
适用于已有多维表格，需要更新/追加数据的场景。

### 命令示例
```bash
python scripts/excel_sync_bitable.py \
  --input /path/to/your/file.xlsx \
  --mode sync \
  --url "https://xxx.feishu.cn/base/xxx?table=xxx" \
  --table-name "员工列表" \
  --key "员工编号"
```

### 参数说明
| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | Excel文件路径 |
| `--mode sync` | 是 | 指定为同步模式 |
| `--url` | 是 | 目标多维表格的URL |
| `--table-name` | 是 | 目标数据表的名称 |
| `--key` | 是 | 主键字段名（用于匹配现有记录） |
| `--no-create-missing` | 否 | 不自动插入主键不存在的新记录（默认自动插入） |

### 同步逻辑
- 主键匹配到现有记录 → 更新该行数据
- 主键未匹配到 → 自动插入新行（除非加了`--no-create-missing`）
- 未在Excel中出现的字段 → 保持原有数据不变

---

## 功能三：从多维表格/电子表格导出数据 ⭐

支持两种表格类型的导出：
- **多维表格（bitable）**：URL 包含 `/base/` 或 wiki 链接指向多维表格
- **电子表格（sheet）**：URL 包含 `/sheets/` 或 wiki 链接指向电子表格

### 1. 导出多维表格

```bash
# 导出为CSV格式
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/base/xxx" \
  --table-name "员工列表" \
  --output employees.csv

# 导出为Excel格式
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/base/xxx" \
  --table-name "员工列表" \
  --output employees.xlsx \
  --format excel

# 导出多个数据表
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/base/xxx" \
  --table-name "员工列表" "部门信息" "项目数据" \
  --output all_data.xlsx \
  --format excel
```

### 2. 导出电子表格

```bash
# 导出所有工作表（不指定 --table-name）
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/sheets/xxx" \
  --output spreadsheet.xlsx \
  --format excel

# 导出指定工作表
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/sheets/xxx" \
  --table-name "Sheet1" "Sheet2" \
  --output selected.xlsx \
  --format excel

# 支持 wiki 链接（自动识别类型）
python scripts/excel_sync_bitable.py \
  --mode export \
  --url "https://xxx.feishu.cn/wiki/xxx" \
  --output wiki_export.xlsx \
  --format excel
```

### 参数说明
| 参数 | 必填 | 说明 |
|------|------|------|
| `--mode export` | 是 | 指定为导出模式 |
| `--url` | 是 | 目标表格的URL（支持 wiki/base/sheets） |
| `--table-name` | 否 | 数据表/工作表名称（不指定则导出所有） |
| `--output` | 是 | 输出文件路径 |
| `--format` | 否 | 导出格式：csv或excel（默认csv） |
| `--no-record-id` | 否 | 不包含_record_id字段 |
| `--sheet-name` | 否 | Excel工作表名称（仅format=excel时有效） |

---

## 字段类型自动推断规则
| Excel数据类型 | 映射到飞书多维表格类型 |
|---------------|------------------------|
| 整数/浮点数 | number（数字） |
| 日期/时间类型 | datetime（日期） |
| 字符串/其他 | text（文本） |

### 日期格式说明
脚本会自动将Excel中的日期转换为飞书要求的ISO格式：`YYYY-MM-DDTHH:MM:SS+08:00`

---

## 导入功能技术实现（新版 lark-cli 命令）

导入功能已更新为使用新版 lark-cli 命令，提供更好的兼容性和稳定性：

### 创建新多维表格流程
1. **创建 Base**：`lark-cli base +create --name "应用名称"`
2. **创建数据表**：`lark-cli base +table-create --base-token TOKEN --name "表名"`
3. **创建字段**：`lark-cli base +field-create --base-token TOKEN --table-id ID --name 字段名 --type 类型`
4. **插入记录**：`lark-cli base +record-upsert --base-token TOKEN --table-id ID --json '{"字段":"值"}'`

### 同步到现有表格流程
1. **解析 URL**：自动提取 base_token 和 table_id
2. **字段匹配**：根据 Excel 列名匹配现有字段
3. **批量同步**：逐条调用 `+record-upsert` 插入或更新记录

### 新版命令优势
- ✅ 更好的错误处理和提示
- ✅ 支持更复杂的字段类型
- ✅ 更稳定的 API 接口
- ✅ 完整的字段创建支持

---

## 使用场景

### 场景1：批量导入Excel数据
```bash
# 将本地Excel数据导入到飞书，创建新表
python scripts/excel_sync_bitable.py --input sales.xlsx --mode create --app-name "销售数据" --table-name "销售记录"
```

### 场景2：定期同步Excel数据
```bash
# 每月同步最新的销售数据到现有多维表格
python scripts/excel_sync_bitable.py --input monthly_sales.xlsx --mode sync --url "xxx" --table-name "销售记录" --key "订单号"
```

### 场景3：备份多维表格数据
```bash
# 定期备份多维表格数据到本地Excel
python scripts/excel_sync_bitable.py --mode export --url "xxx" --table-name "销售记录" --output backup_$(date +%Y%m%d).xlsx --format excel
```

### 场景4：数据迁移与分析
```bash
# 导出多维表格数据用于本地分析
python scripts/excel_sync_bitable.py --mode export --url "xxx" --table-name "员工列表" --output analysis.xlsx --format excel
```

---

## 依赖要求
- Python环境已安装 `pandas` 和 `openpyxl` 库（默认沙箱环境已预装）
- 已正确配置飞书CLI（lark-cli）权限

---

## 飞书CLI安装与配置指南

### 🔔 环境要求

飞书 CLI（lark-cli）需要以下环境：

- **Node.js 16.0** 及以上版本
- **npm** 或 **yarn** 包管理器

#### 检查环境

```bash
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version
```

如果未安装 Node.js，请先安装：
- **Windows/macOS**: 访问 [nodejs.org](https://nodejs.org/) 下载安装包
- **macOS (Homebrew)**: `brew install node`
- **Linux (Ubuntu/Debian)**: `sudo apt install nodejs npm`
- **Linux (CentOS/RHEL)**: `sudo yum install nodejs npm`

**💡 提示：** 安装Node.js后，建议重启终端或执行 `source ~/.bashrc`（或 `source ~/.zshrc`）使环境变量生效。

---

### 📦 安装步骤

#### 第一步：安装 lark-cli

```bash
npm install -g @larksuite/cli
```

#### 第二步：安装相关 Skills

```bash
npx skills add https://github.com/larksuite/cli -y -g
```

#### 第三步：初始化应用配置

```bash
lark-cli config init --new
```

配置过程中，默认会创建一个新应用，也可以选择一个已有应用。

**⚠️ 重要提示：** 为了确保 skills 完整加载，配置完成后需要**重启你的 AI Agent 工具**（如 Trae、Cursor、Codex、Claude Code），然后便可以发送指令开始操作飞书。

---

### ✅ 验证安装

```bash
# 查看命令总览
lark-cli help

# 查看当前登录状态
lark-cli auth status
```

---

### 🔐 用户授权（可选）

飞书 CLI 支持两种工作模式：

**不授权模式：**
- AI 仍可执行发消息、创建文档等操作
- 无法访问个人数据（如日程、私信、收件箱）

**授权模式（以你的身份操作）：**
- AI 可以访问个人日历、消息、文档
- 以你的名义执行操作

#### 授权命令

```bash
lark-cli auth login
```

执行命令后，打开链接在飞书中确认即可。

**提示：** 如果暂时跳过，后续 AI 在需要访问你个人数据时，也会自动发起授权提示。

---

### 💡 开启第一个任务

安装完成后，打开你的 AI Agent 工具（如 Trae、Cursor、Claude Code），在对话框中输入：

```
帮我创建一篇云文档，介绍飞书 CLI 的能力有哪些
```

AI 会自动调用飞书 CLI 完成任务。

---

### 📚 更多资源

- **GitHub开源地址**: https://github.com/larksuite/cli
- **官方安装指南**: https://www.feishu.cn/content/article/7623291503305083853
- **命令帮助**: 执行 `lark-cli help` 或 `lark-cli <command> --help`

---

## 技能可复用性
本技能可打包为`.skill`文件，在其他安装了Aily助手和飞书CLI的环境中直接安装使用，无需重复开发。
