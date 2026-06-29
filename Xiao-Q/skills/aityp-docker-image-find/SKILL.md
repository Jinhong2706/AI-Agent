---
name: aityp-docker-image-find
description: 从 docker.aityp.com 搜索 Docker 国内镜像，获取镜像列表和拉取地址
version: 1.0.0
author: SiberianHusky
last_updated: 2026-06-16
---

# 🐳 Docker 国内镜像搜索

## 什么时候用
用户需要搜索 Docker 镜像、查找国内镜像源可用镜像、获取 `docker pull` 拉取命令时触发。

**触发词**:
- "搜索 docker 镜像"
- "查找 docker 镜像"
- "docker 镜像搜索"
- "获取镜像拉取地址"
- "docker pull 命令"

## 怎么用

1. 提取用户输入中的**镜像关键词**（如 nginx、redis、mysql）
2. 调用 `scripts/docker-search-cli.py search <image>` 搜索镜像列表
3. 如需拉取地址，调用 `scripts/docker-search-cli.py detail <url>` 获取具体镜像的 `docker pull` 地址
4. 将结果整理后返回给用户

## 输入格式

用户应该说：
- "帮我搜索 nginx 的 docker 镜像"
- "查找 redis 镜像"
- "获取 mysql 镜像的拉取命令"

## 输出格式

### 搜索列表输出
```
【Docker 镜像搜索结果】关键词: [keyword]

┌────┬─────────────────────┬──────────┬────────────────────────────────────┐
│ ID │ 镜像名称            │ 平台     │ 详情链接                           │
├────┼─────────────────────┼──────────┼────────────────────────────────────┤
│ 0  │ library/nginx       │ linux    │ /i/library/nginx                   │
│ 1  │ bitnami/nginx       │ linux    │ /i/bitnami/nginx                   │
└────┴─────────────────────┴──────────┴────────────────────────────────────┘

共找到 [N] 条结果
```

### 拉取地址输出
```
【镜像拉取地址】

镜像: [name]
拉取地址: [registry/namespace/name:tag]
命令: docker pull [registry/namespace/name:tag]
```

## 注意事项
- 搜索关键词应尽量准确，支持模糊匹配
- `detail` 命令需要传入镜像详情页的相对路径（如 `/i/library/nginx`）
- 拉取地址来自 docker.aityp.com 的解析结果，实际可用性以本地网络环境为准
- 脚本依赖 `requests` 和 `parsel`，运行前请确保已安装

## 依赖
- Python 3.8+
- requests
- parsel
