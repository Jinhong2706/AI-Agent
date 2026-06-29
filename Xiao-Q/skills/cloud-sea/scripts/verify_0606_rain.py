#!/usr/bin/env python3
"""核实06-06逐时天气码和降水数据，对比Windy/莉景"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

wd = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-06.json', 'r', encoding='utf-8'))
peaks = wd.get('peaks', {})

# WMO天气码解读
WMO_CODES = {
    0: '晴', 1: '大部晴', 2: '多云', 3: '阴',
    45: '雾', 48: '沉积雾', 51: '小毛毛雨', 53: '中毛毛雨', 55: '大毛毛雨',
    56: '冻毛毛雨', 57: '密集冻毛毛雨',
    61: '小雨', 63: '中雨', 65: '大雨',
    66: '冻雨(小)', 67: '冻雨(大)',
    71: '小雪', 73: '中雪', 75: '大雪',
    80: '小阵雨', 81: '中阵雨', 82: '大阵雨',
    85: '小阵雪', 86: '大阵雪',
    95: '雷暴', 96: '雷暴+小冰雹', 99: '雷暴+大冰雹',
}

target = '2026-06-06'
focus_peaks = ['长峪城', '妙峰山', '海坨山', '白草畔', '白石山', '雾灵山', '百花山']

print("=" * 80)
print(f"06-06 逐时天气码 + 降水核实")
print("=" * 80)

for name in focus_peaks:
    pk = peaks.get(name, {})
    hourly = pk.get('hourly', [])
    
    print(f"\n{'='*60}")
    print(f"【{name}】 summit_elev={pk.get('summit_elev', pk.get('elevation', '?'))}m, API elev={pk.get('elevation', '?')}m")
    print(f"{'时间':<22} {'T':>5} {'Td':>5} {'RH':>5} {'WMO':>5} {'天气':>8} {'降水mm':>7} {'cc':>4} {'cc_low':>6} {'ws':>6}")
    print("-" * 90)
    
    for h in hourly:
        t = h.get('time', '')
        if not t.startswith(target):
            continue
        hour = int(t[11:13])
        if hour < 0 or hour > 23:
            continue
            
        T = h.get('T_C', h.get('temperature_2m', '?'))
        Td = h.get('Td_C', h.get('dew_point_2m', '?'))
        RH = h.get('RH_pct', h.get('relative_humidity_2m', '?'))
        wmo = h.get('weather_code', h.get('wmo_code', '?'))
        rain = h.get('precipitation', h.get('rain_mm', 0))
        cc = h.get('cloud_cover', h.get('total_cloud_cover', '?'))
        cc_low = h.get('cloud_cover_low', h.get('cc_low', '?'))
        ws = h.get('wind_kmh', h.get('wind_speed_10m', '?'))
        
        wmo_str = str(wmo) if wmo is not None else '?'
        weather_str = WMO_CODES.get(wmo, f'未知({wmo})') if wmo is not None else '?'
        
        print(f"{t:<22} {T:>5} {Td:>5} {RH:>5} {wmo_str:>5} {weather_str:>8} {rain:>7} {cc:>4} {cc_low:>6} {ws:>6}")
