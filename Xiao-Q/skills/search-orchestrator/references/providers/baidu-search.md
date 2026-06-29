# 配置 Baidu AI Search

## 获取 API Key

1. 访问 [百度智能云控制台](https://console.bce.baidu.com/ai-search/qianfan/ais/console/apiKey)
2. 登录后创建 API Key
3. 复制生成的 Key

## 环境变量

```bash
export BAIDU_API_KEY="bce-v3/ALTAK-..."
```

推荐写入 `~/.openclaw/.env` 持久化。

## 安装 Skill

```bash
# 从 ClawHub 安装
openclaw skill install baidu-search

# 或手动克隆到 skills/baidu-search/
```

## 能力

- 中文内容搜索（最佳覆盖）
- 时效性过滤（pd/pw/pm/py）
- 日期范围搜索
- 返回数 1-50

## 验证

```bash
cd skills/baidu-search && python3 scripts/search.py '{"query":"测试","count":1}'
```
