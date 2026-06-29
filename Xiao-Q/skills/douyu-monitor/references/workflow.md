# 详细工作流

## 整体流程

```
用户输入
   ↓
意图识别（add/remove/list/check/notify）
   ↓
执行对应action
   ↓
调用斗鱼API
   ↓
处理返回数据
   ↓
生成回复/触发提醒
```

---

## 意图识别详细逻辑

### 关键词映射表

| action | 关键词 | 优先级 |
|--------|--------|--------|
| add | 监控、添加、关注、订阅、加、加入 | 高 |
| remove | 取消、删除、移除、不用、停止、去掉 | 高 |
| list | 列表、哪些、查看、监控、显示、看看 | 中 |
| check | 开播了吗、在直播吗、状态、查、看一下 | 中 |
| notify | （定时任务触发，无用户输入） | - |

### 识别顺序
1. 先匹配精确动作词（添加/取消/查看）
2. 再匹配状态查询词（开播了吗/状态）
3. 默认 = `check`

---

## API 调用详细说明

### 斗鱼开放API

**接口地址：**
```
https://open.douyutv.com/api/RoomApi/room/{room_id}
```

**请求示例：**
```bash
curl -s "https://open.douyutv.com/api/RoomApi/room/12345"
```

**返回数据结构：**
```json
{
  "error": 0,
  "data": {
    "room_id": "12345",
    "room_name": "今晚冲国服！",
    "nickname": "张大仙",
    "room_status": "1",
    "cate_name": "王者荣耀",
    "start_time": "2026-06-20 20:00:00",
    "owner_avatar": "https://...",
    "room_thumb": "https://..."
  }
}
```

**字段说明：**
| 字段 | 说明 | 备注 |
|------|------|------|
| room_id | 房间号 | 唯一标识 |
| room_name | 直播标题 | 开播时显示 |
| nickname | 主播昵称 | 显示用 |
| room_status | 房间状态 | 1=直播中，0=未开播 |
| cate_name | 分类名称 | 如"王者荣耀" |
| start_time | 开播时间 | 格式：YYYY-MM-DD HH:MM:SS |

---

## 状态对比逻辑

### 轮询流程
```
读取 monitored_rooms.json
   ↓
for each room_id:
   调用API获取当前状态
   ↓
读取 last_status.json
   ↓
对比：上次状态 vs 当前状态
   ↓
if 上次=off AND 当前=on:
      触发开播提醒
   ↓
更新 last_status.json
```

### 状态记录格式
```json
{
  "12345": {
    "status": "on",
    "room_name": "今晚冲国服！",
    "cate_name": "王者荣耀",
    "checked_at": "2026-06-20 20:10:00"
  },
  "67890": {
    "status": "off",
    "checked_at": "2026-06-20 20:10:00"
  }
}
```

---

## 文件存储结构

### monitored_rooms.json
```json
{
  "rooms": [
    {
      "room_id": "12345",
      "nickname": "张大仙",
      "added_at": "2026-06-20 20:00:00"
    }
  ]
}
```

### last_status.json
```json
{
  "12345": {
    "status": "on",
    "room_name": "今晚冲国服！",
    "cate_name": "王者荣耀",
    "checked_at": "2026-06-20 20:10:00"
  }
}
```

---

## 定时任务配置

### 推荐轮询间隔
- **普通用户**：60秒（1分钟）
- **重度用户**：30秒
- **不推荐**：< 30秒（可能触发API限流）

### Cron 表达式示例
```cron
# 每1分钟执行一次
*/1 * * * *

# 每30秒执行一次（需要sleep技巧）
* * * * * /path/to/check.sh
* * * * * sleep 30 && /path/to/check.sh
```

---

## 昵称搜索备选方案

当用户输入昵称而非房间号时，可用以下方式获取房间号：

### 方案1：斗鱼搜索页面解析
```bash
curl -s "https://www.douyu.com/search/?kw={{nickname}}" | grep -o 'room_id=[0-9]*'
```

### 方案2：直接尝试访问
```bash
# 假设昵称即房间号（部分主播房间号=昵称）
curl -s "https://www.douyu.com/{{nickname}}"
```

### 方案3：提示用户手动提供
当无法自动获取时，提示用户：
```
未找到"{{nickname}}"的房间号，请提供斗鱼房间号（数字）
可在主播直播间URL中找到，如：https://www.douyu.com/12345
```
