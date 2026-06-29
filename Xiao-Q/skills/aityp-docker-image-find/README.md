# 🐳 aityp-docker-image-find

> 从 [docker.aityp.com](https://docker.aityp.com) 搜索 Docker 国内镜像，快速获取镜像列表和 `docker pull` 拉取地址。

---

## 📌 功能特性

| 功能 | 说明 |
|------|------|
| 🔍 镜像搜索 | 通过关键词搜索 Docker 镜像，返回名称、平台、详情链接 |
| 📋 列表展示 | 支持表格 / JSON / CSV 三种输出格式 |
| 🔗 拉取地址获取 | 解析镜像详情页，提取可直接 `docker pull` 的国内镜像地址 |
| ⚡ 一条龙拉取 | 搜索关键词 → 自动获取拉取命令，一步到位 |

---

## 📁 目录结构

```
aityp-docker-image-find/
├── SKILL.md                          # 技能说明书（Agent 调用入口）
├── README.md                         # 本文件
├── scripts/
│   └── docker-search-cli.py          # 核心搜索脚本
└── references/
    └── docker-mirrors.md             # 国内镜像源配置参考
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests parsel
```

### 2. 搜索镜像

```bash
python scripts/docker-search-cli.py search nginx
```

输出示例：
```
[*] 正在搜索: nginx ...
+------+------------------------+----------+------------------------------------------+
│  ID  │        镜像名称        │   平台   │                   链接                   │
+------+------------------------+----------+------------------------------------------+
│  0   │ library/nginx          │ linux    │ /i/library/nginx                         │
│  1   │ bitnami/nginx          │ linux    │ /i/bitnami/nginx                         │
+------+------------------------+----------+------------------------------------------+

共找到 2 条结果
```

### 3. 获取拉取地址

```bash
python scripts/docker-search-cli.py detail /i/library/nginx
```

输出示例：
```
[*] 正在获取镜像详情: /i/library/nginx
[+] 拉取地址: registry.cn-hangzhou.aliyuncs.com/library/nginx:latest
[+] 拉取命令: docker pull registry.cn-hangzhou.aliyuncs.com/library/nginx:latest
```

### 4. 一条龙：搜索 + 获取拉取命令

```bash
python scripts/docker-search-cli.py pull redis
```

输出示例：
```
[*] 正在搜索: redis
[*] 获取 [library/redis] 的拉取地址...
  [+] docker pull registry.cn-hangzhou.aliyuncs.com/library/redis:latest
```

---

## 📖 命令详解

### `search` — 搜索镜像列表

```bash
python scripts/docker-search-cli.py search <keyword> [选项]
```

| 选项 | 说明 | 示例 |
|------|------|------|
| `-l, --limit N` | 限制返回数量 | `search nginx -l 5` |
| `-f, --format` | 输出格式：`table` / `json` / `csv` | `search mysql -f json` |
| `-o, --output` | 输出到文件 | `search redis -o result.json` |

### `detail` — 获取镜像拉取地址

```bash
python scripts/docker-search-cli.py detail <url>
```

- `url`：镜像详情页相对路径，如 `/i/library/nginx`
- 返回可直接执行的 `docker pull` 命令

### `pull` — 搜索并自动获取拉取命令

```bash
python scripts/docker-search-cli.py pull <keyword> [选项]
```

| 选项 | 说明 | 示例 |
|------|------|------|
| `-l, --limit N` | 获取前 N 个结果的拉取地址 | `pull python -l 3` |

---

## 🛠️ 作为 Agent Skill 使用

本 Skill 遵循 **Agent Skills 四件套规范**：

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 技能说明书，定义触发条件、操作流程、输入输出格式 |
| `scripts/docker-search-cli.py` | 可执行脚本，负责实际的网络请求和数据解析 |
| `references/docker-mirrors.md` | 参考文档，存放国内镜像源配置方法 |

将本目录放入你的 Agent Skills 加载路径（如 `/app/.agents/skills/`），Agent 读取 `SKILL.md` 后即可按规范自动调用脚本。

---

## ⚠️ 注意事项

1. **网络依赖**：脚本需要访问 `docker.aityp.com`，请确保网络通畅
2. **Python 版本**：要求 Python 3.8+
3. **依赖库**：`requests` 和 `parsel` 必须预先安装
4. **拉取地址可用性**：解析出的地址来自 docker.aityp.com，实际能否拉取取决于你本地 Docker 配置的镜像源和网络环境
5. **URL 格式**：`detail` 命令传入的必须是相对路径（如 `/i/library/nginx`），不是完整 URL

---

## 📄 许可证

MIT License

---

*作者: SiberianHusky | 最后更新: 2026-06-16*
