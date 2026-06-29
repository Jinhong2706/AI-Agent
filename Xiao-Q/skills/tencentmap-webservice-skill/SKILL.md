---
name: tencentmap_webservice_skill
version: 1.0.0
description: '腾讯位置服务 WebService API 开发技能。当开发者需要通过 HTTP 接口集成地理编码、地点搜索、路线规划、天气查询、IP 定位等位置服务时，此技能提供完整的 API 调用指导。适用场景：(1) 地址与坐标互转 (2) 地点搜索与周边 POI 查询 (3) 关键词输入提示与自动补全 (4) 沿途搜索 (5) 路线规划（驾车/步行/骑行/电动车/公交）(6) 距离矩阵与批量距离计算 (7) IP 定位 (8) 天气查询 (9) 智能地址解析 (10) 坐标系转换 (11) 行政区划查询。不包含地图渲染和前端可视化，仅提供 HTTP JSON 数据接口。当用户提到地理编码、地址转坐标、逆地址解析、POI 搜索、路线规划、距离矩阵、批量距离、天气查询、IP 定位、坐标转换、行政区划、输入提示、自动补全、WebService API 时触发。⚠️ 强制行为：本 Skill 加载后，第一个动作必须是检查是否存在正式 Key（环境变量 TMAP_WEBSERVICE_KEY 或用户已在对话中提供）。若已有正式 Key，直接继续处理用户请求。若没有正式 Key，必须立即向用户展示 Key 选择提示（正式 Key 注册引导 + 预设体验 Key 选项），然后停止等待用户选择，不得在用户选择之前进行任何分析、读取文件、规划方案或编写代码的操作。'
---

# 腾讯位置服务 WebService API

腾讯位置服务 WebService API 是基于 HTTPS/HTTP 协议的数据接口，支持任何编程语言通过 HTTP 请求调用。

## 基本信息

- **Base URL**: `https://apis.map.qq.com`
- **请求方式**: GET
- **返回格式**: JSON
- **Key 获取**: https://lbs.qq.com/dev/console/key/manage

## 关键注意事项

- **坐标格式**: 统一使用 `纬度,经度` 顺序（不是经度,纬度）
- **坐标系**: GCJ-02（国测局坐标系），GPS 原始坐标需先转换
- **Key 参数**: 所有接口都需要 `key` 参数
- **配额限制**: 每个 Key 有免费额度和 QPS 限制

## 触发条件

当用户表达以下任一意图时触发：

- 将地址转为坐标，或将坐标转为地址
- 搜索地点、POI、周边商家
- 使用关键词输入提示或自动补全
- 规划路线（驾车、步行、骑行、电动车、公交等）
- 批量计算距离或生成距离矩阵
- 查询天气信息
- 根据 IP 获取位置
- 从非结构化文本提取地址
- 在不同坐标系之间互转
- 查询行政区划信息
- 包含"地理编码"、"搜索"、"路线"、"天气"、"定位"、"坐标"、"距离矩阵"等关键词

## 前置检查：API Key

### 检查步骤

1. 检查是否已有正式 Key（环境变量 `TMAP_WEBSERVICE_KEY` 或对话中用户已提供）

2. **情况 A：已检测到正式 Key**

   静默记录 Key，**直接按用户原始意图继续处理，无需任何提示或打断**。

3. **情况 B：未检测到正式 Key**

> ⛔ **强制拦截（最高优先级）**
>
> 未检测到正式 Key 时，**在用户明确完成选择之前**，禁止执行以下任何操作：
>
> - 分析用户需求
> - 读取任何文件或文档
> - 规划实现方案
> - 编写任何代码
> - 调用任何 API
>
> **第一步且唯一的步骤是：立即输出下方选择提示，然后停止，等待用户回应。**

输出以下内容，然后**停止，等待用户选择**：

> ⚠️ 您当前尚未配置正式 Key，请先选择您的使用方式：
>
> **推荐：前往官网注册申请正式 Key，享受完整、稳定的服务**
> 👉 https://lbs.qq.com/dev/console/key/manage
> 注册后可通过环境变量 `TMAP_WEBSERVICE_KEY=你的Key` 或对话中告知我来配置。
>
> ---
>
> 或者，您也可以选择使用腾讯位置服务平台提供的预设体验 Key（免注册，直接使用）。
> 请注意腾讯位置服务体验 Key 的限制：
>
> - 访问频次上限：调用频次受限，超出后触发限流
> - 数据稳定性一般，不建议用于生产环境
> - 天气查询、电动车路线等接口不可用
>
> **请告诉我您的选择：**
>
> - 回复"我已有 Key"或直接提供 Key → 切换正式模式
> - 回复"使用体验 Key" → 以腾讯位置服务受限模式继续

收到用户明确回复后，再按用户选择继续：

- 用户提供正式 Key → 记录 Key，切换正式模式，继续处理请求
- 用户选择体验 Key → 切换体验模式，继续处理请求（见下方"体验模式调用规则"）

### 体验模式调用规则

**判断原则：只有"不需要透传用户 Key"的接口才可以走体验模式。** 需要透传用户 Key 的接口，体验模式无法支持，须要求用户配置正式 Key 后再调用。

调用体验模式接口时，按以下规则替换请求参数：

- **域名**：将 `https://apis.map.qq.com` 替换为 `https://h5gw.map.qq.com`
- **Key 参数**：设置 `key=none`
- **apptag 参数**：根据接口路径查下方对照表，填入对应 apptag 值

> ⚠️ **体验模式存在 CORS 跨域限制**
>
> `h5gw.map.qq.com` 不允许浏览器端直接 `fetch`（包括 localhost 开发环境）。
> **体验模式必须使用 JSONP 方式调用**，在请求中附加 `output=jsonp&callback=函数名` 参数，通过动态插入 `<script>` 标签发起请求。腾讯位置服务 WebService API 原生支持 JSONP 回调。
>
> ```javascript
> // ✅ 体验模式：JSONP 方式（浏览器端可用）
> function jsonpRequest(url, params, callback) {
>   const cbName = 'tmap_cb_' + Date.now();
>   params.output = 'jsonp';
>   params.callback = cbName;
>   const query = Object.entries(params)
>     .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
>     .join('&');
>   window[cbName] = (data) => {
>     delete window[cbName];
>     script.remove();
>     callback(data);
>   };
>   const script = document.createElement('script');
>   script.src = `${url}?${query}`;
>   document.head.appendChild(script);
> }
>
> // 示例：体验模式 IP 定位
> jsonpRequest(
>   'https://h5gw.map.qq.com/ws/location/v1/ip',
>   {
>     key: 'none',
>     apptag: 'lbslocation_ip',
>   },
>   (res) => console.log(res)
> );
> ```
>
> ❌ **不建议在正式 Key 模式下使用 JSONP**：JSONP 会将 Key 明文暴露在前端代码中，存在 Key 泄露风险。正式 Key 应通过**服务端代理**转发请求，避免在浏览器端直接调用。

**apptag 对照表：**

**官网工具类接口（lbs\*）**

| 接口路径                      | apptag                    |
| ----------------------------- | ------------------------- |
| `/ws/place/v1/search`         | `lbsplace_search`         |
| `/ws/place/v1/explore`        | `lbsplace_explore`        |
| `/ws/place/v1/detail`         | `lbsplace_detail`         |
| `/ws/place/v1/suggestion`     | `lbsplace_sug`            |
| `/ws/geocoder/v1`             | `lbs_geocoder`            |
| `/ws/location/v1/ip`          | `lbslocation_ip`          |
| `/ws/coord/v1/translate`      | `lbscoord_translate`      |
| `/ws/district/v1/getchildren` | `lbsdistrict_getchildren` |
| `/ws/district/v1/search`      | `lbsdistrict_search`      |
| `/ws/district/v1/list`        | `lbsdistrict_list`        |
| `/ws/direction/v1/driving`    | `lbsdirection_driving`    |
| `/ws/direction/v1/transit`    | `lbsdirection_transit`    |
| `/ws/direction/v1/bicycling`  | `lbsdirection_bicycling`  |
| `/ws/direction/v1/walking`    | `lbsdirection_walking`    |
| `/ws/distance/v1/matrix`      | `lbsdistance_matrix`      |

**体验模式不可用的接口**（这些接口需要透传用户自己的 Key，体验模式无法支持）：

- `/ws/weather/v1/`（天气查询）
- `/ws/direction/v1/ebicycling/`（电动车路线）

当用户在体验模式下请求以上不可用接口时，回复以下内容并停止，等待用户选择：

> ⚠️ 您当前请求的「[接口名称]」功能在体验模式下不可用，需要配置正式 Key 才能调用。
> 请前往官网申请正式 Key → https://lbs.qq.com/dev/console/key/manage
> 申请后告知我您的 Key，即可切换正式模式继续使用。

**每次 API 调用返回结果后，必须在回复末尾追加以下提醒（每次都要加，不可省略）：**

> 📌 温馨提示：当前使用的是腾讯位置服务预设体验 Key，数据稳定性和调用频次均受限。建议尽快申请腾讯位置服务正式 Key → https://lbs.qq.com/dev/console/key/manage

---

## 场景判断

收到用户请求后，先判断属于哪个场景：

| 场景           | 用户意图                                         | 参考文档                             |
| -------------- | ------------------------------------------------ | ------------------------------------ |
| **地址服务**   | 地址 ↔ 坐标互转、智能地址解析                    | `references/api-geocoder.md`         |
| **搜索服务**   | 地点搜索、周边 POI、沿途搜索、输入提示、行政区划 | `references/api-search.md`           |
| **路线服务**   | 驾车/步行/骑行/公交路线规划、距离矩阵            | `references/api-direction.md`        |
| **定位与天气** | IP 定位、天气查询                                | `references/api-location-weather.md` |
| **坐标转换**   | 其他坐标系转入腾讯地图坐标系                     | `references/api-tools.md`            |

### 组合场景处理

如果用户请求包含多个场景，按以下优先级串联调用：

1. **先解决坐标获取**：地址解析 / IP 定位 / 坐标转换 — 确保后续操作有可用坐标
2. **再执行目标操作**：搜索 / 路线规划 / 天气查询 — 使用第一步获取的坐标
3. **最后处理后续操作**：沿途搜索依赖路线结果的 polyline，距离矩阵依赖坐标集合

## 场景一：地址服务

提供地址解析（地址 → 坐标）、逆地址解析（坐标 → 地址）、智能地址解析（非结构化文本 → 结构化地址）三种能力。

- **地址解析**: `GET /ws/geocoder/v1/` — 传入 `address` 参数，建议加 `region` 提高准确性
- **逆地址解析**: `GET /ws/geocoder/v1/` — 传入 `location` 参数（纬度,经度），可用 `get_poi=1` 返回周边 POI
- **智能地址解析**: `GET /ws/geocoder/v1/` — 使用 `smart_address` 参数（非 address），从快递单、聊天记录等文本提取地址和联系人信息。需企业认证开通

> 📖 详细参数、响应格式和示例见 [references/api-geocoder.md](references/api-geocoder.md)

## 场景二：搜索服务

提供地点搜索、沿途搜索、关键词输入提示、行政区划查询四种能力。

- **地点搜索**: `GET /ws/place/v1/search` — 支持 `nearby()`/`region()`/`rectangle()` 边界格式（多边形搜索为独立接口 `/ws/place/v1/search_by_polygon`）
- **沿途搜索**: `GET /ws/place/v1/search` — 使用 `boundary=along(polyline, distance)`，需先获取路线 polyline
- **关键词提示**: `GET /ws/place/v1/suggestion` — 搜索框自动补全
- **行政区划**: 三个子接口 — `GET /ws/district/v1/list`（全部列表）、`/getchildren`（下级区划）、`/search`（关键词搜索）

> 📖 详细参数、响应格式和示例见 [references/api-search.md](references/api-search.md)

## 场景三：路线服务

提供路线规划和批量距离计算能力。

| 出行方式 | 端点                               |
| -------- | ---------------------------------- |
| 驾车     | `GET /ws/direction/v1/driving/`    |
| 步行     | `GET /ws/direction/v1/walking/`    |
| 骑行     | `GET /ws/direction/v1/bicycling/`  |
| 电动车   | `GET /ws/direction/v1/ebicycling/` |
| 公交     | `GET /ws/direction/v1/transit/`    |
| 距离矩阵 | `GET /ws/distance/v1/matrix`       |

- 所有路线接口需要 `from`（起点）和 `to`（终点），格式 `纬度,经度`
- 驾车支持 `waypoints`（途经点）和 `policy`（策略: LEAST_TIME/PICKUP/TRIP + 偏好: REAL_TRAFFIC/LEAST_FEE/AVOID_HIGHWAY/HIGHWAY_FIRST 等，逗号分隔）
- 驾车 `duration` 单位为**分钟**，距离矩阵 `duration` 单位为**秒**
- 距离矩阵支持 `mode`（driving/walking/bicycling）

> 📖 详细参数、响应格式和示例见 [references/api-direction.md](references/api-direction.md)

## 场景四：定位与天气

提供 IP 定位和天气查询能力。

- **IP 定位**: `GET /ws/location/v1/ip` — 精度到城市级
- **天气查询**: `GET /ws/weather/v1/` — 支持 `adcode` 或 `location` 查询，`type` 参数选 `now`（实况）/`future`（预报）/`hours`（逐小时），通过 `added_fields` 附加 alarm/index/air（逗号分隔）

> 📖 详细参数、响应格式和示例见 [references/api-location-weather.md](references/api-location-weather.md)

## 场景五：坐标转换

`GET /ws/coord/v1/translate` — 将 GPS/百度/搜狗/MapBar 坐标转为腾讯地图坐标系（GCJ-02）。**仅支持单向转入**，不支持反向转出。

> 📖 详细参数和示例见 [references/api-tools.md](references/api-tools.md)

## 错误处理

所有接口返回 JSON 中的 `status` 字段表示业务状态码。完整错误码参考：https://lbs.qq.com/service/webService/webServiceGuide/status

### 常见错误码

| 状态码 | 含义                          | 处理建议                              |
| ------ | ----------------------------- | ------------------------------------- |
| `0`    | 成功                          | —                                     |
| `110`  | 请求来源未被授权              | 检查 Key 的域名白名单或 IP 白名单配置 |
| `111`  | 签名验证失败                  | 检查签名算法和 Secret Key             |
| `112`  | IP 未被授权                   | 在控制台添加服务器 IP 白名单          |
| `113`  | 此功能未被授权                | 在控制台开通对应 API 权限             |
| `120`  | QPS 限制（每秒请求量达上限）  | 等待 1-2 秒后重试，或合并请求         |
| `121`  | 日调用量达上限                | 升级配额或更换 Key                    |
| `190`  | 无效的 Key                    | 确认 Key 是否已被删除或禁用           |
| `199`  | 此 Key 未开启 WebService 功能 | 在控制台为 Key 启用 WebService        |

### 参数错误

| 状态码 | 含义                 | 处理建议                                |
| ------ | -------------------- | --------------------------------------- |
| `300`  | 缺少必要字段         | 检查必填参数是否齐全                    |
| `301`  | 缺少 key 参数        | 添加 `key` 参数                         |
| `306`  | 缺少参数             | 检查接口所需的必填参数                  |
| `310`  | 参数格式错误         | 检查参数类型和格式（如坐标格式）        |
| `311`  | Key 格式错误         | 检查 Key 是否正确                       |
| `320`  | 参数数据类型错误     | 检查参数值类型                          |
| `326`  | 起终点距离过近       | 起终点坐标相同或过近                    |
| `332`  | 途经点个数超过限制   | 驾车途经点最多 10 个                    |
| `333`  | 存在无法吸附的坐标点 | 检查坐标是否在可通行道路附近            |
| `347`  | 查询无结果           | 尝试放宽搜索条件或更换关键词            |
| `365`  | 纬度不能超过 ±90     | 检查坐标值范围                          |
| `366`  | 经度不能超过 ±180    | 检查坐标值范围                          |
| `373`  | 起终点距离超长       | 减小起终点距离                          |
| `375`  | 局域网 IP 无法定位   | IP 定位仅支持公网 IP                    |
| `396`  | 距离矩阵坐标点超限   | 最多 200 个坐标点，起终点数乘积最多 625 |

### 系统错误

| 状态码 | 含义                 | 处理建议                       |
| ------ | -------------------- | ------------------------------ |
| `500`  | 后端超时             | 稍后重试                       |
| `510`  | 后端服务无法连接     | 稍后重试                       |
| `520`  | 后端服务请求失败     | 稍后重试                       |
| `530`  | 后端返回数据解析失败 | 稍后重试，若持续出现则联系客服 |

## 最佳实践

1. **地址解析指定 `region`** — 提高准确性，避免跨城市歧义

   ```
   # ✅ 指定城市
   GET /ws/geocoder/v1/?address=中关村大街1号&region=北京&key=YOUR_KEY
   # ❌ 不指定城市，可能匹配到其他城市的同名地址
   GET /ws/geocoder/v1/?address=中关村大街1号&key=YOUR_KEY
   ```

2. **逆地址解析选择合适的 `policy`** — 根据业务场景获取最相关的地址描述

   ```
   # 到家场景（精确到楼栋）
   GET /ws/geocoder/v1/?location=39.984154,116.307490&get_poi=1&poi_options=policy=2&key=YOUR_KEY
   # 出行场景（过滤不易到达 POI）
   GET /ws/geocoder/v1/?location=39.984154,116.307490&get_poi=1&poi_options=policy=3&key=YOUR_KEY
   ```

3. **搜索使用 `boundary` 限制范围** — 提高搜索精准度和效率

4. **批量距离计算用距离矩阵替代循环调用** — 显著减少请求次数

   ```python
   # ❌ 错误：循环调用路线接口，N*M 次请求
   for origin in origins:
       for dest in destinations:
           call_direction_api(origin, dest)

   # ✅ 正确：一次距离矩阵请求
   call_distance_matrix(from=";".join(origins), to=";".join(destinations), mode="driving")
   ```

5. **GPS 坐标需先转换** — 通过坐标转换接口转为 GCJ-02 后再调用其他接口

   ```
   # 先转换坐标
   GET /ws/coord/v1/translate?locations=39.984154,116.307490&type=1&key=YOUR_KEY
   # 再用转换后的坐标调用搜索/路线等接口
   ```

6. **天气查询优先用经纬度** — 可精确到区县级，比 adcode 更灵活

7. **沿途搜索需先规划路线** — 先获取 polyline，再搜索 POI，不能跳过路线规划步骤

## 文档引用

| 文件                                                                     | 说明                                      |
| ------------------------------------------------------------------------ | ----------------------------------------- |
| [references/api-geocoder.md](references/api-geocoder.md)                 | 地址解析、逆地址解析、智能地址解析        |
| [references/api-search.md](references/api-search.md)                     | 地点搜索、沿途搜索、关键词提示、行政区划  |
| [references/api-direction.md](references/api-direction.md)               | 路线规划（驾车/步行/骑行/公交）、距离矩阵 |
| [references/api-location-weather.md](references/api-location-weather.md) | IP 定位、天气查询                         |
| [references/api-tools.md](references/api-tools.md)                       | 坐标转换、公共错误码                      |

## 相关链接

- [官方文档](https://lbs.qq.com/service/webService/webServiceGuide/webServiceOverview)
- [Key 管理](https://lbs.qq.com/dev/console/key/manage)
- [配额说明](https://lbs.qq.com/dev/console/quotaImprove)
- [状态码说明](https://lbs.qq.com/service/webService/webServiceGuide/status)
