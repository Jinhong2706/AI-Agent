# 配置 高德地图 LBS

## 获取 API Key

1. 访问 [高德开放平台](https://lbs.amap.com/api/webservice/create-project-and-key)
2. 注册并创建应用
3. 创建 Web 服务 Key

## 环境变量

```bash
export AMAP_WEBSERVICE_KEY="你的高德Key"
```

推荐写入 `~/.openclaw/.env` 持久化。

## 安装 Skill

```bash
# 从 ClawHub 安装
openclaw skill install amap-lbs-skill

# 或手动克隆到 skills/amap-lbs-skill/
cd skills/amap-lbs-skill && npm install
```

## 能力

- POI 搜索（地点、商家、设施）
- 周边搜索（坐标+半径）
- 路径规划（步行/驾车/骑行/公交）
- 智能旅游规划
- 热力图数据可视化

## 验证

```bash
cd skills/amap-lbs-skill && \
  AMAP_WEBSERVICE_KEY=$AMAP_WEBSERVICE_KEY \
  node -e "const {searchPOI}=require('./index.js');searchPOI({keywords:'北京',city:'北京',offset:1}).then(r=>console.log(r.pois.length))"
```

## 限额

免费用户每日调用量有限制，详见[高德开放平台说明](https://lbs.amap.com/api/webservice/summary)。
