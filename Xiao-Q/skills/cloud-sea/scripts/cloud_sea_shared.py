# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
cloud_sea_shared.py - 云海预测共享常量与辅助函数
唯一真相源(Single Source of Truth)。
所有脚本均须导入此模块,禁止重复定义同名常量。

山峰数据统一从 references/peaks.json 加载,禁止在此文件硬编码峰坐标/海拔。
"""
import pathlib, json

# ═══════════════════════════════════════════════════════════════════
# 懒加载 peaks.json(单向同步:peaks.json 是唯一数据源)
# ═══════════════════════════════════════════════════════════════════
_SKILL_ROOT = pathlib.Path(__file__).parent.parent  # cloud-sea/
_PEAKS_JSON = _SKILL_ROOT / "references" / "peaks.json"

def _load_peaks():
    with open(_PEAKS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    # PEAK_INFO: name -> (lat, lon, summit_elev_m)
    #   ⚠️ 真实station_elev来自API的elevation字段，不在此处存储
    #   ⚠️ 雾顶公式:fog_top = station_elev_from_API + LCL + 100(不用此处的占位值)
    # AUDIT-002 FIX: 从四元组(lat,lon,placeholder,summit)简化为三元组(lat,lon,summit)
    #   旧版第3项=第4项=summit_elev，占位值无意义且增加混淆风险
    PEAK_INFO = {p['name']: (p['latitude'], p['longitude'], p['summit_elev'])
                 for p in data['peaks']}
    PEAK_ELEVATIONS = {p['name']: p['summit_elev'] for p in data['peaks']}
    return PEAK_INFO, PEAK_ELEVATIONS

PEAK_INFO, PEAK_ELEVATIONS = _load_peaks()

# ═══════════════════════════════════════════════════════════════════
# 山顶海拔别名(兼容旧代码)
# ═══════════════════════════════════════════════════════════════════
# PEAK_ELEVATIONS 已由懒加载填充
# PEAK_INFO 已由懒加载填充,格式: name -> (lat, lon, summit_elev)
# 雾顶公式: fog_top = station_elev_from_API + LCL + 100（从 API elevation 字段读取）

# ═══════════════════════════════════════════════════════════════════
# AUDIT-008/011 FIX: 共享常量（从 weather_fetch.py / sunrise_analysis.py 合并）
# ═══════════════════════════════════════════════════════════════════

# 区域天气网编码（供 weather_fetch.py 中国天气网第二轮使用）
DISTRICT_CODES = {
    "延庆": "101010800", "门头沟": "101011400", "密云": "101011300",
    "怀柔": "101010500", "昌平": "101010700", "平谷": "101011500",
    "涞源": "101090201", "兴隆": "101090401", "滦平": "101090301",
    "野三坡": "101090201",  # 白草畔使用涞源编码
}

# 峰 → 区域映射（weather_fetch.py / sunrise_analysis.py 共用）
PEAK_DISTRICT = {
    "东指壶": "平谷", "东灵山": "门头沟", "云蒙山": "怀柔",
    "白草畔": "野三坡", "北灵山": "门头沟", "妙峰山": "门头沟",
    "海坨山": "延庆", "燕羽山": "延庆", "白石山": "涞源",
    "百花山": "门头沟", "箭扣长城": "延庆", "西南灵山": "门头沟",
    "金山岭长城": "滦平", "长峪城": "昌平", "雾灵山": "密云",
    "黄草梁": "门头沟",
}

# 峰 → 区域简称（sunrise_analysis.py 使用）
PEAK_REGION = {
    "海坨山":    "延庆", "东灵山":    "门头沟", "雾灵山":    "密云",
    "百花山":    "门头沟", "云蒙山":    "怀柔", "妙峰山":    "门头沟",
    "黄草梁":    "门头沟", "长峪城":    "昌平", "东指壶":    "平谷",
    "燕羽山":    "延庆", "北灵山":    "门头沟", "西南灵山":  "门头沟",
    "箭扣长城":  "延庆", "金山岭长城": "滦平", "白石山":    "涞源",
    "白草畔":    "野三坡",
}

# 城区监测点坐标（AUDIT-010 FIX: 统一到单一常量，lon=116.40）
URBAN_MONITOR = {
    "name": "beijing_urban",
    "lat": 39.92,
    "lon": 116.40,
    "elev": 45,
}

# ═══════════════════════════════════════════════════════════════════
# 临近水体的山峰(用于蒸发雾诊断)
# 长峪城: 临近官厅水库; 东指壶: 临近金海湖
# ═══════════════════════════════════════════════════════════════════
NEAR_WATER_PEAKS = {
    "长峪城", "东指壶",
}

# ═══════════════════════════════════════════════════════════════════
# 日出时间表(统一使用,analyzer 和 weather_fetch 共用)
# ═══════════════════════════════════════════════════════════════════
# AUDIT-013 NOTE: _SUNRISE_TABLE 为手工估算值，精度约±15分钟
# 7月值5.0实际约4:50，4月值5.8实际约5:40，5月值5.2实际约5:10
_SUNRISE_TABLE = {
    1: 7.5, 2: 7.0, 3: 6.3, 4: 5.5, 5: 5.2, 6: 4.8,
    7: 5.0, 8: 5.5, 9: 6.0, 10: 6.3, 11: 6.8, 12: 7.4,
}

# ═══════════════════════════════════════════════════════════════════
# 4. 雾型元数据(2026-04-23 合并,合并了 report_gen.py 的 FOG_TYPES)
# ═══════════════════════════════════════════════════════════════════
# 雾型云海效果分 + 展示元数据(单一定义,report_gen 和 _build_html_v3 共享)
FOG_TYPES = {
    "上坡雾": {
        "cloud_sea_score": 8.3,
        "icon": "&#127794;", "stars": "&#9733;&#9733;&#9733;&#9733;&#9733;",
        "badge_class": "badge-upslope", "bonus": "+5(最佳)",
        "duration": "05:00 - 09:00,持续较长",
        "desc": "暖湿气流沿山坡被迫抬升形成,北京春季最壮观云海",
        "poetry": "山顶穿云,云如瀑布沿山坡倾泻,金色阳光从云缝洒下",
        "peak_visual": "★★★★★",
    },
    "平流雾": {
        "cloud_sea_score": 7.0,
        "icon": "&#127787;", "stars": "&#9733;&#9733;&#9733;&#9733;",
        "badge_class": "badge-advection", "bonus": "+3(范围大)",
        "duration": "持续到午后(12-24小时)",
        "desc": "暖湿气流水平移动经过较冷下垫面形成,覆盖范围最广",
        "poetry": "云海如银色绸缎铺满山谷,山峰若隐若现,仙气缭绕",
        "peak_visual": "★★★★",
    },
    "辐射雾": {
        "cloud_sea_score": 6.3,
        "icon": "&#127774;", "stars": "&#9733;&#9733;&#9733;",
        "badge_class": "badge-radiation", "bonus": "+0",
        "duration": "04:30 - 07:00,日出后1-2小时消散",
        "desc": "晴夜地面辐射冷却形成,多见于山谷低洼处",
        "poetry": "山谷雾海翻涌,远处山峰如岛屿浮于云上",
        "peak_visual": "★★★",
    },
    "谷雾": {
        "cloud_sea_score": 6.8,
        "icon": "&#127793;", "stars": "&#9733;&#9733;&#9733;",
        "badge_class": "badge-valley", "bonus": "+0",
        "duration": "04:00 - 08:00,谷口开启后消散",
        "desc": "辐射雾被困于山谷地形,浓雾填满沟壑",
        "poetry": "浓雾填满沟壑,山尖如浮岛,层次分明",
        "peak_visual": "★★★★",
    },
    "锋面雾": {
        "cloud_sea_score": 3.8,
        "icon": "&#9929;", "stars": "&#9733;&#9733;",
        "badge_class": "badge-frontal", "bonus": "-2(光线暗)",
        "duration": "全天持续,视锋面系统而定",
        "desc": "锋面过境时暖空气爬升到冷空气之上形成",
        "poetry": "云层灰厚,天地混沌,远山隐没于茫茫雾中",
        "peak_visual": "★★",
    },
    "混合雾": {
        "cloud_sea_score": 5.0,
        "icon": "&#127787;", "stars": "&#9733;&#9733;",
        "badge_class": "badge-mixed", "bonus": "+0",
        "duration": "04:30 - 08:00",
        "desc": "多种雾型叠加,视觉效果取决于主导类型",
        "poetry": "云雾交融,山峦若隐若现,层次丰富",
        "peak_visual": "★★★",
    },
    "层云雾": {
        "cloud_sea_score": 3.0,
        "icon": "&#9729;&#65039;", "stars": "&#9733;",
        "badge_class": "badge-stratus", "bonus": "-2",
        "duration": "全天(低层云覆盖,不形成典型雾)",
        "desc": "干冷气流或稳定大气下低层层状云覆盖,非辐射雾",
        "poetry": "灰蒙蒙的低云笼罩,山峦朦胧不清",
        "peak_visual": "★★",
    },
    "蒸发雾": {
        "cloud_sea_score": 4.0,
        "icon": "&#128167;", "stars": "&#9733;&#9733;",
        "badge_class": "badge-evaporation", "bonus": "0",
        "duration": "06:00-08:00(清晨水面蒸发最强时)",
        "desc": "冷空气流经暖水面蒸发形成,常见于水库/湖泊附近",
        "poetry": "薄雾缭绕水面,如丝如纱,清晨最浓午后消散",
        "peak_visual": "★★★",
    },
}

# 雾型形成机制(简称映射)
_MECH_BASE = {
    "辐射雾": "晴夜地面辐射冷却,近地面水汽凝结",
    "平流雾": "暖湿气流经过冷地面,下层冷却凝结",
    "上坡雾": "湿空气沿山坡抬升,膨胀冷却达露点",
    "谷雾":   "辐射雾被困于山谷地形,浓雾填满沟壑",
    "锋面雾": "冷暖锋面附近降水使低层空气饱和",
    "混合雾": "多种雾型叠加,取决于主导类型",
    "层云雾": "稳定大气条件下低层层状云覆盖",
    "蒸发雾": "水面蒸发使空气超饱和",
}
# 含全称别名(向后兼容 _build_html_v3.py 等模板代码传入 "辐射雾型" 等)
FOG_MECHANISM_MAP = {**_MECH_BASE, **{k + "型": v for k, v in _MECH_BASE.items()}}

# 雾型最佳出行时间
_BEST_BASE = {
    "辐射雾": "04:30-07:00",
    "平流雾": "05:00-09:00",
    "上坡雾": "05:00-10:00",
    "谷雾":   "04:00-08:00",
    "锋面雾": "04:30-08:00",
    "混合雾": "04:30-08:00",
    "层云雾": "05:00-08:00",
    "蒸发雾": "06:00-08:00",
}
FOG_BEST_TIME_MAP = {**_BEST_BASE, **{k + "型": v for k, v in _BEST_BASE.items()}}

# 雾型图标
FOG_ICONS = {
    "辐射雾": "🌙", "平流雾": "🌊", "上坡雾": "⛰️",
    "谷雾": "🌫️", "蒸发雾": "💧", "锋面雾": "⛈️",
    "混合雾": "🌫️", "层云雾": "☁️",
    # 全称别名(向后兼容)
    "辐射雾型": "🌙", "平流雾型": "🌊", "上坡雾型": "⛰️",
    "谷雾型": "🌫️", "蒸发雾型": "💧", "锋面雾型": "⛈️",
    "层云雾型": "☁️", "混合雾型": "🌫️",
}

# FOG_STARS 已删除 (2026-04-29 self-improving) - 定义后从未调用,直接用 FOG_TYPES[name]['stars']

# L-1 FIX: 雾型组合加成(从5对扩展到12对,覆盖全部8种雾型组合)
FOG_COMBO_BONUS = {
    ("上坡雾",     "辐射雾"):   "+8(双型壮丽)",
    ("上坡雾",     "平流雾"):   "+10(最佳组合)",
    ("辐射雾",     "谷雾"):     "+6(山谷深邃)",
    ("上坡雾",     "谷雾"):     "+7(层次丰富)",
    ("平流雾",     "锋面雾"):   "-4(光线暗淡)",
    ("层云雾",     "层云雾"):   "+0(单型)",
    ("层云雾",     "上坡雾"):   "+3(过渡型)",
    ("层云雾",     "辐射雾"):   "+2(干燥型)",
    ("蒸发雾",     "辐射雾"):   "+4(水面特色)",
    ("蒸发雾",     "平流雾"):   "+2(水面平流)",
    ("谷雾",       "平流雾"):   "+5(山谷平流)",
    ("谷雾",       "谷雾"):     "+3(谷底浓雾)",
    ("混合雾",     "辐射雾"):   "+2(混合辐射)",
    ("混合雾",     "平流雾"):   "+1(混合平流)",
    ("混合雾",     "混合雾"):   "+0(中性)",
}

# ═══════════════════════════════════════════════════════════════════
# 4. 装备清单默认值
# ═══════════════════════════════════════════════════════════════════
DEFAULT_EQUIP_ITEMS = [
    ("&#128367;", "头灯/手电", "凌晨登山必备"),
    ("&#129533;", "保暖衣物", "山顶气温低"),
    ("&#129504;", "登山杖", "山路崎岖"),
    ("&#129380;", "热水/保温杯", "暖身补充体力"),
    ("&#128247;", "相机/手机", "记录云海日出"),
    ("&#128267;", "充电宝", "低温耗电快"),
    ("&#129532;", "防晒霜", "日出紫外线强"),
    ("&#127973;", "雨具/冲锋衣", "山顶天气多变"),
]

# ═══════════════════════════════════════════════════════════════════
# 12因子权重(唯一真相源,analyzer.py 和 report_gen.py 共享)
# ═══════════════════════════════════════════════════════════════════
# P0 FIX (2026-05-21): 权重总和修正为精确1.00
# 修复前总和=1.05(5%偏高), 所有概率结果虚高
# 方案: 因子1/2/3各从0.15→0.14(物理重要性仍排前三), 因子6从0.15→0.13(仍为核心因子)
# 验证: 0.14×3 + 0.13 + 0.10 + 0.08×2 + 0.05×2 + 0.03×3 = 1.00
FACTOR_WEIGHTS = [
    ("辐射冷却",     0.14),  # 因子1: 晴夜 + 大温差 = 强冷却（FIX: 0.15→0.14）
    ("稳定层结",     0.14),  # 因子2: 逆温层 + 气压稳定（FIX: 0.15→0.14）
    ("风力条件",     0.14),  # 因子3: 微风2-8km/h最佳（FIX: 0.15→0.14）
    ("水汽供给",     0.10),  # 因子4: 湿度/露点
    ("前置降水",     0.08),  # 因子5: 雨后初晴加分
    ("云底 vs 海拔", 0.13),  # 因子6: 山顶在云中/云上/云下 — 核心因子（FIX: 0.15→0.13）
    ("日出时机",     0.08),  # 因子7: 日出在湿度峰值窗口
    ("季节调整",     0.05),  # 因子8: 春秋云海高发
    ("地形优势",     0.05),  # 因子9: 迎风坡/背风波
    ("夜间晴空",     0.03),  # 因子10: 晴夜低云量=辐射冷却窗口
    ("能见度",       0.03),  # 因子11: 能见度/AQI/通透度
    ("不确定性",     0.03),  # 因子12: 多模型一致
]
# P3调整说明 (2026-05-20):
# - 因子6"云底 vs 海拔"提升到15%：这是最核心因子，直接决定山顶是否可见云海
# - 因子7"日出时机"提升到8%：日出是最佳观测窗口
# - 因子5"前置降水"降为8%：雨后初晴虽有利，但不如险差关键
# - 因子12"不确定性"提升到3%：ENS集合标准差应作为置信度指标

# 纯权重列表(report_gen.py 需要)
FACTOR_WEIGHT_VALUES = [w for _, w in FACTOR_WEIGHTS]







def estimate_transparency(score, rh=50):
    """
    根据评分(0-10)和RH估算通透度等级。
    返回dict: {"score": {"level": ..., "value": ...}, "detail": {...}}
    """
    if not isinstance(score, (int, float)) or score is None:
        return {"score": {"level": "未知", "value": 0}, "detail": {}}
    if score >= 9:
        level = "极佳"
    elif score >= 8:
        level = "优秀"
    elif score >= 7:
        level = "良好"
    elif score >= 6:
        level = "中等"
    elif score >= 5:
        level = "一般"
    else:
        level = "较差"
    return {
        "score": {"level": level, "value": score},
        "detail": {"rh": rh, "level": level},
    }



# fog_stars() 已删除 (2026-04-27 self-improving) - 定义后从未调用

def calc_fog_type(wind_dir, wind_kmh, rh, td_spread,
                  near_water=False, surface_temp=None, air_temp=None,
                  peak_name=None):
    """诊断雾型(八轮审计修复版 2026-05-21)

    P3 FIX: 上坡雾判定从硬编码北风扩展到多风向
    物理原理:上坡雾=湿空气沿山坡抬升冷却,关键是风有向上分量
    北京山区太行山(NE-SW走向)+燕山(EW走向),东风/南风/北风均可触发

    返回: (type_key, zh_name, description)
    """
    # wind_dir=None 诊断(第七轮修复)
    if wind_dir is None:
        wind_dir = -1  # 标记为未知

    is_north = _is_north_wind(wind_dir)
    is_south = _is_south_wind(wind_dir)
    is_east = _is_east_wind(wind_dir)

    # Rule 1: 辐射雾 — 静风+高湿+大T-Td展宽
    if wind_kmh <= 3 and rh >= 90 and td_spread >= 5:
        return ("radiation", "辐射雾", "静风辐射冷却，地面雾层")

    # Rule 2: 上坡雾 — 风吹向山坡(优先于平流雾判定)
    # P1 FIX (2026-05-21): 上坡雾移到平流雾之前
    # 物理原理: 北风/东风+低风速(<=5)+高湿(>=80%) → 地形抬升冷却
    # 旧版上坡雾在平流雾之后,北风+RH>=92时被平流雾短路,永远不触发
    # 太行山NE-SW走向: 东风/东南风 → 面向山坡
    # 燕山EW走向: 南风/北风 → 面向山坡
    if (is_north or is_east) and wind_kmh <= 5 and rh >= 80:
        return ("upslope", "上坡雾", "地形抬升冷却")

    # Rule 3: 平流雾 — 南风(暖湿气流)+高湿
    # 第七轮修复: 北风+高湿也判平流雾(北方冷平流)
    # P1 FIX: 排除已匹配上坡雾的风向(is_north/is_east + wind<=5)
    if rh >= 85 and (is_south or (is_north and rh >= 92)) and wind_kmh > 5:
        return ("advection", "平流雾", "暖湿/冷湿平流输送")

    # Rule 4: 蒸发雾 — 冷空气过暖水面(第十轮修复)
    if (surface_temp is not None and air_temp is not None
            and surface_temp > air_temp + 5 and rh >= 80):
        return ("evaporation", "蒸发雾", "暖水面蒸发遇冷凝")
    # 近水面简化判断
    if near_water and rh >= 85 and td_spread <= 3:
        return ("evaporation", "蒸发雾", "水面蒸发冷却")

    # Rule 5: 锋面雾 — 降水后高湿(第五轮修复: 缩窄条件)
    if rh >= 95 and td_spread <= 2 and wind_kmh > 5:
        return ("frontal", "锋面雾", "锋面降水伴雾")

    # Rule 6: 兜底(第六轮修复: 混合雾替代层云雾)
    # 第十一轮修复: T-Td >= 3.5 → 干燥无雾
    # 第十二轮修复: wind <= 2 时阈值放宽(近静风高湿=辐射雾窗口)
    # 长峪城 05-30: wind=0.7km/h RH=83% T-Td=2.8°C → 辐射雾潜力
    if rh >= 75:
        if td_spread < 3.5:
            return ("mixed", "混合雾", "多机制混合")
        if wind_kmh <= 2 and td_spread < 5.0 and rh >= 80:
            return ("mixed", "混合雾", "近静风高湿混合")
        return ("none", "无雾", "空气干燥")

    # 干燥无雾
    return ("none", "无雾", "空气干燥")


def _is_north_wind(wind_dir):
    """判断是否为北风(N/NE/NW)"""
    return (0 <= wind_dir < 90) or (270 < wind_dir <= 360)

def _is_south_wind(wind_dir):
    """判断是否为南风(SE/S/SW),不含正东(90°)和正西(270°)"""
    return 90 < wind_dir < 270

def _is_east_wind(wind_dir):
    """判断是否为东风(NE/SE),含正东(90°)
    P3 FIX (2026-05-21): 新增,用于上坡雾判定
    太行山NE-SW走向,东风/东南风面向山坡可触发上坡雾
    """
    return 45 <= wind_dir <= 135


# ═══════════════════════════════════════════════════════════════════
# 评分阈值常量(2026-05-22 重构: 集中管理,消除魔法数字)
# ═══════════════════════════════════════════════════════════════════
class SunriseThresholds:
    """日出评级阈值 - V3 (LCL为主判据)"""
    # 优先级1: 干燥气团否决
    DRY_RH_STRICT = 65
    DRY_RH_LOOSE = 55
    DRY_LCL_THRESHOLD = 400

    # 优先级2: 浅雾 (LCL<100m)
    SHALLOW_LCL = 100
    SHALLOW_RH = 85
    SHALLOW_VIS_GOOD = 15
    SHALLOW_VIS_PERFECT = 20

    # 优先级3: 中层雾 (LCL 100-300m)
    MEDIUM_LCL = 300
    MEDIUM_RH = 90
    MEDIUM_VIS = 15

    # 优先级4: 厚雾 (LCL 300-500m)
    THICK_LCL = 500

    # 雾评分阈值 (0-100量纲)
    FOG_SCORE_HIGH = 60
    FOG_SCORE_MED = 45
    FOG_SCORE_LOW = 30
    FOG_SCORE_MIN = 20


class FactorThresholds:
    """12因子计算阈值"""
    F6_OFFSET = 100          # 因子6: (diff+100)/100
    WIND_ELEV_DIFF = 500     # 高海拔风速修正触发条件
    WIND_ELEV_FACTOR = 1.5   # 高海拔风速乘数
    SEASON_SCORES = {
        1: 3, 2: 4, 3: 6, 4: 7, 5: 7, 6: 5,
        7: 4, 8: 4, 9: 7, 10: 9, 11: 9, 12: 5
    }


class VetoThresholds:
    """否决逻辑阈值"""
    CLEAR_SKY_WC = 2.0       # 晴空否决: 云量≤2.0
    RH_EXCEPTION = 70        # RH≥70%豁免晴空否决

