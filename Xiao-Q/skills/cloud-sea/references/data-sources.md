# 云海预测数据源速查

> **LCL V2.0 三层融合已取代旧版三重核实。**
> 本文档仅保留当前架构中实际使用的数据源。

## ⚠️ 关键教训：dew_point_2m 是必取字段

> **2026-04-16 事故记录**：此前数据源说明未强调 dew_point_2m，
> 导致云底估算时误设 Td=7°C，得出云底 1875m 的严重错误。
> 妙峰山实际 Td=8.1-10.2°C（来自 Open-Meteo 实测），
> 正确 LCL_ag ≈ 37m，雾顶约 680m，妙峰山顶 1291m **远在雾上方**。
> **结论：dew_point_2m 是云底估算的生死线，必须获取，不得假设。**

---

## LCL V2.0 三层融合数据源架构

| 层级 | 数据源 | 方式 | 说明 |
|:----:|--------|------|------|
| **Layer 1** | **ECMWF IFS 0.25°** | Open-Meteo API (`models=ecmwf_ifs025`) | 欧洲中期天气预报中心，Windy 默认数据源，高精度数值模型 |
| **Layer 2** | **CMA GRAPES** | Open-Meteo API（默认模型） | 中国气象局全球区域同化预报系统，国内权威实测数据 |
| **Layer 3** | **ECMWF ENS** | ECMWF Azure Blob (GRIB2) | 集合预报 5 成员采样，概率分布估算不确定性 |

> **注意**：`ecmwf_ifs04` (0.4°) 返回空数据，必须使用 `ecmwf_ifs025` (0.25°)。

---

## 一、主要数据源：Open-Meteo API

**网址**：https://open-meteo.com/

**优势**：
- 完全免费，无需 API Key
- 支持 ECMWF IFS 0.25° 高精度模型
- 提供 `dew_point_2m`（云底估算生死线）
- GitHub 12k+ stars，活跃维护
- 支持 `ecmwf_ifs025` 模型（Windy 同源）

**核心字段**：

| 字段 | 用途 |
|------|------|
| `temperature_2m` | 气温 |
| `dew_point_2m` | **露点温度（必取）** |
| `relative_humidity_2m` | 相对湿度 |
| `precipitation_probability` | 降水概率 |
| `precipitation` | 降水量 |
| `surface_pressure` | 气压 |
| `wind_speed_10m` | 风速 |
| `wind_direction_10m` | 风向 |
| `cloud_cover` | 云量 |
| `cloud_cover_low` | 低云量 |

**API 示例**（ECMWF IFS 0.25°）：

```
GET https://api.open-meteo.com/v1/forecast
?latitude=40.05&longitude=115.53
&models=ecmwf_ifs025
&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,
     precipitation_probability,precipitation,surface_pressure,
     wind_speed_10m,wind_direction_10m,cloud_cover,cloud_cover_low
&forecast_days=3
&timezone=Asia/Shanghai
```

---

## 二、辅助数据源

### Timeanddate（日出时间）

**网址**：https://www.timeanddate.com/

**用途**：获取精确日出时间，用于因子 8「日出时机」评分。

**API**：
```
GET https://www.timeanddate.com/sun/china/beijing
```

**提取**：`sunrise` 时间（如 05:34）

---

### Air Quality API（通透度）

**网址**：https://open-meteo.com/en/docs/air-quality-api

**用途**：获取 PM2.5、PM10、AOD、AQI 等指标，用于通透度评估。

**核心字段**：

| 字段 | 用途 |
|------|------|
| `pm2_5` | PM2.5 浓度 |
| `pm10` | PM10 浓度 |
| `aod` | 气溶胶光学厚度 |
| `us_aqi` | 美国 AQI 指数 |
| `no2` | 二氧化氮浓度 |

**API 示例**：
```
GET https://air-quality-api.open-meteo.com/v1/air-quality
?latitude=39.90&longitude=116.40
&hourly=pm2_5,pm10,aod,us_aqi,no2
&forecast_days=3
&timezone=Asia/Shanghai
```

---

## 三、山峰坐标（官方 16 峰）

**详见**：`references/peaks.json`

> **禁止硬编码峰坐标**，所有脚本统一从 `peaks.json` 读取。

---

## 四、已移除的数据源

以下数据源已从 LCL V2.0 架构中移除，不再使用：

| 数据源 | 移除原因 |
|--------|---------|
| **Meteoblue** | HTML 抓取方式不稳定，已被 ECMWF IFS API 取代 |
| **中国天气网** | 仅提供城市级预报，无山峰坐标支持，已被 CMA GRAPES API 取代 |
| **NMC（国家气象信息中心）** | 仅主页可访问性检查，无实际预报数据，已移除 |
| **NOAA CPC** | Open-Meteo 已整合 GFS 数据，无需单独调用 |

---

## 五、API 调用统计

| 场景 | API 调用次数 |
|------|-------------|
| 16 峰预测（LCL V2.0） | 2 次（Open-Meteo + CMA）+ ENS 按需 |
| 通透度评估 | 1 次（Air Quality API） |
| 日出时间 | 1 次（Timeanddate） |

---

## 六、关键常量

| 常量 | 值 | 说明 |
|------|---:|------|
| `LCL_FACTOR` | 125.0 | `LCL_ag = 125 × (T - Td)` |
| `MAGNUS_A` | 17.27 | Magnus 公式参数 |
| `MAGNUS_B` | 237.7 | Magnus 公式参数 |
| `DISAGREEMENT_THRESHOLD` | 200m | L1-L2 分歧阈值，超过则触发 ENS 仲裁 |
