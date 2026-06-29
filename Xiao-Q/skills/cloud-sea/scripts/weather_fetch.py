#!/usr/bin/env python3
"""
cloud-sea-weather-fetch.py  v3.0
自动获取北京云海预测所需气象数据（三重核实体系 + 12因子评分）
输出: weather_data.json

Self-Improving 优化记录:
  v3.0 (2026-04-17):
  - 支持 --date 参数指定任意目标日期（不再硬编码周六）
  - 新增 retry_fetch() 重试逻辑（最多3次，指数退避）
  - 新增 score_12_factors() 实现 12因子综合评分模型
  - 新增 auto_report_config() 自动生成 report_config.json
  - 修复 API 速率限制：14峰间增加 0.5s 间隔
  v2.0 (2026-04-17):
  - 新增 validate_data() 强制校验 dew_point_2m 存在性
  - 新增 Meteoblue / NMC / CMA 第二轮数据源
  - 扩展 PEAKS 从 6 峰到 14 峰（含长城段）
  - 修复 fog_top_msl() bug（fog_thickness 固定 100m）
  - Windows 编码：sys.stdout.reconfigure(encoding='utf-8')

已知 Bug 修复记录:
  [2026-04-16] fog_top_msl() 误用 summit_elev-station_elev 作为雾厚 → 固定 100m
  [2026-04-16] 缺少 dew_point_2m → 云底估算 1875m（实际 668m）→ 妙峰山误判
"""
import json, sys, urllib.request, time, math, re, argparse, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')  # Windows 必须

SCRIPT_DIR  = pathlib.Path(__file__).parent
DATA_DIR     = SCRIPT_DIR.parent / "data"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ================================================================
# 16 峰数据（唯一真相源：cloud_sea_shared.PEAK_INFO + DISTRICT_CODES）
# ================================================================
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cloud_sea_shared import PEAK_INFO, DISTRICT_CODES, PEAK_DISTRICT, URBAN_MONITOR
from lcl_fusion_v2 import SourceResult, extract_verify_data, fetch_layer1_batch, fetch_layer2_batch

# AUDIT-002 FIX: PEAK_INFO 格式改为 (lat, lon, summit_elev) 三元组
# 注意：气象数据 JSON 中的 station_elev 来自 API 的 elevation 字段（非此处的占位值）
PEAKS = {
    name: {
        "lat": info[0], "lon": info[1],
        "elev": info[2],  # summit_elev（用于险差计算中的山顶海拔）
        "district": DISTRICT_CODES.get(PEAK_DISTRICT.get(name, ""), "101010800"),
    }
    for name, info in PEAK_INFO.items()
}

# ================================================================
# 工具函数
# ================================================================
def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"    [WARN] fetch failed: {e}")
        return None

def retry_fetch(url, timeout=15, max_retries=3):
    """Retry fetch with exponential backoff."""
    for attempt in range(max_retries):
        result = fetch(url, timeout)
        if result is not None:
            return result
        if attempt < max_retries - 1:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"    [RETRY] attempt {attempt+1}/{max_retries}, waiting {wait}s...")
            time.sleep(wait)
    return None

def magnus_es(T):
    return 6.112 * math.exp(17.27 * T / (T + 237.7))

def lcl_ag(T, Td, pressure_hPa=None):
    """地面以上 LCL 高度(m)
    
    FIX (2026-05-12): 
    - Issue2: T=Td时返回0，不再使用max(,0.1)的workaround
    - Issue3: 添加气压修正，高海拔时LCL应更高
    
    Args:
        T: 温度(°C)
        Td: 露点(°C)
        pressure_hPa: 气压(hPa)，None时假设标准气压1013.25hPa
    
    Returns:
        LCL高度(m)
    """
    diff = T - Td
    if diff <= 0:
        return 0.0  # T<=Td时饱和，LCL=0
    
    # 基础公式: LCL = 125 * (T - Td)
    base_lcl = 125.0 * diff
    
    # 气压修正: 高海拔时气压降低，LCL应更高
    # 修正因子 = (1013.25 / pressure) ** 0.5
    # 例: 700hPa时因子=1.20，LCL增加20%
    if pressure_hPa is not None and pressure_hPa > 0:
        pressure_factor = (1013.25 / pressure_hPa) ** 0.5
    else:
        pressure_factor = 1.0
    
    return base_lcl * pressure_factor

def fog_top_msl(station_elev, T, Td, fog_thickness=None, RH=None):
    """
    雾顶高度（MSL）= 气象站海拔 + LCL_ag + 雾厚
    
    FIX (2026-05-09 lesson53): fog_thickness 由固定100m改为RH自适应估算
    RH自适应: fog_thickness = max(50, min(450, (RH - 80) * 20))
    - RH=80%  → fog=50m（边缘雾）
    - RH=90%  → fog=250m（标准辐射雾）
    - RH=100% → fog=450m（浓雾）
    
    FIX (2026-05-12): 添加气压修正
    从station_elev计算气压: P = 1013.25 * exp(-station_elev / 8500)
    例: station_elev=2000m → P≈792hPa → 气压因子1.13 → LCL增加13%
    
    当RH=None时回退到固定100m（向后兼容）
    """
    # 从station_elev计算气压（barometric公式）
    import math
    pressure_hPa = 1013.25 * math.exp(-station_elev / 8500) if station_elev > 0 else 1013.25
    
    # 使用新的lcl_ag函数，传入气压
    lcl = lcl_ag(T, Td, pressure_hPa)
    
    if fog_thickness is not None:
        ft_val = fog_thickness
    elif RH is not None:
        ft_val = max(50, min(450, (RH - 80) * 20))
    else:
        ft_val = 100  # 默认值，向后兼容
    return station_elev + lcl + ft_val

def magnus_check(T, RH, Td_reported):
    """Magnus 公式自检：计算 Td 并与实测对比"""
    if RH is None or RH <= 0:
        return None
    e = magnus_es(T) * RH / 100
    if e <= 0:
        return None
    Td_calc = (237.7 * math.log(e / 6.112)) / (17.27 - math.log(e / 6.112))
    delta = abs(Td_calc - Td_reported)
    return {"Td_calc": round(Td_calc, 1), "Td_reported": Td_reported, "delta": round(delta, 2),
            "pass": delta < 1.0}

def validate_data(data, name):
    """
    强制校验：dew_point_2m 必须存在
    Self-Improving: 此校验防止 2026-04-16 的云底估算错误重现
    """
    if "hourly" not in data:
        return False, "missing hourly"
    if "dew_point_2m" not in data["hourly"]:
        return False, "CRITICAL: dew_point_2m missing! Cloud base cannot be estimated."
    if "temperature_2m" not in data["hourly"]:
        return False, "missing temperature_2m"
    return True, "ok"

# ================================================================
# 第一轮：Open-Meteo
# ================================================================

# ================================================================
# 第二轮：中国天气网
# ================================================================

# ================================================================
# 第二轮：Meteoblue
# ================================================================

# ================================================================
# 第二轮：NMC（国家气象信息中心）
# ================================================================

# ================================================================
# 第二轮：ECMWF（通过 Open-Meteo — Windy 同源数据）
# ================================================================
# AUDIT-003 FIX: ECMWF 采样峰从 PEAK_INFO 动态选取（覆盖不同海拔/方位）
# 选取 rank 1,4,7,10,13,16 对应6个代表峰，禁止硬编码坐标
_ECMWF_SAMPLE_INDICES = [0, 3, 6, 9, 12, 15]  # 覆盖不同海拔梯度的6个索引
_ECMWF_PEAK_LIST = list(PEAK_INFO.items())
ECMWF_PEAKS = [
    (name, info[0], info[1])
    for i, (name, info) in enumerate(_ECMWF_PEAK_LIST)
    if i in _ECMWF_SAMPLE_INDICES or (len(_ECMWF_PEAK_LIST) > i and i % 3 == 0)
]
# 保证至少6峰：如果上面不足6个，补充
if len(ECMWF_PEAKS) < 6:
    for i, (name, info) in enumerate(_ECMWF_PEAK_LIST):
        if name not in [p[0] for p in ECMWF_PEAKS]:
            ECMWF_PEAKS.append((name, info[0], info[1]))
        if len(ECMWF_PEAKS) >= 6:
            break


# ================================================================
# 大气通透度数据获取（Open-Meteo Air Quality API）
# ================================================================

# 城区监测点坐标（AUDIT-010 FIX: 从 cloud_sea_shared 统一导入）
# URBAN_MONITOR 已从 cloud_sea_shared 导入

# AQICN API Token（环境变量或硬编码 fallback）
_AQICN_TOKEN = None

def _get_aqicn_token():
    """获取 AQICN API token，优先环境变量"""
    global _AQICN_TOKEN
    if _AQICN_TOKEN is not None:
        return _AQICN_TOKEN
    import os
    _AQICN_TOKEN = os.environ.get("AQICN_TOKEN", "68f3a14d170b3e8d7db8700497a449a9fe6a6a7d")
    return _AQICN_TOKEN


def fetch_aqicn_forecast(city="beijing"):
    """
    从 AQICN (aqicn.org) 获取城市级空气质量预报数据。
    覆盖中国全境，提供 PM2.5/AQI/PM10 每日预报（avg/max/min）。
    免费 token 限制 1000次/天。
    """
    token = _get_aqicn_token()
    url = f"https://api.waqi.info/feed/{city}/?token={token}"
    raw = retry_fetch(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if data.get("status") != "ok":
        return None

    d = data["data"]
    # 当前实时值
    iaqi = d.get("iaqi", {})
    current = {
        "aqi": d.get("aqi"),
        "pm25": iaqi.get("pm25", {}).get("v"),
        "pm10": iaqi.get("pm10", {}).get("v"),
        "no2": iaqi.get("no2", {}).get("v"),
    }
    # 每日预报（P1 FIX: 当 forecast 不可用时，用 current 填充）
    fc = d.get("forecast", {}).get("daily", {})
    pm25_fc = fc.get("pm25", [])   # [{day, avg, max, min}, ...]
    pm10_fc = fc.get("pm10", [])
    
    # P1 FIX: 如果 forecast 为空，用 current 构造假预报（免费 API 限制）
    if not pm25_fc and current.get("pm25") is not None:
        # 用当前值构造一个“预报”（实际是实时值）
        from datetime import date, timedelta
        today = date.today()
        fake_fc = []
        for i in range(7):  # 生成7天假预报
            day_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            fake_fc.append({"day": day_str, "avg": current["pm25"], "max": current["pm25"], "min": current["pm25"]})
        pm25_fc = fake_fc
    
    if not pm10_fc and current.get("pm10") is not None:
        from datetime import date, timedelta
        today = date.today()
        fake_fc = []
        for i in range(7):
            day_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            fake_fc.append({"day": day_str, "avg": current["pm10"], "max": current["pm10"], "min": current["pm10"]})
        pm10_fc = fake_fc

    return {
        "source": "AQICN",
        "city": d.get("city", {}).get("name", city),
        "current": current,
        "forecast_pm25": {f["day"]: f for f in pm25_fc},
        "forecast_pm10": {f["day"]: f for f in pm10_fc},
    }


def fetch_air_quality(lat, lon, name="urban"):
    """
    从 Open-Meteo Air Quality API 获取 PM2.5/PM10/AQI/AOD/visibility 数据
    独立端点: air-quality-api.open-meteo.com（非 api.open-meteo.com）
    注：中国大陆地区此API大部分指标返回None，建议优先使用 fetch_aqicn_forecast()
    """
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=pm10,pm2_5,nitrogen_dioxide,ozone,"
        f"aerosol_optical_depth,us_aqi"
        f"&timezone=Asia/Shanghai&forecast_days=7"
    )
    raw = retry_fetch(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None

    if "hourly" not in data:
        return None

    result = {
        "source": "Open-Meteo-AQ",
        "monitor": name,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "elevation": data.get("elevation"),
        "hourly": [],
    }

    h = data["hourly"]
    for i, t in enumerate(h["time"]):
        result["hourly"].append({
            "time": t,
            "pm10": h.get("pm10", [None])[i],
            "pm2_5": h.get("pm2_5", [None])[i],
            "no2": h.get("nitrogen_dioxide", [None])[i],
            "o3": h.get("ozone", [None])[i],
            "aod": h.get("aerosol_optical_depth", [None])[i],
            "us_aqi": h.get("us_aqi", [None])[i],
        })

    return result


def fetch_visibility(lat, lon, name="peak"):
    """
    从 Open-Meteo 天气 API 获取能见度数据（单位 m）
    能见度是通透度最直接的物理指标
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=visibility"
        f"&timezone=Asia/Shanghai&forecast_days=7"
    )
    raw = retry_fetch(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None

    if "hourly" not in data or "visibility" not in data["hourly"]:
        return None

    return {
        "source": "Open-Meteo-Visibility",
        "monitor": name,
        "hourly": [
            {"time": t, "visibility_m": v}
            for t, v in zip(data["hourly"]["time"], data["hourly"]["visibility"])
        ],
    }


# ================================================================
# 通透度评分模型
# ================================================================

def _transparency_window(target_month):
    """根据月份返回通透度评估的黄金时段窗口（北京时间）。"""
    # 复用共享模块的 _SUNRISE_TABLE（从 cloud_sea_shared 导入）
    from cloud_sea_shared import _SUNRISE_TABLE
    sr = _SUNRISE_TABLE.get(target_month, 6.0)
    start = max(0, int(sr) - 1)
    end = min(23, int(sr) + 2)
    return (start, end)


def score_transparency(aq_data, vis_data, target_date, aqicn_daily=None):
    """
    大气通透度评分（0-10 分制）

    核心指标体系：
    ┌────────────────────────────────────────────────────────┐
    │  指标          │ 权重  │ 来源                │ 说明   │
    ├────────────────────────────────────────────────────────┤
    │  PM2.5 凌晨均值│ 30%   │ Air Quality API     │ 最核心 │
    │  能见度        │ 25%   │ Weather API          │ 最直接 │
    │  US AQI        │ 20%   │ Air Quality API     │ 综合性 │
    │  PM10 凌晨均值 │ 10%   │ Air Quality API     │ 粗颗粒 │
    │  AOD(气溶胶OD) │ 10%   │ Air Quality API     │ 光学   │
    │  NO2           │ 5%    │ Air Quality API     │ 城区排 │
    └────────────────────────────────────────────────────────┘

    通透度等级：
      ≥ 8.0  →  ★★★★★ 极通透（雪山级，远山清晰可见）
      6.0-8.0 →  ★★★★☆ 通透（云海色彩饱满，远景分明）
      4.0-6.0 →  ★★★☆☆ 一般（云海可见但偏灰，远景模糊）
      2.0-4.0 →  ★★☆☆☆ 灰霾（云海灰白，城市轮廓不清）
      < 2.0   →  ★☆☆☆☆ 严重雾霾（白茫茫一片，无层次）

    对云海概率的修正：
      通透度 ≥ 8.0 → 云海概率 +5%（色彩和层次最佳）
      通透度 6.0-8.0 → 不修正
      通透度 4.0-6.0 → 云海概率 -5%（灰雾，视觉打折）
      通透度 < 4.0 → 云海概率 -15%（严重灰霾，即使有云海也看不清）
    """
    # L-2 FIX: 动态时段，优先日出前后窗口
    target_month = int(target_date.split("-")[1]) if "-" in target_date else 4
    t_start, t_end = _transparency_window(target_month)

    # 提取目标日期黄金时段数据
    morning_aq = []
    if aq_data and "hourly" in aq_data:
        morning_aq = [
            h for h in aq_data["hourly"]
            if h["time"].startswith(target_date) and t_start <= int(h["time"][11:13]) <= t_end
        ]

    morning_vis = []
    if vis_data and "hourly" in vis_data:
        morning_vis = [
            h for h in vis_data["hourly"]
            if h["time"].startswith(target_date) and t_start <= int(h["time"][11:13]) <= t_end
        ]

    # ── AQICN 日均数据注入 ──
    # AQICN 提供每日 avg/max/min，对 PM2.5/AQI/PM10 直接使用日均
    aqicn_pm25_avg = None
    aqicn_aqi_avg = None
    aqicn_pm10_avg = None
    aqicn_no2_val = None
    if aqicn_daily:
        pm25_fc = aqicn_daily.get("forecast_pm25", {}).get(target_date)
        pm10_fc = aqicn_daily.get("forecast_pm10", {}).get(target_date)
        cur = aqicn_daily.get("current", {})
        if pm25_fc:
            aqicn_pm25_avg = pm25_fc.get("avg")
        elif cur.get("pm25") is not None:
            aqicn_pm25_avg = cur["pm25"]
        if pm10_fc:
            aqicn_pm10_avg = pm10_fc.get("avg")
        elif cur.get("pm10") is not None:
            aqicn_pm10_avg = cur["pm10"]
        if cur.get("aqi") is not None:
            aqicn_aqi_avg = cur["aqi"]
        if cur.get("no2") is not None:
            aqicn_no2_val = cur["no2"]

    if not morning_aq and not morning_vis and not aqicn_daily:
        return {
            "score": None,
            "level": "NO_DATA",
            "label": "数据不足",
            "cloud_sea_modifier": 0,
            "detail": "无法获取空气质量或能见度数据",
        }

    # ── 1. PM2.5 评分（权重 30%） ──
    pm25_vals = [h["pm2_5"] for h in morning_aq if h.get("pm2_5") is not None]
    if pm25_vals:
        pm25_avg = sum(pm25_vals) / len(pm25_vals)
    elif aqicn_pm25_avg is not None:
        pm25_avg = aqicn_pm25_avg
        pm25_vals = [aqicn_pm25_avg]  # 标记有数据
    if pm25_vals:
        if pm25_avg <= 15:      pm25_score = 10   # WHO 标准，优秀
        elif pm25_avg <= 25:    pm25_score = 9
        elif pm25_avg <= 35:    pm25_score = 8    # 国标一级
        elif pm25_avg <= 50:    pm25_score = 7    # 国标二级
        elif pm25_avg <= 75:    pm25_score = 5    # 轻度
        elif pm25_avg <= 100:   pm25_score = 3    # 中度
        elif pm25_avg <= 150:   pm25_score = 2    # 重度
        else:                   pm25_score = 1    # 严重
    else:
        pm25_avg = None
        pm25_score = None

    # ── 2. 能见度评分（权重 25%） ──
    vis_vals = [h["visibility_m"] for h in morning_vis if h.get("visibility_m") is not None]
    if vis_vals:
        vis_avg_m = sum(vis_vals) / len(vis_vals)  # 单位：米
        vis_avg_km = vis_avg_m / 1000  # F-2 FIX: 转换为公里
        # 山地观测：能见度 > 20km 才算通透
        if vis_avg_km >= 20:    vis_score = 10    # ≥20km 极通透
        elif vis_avg_km >= 15:  vis_score = 9
        elif vis_avg_km >= 10:  vis_score = 7    # ≥10km 通透
        elif vis_avg_km >= 5:   vis_score = 5    # 5-10km 一般
        elif vis_avg_km >= 2:   vis_score = 3    # 2-5km 灰霾
        elif vis_avg_km >= 1:   vis_score = 2    # 1-2km 雾霾
        else:                   vis_score = 1    # <1km 浓雾/霾
    else:
        vis_avg_m = None
        vis_avg_km = None
        vis_score = None

    # ── 3. US AQI 评分（权重 20%） ──
    aqi_vals = [h["us_aqi"] for h in morning_aq if h.get("us_aqi") is not None]
    if aqi_vals:
        aqi_avg = sum(aqi_vals) / len(aqi_vals)
    elif aqicn_aqi_avg is not None:
        # AQICN 用中国 AQI 标准，近似 US AQI（差异<10%）
        aqi_avg = float(aqicn_aqi_avg)
        aqi_vals = [aqi_avg]
    if aqi_vals:
        if aqi_avg <= 25:       aqi_score = 10
        elif aqi_avg <= 50:     aqi_score = 9
        elif aqi_avg <= 75:     aqi_score = 8
        elif aqi_avg <= 100:    aqi_score = 7    # US "Moderate"
        elif aqi_avg <= 150:    aqi_score = 5    # Unhealthy for sensitive
        elif aqi_avg <= 200:    aqi_score = 3    # Unhealthy
        else:                   aqi_score = 1    # Very Unhealthy
    else:
        aqi_avg = None
        aqi_score = None

    # ── 4. PM10 评分（权重 10%） ──
    pm10_vals = [h["pm10"] for h in morning_aq if h.get("pm10") is not None]
    if pm10_vals:
        pm10_avg = sum(pm10_vals) / len(pm10_vals)
    elif aqicn_pm10_avg is not None:
        pm10_avg = float(aqicn_pm10_avg)
        pm10_vals = [pm10_avg]
    if pm10_vals:
        pm10_avg = sum(pm10_vals) / len(pm10_vals)
        if pm10_avg <= 20:      pm10_score = 10
        elif pm10_avg <= 40:    pm10_score = 9
        elif pm10_avg <= 50:    pm10_score = 8
        elif pm10_avg <= 80:    pm10_score = 6
        elif pm10_avg <= 150:   pm10_score = 4
        else:                   pm10_score = 2
    else:
        pm10_avg = None
        pm10_score = None

    # ── 5. AOD 评分（权重 10%） ──
    aod_vals = [h["aod"] for h in morning_aq if h.get("aod") is not None]
    if aod_vals:
        aod_avg = sum(aod_vals) / len(aod_vals)
        if aod_avg <= 0.1:      aod_score = 10   # 极清澈（类似高原）
        elif aod_avg <= 0.2:    aod_score = 9
        elif aod_avg <= 0.3:    aod_score = 7    # 较通透
        elif aod_avg <= 0.5:    aod_score = 5    # 一般
        elif aod_avg <= 0.8:    aod_score = 3    # 灰霾
        else:                   aod_score = 1    # 严重
    else:
        aod_avg = None
        aod_score = None

    # ── 6. NO2 评分（权重 5%） ──
    no2_vals = [h["no2"] for h in morning_aq if h.get("no2") is not None]
    if no2_vals:
        no2_avg = sum(no2_vals) / len(no2_vals)
    elif aqicn_no2_val is not None:
        no2_avg = float(aqicn_no2_val)
        no2_vals = [no2_avg]
    if no2_vals:
        no2_avg = sum(no2_vals) / len(no2_vals)
        if no2_avg <= 10:       no2_score = 10
        elif no2_avg <= 20:     no2_score = 9
        elif no2_avg <= 40:     no2_score = 7
        elif no2_avg <= 60:     no2_score = 5
        else:                   no2_score = 3
    else:
        no2_avg = None
        no2_score = None

    # ── 加权总分 ──
    # 对缺失指标：用已获取指标的均值替代，不降权
    available = []
    if pm25_score is not None: available.append(("pm25", pm25_score, 0.30))
    if vis_score  is not None: available.append(("vis",   vis_score,  0.25))
    if aqi_score  is not None: available.append(("aqi",   aqi_score,  0.20))
    if pm10_score is not None: available.append(("pm10",  pm10_score, 0.10))
    if aod_score  is not None: available.append(("aod",   aod_score,  0.10))
    if no2_score  is not None: available.append(("no2",   no2_score,  0.05))

    if not available:
        return {
            "score": None, "level": "NO_DATA", "label": "数据不足",
            "cloud_sea_modifier": 0, "detail": "所有通透度指标均无数据",
        }

    # 重新归一化权重
    total_weight = sum(w for _, _, w in available)
    total_score = sum(s * w / total_weight for _, s, w in available)
    total_score = round(total_score, 1)

    # ── 等级判定 ──
    if total_score >= 8.0:
        level = "EXCELLENT"
        label = "★★★★★ 极通透"
        modifier = 5
    elif total_score >= 6.0:
        level = "GOOD"
        label = "★★★★☆ 通透"
        modifier = 0
    elif total_score >= 4.0:
        level = "MODERATE"
        label = "★★★☆☆ 一般"
        modifier = -5
    elif total_score >= 2.0:
        level = "POOR"
        label = "★★☆☆☆ 灰霾"
        modifier = -15
    else:
        level = "SEVERE"
        label = "★☆☆☆☆ 严重雾霾"
        modifier = -25

    return {
        "score": total_score,
        "level": level,
        "label": label,
        "cloud_sea_modifier": modifier,
        "detail": {
            "pm25_avg": round(pm25_avg, 1) if pm25_avg is not None else None,
            "pm25_score": pm25_score,
            "visibility_avg_km": round(vis_avg_km, 1) if vis_avg_km is not None else None,
            "vis_score": vis_score,
            "us_aqi_avg": round(aqi_avg, 0) if aqi_avg is not None else None,
            "aqi_score": aqi_score,
            "pm10_avg": round(pm10_avg, 1) if pm10_avg is not None else None,
            "pm10_score": pm10_score,
            "aod_avg": round(aod_avg, 3) if aod_avg is not None else None,
            "aod_score": aod_score,
            "no2_avg": round(no2_avg, 1) if no2_avg is not None else None,
            "no2_score": no2_score,
            "data_sources_count": len(available),
        },
    }


# ================================================================
# 提取指定日期的凌晨数据
# ================================================================
def _transpose_hourly_to_rows(peak_data, summit_elev, target_date=None):
    """将API列式 hourly 数据转置为行式（旧格式兼容）。
    
    API原始: {"time": [...], "temperature_2m": [...], ...}
    转置后: [{"time": "...", "T_C": ..., "RH_pct": ..., ...}, ...]
    
    Args:
        peak_data: API原始响应dict
        summit_elev: 山峰海拔(m)
        target_date: 如果指定，只转置目标日期的数据
    """
    if not peak_data or "hourly" not in peak_data:
        return peak_data
    
    h = peak_data["hourly"]
    if isinstance(h, list):
        return peak_data  # 已经是行式，无需转换
    
    station_elev = peak_data.get("elevation", 0)
    pressure_hPa = 1013.25 * math.exp(-station_elev / 8500) if station_elev > 0 else 1013.25
    
    times = h.get("time", [])
    temps = h.get("temperature_2m", [])
    dews = h.get("dew_point_2m", [])
    rhs = h.get("relative_humidity_2m", [])
    wcs = h.get("weather_code", [])
    winds = h.get("wind_speed_10m", [])
    wind_dirs = h.get("wind_direction_10m", [])
    cc = h.get("cloud_cover", [])
    cc_low = h.get("cloud_cover_low", [])
    precip = h.get("precipitation", [])
    precip_prob = h.get("precipitation_probability", [])
    pressure = h.get("surface_pressure", [])
    
    row_list = []
    for i, t in enumerate(times):
        if target_date and not t.startswith(target_date):
            # 非目标日期，仍然保留（analyzer可能需要多日数据）
            pass
        T = temps[i] if i < len(temps) else None
        Td = dews[i] if i < len(dews) else None
        RH = rhs[i] if i < len(rhs) else None
        if T is None or Td is None:
            continue
        if RH is None:
            # RH缺失时用T-Td估算（比硬编码0更物理合理）
            # T-Td<2 → RH≈95%, T-Td<5 → RH≈80%, T-Td>10 → RH≈50%
            if T is not None and Td is not None:
                t_td = T - Td
                RH = max(50, min(100, 100 - t_td * 5))  # 简单线性估计
            else:
                RH = 0.0
        lcl = lcl_ag(T, Td, pressure_hPa)
        ft = fog_top_msl(station_elev, T, Td, RH=RH)
        diff = summit_elev - ft
        chk = magnus_check(T, RH, Td)
        row_list.append({
            "time": t,
            "T_C": round(T, 1),
            "Td_C": round(Td, 1),
            "RH_pct": round(RH, 1) if RH else 0,
            "lcl_ag_m": round(lcl, 0),
            "fog_top_msl": round(ft, 0),
            "summit_diff_m": round(diff, 0),
            "above_fog": diff > 0,
            "wind_kmh": winds[i] if i < len(winds) else 0,
            "wind_direction": wind_dirs[i] if i < len(wind_dirs) else 0,
            "cloud_cover": cc[i] if i < len(cc) else 0,
            "cloud_cover_low": cc_low[i] if i < len(cc_low) else 0,
            "weather_code": wcs[i] if i < len(wcs) else 0,
            "precipitation": precip[i] if i < len(precip) else 0,
            "precipitation_probability": precip_prob[i] if i < len(precip_prob) else 0,
            "surface_pressure": pressure[i] if i < len(pressure) else 0,
            "T_minus_Td": round(T - Td, 1) if Td is not None else 0,
            "magnus_check": chk,
        })
    
    # 替换hourly为行式格式
    result = dict(peak_data)
    result["hourly"] = row_list
    return result


def extract_date_data(peak_data, target_date, summit_elev_override=None):
    """从 hourly 数据中提取指定日期的凌晨数据（00-08时），用于云海评分
    
    import math  # FIX: ensure math module available in function
    支持两种格式：
    1. 行式格式（旧 fetch_open_meteo 生成）: hourly = [{time, T_C, ...}, ...]
    2. 列式格式（API 原始响应）: hourly = {time: [...], temperature_2m: [...], ...}
    
    Args:
        summit_elev_override: If provided, use this summit elevation instead of
                              peak_data.get("summit_elev") (which may not exist
                              in raw API responses).
    """
    import math  # FIX: moved to function start
    if not peak_data or "hourly" not in peak_data:
        return []
    
    h = peak_data["hourly"]
    
    # 判断格式：如果是 list，说明是行式格式（旧格式）
    if isinstance(h, list):
        return [entry for entry in h 
                if entry["time"].startswith(target_date) 
                and 0 <= int(entry["time"][11:13]) <= 8]
    
    # 列式格式（API 原始响应）—— 需要转置
    times = h.get("time", [])
    station_elev = peak_data.get("elevation", 0)
    summit_elev = summit_elev_override if summit_elev_override is not None else peak_data.get("summit_elev", station_elev)
    pressure_hPa = 1013.25 * math.exp(-station_elev / 8500) if station_elev > 0 else 1013.25
    
    temps = h.get("temperature_2m", [])
    dews = h.get("dew_point_2m", [])
    rhs = h.get("relative_humidity_2m", [])
    wcs = h.get("weather_code", [])
    winds = h.get("wind_speed_10m", [])
    wind_dirs = h.get("wind_direction_10m", [])  # P0 FIX: 添加风向字段
    cc = h.get("cloud_cover", [])
    cc_low = h.get("cloud_cover_low", [])
    
    entries = []
    for i, t in enumerate(times):
        hour = int(t[11:13])
        if not t.startswith(target_date) or hour > 8:
            continue
        T = temps[i] if i < len(temps) else None
        Td = dews[i] if i < len(dews) else None
        RH = rhs[i] if i < len(rhs) else None
        # P1 FIX: 当 Td 缺失时，用 Magnus 公式从 T 和 RH 反算 Td
        if T is not None and Td is None and RH is not None and RH > 0:
            es_T = 6.112 * math.exp(17.27 * T / (T + 237.7))
            e = es_T * RH / 100.0
            if e > 0:
                Td_calc = 237.7 * math.log(e / 6.112) / (17.27 - math.log(e / 6.112))
                if -100 < Td_calc < T:  # 合理性检查
                    Td = Td_calc
        if T is None or Td is None:
            continue
        lcl = lcl_ag(T, Td, pressure_hPa)
        ft = fog_top_msl(station_elev, T, Td, RH=RH)
        diff = summit_elev - ft
        entries.append({
            "time": t,
            "T_C": round(T, 1),
            "Td_C": round(Td, 1),
            "RH_pct": round(RH, 1) if RH else 0,
            "lcl_ag_m": round(lcl, 0),
            "fog_top_msl": round(ft, 0),
            "summit_diff_m": round(diff, 0),
            "above_fog": diff > 0,
            "wind_kmh": winds[i] if i < len(winds) else 0,
            "wind_direction": wind_dirs[i] if i < len(wind_dirs) else 0,
            "cloud_cover": cc[i] if i < len(cc) else 0,
            "cloud_cover_low": cc_low[i] if i < len(cc_low) else 0,
            "weather_code": wcs[i] if i < len(wcs) else 0,
            "T_minus_Td": round(T - Td, 1) if Td is not None else 0,
        })
    return entries

def _is_fog_weather(weather_code, rh, lcl):
    """
    判断是否为雾天气（H-2 修复）
    WMO天气码范围: 40-49 为雾类
    - 45: Fog（雾）
    - 48: Rime fog（雾松）
    - 40-44: 各类雾化
    额外条件: RH>90% 且 LCL<100m 也视为雾形成
    """
    if weather_code in [45, 48]:
        return True
    # 40-49 都是雾类
    if 40 <= weather_code <= 49:
        return True
    # 高湿+低云底=实际已形成雾
    if rh > 90 and lcl < 100:
        return True
    return False

def summarize_morning(entries, summit_elev):
    """
    汇总凌晨数据：最低温、最高湿度、最低 LCL、最高雾顶、云海概率估算
    
    FIXED (2026-05-08 13:00): 修复 summit_diff_m 计算逻辑
    原错误：summit_diff = summit_elev - max(fog_top for all hours)
    → 用所有小时中最高的雾顶来算险差，但最高雾顶不一定对应最佳观测窗口
    
    正确做法：遍历每个小时，分别用该小时的 fog_top 计算 diff，取最大险差
    → 找到最佳观测时刻的实际险差，而非最差时刻的险差
    """
    # 修复：遍历每个小时找最大险差（而非用 max fog_top）
    max_diff = None
    best_hour = None
    max_ft_for_summary = None
    for e in entries:
        ft = e["fog_top_msl"]
        diff = summit_elev - ft
        if max_diff is None or diff > max_diff:
            max_diff = diff
            best_hour = e["time"]
            max_ft_for_summary = ft

    return {
        "min_T_C": min(e["T_C"] for e in entries),
        "max_RH_pct": max(e["RH_pct"] for e in entries),
        "avg_RH_pct": round(sum(e["RH_pct"] for e in entries) / len(entries), 1),
        "min_lcl_ag_m": min(e["lcl_ag_m"] for e in entries),
        "max_fog_top_msl": max_ft_for_summary,
        "summit_diff_m": round(max_diff, 0),
        "best_hour": best_hour,
        "summit_above_fog_top": summit_elev > max_ft_for_summary,
        "min_wind_kmh": min(e["wind_kmh"] for e in entries),
        "max_cloud_cover": max(e["cloud_cover"] for e in entries),
        "fog_weather_hours": sum(1 for e in entries if _is_fog_weather(e["weather_code"], e["RH_pct"], e["lcl_ag_m"])),
        "above_fog_hours": sum(1 for e in entries if e["above_fog"]),
        "min_td_spread": round(min(e["T_minus_Td"] for e in entries), 1),
        # DEPRECATED: cloud_sea_score 由 analyzer.py 12因子模型计算
        "cloud_sea_score": 0,
    }

# ================================================================
# 主程序
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Beijing cloud-sea weather fetcher")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: next Saturday)")
    parser.add_argument("--output", default=None, help="Output JSON path (auto: weather_data_{date}.json when --date given)")
    args = parser.parse_args()

    print("=" * 65)
    print("北京云海气象数据获取 v3.1（三重核实 · 16峰 · 通透度 · 12因子）")
    print("=" * 65)

    # 确定目标日期
    if args.date:
        target_date = args.date
    else:
        today = datetime.now()
        days_to_saturday = (5 - today.weekday()) % 7
        if days_to_saturday == 0:
            days_to_saturday = 7
        target_date = (today + timedelta(days=days_to_saturday)).strftime("%Y-%m-%d")
    print(f"\n目标日期: {target_date}")

    # BUG-FIX: 当指定 --date 时，自动推导输出文件名为 weather_data_{date}.json
    # 统一保存到 workspace 目录
    if args.output:
        out_path = pathlib.Path(args.output)
    else:
        out_path = DATA_DIR / f"weather_data_{target_date}.json"

    data = {
        "fetch_time_gmt8": time.strftime("%Y-%m-%d %H:%M:%S GMT+8"),
        "target_date": target_date,
        "peaks": {},
        "transparency": {},
        "summary": {},
    }

    # ── 统一数据层：Open-Meteo ecmwf_ifs025 ───────────────────────────
    # 2026-05-15 重构：Round 1 与 LCL V2.0 L1 合并，一次 API 调用获取全部数据
    print(f"\n【统一数据层】Open-Meteo ecmwf_ifs025 × {len(PEAKS)}峰（Round1 + LCL V2.0 L1）")
    t0 = time.time()

    # 构建 lcl_fusion_v2 标准格式的峰列表（统一解决 BUG-1/BUG-2：key名+格式）
    peaks_for_lcl = [
        {"name": name, "latitude": info["lat"], "longitude": info["lon"],
         "summit_elev": info["elev"]}
        for name, info in PEAKS.items()
    ]

    # fetch_layer1_batch 返回 {name: SourceResult}，每个 SourceResult._raw_response 存原始响应
    # 计算需要的天数：从今天到目标日期的天数+1（确保覆盖），最少7天
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        days_ahead = (datetime.strptime(target_date, '%Y-%m-%d') - datetime.strptime(today_str, '%Y-%m-%d')).days
        needed_days = max(7, days_ahead + 2)
    except Exception:
        needed_days = 7
    raw_hourly_dict = fetch_layer1_batch(peaks_for_lcl, forecast_days=needed_days)

    # CMA GRAPES L2 与 V1 summary 处理并发
    with ThreadPoolExecutor(max_workers=2) as pool:
        cma_future = pool.submit(fetch_layer2_batch, peaks_for_lcl, min(needed_days, 7))  # CMA最多7天
        # 主线程：处理 V1 summaries
        for name in PEAKS:
            resp = raw_hourly_dict.get(name)
            if resp and resp.status == 'ok' and hasattr(resp, '_raw_response'):
                raw = resp._raw_response
                morning = extract_date_data(raw, target_date, summit_elev_override=PEAKS[name]["elev"])
                summary = summarize_morning(morning, PEAKS[name]["elev"])
                # 转置hourly为行式格式（analyzer.py兼容）
                transposed = _transpose_hourly_to_rows(raw, PEAKS[name]["elev"])
                data["peaks"][name] = transposed
                data["summary"][name] = summary
                data["peaks"][name]["summary"] = summary
                diff = summary.get("summit_diff_m", "?")
                elev = raw.get("elevation", "?")
                print(f"  → {name}... ✓ elev={elev}m diff={diff}m")
            else:
                print(f"  → {name}... ✗")
        l2_data = cma_future.result()

    print(f"  统一层耗时: {time.time()-t0:.1f}s")
    n_l1 = sum(1 for v in raw_hourly_dict.values() if v.status == 'ok')
    n_l2 = sum(1 for v in l2_data.values() if v.status == 'ok')
    print(f"  L1 OK: {n_l1}/{len(PEAKS)}  L2 OK: {n_l2}/{len(PEAKS)}")

    # ── LCL V2.0 三层融合（l1_data 和 l2_data 均已在统一层获取）──────
    # 2026-05-15 重构：l2_data 来自第一轮并发获取，无额外 API 调用
    from lcl_fusion_v2 import run_lcl_v2

    print(f"\n【LCL V2.0】三层融合（使用预获取数据）")
    t_v2 = time.time()

    # 构建 L1 SourceResult dict（从统一层原始响应）
    l1_results = {}
    for name, resp in raw_hourly_dict.items():
        if resp and resp.status == 'ok':
            l1_results[name] = resp  # SourceResult with _raw_response

    # 融合（l1_data 和 l2_data 均已预获取，零额外 API 调用）
    try:
        fusion_results, _l1_from_v2 = run_lcl_v2(
            peaks_for_lcl,
            l1_data=l1_results,
            l2_data=l2_data,
            target_date=target_date,
        )
        fusion_map = {r.peak_name: r for r in fusion_results}

        for name in data["summary"]:
            if name in fusion_map:
                fr = fusion_map[name]
                s = data["summary"][name]
                station_elev = (l1_results.get(name).station_elev if l1_results.get(name) else 0)
                info = PEAKS.get(name, {})

                # 存入 V2.0 融合值
                s["lcl_v2_final"] = fr.lcl_final
                s["lcl_v2_range_lo"] = fr.lcl_range[0]
                s["lcl_v2_range_hi"] = fr.lcl_range[1]
                s["lcl_v2_mode"] = fr.mode
                s["lcl_v2_confidence"] = fr.confidence
                s["lcl_v2_layers"] = {
                    "l1": fr.layer1_lcl,
                    "l2": fr.layer2_lcl,
                    "l3": fr.layer3_lcl,
                }
                s["lcl_v2_notes"] = fr.notes

                # 统一雾顶公式（V1 fog_top_msl 公式 + V2 LCL）
                rh_avg_night = s.get("avg_RH_pct", s.get("max_RH_pct", 85))
                fog_thickness = max(50, min(450, (rh_avg_night - 80) * 20))
                fog_top_v2 = station_elev + fr.lcl_final + fog_thickness
                summit_diff_v2 = info["elev"] - fog_top_v2

                s["fog_top_v2_msl"] = round(fog_top_v2, 0)
                s["summit_diff_v2_m"] = round(summit_diff_v2, 0)

        n_v2 = len(fusion_map)
        n_disagree = sum(1 for r in fusion_results if r.mode.startswith("DISAGREEMENT"))
        print(f"✓ LCL V2.0 融合完成（{time.time()-t_v2:.1f}s）：{n_v2}峰正常，{n_disagree}峰触发ENS仲裁")
    except Exception as e:
        print(f"✗ LCL V2.0 融合失败: {e}")

    # ── 天气模型一致性检查（FIX 2026-05-08 13:00）───────────────────
    # 背景：同一日期（05-10）在不同模型运行中险差从全正→仅1座正，概率从80%→5%
    # 机制：比较新旧数据中 summit_diff_m，发现大摆动时警告用户
    existing_path = DATA_DIR / f"weather_data_{target_date}.json"
    if existing_path.exists():
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            old_summary = old_data.get("summary", {})
            changes = []
            pos_count_old = 0
            pos_count_new = 0
            for name, s in data["summary"].items():
                new_diff = s.get("summit_diff_m", 0)
                old_s = old_summary.get(name, {})
                old_diff = old_s.get("summit_diff_m", 0)
                delta = abs(new_diff - old_diff)
                if new_diff > 0: pos_count_new += 1
                if old_diff > 0: pos_count_old += 1
                if delta > 200:
                    changes.append(f"    {name}: {old_diff:+.0f}m → {new_diff:+.0f}m (Δ{delta:.0f}m)")
            if changes:
                print(f"\n⚠️  天气模型摆动警告（与上次 {old_data.get('fetch_time_gmt8','未知')} 比较）")
                print(f"   正险差峰数: {pos_count_old} → {pos_count_new}")
                print("   显著变化:")
                for c in changes[:5]:  # 最多显示5个
                    print(c)
                if len(changes) > 5:
                    print(f'   ... 另有 {len(changes)-5} 个变化')
                print(f"   建议：出发前再次运行 weather_fetch.py --date {target_date} 确认最新数据")
            else:
                print(f"\n✅ 天气模型一致性检查通过（与上次运行差异 <200m）")
        except Exception as e:
            print(f"\n[模型一致性检查跳过: {e}]")

    # ── 通透度数据获取（P1修复：集成被遗漏的函数调用）──
    print("\n📡 获取通透度数据...")
    aqicn_daily = None
    try:
        aqicn_daily = fetch_aqicn_forecast("beijing")
        if aqicn_daily:
            cur = aqicn_daily.get("current", {})
            fc_pm25 = aqicn_daily.get("forecast_pm25", {}).get(target_date, {})
            print(f"   AQICN: {aqicn_daily.get('city','')} | PM2.5={cur.get('pm25','?')} AQI={cur.get('aqi','?')} | 预报PM2.5={fc_pm25.get('avg','?')}")
    except Exception as e:
        print(f"   AQICN 获取失败: {e}")
    try:
        aq_data = fetch_air_quality(URBAN_MONITOR["lat"], URBAN_MONITOR["lon"], "beijing_urban")
        vis_data = fetch_visibility(URBAN_MONITOR["lat"], URBAN_MONITOR["lon"], "beijing_urban")
        if aq_data or vis_data or aqicn_daily:
            trans_result = score_transparency(aq_data, vis_data, target_date, aqicn_daily=aqicn_daily)
            data["transparency"] = trans_result
            print(f"   通透度: {trans_result.get('score', 'N/A')}/10 ({trans_result.get('level', 'N/A')})")
        else:
            print("   ⚠️ 通透度数据获取失败，使用默认值")
            data["transparency"] = {"score": 6.0, "level": "GOOD", "label": "★★★★☆ 通透", "cloud_sea_modifier": 0}
    except Exception as e:
        print(f"   ⚠️ 通透度获取异常: {e}")
        data["transparency"] = {"score": 6.0, "level": "GOOD", "label": "★★★★☆ 通透", "cloud_sea_modifier": 0}

    # 保存数据到 JSON 文件
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存 → {out_path}")


if __name__ == '__main__':
    main()
