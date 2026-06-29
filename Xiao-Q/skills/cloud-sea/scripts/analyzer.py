# -*- coding: utf-8 -*-
"""
analyzer.py - 统一的云海数据分析脚本

用法:
    python analyzer.py                          # 分析 weather_data.json(默认日期)
    python analyzer.py --date 2026-04-23       # 指定目标日期
    python analyzer.py --date 2026-04-25 --print  # 打印完整分析
    python analyzer.py --date 2026-04-25 --config  # 生成 report_config.json
    python analyzer.py --date 2026-04-25 --all  # 打印 + 生成配置

本脚本统一了 analyze_apr23/24/25.py 和 build_report_config*.py 的逻辑。
不再需要每个日期新建一个脚本。
"""
import json, sys, pathlib, argparse
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# 共享常量
sys.path.insert(0, str(pathlib.Path(__file__).parent))
SCRIPT_DIR = pathlib.Path(__file__).parent
from cloud_sea_shared import (
    FACTOR_WEIGHTS, FACTOR_WEIGHT_VALUES, calc_fog_type,
    PEAK_ELEVATIONS, NEAR_WATER_PEAKS, _SUNRISE_TABLE,
    SunriseThresholds, FactorThresholds, VetoThresholds
)

# ============================================================
# 雾型诊断(统一逻辑,从 build_report_config_apr25.py 提炼)
# ============================================================

# calc_fog_type 已从 cloud_sea_shared 导入(唯一真相源)
# _SUNRISE_TABLE 已从 cloud_sea_shared 导入,禁止重复定义

# ============================================================
# LCL V2.0 辅助函数(2026-05-14 Phase 3 集成)
# ============================================================
def _v2_lcl(s):
    """获取LCL值:优先V2.0融合值,回退V1单源值"""
    # 优先从 summary 层取 V2（weather_fetch 写入位置）
    summary = s.get("summary", {})
    v2 = s.get("lcl_v2_final") or summary.get("lcl_v2_final")
    if v2 is not None:
        return v2
    return s.get("min_lcl_ag_m", 9999)

def _v2_diff(s):
    """"获取险差:优先V2.0,回退V1"""
    # 优先从 summary 层取 V2（weather_fetch 写入位置）
    summary = s.get("summary", {})
    v2 = s.get("summit_diff_v2_m") or summary.get("summit_diff_v2_m")
    if v2 is not None:
        return v2
    return s.get("summit_diff_m", 0)

def _v2_fog_top(s):
    """"获取雾顶:优先V2.0,回退V1"""
    # 优先从 summary 层取 V2（weather_fetch 写入位置）
    summary = s.get("summary", {})
    v2 = s.get("fog_top_v2_msl") or summary.get("fog_top_v2_msl")
    if v2 is not None:
        return v2
    return s.get("max_fog_top_msl", 0)
    if v2 is not None:
        return v2
    return s.get("max_fog_top_msl", 0)

# NOTE: _v2_is_active() removed (2026-05-15) - was dead code (0 calls)
# V2.0 availability is checked inline via .get() fallback in _v2_lcl/_v2_diff/_v2_fog_top

def sunny_rating(cc, fog_score, above_positive, rh, vis, score, lcl=0):
    """日出评分（1-5星）

    2026-05-22 V3重构: 用LCL+RH替代cc作为主判据
    """

    # Guard against None values
    vis = vis if vis is not None else 0
    score = score if score is not None else 0
    lcl = lcl if lcl is not None else 0
    T = SunriseThresholds
    
    # === 优先级1: 干燥气团否决 ===
    # 低湿+高LCL=无雾假象,即使模型给出正diff也不可信
    if rh < T.DRY_RH_STRICT and lcl > T.DRY_LCL_THRESHOLD and above_positive:
        return 2 if vis >= T.SHALLOW_VIS_PERFECT else 1
    if rh < T.DRY_RH_LOOSE and lcl > 200 and above_positive:
        return 2

    # 必须有雾(above_positive=True)才有意义
    if not above_positive:
        return 1

    # === 优先级2: 稳定浅雾+云海(最理想场景) ===
    # LCL<100m=雾层极薄,山顶完全在雾上; RH高=雾层稳定; 通透度好=日出可见
    if lcl < T.SHALLOW_LCL and rh >= T.SHALLOW_RH and vis >= T.SHALLOW_VIS_GOOD:
        if fog_score >= T.FOG_SCORE_HIGH and vis >= T.SHALLOW_VIS_PERFECT:
            return 5  # 完美: 浅雾+高稳定+高通透
        if fog_score >= T.FOG_SCORE_MED:
            return 4  # 优秀: 浅雾+稳定
    if lcl < T.SHALLOW_LCL and rh >= 80 and vis >= 10:
        return 3  # 良好: 浅雾+一般通透

    # === 优先级3: 中层雾+云海 ===
    # LCL 100-300m: 雾层中等厚度,需RH和通透度配合
    if lcl < T.MEDIUM_LCL and rh >= T.MEDIUM_RH and vis >= T.MEDIUM_VIS:
        if fog_score >= T.FOG_SCORE_HIGH:
            return 4  # 高湿稳定+好通透
        return 3  # 条件尚可
    if lcl < 200 and rh >= 85 and vis >= 10:
        return 3

    # === 优先级4: 厚雾/多云(普通场景) ===
    # LCL 300-500m: 雾层厚,日出被部分遮蔽; 或cc高说明高层云多
    if lcl < T.THICK_LCL and rh >= T.SHALLOW_RH and fog_score >= T.FOG_SCORE_LOW:
        return 2

    # === 优先级5: 兜底 ===
    # LCL>500m 或 RH偏低: 雾层太厚/不稳定,日出不可见
    if fog_score >= T.FOG_SCORE_MIN:
        return 2
    return 1


# FIX (2026-05-09 lesson53): 高海拔LCL阈值调整函数
# 原理:海拔越高,低层大气越稀薄,需要更大的T-Td差才能形成雾。
# 对于station_elev~1500m的山峰,固定阈值600m过于严苛。
# 方案:每升高100m,阈值增加25m(上限+500m)
def _lcl_thresholds_for_altitude(station_elev):
    """返回高海拔调整后的LCL阈值(t1,t2,t3,t4)

    2026-05-21 P4重构: 基于LCL观测数据的经验公式
    数据源: 16峰×9小时×2天 = 288个逐时LCL观测值

    物理原理:
    - LCL = 125 × (T - Td), 主要取决于温度露点差
    - 高海拔气压低→同T-Td差的LCL更大, 但差异被大气柱水汽分布部分抵消
    - 实际观测显示LCL与海拔相关性R²=0.56(中等), 天气条件是主导因素

    经验公式:
    - 基于逐时LCL的分位数回归, 按海拔线性插值
    - t1(p25)=优秀阈值, t2(p50)=良好, t3(p75)=中等, t4(p90)=较差
    - 下界保护: t1≥25m(避免LCL≈0时trivially满分)
    - 上界保护: t4≤800m(避免高海拔过度惩罚)

    示例:
    - station_elev=154m (长峪城):  (25, 51, 103, 164)
    - station_elev=506m (妙峰山):   (25, 51, 103, 164)
    - station_elev=1034m (百花山):  (25, 78, 156, 345)
    - station_elev=1447m (西南灵山): (25, 54, 244, 584)
    """
    # 三档分位数阈值(基于288个观测点)
    # 格式: (elev_lo, elev_hi, t1, t2, t3, t4)
    BANDS = [
        (0,    600,   25,  51, 103, 164),   # 低海拔: 9峰
        (600,  1100,  25,  78, 156, 345),   # 中海拔: 4峰
        (1100, 3000,  25,  54, 244, 584),   # 高海拔: 3峰
    ]

    # 找到对应海拔档, 线性插值
    elev = max(0, min(station_elev, 3000))
    for i, (lo, hi, t1, t2, t3, t4) in enumerate(BANDS):
        if lo <= elev < hi:
            return t1, t2, t3, t4
    # 超出范围 → 使用最近档
    if elev < BANDS[0][0]:
        return BANDS[0][2], BANDS[0][3], BANDS[0][4], BANDS[0][5]
    return BANDS[-1][2], BANDS[-1][3], BANDS[-1][4], BANDS[-1][5]


# ============================================================
# 天气否决辅助函数(P1重构 2026-05-21)
# 3套否决逻辑拆分为独立函数,统一返回 (override, factor_score, detail)
# override: None=不否决, 数值=否决强度(直接短路factor_total)
# factor_score: 因子1的评分(1-10)
# detail: 诊断信息字符串
# ============================================================

def _veto_clear_sky(wc_list, rh_list):
    """否决1: 晴空否决 — 天气代码过多晴朗,辐射雾条件不足

    物理原理: 晴夜虽有利于辐射冷却,但需高湿度配合。
    WMO天气码 0/1=晴/少云,若00-08时全晴且RH低,雾不可能形成。
    但晴夜+RH≥70%时是辐射雾理想条件,不应否决。
    """
    if not wc_list:
        return None, None, ""
    avg_wc = sum(wc_list) / len(wc_list)
    clear_count = sum(1 for wc in wc_list if wc <= 1)
    clear_ratio = clear_count / len(wc_list)
    detail = f"均码={avg_wc:.1f},晴夜{clear_count}/{len(wc_list)}时"

    # 由强到弱判定
    avg_rh = sum(rh_list) / len(rh_list) if rh_list else 0

    # P0 FIX (2026-05-22): 晴夜+高湿是辐射雾理想条件，不应否决！
    # RH≥70%时无论多晴都不否决(辐射冷却+水汽充足=辐射雾)
    if avg_rh >= VetoThresholds.RH_EXCEPTION:
        return None, 8, f"{detail}(晴夜+高湿{avg_rh:.0f}%,辐射雾理想)"

    # 以下仅在RH<{VetoThresholds.RH_EXCEPTION}%时触发(水汽不足,晴夜也不会形成雾)
    if avg_wc <= 0.5 and clear_ratio >= 1.0:
        return 0.3, 1, f"{detail}(全程晴朗+干燥,强否决)"
    if avg_wc <= 1.0 and clear_ratio >= 0.875:
        return 0.5, 1, f"{detail}(几乎全程晴朗+干燥,强否决)"
    if avg_wc <= 1.5 and clear_ratio >= 0.75:
        return 1.5, 2, f"{detail}(大部晴朗+干燥,否决)"
    if avg_wc <= VetoThresholds.CLEAR_SKY_WC and clear_ratio >= 0.5:
        return None, 4, f"{detail}(半数晴朗+干燥,轻度降分)"

    # 多云/阴天: 不否决
    if avg_rh >= 60:
        return None, 7, f"{detail}(多云/阴,正常评分)"
    return None, 5, f"{detail}(多云/阴+偏干,略降)"


def _veto_dry_air(rh_list):
    """否决2: 干空气否决 — 夜间RH过低,水汽不足

    物理原理: 辐射雾需要RH≥70%才可能形成。
    RH<50%=极干(几乎不可能), RH<60%=强干, RH<70%=中干
    此否决与晴空否决独立,取两者中更强者。
    """
    if not rh_list:
        return None, None, ""
    avg_rh = sum(rh_list) / len(rh_list)
    min_rh = min(rh_list)
    detail = f"干空气否决-RH{avg_rh:.0f}%均值/{min_rh:.0f}%最低"

    if avg_rh < 50:
        return 0.3, 1, detail  # 极干
    if avg_rh < 60:
        return 0.5, 1, detail  # 强干
    if avg_rh < 70:
        return 1.0, 3, detail  # 中干
    return None, None, ""  # RH足够,不否决


def _veto_low_cloud(cc_low_list, rh_06_list):
    """否决3: 低云检查 — ECMWF cc_low在0.25°下几乎永远=0

    物理原理: 模型无法解析1-10km尺度的山谷辐射雾/地形雾。
    cc_low=0不能等同于"无雾",需结合RH判断:
    - cc_low=0 + RH<70%: 确实干燥,否决
    - cc_low=0 + RH≥80%: 高湿,模型漏判,仅降因子分
    - cc_low>30%: 模型确认低云,支持雾型
    """
    if not cc_low_list:
        return None, None, ""
    cc_avg = sum(cc_low_list) / len(cc_low_list)
    rh_avg = sum(rh_06_list) / len(rh_06_list) if rh_06_list else 0
    detail = f"低云均={cc_avg:.1f}%({len(cc_low_list)}时) RH06={rh_avg:.0f}%"

    if cc_avg > 30.0:
        return None, 7, f"{detail}(丰富低云)"
    if cc_avg > 15.0:
        return None, 5, f"{detail}(中等低云)"
    if cc_avg > 5.0:
        if rh_avg >= 80:
            return None, 3, f"{detail}(少低云+高湿,仅降因子分)"
        return 1.2, 3, f"{detail}(少低云,轻否决)"
    if cc_avg > 0.5:
        if rh_avg >= 80:
            return None, 2, f"{detail}(微量低云+高湿,仅降因子分)"
        if rh_avg >= 70:
            return 1.5, 2, f"{detail}(微量低云+RH中等,轻否决)"
        return 0.6, 2, f"{detail}(微量低云+干燥,否决)"
    # cc_low=0
    if rh_avg >= 90:
        return None, 3, f"{detail}(全0但RH≥90%,模型漏判,仅降因子分)"
    if rh_avg >= 80:
        return None, 2, f"{detail}(全0但RH≥80%,模型漏判,仅降因子分)"
    if rh_avg >= 70:
        return 2.0, 2, f"{detail}(全0+RH中等,轻否决)"
    return 0.3, 1, f"{detail}(全0+干燥,强否决)"


# ============================================================
# 12因子评分(从 build_report_config.py 提炼)
# ============================================================

# 12因子权重(来自 cloud_sea_shared,禁止重复定义)
# FACTOR_WEIGHTS 已从共享模块导入

def build_12factors(s, top_pk=None, target_month=4, target_date=None, peak_name=""):
    """从峰摘要构建12因子评分列表

    s: summary dict (per-peak summary from weather_fetch.py)
    top_pk: peaks[name] dict (raw peak data with hourly/daily, optional for enriched scores)
    target_month: int, 目标月份 (1-12), 用于季节调整
    target_date: str, 目标日期 "YYYY-MM-DD", 用于定位 daily/hourly 数据的正确索引

    Returns:
        (factors, weather_override, clear_ratio): 12个评分因子 + 天气否决值(None=不否决) + 晴时段占比(0.0~1.0)
    """
    factors = []
    rh_night = s.get("max_RH_pct", 80)

    # 辅助:获取 daily 数据中目标日期的索引
    def _daily_idx(daily_data, tdate):
        """在 daily['time'] 中查找目标日期的索引,未找到则返回 0"""
        times = daily_data.get("time", [])
        if tdate and tdate in times:
            return times.index(tdate)
        return 0  # fallback

    # ============================================================
    # 天气否决系统(P1重构 2026-05-21)
    # 将3套否决(晴空/干空气/低云)拆分为独立函数,统一接口
    # ============================================================
    weather_override = None  # None=不否决,否则覆盖 f_total
    weather_factor_score = 5  # 默认中间分
    weather_detail = "无数据"

    # 提取00-08时数据(供多个否决函数共用)
    _wc_list = []   # 天气代码
    _rh_list = []   # 湿度%
    _cc_low_list = []  # 低云量%
    _rh_06_list = []  # 00-06湿度(日出前)
    if top_pk and target_date:
        hourly = top_pk.get("hourly", [])
        for h in hourly:
            t = h.get("time", "")
            if not t.startswith(target_date):
                continue
            hour = int(t[11:13]) if len(t) >= 13 else -1
            if 0 <= hour <= 8:
                wc = h.get("weather_code")
                if wc is not None:
                    _wc_list.append(int(wc))
                rh = h.get("RH_pct")
                if rh is not None:
                    _rh_list.append(float(rh))
                cc_low = h.get("cc_low") or h.get("cloud_cover_low")
                if cc_low is not None:
                    _cc_low_list.append(float(cc_low))
                if 0 <= hour <= 6:
                    rh6 = h.get("RH_pct") or h.get("rh")
                    if rh6 is not None:
                        _rh_06_list.append(float(rh6))

    # 否决1: 晴空否决(天气代码过多晴朗→辐射雾条件不足)
    sky_override, sky_score, sky_detail = _veto_clear_sky(_wc_list, _rh_list)
    if sky_override is not None:
        weather_override = sky_override
        weather_factor_score = sky_score
        weather_detail = sky_detail

    # 否决2: 干空气否决(RH过低→水汽不足,无论晴空规则是否触发)
    dry_override, dry_score, dry_detail = _veto_dry_air(_rh_list)
    if dry_override is not None:
        if weather_override is None:
            weather_override = dry_override
            weather_factor_score = dry_score
            weather_detail = dry_detail
        elif weather_override < dry_override:
            # 干空气否决比晴空否决更强,替换
            weather_override = dry_override
            weather_factor_score = dry_score
            weather_detail = f"{weather_detail} -> {dry_detail}"

    # 否决3: 低云检查(cc_low=0时结合RH判断模型是否漏判)
    # P3 FIX (2026-05-21): 低云否决(cc_low物理依据最弱)不应覆盖更强的晴空/干空气否决
    cc_low_override, cc_low_score, cc_low_detail = _veto_low_cloud(_cc_low_list, _rh_06_list)
    if cc_low_override is not None and (weather_override is None or weather_override > cc_low_override):
        weather_override = cc_low_override
        weather_factor_score = cc_low_score
        weather_detail = f"{weather_detail} | {cc_low_detail}"
    elif cc_low_score is not None:
        weather_factor_score = cc_low_score
        weather_detail = f"{weather_detail} | {cc_low_detail}"

    # ============================================================
    # 阴雨天气否决(2026-05-15 FIX - 用户发现的74%假阳性)
    # 2026-05-17 FIX: 全天否决→逐时段否决
    # 2026-05-21 FIX: 删除重复的第二遍代码(原第390-420行为死代码副本)
    # ============================================================
    clear_hours = 0   # 可观测时段数
    total_hours = 0   # 总时段数(00-08)
    rain_hours_detail = []  # 雨时段明细
    if top_pk and target_date:
        hourly = top_pk.get("hourly", [])
        for h in hourly:
            t = h.get("time", "")
            if not t.startswith(target_date):
                continue
            hour = int(t[11:13]) if len(t) >= 13 else -1
            if 0 <= hour <= 8:
                total_hours += 1
                cc_val = h.get("cloud_cover", 0) or 0
                pp_val = h.get("precipitation_probability", 0) or 0
                is_rain_hour = (float(cc_val) >= 90 and float(pp_val) >= 50)
                if is_rain_hour:
                    rain_hours_detail.append(f"{hour:02d}:00(cc={int(cc_val)}% pp={int(pp_val)}%)")
                else:
                    clear_hours += 1
    # 计算晴时段占比
    if total_hours > 0:
        clear_ratio = clear_hours / total_hours  # 0.0~1.0
    else:
        clear_ratio = 1.0  # 无数据时不否决
    # 存储到因子供后续使用
    _rain_clear_ratio = clear_ratio
    _rain_hours_detail = rain_hours_detail

    # 因子1: 辐射冷却(夜间温差 T_max - T_min,大温差=强辐射冷却)
    # H-5 FIX: 使用目标日期的 daily 索引,而非 [0](=今天)
    if top_pk:
        daily = top_pk.get("daily", {})
        idx = _daily_idx(daily, target_date)
        t_max_list = daily.get("temperature_2m_max", [20])
        t_min_list = daily.get("temperature_2m_min", [10])
        t_max = t_max_list[idx] if isinstance(t_max_list, list) and idx < len(t_max_list) else t_max_list[0] if isinstance(t_max_list, list) else t_max_list
        t_min = t_min_list[idx] if isinstance(t_min_list, list) and idx < len(t_min_list) else t_min_list[0] if isinstance(t_min_list, list) else t_min_list
        temp_range = t_max - t_min
        # 温差评分: >=15°C → 10分, 10°C → 7分, 5°C → 3分, <3°C → 1分
        if temp_range >= 15:   f1 = 10
        elif temp_range >= 10: f1 = 7
        elif temp_range >= 5:  f1 = 3
        else:                  f1 = 1
    else:
        # fallback: 无 daily 数据时用 RH 反推(高RH抑制辐射冷却)
        f1 = max(1, round(10 - (rh_night - 50) / 5))
    factors.append(("辐射冷却", f1))

    # 因子2: 稳定层结(LCL低=层结稳定)
    # AUDIT-005 FIX: 改为分段评分(原线性公式在100-300m区间过惩罚)
    # 2026-05-09 lesson53 FIX: 高海拔阈值调整(每100m +25m,上限+500m)
    lcl = _v2_lcl(s)  # Phase 3: 优先V2.0融合LCL,回退V1单源
    if top_pk:
        # P4 FIX: 使用station_elev(API格点海拔)而非summit_elev(山峰海拔)
        # _lcl_thresholds_for_altitude基于station_elev的LCL观测数据建立
        stn_elev = top_pk.get('elevation', top_pk.get('station_elev', 50))
        t1, t2, t3, t4 = _lcl_thresholds_for_altitude(stn_elev)
    else:
        # 无top_pk时使用固定阈值
        t1, t2, t3, t4 = 100, 200, 400, 600
    if lcl < t1:     f2 = 10
    elif lcl < t2:   f2 = 8
    elif lcl < t3:   f2 = 5
    elif lcl < t4:   f2 = 3
    else:            f2 = 1
    factors.append(("稳定层结", f2))

    # 因子3: 风力条件
    wind = s.get("min_wind_kmh", 999)
    # P1 FIX (2026-05-22): 高海拔风速修正
    # 原理: API返回的是格点/站点海拔风速，山顶风速通常更大
    # MEMORY.md: 等效风速 = 观测风速 × 0.7 (海拔>1500m时反推站点风速)
    # 但我们反过来: 山顶风速 ≈ 站点风速 / 0.7 (站点在山脚)
    # 更保守: station_elev < summit_elev - 500m 时修正
    stn_elev_3 = top_pk.get('elevation', 0) if top_pk else 0
    summit_3 = PEAK_ELEVATIONS.get(peak_name, stn_elev_3)
    if summit_3 - stn_elev_3 > 500 and stn_elev_3 > 0:
        # 山顶比站点高500m+，山顶风速≈站点×1.5
        wind_eff = wind * 1.5
    else:
        wind_eff = wind
    if wind_eff <= 1:      f3 = 10
    elif wind_eff <= 3:    f3 = 8
    elif wind_eff <= 6:    f3 = 5
    elif wind_eff <= 10:   f3 = 2
    else:              f3 = 0
    factors.append(("风力条件", f3))

    # 因子4: 水汽供给(夜间最大RH)
    factors.append(("水汽供给", min(10, rh_night / 10)))

    # 因子5: 前置降水(从 hourly 实际降水量计算)
    # H-3 FIX: 前置降水应为前1天,而非前2天(7天预报数据可能不足)
    if top_pk:
        hourly = top_pk.get("hourly", [])
        if target_date:
            try:
                d1 = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                target_hours = [h for h in hourly if h.get("time", "").startswith(d1)]
            except Exception:
                target_hours = []
            precip_sum = sum(h.get("precip_mm", 0) for h in target_hours) if target_hours else 0
        else:
            precip_sum = sum(h.get("precip_mm", 0) for h in hourly[:24]) if hourly else 0
        # 评分: >5mm → 10, 2-5mm → 8, 0.5-2mm → 5, <0.5mm → 2
        if precip_sum > 5:     f5 = 10
        elif precip_sum > 2:   f5 = 8
        elif precip_sum > 0.5: f5 = 5
        else:                  f5 = 2
    else:
        f5 = 5  # 无数据时给中间分
    factors.append(("前置降水", f5))

    # 因子6: 云底 vs 海拔
    diff = _v2_diff(s)  # Phase 3: 优先V2.0融合险差
    # P1 FIX (2026-05-22): 常数300→100，使diff=0（临界可见）→f6=1.0而非3.0
    if diff > 0:
        f6 = min(10, max(0, (diff + 100) / 100))
    else:
        f6 = max(0, diff / 50 + 3)
    factors.append(("云底 vs 海拔", round(f6, 1)))

    # 因子7: 日出时机(云量)
    # H-3 FIX: 使用日出时刻的云量,而非 max_cloud_cover(凌晨最差云量)
    # sunrise_cc 来自 sunrise_h 的 cloud_cover,若无则 fallback 到 max_cloud_cover
    sunrise_cc = s.get("sunrise_cloud_cover", s.get("max_cloud_cover", 999))
    if sunrise_cc <= 10:   f7 = 10
    elif sunrise_cc <= 30: f7 = 7
    elif sunrise_cc <= 60: f7 = 4
    else:                  f7 = 1
    factors.append(("日出时机", f7))

    # 因子8: 季节调整(按月份动态评分)
    # P1 FIX (2026-05-22): 5月下旬受东亚季风前缘影响,通透度差
    # 4月初/9-10月最佳, 5月下旬/6-8月较差
    f8 = FactorThresholds.SEASON_SCORES.get(target_month, 5)
    factors.append(("季节调整", f8))

    # 因子9: 地形优势(从 PEAK_ELEVATIONS 获取真实山峰海拔)
    # P0 FIX (2026-05-21): 旧版用 s.get("summit_elev", 1000) 但 summary 无此键,永远1000→f9=3
    # 改为从 PEAK_ELEVATIONS(权威数据源)获取,通过 peak_name 参数传入
    summit = PEAK_ELEVATIONS.get(peak_name, 1000)
    if summit >= 2000: f9 = 9
    elif summit >= 1500: f9 = 7
    elif summit >= 1200: f9 = 5
    else: f9 = 3
    factors.append(("地形优势", f9))

    # 因子10: 夜间晴空(云量近似,用 MIN!晴空=低云量)
    cc_night = s.get("min_cloud_cover", 50)
    factors.append(("夜间晴空", max(0, 10 - cc_night / 10)))

    # 因子11: 能见度(C-2 FIX: 从通透度评分或山顶能见度实际推导)
    # 优先级: transparency_score > peak_visibility > 城区能见度 > 默认5分
    vis_score = s.get("transparency_score", None)
    if vis_score is not None and isinstance(vis_score, (int, float)):
        f11 = min(10, vis_score)
    elif isinstance(vis_score, dict) and "value" in vis_score:
        f11 = min(10, vis_score["value"])
    elif s.get("max_visibility_km") is not None:
        # H-1 FIX: 使用实际能见度数据(不再是硬编码20km)
        vis_val = s["max_visibility_km"]
        f11 = min(10, vis_val / 2)  # 20km → 10分
    else:
        f11 = 5  # C-2 FIX: 无数据时给中等分5(非6,更保守)
    factors.append(("能见度", f11))

    # 因子12: 不确定性 — 集成ENS集合标准差
    # P3 FIX (2026-05-22): 使用V2融合时的ENS std，标准差越大→不确定性越高→分越低
    ens_std = s.get("ens_std_m")
    if ens_std is not None and ens_std > 0:
        # ENS std: 0-50m=10分, 50-150m=7分, 150-300m=4分, >300m=1分
        if ens_std <= 50:
            f12 = 10
        elif ens_std <= 150:
            f12 = 7
        elif ens_std <= 300:
            f12 = 4
        else:
            f12 = 1
    else:
        f12 = 5  # 无ENS数据时保守给中间分
    factors.append(("不确定性", f12))

    return factors, weather_override, _rain_clear_ratio


def factor_total(factors, weather_override=None):
    """计算12因子加权总分

    factors: 12个评分因子的列表 [(name, score), ...]
    weather_override: 天气否决值(晴天/干空气/低云检查触发的覆盖分数)
        - None = 不否决,正常加权
        - 数值 = 直接返回此分数(短路所有因子)

    2026-05-14 AUDIT FIX: 修复加权评分从未被执行的致命bug
    - 旧版:天气代码作为第13因子插入,导致 len!=12 永远为 True
    - 新版:天气代码不再参与评分,weather_override 作为独立参数传入
    """
    # 天气否决:当天气代码/干空气/低云检查触发时,直接返回否决分数
    if weather_override is not None:
        return round(weather_override, 1)

    if len(factors) != 12:
        # 安全回退:因子数量异常时用简单平均
        return round(sum(s for _, s in factors) / max(len(factors), 1), 1)

    weights = FACTOR_WEIGHT_VALUES
    return round(sum(s * w for (_, s), w in zip(factors, weights)), 1)


# ============================================================
# 风险矩阵
# ============================================================

def build_risks(s):
    risks = []
    wind = s.get("min_wind_kmh", 999)
    if wind > 15:
        risks.append({"level": "high", "name": "强风风险", "pct": f"{wind:.0f}km/h", "css": "r-high"})
    elif wind > 8:
        risks.append({"level": "mid", "name": "中等风力", "pct": f"{wind:.0f}km/h", "css": "r-mid"})
    else:
        risks.append({"level": "low", "name": "风力正常", "pct": f"{wind:.0f}km/h", "css": "r-low"})

    lcl = _v2_lcl(s)  # Phase 3: 优先V2.0融合LCL
    if lcl > 500:
        risks.append({"level": "mid", "name": "LCL偏高", "pct": f"{lcl:.0f}m", "css": "r-mid"})
    else:
        risks.append({"level": "low", "name": "LCL正常", "pct": f"{lcl:.0f}m", "css": "r-low"})

    diff = _v2_diff(s)  # Phase 3: 优先V2.0融合险差
    if diff < 0:
        risks.append({"level": "mid", "name": "山顶在雾中", "pct": f"差{diff:.0f}m", "css": "r-mid"})
    return risks


# ============================================================
# 时间轴 & 出行流程 & 对比分析
# ============================================================

def _sunrise_hour_for_month(month):
    """根据月份估算日出时间(北京时间)。已从共享模块导入,直接查表。"""
    return _SUNRISE_TABLE.get(month, 6.0)

def _fmt_hhmm(hours):
    """小数小时 → HH:MM 格式"""
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"

def build_timeline(score, target_month=4):
    """时间轴(日出时间根据月份动态调整)"""
    sr = _sunrise_hour_for_month(target_month)
    return [
        {"time": _fmt_hhmm(sr - 2), "event": "出发/抵达山顶",      "prob": max(0, score - 10)},
        {"time": _fmt_hhmm(sr - 0.5), "event": "谷雾开始形成",    "prob": max(0, score - 5)},
        {"time": _fmt_hhmm(sr), "event": "日出+云海同框 🌅",     "prob": score,          "peak": True},
        {"time": _fmt_hhmm(sr + 1.5), "event": "谷口开启,雾层渐散", "prob": max(0, score - 20)},
        {"time": _fmt_hhmm(sr + 2.5), "event": "收队下山或山上午餐", "prob": max(0, score - 40)},
    ]

def build_flow(target_month=4):
    """出行流程(日出时间根据月份动态调整)"""
    sr = _sunrise_hour_for_month(target_month)
    return [
        {"time": _fmt_hhmm(sr - 2), "action": "起床检查天气(APP确认云量<30%)", "tag": "check", "tag_text": "确认"},
        {"time": _fmt_hhmm(sr - 1.5), "action": "出发(山路约1-1.5h)",         "tag": "go",    "tag_text": "出发"},
        {"time": _fmt_hhmm(sr - 0.5), "action": "抵达山顶,寻找观景点",        "tag": "wait",  "tag_text": "等待"},
        {"time": _fmt_hhmm(sr), "action": "🌅 日出+云海拍摄",             "tag": "peak",  "tag_text": "最佳"},
        {"time": _fmt_hhmm(sr + 1.5), "action": "收队下山或山上午餐",        "tag": "wait",  "tag_text": "等待"},
    ]

def build_compare(top3):
    if len(top3) < 2:
        return []
    metrics = [
        ("概率",      "cloud_sea_score",  False),
        ("险差",      "summit_diff_m",    True),   # 越小越好
        ("LCL最低",   "min_lcl_ag_m",     True),
        ("最高RH",    "max_RH_pct",       False),
        ("最低风速",  "min_wind_kmh",     True),
        ("可观时段",  "above_fog_hours",   False),
    ]
    rows = []
    for label, key, invert in metrics:
        vals = [p.get(key, 0) for p in top3]
        best_idx = vals.index(min(vals)) if invert else vals.index(max(vals))
        v1 = f"{vals[0]:.0f}" if isinstance(vals[0], float) else str(vals[0])
        v2 = f"{vals[1]:.0f}" if isinstance(vals[1], float) else str(vals[1])
        winner = top3[best_idx]["name"] if best_idx < len(top3) else top3[0]["name"]
        rows.append({"item": label, "v1": v1, "v2": v2, "note": winner})
    return rows


# ============================================================
# 逐时数据提取(从 peaks[peak]['hourly'] 真实读取)
# ============================================================

def extract_hourly(peak_data, target_date, hour_range=(3, 10)):
    """
    从 peaks[peak] 的 hourly 列表中提取目标日期指定时段的数据。
    hourly_data 格式: list of dict (from weather_fetch.py)
    返回: (hours, probs, temps, sunrise_rows)
    """
    hourly = peak_data.get("hourly", [])
    if isinstance(hourly, dict):
        hourly = list(hourly.values())  # 防御:dict → list

    hours_out, temps_out, sunrise_rows = [], [], []

    for h in hourly:
        t = h.get("time", "")
        if "T" not in t:
            continue
        date_part, hour_part = t.split("T")
        if date_part != target_date:
            continue
        hour = int(hour_part.split(":")[0])
        if not (hour_range[0] <= hour <= hour_range[1]):
            continue
        hours_out.append(f"{hour:02d}:00")
        temps_out.append(h.get("T_C", 0))
        sunrise_rows.append({
            "time": t,
            "hour": f"{hour:02d}:00",
            "T": h.get("T_C", 0),
            "Td": h.get("Td_C", 0),
            "RH": h.get("RH_pct", 0),
            "wind": h.get("wind_kmh", 0),
            "lcl": h.get("lcl_ag_m", 0),
            "fog_top": h.get("fog_top_msl", 0),
            "diff": h.get("summit_diff_m", 0),
            "cc": h.get("cloud_cover", 0),
            "rain": h.get("precip_pct", 0),
            "status": "above" if h.get("above_fog") else "below",
        })

    # 估算概率:从险差推算
    top_score = 0
    for row in sunrise_rows:
        diff = row["diff"]
        rh = row["RH"]
        if diff > 0:
            p = min(100, int(50 + diff / 10 + (rh - 80)))
        else:
            p = max(0, int(50 + diff / 10 + (rh - 80)))
        row["prob"] = max(0, min(100, p))
    probs_out = [r["prob"] for r in sunrise_rows]

    return hours_out, probs_out, temps_out, sunrise_rows


# ============================================================
# 通透度
# ============================================================

def build_transparency(trans):
    """从 weather_data.json 的 transparency 字段构建透明度配置"""
    score = trans.get("score", 6.0)
    if isinstance(score, dict):
        score = score.get("score", 6.0)
    detail = trans.get("detail", {})
    return {
        "score": score,
        "level": trans.get("level", "良好"),
        "label": trans.get("label", "★★★★☆ 通透"),
        "cloud_sea_modifier": trans.get("cloud_sea_modifier", 0),
        "detail": detail,
    }


# ============================================================
# 统一计算层 (重构 2026-05-22: 消除双路径漂移)
# ============================================================

def compute_peaks(weather_data, target_date):
    """
    统一计算层 - 唯一真相源。
    对所有16峰执行: 12因子评分 + 否决 + 日出评级 + 雾型诊断 + 概率计算。
    返回 list[dict]，每峰一个字典，包含所有计算结果。
    
    print_analysis() 和 build_report_config() 都调用此函数获取数据。
    """
    import math as _math_cp
    
    summary = weather_data.get("summary", {})
    peaks = weather_data.get("peaks", {})
    trans = weather_data.get("transparency", {})
    peak_trans = weather_data.get('peak_transparency', {})
    target_month = int(target_date.split("-")[1]) if "-" in target_date else 4
    
    # 获取通透度数据
    trans_score_val = trans.get("score", None)
    if isinstance(trans_score_val, dict):
        trans_score_val = trans_score_val.get("value", None)
    trans_detail = trans.get("detail", {})
    trans_mod = trans.get("cloud_sea_modifier", 0)
    
    # VIS KM: 从通透度数据获取
    vis_km = trans_detail.get("visibility_avg_km", 20)
    if isinstance(vis_km, str):
        try:
            vis_km = float(vis_km)
        except (ValueError, TypeError):
            vis_km = 20
    
    results = []
    
    for name, s in summary.items():
        pk = peaks.get(name, {})
        hourly = pk.get("hourly", [])
        
        # === 构建 enriched summary ===
        s_enriched = dict(s)
        pt = peak_trans.get(name, {})
        if isinstance(pt, dict) and 'score' in pt:
            score_dict = pt['score']
            if isinstance(score_dict, dict) and "value" in score_dict:
                s_enriched["transparency_score"] = score_dict["value"]
            else:
                s_enriched["transparency_score"] = None
        else:
            s_enriched["transparency_score"] = trans_score_val
        s_enriched["transparency_modifier"] = trans_mod
        
        # 从山顶能见度数据获取 max_visibility_km
        peak_vis = trans.get("peak_visibility", {}).get(name, {})
        if peak_vis and "hourly" in peak_vis:
            morning_vis = [h["visibility_m"] for h in peak_vis["hourly"]
                              if h.get("time", "").startswith(target_date)
                              and 0 <= int(h["time"][11:13]) <= 8
                              and h.get("visibility_m") is not None]
            if morning_vis:
                s_enriched["max_visibility_km"] = max(morning_vis) / 1000
        if "max_visibility_km" not in s_enriched and trans_detail.get("visibility_avg_km") is not None:
            s_enriched["max_visibility_km"] = trans_detail["visibility_avg_km"]
        
        # === 12因子评分 ===
        factors, weather_ovr, clear_ratio = build_12factors(s_enriched, pk, target_month, target_date, name)
        f_total = factor_total(factors, weather_ovr)
        
        # === 天气否决日志 ===
        veto_log = ""
        if weather_ovr is not None and weather_ovr < f_total:
            veto_log = f"weather_override={weather_ovr:.1f} 生效, f_total {f_total:.1f} → {weather_ovr:.1f}"
        
        # === 概率计算 ===
        prob_pct = min(95, max(5, int(f_total * 10 * clear_ratio)))
        
        # cc_low=0 强约束: ECMWF 模型预测无低云/雾时，概率上限压低
        # 物理依据: cc_low 是模型综合所有物理过程后的最终预测,
        #   cc_low=0 表示模型认为不会形成任何低层云/雾,
        #   即使 LCL 理论值低(RH高), 模型已考虑湍流混合/下沉气流等抑制因素
        # 阈值: cc_low 均值 < 1% 视为"模型确认无低云"
        # 但 ECMWF IFS 0.25° 无法解析山谷辐射雾，cc_low=0 不等于无雾
        # 需结合 RH 判断: RH>=80% 时 cc_low=0 更可能是模型分辨率问题
        # 从 hourly 提取 cc_low(与 build_12factors 独立，避免 scope 问题)
        _cc_low_vals = [float(h["cloud_cover_low"]) for h in hourly
                        if h.get("time","").startswith(target_date)
                        and 0 <= int(h.get("time","T00:00")[11:13]) <= 8
                        and h.get("cloud_cover_low") is not None]
        cc_low_avg = sum(_cc_low_vals) / len(_cc_low_vals) if _cc_low_vals else -1
        # 同步提取 RH 用于豁免判断（用最大RH而非平均，捕捉短时高湿窗口）
        _rh_morning_vals = [float(h["RH_pct"]) for h in hourly
                            if h.get("time","").startswith(target_date)
                            and 0 <= int(h.get("time","T00:00")[11:13]) <= 6
                            and h.get("RH_pct") is not None]
        _rh_morning_max = max(_rh_morning_vals) if _rh_morning_vals else 0
        _rh_morning_avg = sum(_rh_morning_vals) / len(_rh_morning_vals) if _rh_morning_vals else 0

        # === cc_low 地形修正 (2026-06-02 三站验证通过) ===
        # ECMWF IFS 0.25° 无法解析山地辐射雾，低海拔格点 cc_low=0 不代表山上无雾
        # 修正条件: summit_elev - api_elev > 500m 且 cc_low_avg < 10%
        # 验证结论: RH>=85%门槛精准区分有雾/无雾站点（长峪城95%触发/金山岭75%不触发/雾灵山75%不触发）
        _api_elev = pk.get("elevation", 0)
        _summit_elev = PEAK_ELEVATIONS.get(name, _api_elev)
        _cc_low_original = cc_low_avg  # 保留原始值
        if _summit_elev - _api_elev > 500 and cc_low_avg >= 0 and cc_low_avg < 10:
            # 方案A: RH替代法 — RH>=85%时用 RH 推算 cc_low（2026-06-02 修正: 从90%降至85%）
            if _rh_morning_avg >= 85:
                cc_low_avg = max(cc_low_avg, min(50, _rh_morning_avg - 50))
            # 方案B: API海拔<600m 强制下限20%
            elif _api_elev < 600:
                cc_low_avg = max(cc_low_avg, 20)
            # 方案C: API海拔600-1000m 且 RH>=80% → 下限15%（捕捉中海拔站的高湿窗口）
            elif _api_elev < 1000 and _rh_morning_avg >= 80:
                cc_low_avg = max(cc_low_avg, 15)

        if cc_low_avg >= 0 and cc_low_avg < 1.0:
            if _rh_morning_max >= 80:
                # RH>=80%: cc_low=0 是模型分辨率漏判，不强否决，仅打7折
                # 2026-05-28 FIX: 用 max RH 而非 avg，捕捉短时高湿窗口
                prob_pct = min(prob_pct, int(prob_pct * 0.7))
            else:
                prob_pct = min(prob_pct, 3)
        elif cc_low_avg >= 1.0 and cc_low_avg < 5.0:
            if _rh_morning_max >= 80:
                # cc_low微量+高湿: 仅打85折
                prob_pct = min(prob_pct, int(prob_pct * 0.85))
            else:
                prob_pct = min(prob_pct, int(prob_pct * 0.6))  # cc_low很低，概率打6折
        
        # diff<0 概率兜底: 山顶在雾中时概率强制 ≤10%
        peak_diff = _v2_diff(s)
        if peak_diff is not None and peak_diff < 0:
            prob_pct = min(prob_pct, 10)
        
        # === 日出评级 ===
        # 找 06:00 的数据用于日出评分（必须匹配目标日期！）
        # 修复 Bug: endswith("T06:00") 会匹配任何日期的 06:00
        target_prefix = f"{target_date}T06:"
        sunrise_h = None
        for h in hourly:
            if h.get("time", "").startswith(target_prefix):
                sunrise_h = h
                break
        if sunrise_h is None and len(hourly) > 6:
            # fallback：取 hourly[6] 但需检查日期
            fallback = hourly[6]
            if fallback.get("time","").startswith(target_date):
                sunrise_h = fallback
        wind_kmh = sunrise_h["wind_kmh"] if sunrise_h else s.get("min_wind_kmh", 0)
        cc = sunrise_h["cloud_cover"] if sunrise_h else s.get("max_cloud_cover", 0)
        # FIX 2026-05-25: use early-morning min T-Td (most humid) for fog type, not sunrise value
        td_spread = (sunrise_h["T_C"] - sunrise_h["Td_C"]) if sunrise_h else 5.0
        if sunrise_h:
            # Find min T-Td from early morning window 01:00-06:00 (most humid / best fog formation)
            target_hours = [f"{target_date}T0{h}:00" for h in range(1, 7)]
            early_entries = [h for h in hourly if h.get("time", "") in target_hours]
            if early_entries:
                early_td_spreads = [(h.get("T_C") or 0) - (h.get("Td_C") or 0) for h in early_entries]
                td_spread = min(early_td_spreads)
        
        # 风向圆形平均
        morning_wind_entries = [h for h in hourly if h.get("time", "").startswith(target_date)
                                 and 0 <= int(h.get("time", "T00:00")[11:13]) <= 5
                                 and "wind_direction" in h]
        if morning_wind_entries:
            sin_sum = sum(_math_cp.sin(_math_cp.radians(h["wind_direction"])) for h in morning_wind_entries)
            cos_sum = sum(_math_cp.cos(_math_cp.radians(h["wind_direction"])) for h in morning_wind_entries)
            wind_dir = (_math_cp.degrees(_math_cp.atan2(sin_sum, cos_sum)) + 360) % 360
            wind_kmh = sum(h["wind_kmh"] for h in morning_wind_entries) / len(morning_wind_entries)
        else:
            wind_dir = None
            for h in hourly:
                if h.get("time", "").startswith(target_date) and "wind_direction" in h:
                    wind_dir = h["wind_direction"]
                    break
        
        # 雾型诊断
        fog_type = calc_fog_type(wind_dir, wind_kmh, s.get("max_RH_pct", 0),
                            td_spread, near_water=(name in NEAR_WATER_PEAKS))

        # cc_low=0 雾型覆盖: 模型确认无低云时, 雾型强制为"无雾"
        # 2026-05-27 FIX: RH>=80% 时 cc_low=0 是模型分辨率漏判, 不强制覆盖
        if cc_low_avg >= 0 and cc_low_avg < 1.0:
            if _rh_morning_max < 80:
                fog_type = ('none', '无雾', 'ECMWF预测cc_low≈0,无低云/雾形成')
                peak_diff = 0
            # RH>=80%: 不覆盖雾型和险差, 保持 calc_fog_type 的判断
        # 雾型否决: calc_fog_type 返回 none → 强制概率上限 10%
        elif isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2:
            if fog_type[1] in ('none', '无雾', '无云', '晴空雾'):
                prob_pct = min(prob_pct, 10)
                fog_type = (fog_type[0], fog_type[1], *fog_type[2:])
                peak_diff = 0  # 无雾时无险差
        
        # 日出星级
        fog_score_val = min(100, s.get("above_fog_hours", 0) * 20)
        star = sunny_rating(cc, fog_score_val, peak_diff > 0,
                           s.get("max_RH_pct", 0), vis_km,
                           prob_pct, lcl=_v2_lcl(s))
        stars = "⭐" * star + "☆" * (5 - star)
        
        # 出行信息
        travel = TRAVEL_MAP.get(name, ("未知", 0, 0.0))
        
        results.append({
            "name":            name,
            "summit_elev":   PEAK_ELEVATIONS.get(name, pk.get("elevation", 0)),
            "score":         prob_pct,
            "lcl":           _v2_lcl(s),
            "fog_top":       0 if (isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2 and fog_type[1] in ('none', '无雾', '无云', '晴空雾')) else _v2_fog_top(s),
            "diff":          peak_diff,
            "wind":          wind_kmh,
            "rh":            s.get("max_RH_pct", 0),
            "cc":            cc,
            "fog_type":      fog_type[1] if isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2 else str(fog_type),
            "fog_type_raw": fog_type,
            "sunrise_stars": stars,
            "star":          star,
            "clear_ratio":  round(clear_ratio, 2),
            "travel_addr":   travel[0],
            "travel_km":     travel[1],
            "travel_h":      travel[2],
            "transparency_score": peak_trans.get(name, {}).get('score', trans_score_val),
            "factors":      factors,
            "factor_total": f_total,
            "weather_override": weather_ovr,
            "veto_log":      veto_log,
            "cc_low_original": _cc_low_original,
            "cc_low_adjusted": cc_low_avg,
            # 额外字段供 print_analysis 使用
            "summary_dict": s,
            "hourly":       hourly,
        })
    
    # 按概率降序排序
    results.sort(key=lambda x: (-x["score"], -x.get("diff", 0)))
    return results


# ============================================================
# 核心:打印分析结果
# ============================================================

def print_analysis(weather_data, target_date):
    """打印完整的云海分析报告到终端（薄层）"""
    # 调用统一计算层获取数据
    results = compute_peaks(weather_data, target_date)
    
    trans = weather_data.get("transparency", {})
    fetch_time = weather_data.get("fetch_time_gmt8", "")
    
    print("=" * 70)
    print(f"云海预测分析报告 - {target_date} | 获取时间: {fetch_time}")
    print("=" * 70)

    # ---- 排名表 ----
    print("\n【16峰综合排名】")
    print(f"  {'排名':4s} {'峰名':8s} {'概率':>4s} {'LCL':>6s} {'险差':>8s} {'RH':>4s} {'风速':>7s} {'可观':>4s}")
    print(f"  {'-'*4} {'-'*8} {'-'*4} {'-'*6} {'-'*8} {'-'*4} {'-'*7} {'-'*4}")
    for i, r in enumerate(results):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1:2d}"
        diff_s = f"+{r['diff']:.0f}m" if r['diff'] >= 0 else f"{r['diff']:.0f}m"
        color = "🟢" if r['score'] >= 45 else ("🟡" if r['score'] >= 25 else "🔴")
        above = r.get("summary_dict", {}).get("above_fog_hours", 0)
        print(f"  {medal:4s} {color}{r['name']:6s} {r['score']:3d}% {r['lcl']:6.0f}m {diff_s:>8s} {r['rh']:3d}% {r['wind']:5.1f}km {above:3d}h")

    # ---- TOP3 逐时详细 ----
    print("\n" + "=" * 70)
    print(f"【TOP3 逐时数据 - {target_date} 03:00-10:00 BJT】")
    for i, r in enumerate(results[:3]):
        pk = weather_data.get("peaks", {}).get(r["name"], {})
        _, _, _, rows = extract_hourly(pk, target_date)
        print(f"\n  --- {r['name']} (概率={r['score']}%, 险差={r['diff']:+.0f}m) ---")
        if rows:
            print(f"  {'时间':20s} {'T':>5s} {'Td':>5s} {'RH%':>4s} {'风速':>7s} {'LCL':>6s} {'险差':>7s} {'云量':>4s} {'降水':>5s} {'状态':>6s}")
            for row in rows:
                print(f"  {row['time']:20s} {row['T']:5.1f} {row['Td']:5.1f} {row['RH']:4d} "
                      f"{row['wind']:5.1f}km {row['lcl']:6.0f}m {row['diff']:+7.0f}m "
                      f"{row['cc']:4d}% {row['rain']:5d}% {'ABOVE' if row['status']=='above' else 'BELOW':>6s}")
        else:
            print("  (无逐时数据)")

    # ---- 雾型诊断 ----
    print("\n" + "=" * 70)
    print(f"【雾型诊断 - {target_date} 06:00 BJT】")
    target_hr = f"{target_date}T06:00"
    peaks = weather_data.get("peaks", {})
    for r in results[:5]:
        pk = peaks.get(r["name"], {})
        for h in pk.get("hourly", []):
            if h.get("time") == target_hr:
                t   = h.get("T_C", 0)
                td  = h.get("Td_C", 0)
                rh  = h.get("RH_pct", 0)
                wind = h.get("wind_kmh", 0)
                lcl = h.get("lcl_ag_m", 0)
                cc  = h.get("cloud_cover", 0)
                rain = h.get("precip_pct", 0)
                diff = h.get("summit_diff_m", 0)
                fog_t = calc_fog_type(None, wind, rh, t - td, near_water=(r["name"] in NEAR_WATER_PEAKS))
                print(f"  {r['name']:8s}: T={t}C Td={td}C T-Td={t-td:.1f}C RH={rh}% "
                      f"wind={wind}km/h LCL={lcl}m cc={cc}% rain={rain}% diff={diff:+.0f}m → {fog_t}")
                break

    # ---- 通透度 ----
    print("\n" + "=" * 70)
    print("【大气通透度】")
    ts = trans.get("score", {})
    if isinstance(ts, dict):
        ts_score = ts.get("score", 0)
        level = ts.get('level', '?')
    else:
        ts_score = ts
        level = '?'
    det = trans.get("detail", {})
    print(f"  评分: {ts_score}/10 ({level})")
    print(f"  云海修正: {trans.get('cloud_sea_modifier', 0):+d}%")
    for k, v in det.items():
        print(f"  {k}: {v}")

    # ---- 12因子 ----
    print("\n" + "=" * 70)
    top_r = results[0]
    print(f"【12因子评分 - {top_r['name']}】")
    factors = top_r.get("factors", [])
    for i, (fname, fscore) in enumerate(factors):
        bar = "█" * int(fscore) + "░" * (10 - int(fscore))
        print(f"  {i+1:2d}. {fname:<10s} {bar} {fscore:.1f}")
    print(f"  {'-'*30}")
    print(f"  加权总分: {top_r.get('factor_total', 0)}/10")
    if top_r.get("veto_log"):
        print(f"    i️ {top_r['veto_log']}")

    print("\n" + "=" * 70)
    print("✅ 分析完成。运行 --config 生成 report_config.json")


# ============================================================
# 核心:生成 report_config.json
# ============================================================

TRAVEL_MAP = {
    "燕羽山":    ("延庆区永宁镇",        90,  2.0),
    "云蒙山":    ("密云区石城镇",        85,  2.0),
    "海坨山":    ("延庆区张山营镇",      110, 2.5),
    "百花山":    ("门头沟区清水镇",      120, 2.5),
    "东灵山":    ("门头沟区清水镇",      120, 3.0),
    "北灵山":    ("门头沟区斋堂镇",      110, 2.5),
    "黄草梁":    ("门头沟区斋堂镇",      110, 2.5),
    "白石山":    ("保定涞源县",          200, 3.5),
    "雾灵山":    ("承德兴隆县",          130, 2.5),
    "白草畔":    ("房山/涞源野三坡",      180, 3.0),
    "妙峰山":    ("门头沟区军庄镇",       40, 1.0),
    "长峪城":    ("昌平区流村镇",         70, 1.5),
    "东指壶":    ("平谷区镇罗营镇",       90, 2.0),
    "金山岭长城":("承德滦平县",          130, 2.5),
    "箭扣长城":  ("怀柔区渤海镇",         80, 2.0),
    "西南灵山":  ("门头沟区斋堂镇",       115, 2.5),
}

DAYS_CN = {"Monday":"周一","Tuesday":"周二","Wednesday":"周三",
           "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日"}


def build_report_config(weather_data, target_date, out_path=None):
    """
    从 weather_data.json 构建 report_config.json（薄层）。
    写入 out_path(默认: report_config_{date}.json)
    """
    # 调用统一计算层获取数据
    results = compute_peaks(weather_data, target_date)
    
    trans = weather_data.get("transparency", {})
    peak_trans = weather_data.get("peak_transparency", {})
    fetch_time = weather_data.get("fetch_time_gmt8", "")
    peaks = weather_data.get("peaks", {})
    
    # top1 信息
    top_r = results[0] if results else {}
    top_name = top_r.get("name", "-")
    top_pk = peaks.get(top_name, {})
    
    # day of week
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        dow = DAYS_CN.get(dt.strftime("%A"), dt.strftime("%A"))
    except:
        dow = target_date
    
    # ---- 构建 ranked 列表 ----
    ranked_out = []
    for r in results:
        ranked_out.append({
            "name":          r["name"],
            "summit_elev":   r["summit_elev"],
            "score":         r["score"],
            "lcl":           r["lcl"],
            "fog_top":       r["fog_top"],
            "diff":          r["diff"],
            "wind":          r["wind"],
            "rh":            r["rh"],
            "cc":            r["cc"],
            "fog_type":      r["fog_type"],
            "fog_type_raw": r.get("fog_type_raw"),
            "sunrise_stars": r["sunrise_stars"],
            "clear_ratio":  r["clear_ratio"],
            "travel_addr":   r["travel_addr"],
            "travel_km":     r["travel_km"],
            "travel_h":      r["travel_h"],
            "transparency_score": r["transparency_score"],
        })
    
    top3 = ranked_out[:3]

    # ---- 逐时数据(TOP1 峰真实读取)----
    hours_out, probs_out, temps_out, sunrise_rows = extract_hourly(top_pk, target_date)

    # 如果逐时为空,生成静态兜底
    if not hours_out:
        hours_out = ["04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00"]
        base = top_r.get("score", 50)
        probs_out = [max(0, base - 20), base, base, max(0, base - 10),
                     max(0, base - 30), max(0, base - 50), max(0, base - 60)]
        temps_out = [8, 9, 11, 14, 17, 19, 21]

    # ---- 12因子 ----
    target_month = int(target_date.split("-")[1]) if "-" in target_date else 4
    factors = top_r.get("factors", [])
    radar_indicator = [{"name": n, "max": 10} for n, _ in FACTOR_WEIGHTS[:5]]
    radar_value = [s for _, s in factors[:5]]
    f_total = top_r.get("factor_total", 0)

    # ---- 雾型数据 ----
    daily = top_pk.get("daily", {})
    daily_times = daily.get("time", [])
    daily_idx = daily_times.index(target_date) if target_date in daily_times else 0
    temp_max_list = daily.get("temperature_2m_max", [26])
    temp_min_list = daily.get("temperature_2m_min", [10])
    temp_max = temp_max_list[daily_idx] if isinstance(temp_max_list, list) and daily_idx < len(temp_max_list) else 26
    temp_min = temp_min_list[daily_idx] if isinstance(temp_min_list, list) and daily_idx < len(temp_min_list) else 10

    # 估算露点:从凌晨逐时数据取平均 Td
    morning_entries = [h for h in top_pk.get("hourly", [])
                      if h.get("time", "").startswith(target_date)
                      and 2 <= int(h.get("time", "T02:00")[11:13]) <= 8]
    avg_td = (sum(h.get("Td_C", temp_min) for h in morning_entries) / len(morning_entries)) if morning_entries else temp_min
    avg_pressure = (sum(h.get("pressure_hPa", 1013) for h in morning_entries) / len(morning_entries)) if morning_entries else 1013

    top_s = top_r.get("summary_dict", {})
    fog_data = {
        "lcl":             _v2_lcl(top_pk),   # V2回退,传入peak数据
        "rh":              top_r.get("rh", 70),
        "wind":            top_r.get("wind", 0),
        "cc":              top_r.get("cc", 0),
        "peak_elevation":  top_pk.get("summit_elev", 0),  # 从peak数据取,非summary
        "cloud_base":      _v2_fog_top(top_pk),   # V2回退
        "fog_top_msl":     _v2_fog_top(top_pk),   # V2回退
        "summit_diff_m":  _v2_diff(top_pk),   # V2回退
        "temp_max":        round(temp_max, 1),
        "temp_dew":        round(avg_td, 1),
        "pressure":        round(avg_pressure, 0),
    }

    # ---- 天气三日卡片 ----
    td_obj = None
    try:
        td_obj = datetime.strptime(target_date, "%Y-%m-%d")
        day_before = (td_obj - timedelta(days=1))
        day_after = (td_obj + timedelta(days=1))
        day1_str = f"{day_before.month}月{day_before.day}日({DAYS_CN.get(day_before.strftime('%A'), '')})"
        day3_str = f"{day_after.month}月{day_after.day}日({DAYS_CN.get(day_after.strftime('%A'), '')})"
    except Exception:
        day1_str = "前一天"
        day3_str = "后两天"
    day2_str = f"{td_obj.month}月{td_obj.day}日({dow})" if td_obj else f"{dow}(目标日)"

    weather = {
        "day1":        {"date": day1_str,       "temp": "-",   "weather": "前一日"},
        "day2":        {"date": day2_str,        "temp": "-",   "weather": f"{dow}(目标日)"},
        "day3":        {"date": day3_str,        "temp": "-",   "weather": "后一日"},
        "note":        "",
    }

    # fog_forecast 从实际雾型诊断结果构建
    fog_type_counts = {}
    for r in ranked_out:
        ft = r.get("fog_type", "未知")
        fog_type_counts[ft] = fog_type_counts.get(ft, 0) + 1
    sorted_fog = sorted(fog_type_counts.items(), key=lambda x: -x[1])
    fog_forecast = " + ".join(f"{ft}({cnt}峰)" for ft, cnt in sorted_fog[:2])
    fog_forecast = f"{fog_forecast}({top_name}主导)"

    config = {
        "title":        f"🌫️ 云海预测报告 - {target_date}",
        "subtitle":     f"{top_name} · 综合云海概率",
        "update_time":  fetch_time,
        "prob_desc":    (f"{top_name}评分最高,雾顶{_v2_fog_top(top_pk):.0f}m,"
                         f"山顶超出{_v2_diff(top_pk):.0f}m"),

        # 核心概率
        "prob":         top_r.get("score", 50),
        "factor_total": f_total,
        "factors":      factors,

        # 排名
        "ranked":       ranked_out,
        "top3":         top3,

        # 逐时图表
        "hours":         hours_out,
        "probs":         probs_out,
        "temps":         temps_out,
        "sunrise_rows":  sunrise_rows,
        "radar_indicator": radar_indicator,
        "radar_value":   radar_value,
        "radar_name":    "云海评分",

        # 雾型
        "fog_data":      fog_data,
        "fog_forecast":  fog_forecast,

        # 天气 & 风险 & 时间轴
        "weather":       weather,
        "risks":         build_risks(top_s),
        "timeline":      build_timeline(top_r.get("score", 50), target_month),
        "flow":          build_flow(target_month),
        "compare":       build_compare(top3[:3]),
        "sources":       ["Open-Meteo Weather API", "Open-Meteo Air Quality API",
                          "中国天气网(6区)", "Meteoblue Model Blend", "NMC国家气象信息中心"],

        # 通明度
        "transparency":  build_transparency(trans),

        # 出行
        "travel_map":    {r["name"]: (r["travel_addr"], r["travel_km"], r["travel_h"])
                          for r in ranked_out if r.get("travel_addr")},

        # 警告
        "warn":          "",
        "warn_detail":   "",

        # 页脚
        "footer_note":   f"OpenClaw Cloud-Sea Skill · {target_date} · 16峰综合评估",
    }

    # 保存到 workspace 目录
    data_dir = SCRIPT_DIR.parent / "data"
    out_path = out_path or str(data_dir / f"report_config_{target_date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"✅ report_config.json → {out_path}")
    print(f"   目标日: {target_date} {dow}")
    print(f"   TOP峰: {top_name} ({ranked_out[0]['score']}%)")
    print(f"   主导险差: {top_r['diff']:+.0f}m")
    print(f"   12因子总分: {f_total}/10")
    print(f"   逐时数据: {len(hours_out)}点")
    print(f"   全部山峰: {len(ranked_out)}座")
    return config


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="云海预测分析工具(统一版)")
    parser.add_argument("--date",    default=None,
                        help="目标日期 YYYY-MM-DD(默认从 weather_data.json 读取)")
    parser.add_argument("--input",   default=None,
                        help="输入 weather_data.json 路径")
    parser.add_argument("--output",  default=None,
                        help="输出 report_config.json 路径")
    parser.add_argument("--print",   action="store_true",
                        help="打印完整分析报告")
    parser.add_argument("--config",  action="store_true",
                        help="生成 report_config.json")
    parser.add_argument("--all",     action="store_true",
                        help="相当于 --print --config")
    args = parser.parse_args()

    # 修复默认行为：无标志时默认生成 report_config.json
    # 防止用户运行 `python analyzer.py --date XXX` 后 report_config 未更新
    if not (args.print or args.config or args.all):
        print("⚠️  未指定 --print/--config/--all，默认执行 --config")
        args.config = True

    # 确定输入文件
    # BUG-FIX: 原来总是读 weather_data.json,导致 --date 04-25 时读了 04-23 的数据
    # 修复:当指定 --date 时,先找 weather_data_{date}.json(与 weather_fetch.py 输出格式一致)
    # BUG-FIX-2: weather_fetch.py 输出到 workspace 目录,但 analyzer 在 scripts 目录查找
    # 修复:优先在 workspace 目录查找,再到 scripts 目录
    scripts_dir = pathlib.Path(__file__).parent
    data_dir = SCRIPT_DIR.parent / "data"

    if args.input:
        data_path = pathlib.Path(args.input)
    elif args.date:
        # 从日期推导 weather_data 文件名:weather_data_2026-04-25.json
        # 优先 workspace(weather_fetch.py 输出目录)
        data_path = data_dir / f"weather_data_{args.date}.json"
        if not data_path.exists():
            data_path = scripts_dir / f"weather_data_{args.date}.json"
        if not data_path.exists():
            data_path = data_dir / "weather_data.json"  # fallback
        if not data_path.exists():
            data_path = scripts_dir / "weather_data.json"  # final fallback
    else:
        data_path = data_dir / "weather_data.json"
        if not data_path.exists():
            data_path = scripts_dir / "weather_data.json"
    if not data_path.exists():
        print(f"❌ 文件不存在: {data_path}", file=sys.stderr)
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        weather_data = json.load(f)

    # 确定目标日期
    target = args.date or weather_data.get("target_date", "")
    if not target:
        # 尝试从 weather_data.json 推断最近的预测日
        peaks = weather_data.get("peaks", {})
        for name, pk in list(peaks.items())[:1]:
            hourly = pk.get("hourly", [])
            for h in hourly:
                t = h.get("time", "")
                if "T" in t:
                    target = t.split("T")[0]
                    break
            break
    if not target:
        target = "2026-04-25"  # fallback
        print(f"[WARN] 无法确定目标日期,使用默认值: {target}", file=sys.stderr)

    print(f"📡 数据: {data_path.name}  目标日: {target}")

    if args.all or args.print:
        print_analysis(weather_data, target)

    if args.all or args.config:
        build_report_config(weather_data, target, args.output)


if __name__ == "__main__":
    main()
