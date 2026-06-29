---
name: clash-tournament
description: 部落冲突比赛报名管理系统。支持玩家/战队注册报名、实时排名统计、转会交易管理。适用于组织部落冲突联赛、杯赛、友谊赛等赛事场景。当用户需要创建比赛系统、管理报名、查看排行榜、处理转会时触发。
---

# 部落冲突比赛报名系统

这是一个完整的部落冲突赛事管理系统，包含注册、排名、转会三大核心功能。

## 快速开始

### 初始化系统
```bash
python scripts/setup.py
```

### 注册新玩家/战队
```bash
python scripts/register.py --name "玩家名" --tag "#ABC123" --clan "部落名"
```

### 查看排名
```bash
python scripts/ranking.py --type individual  # 个人榜
python scripts/ranking.py --type clan        # 部落榜
```

### 处理转会
```bash
python scripts/transfer.py --request "#ABC123" "新部落"
```

## 核心功能

### 1. 注册板块
- 玩家个人报名
- 战队集体报名
- 资格审核
- 报名信息修改

### 2. 排名板块
- 个人积分榜
- 部落积分榜
- 战绩统计
- 历史记录查询

### 3. 转会板块
- 球员转会申请
- 转会审批流程
- 交易记录
- 转会市场

详细文档请参考 references/ 目录。
