#!/usr/bin/env python3
"""核实妙峰山06-07数据"""
import json
import sys

# 读取数据
with open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-07.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

pk = d['peaks']['妙峰山']
hourly = pk.get('hourly', [])

print('=== 妙峰山 06-07 凌晨01-06时数据 (云海观测窗口) ===')
api_elev = pk.get('elevation', '?')
print(f'API格点海拔: {api_elev}m, 山顶: 1291m, 差值: {1291-float(api_elev) if isinstance(api_elev, (int,float)) else "?"}m')
print()

# 凌晨01-06时
cc_list, rh_list, t_list, td_list = [], [], [], []
print(f'{"时间":<8} {"T(°C)":<10} {"Td(°C)":<10} {"RH(%)":<10} {"cc_low(%)":<12} {"降水(mm)":<10}')
print('-' * 70)
for h in hourly:
    t = h.get('time', '')
    if '2026-06-07' in str(t):
        hr = int(str(t)[11:13])
        if 1 <= hr <= 6:
            cc = h.get('cloud_cover_low', h.get('cc_low', None))
            rh = h.get('RH_pct', None)
            tmp = h.get('T_C', None)
            tdew = h.get('dew_point_2m', None)
            precip = h.get('precipitation', 0)
            
            if cc is not None: cc_list.append(cc)
            if rh is not None: rh_list.append(rh)
            if tmp is not None: t_list.append(tmp)
            if tdew is not None: td_list.append(tdew)
            
            print(f'{hr:02d}:00    {str(tmp):<10} {str(tdew):<10} {str(rh):<10} {str(cc):<12} {precip}')

print()
if cc_list and rh_list:
    print(f'01-06时平均: cc_low={sum(cc_list)/len(cc_list):.1f}%, RH={sum(rh_list)/len(rh_list):.1f}%')
    print(f'01-06时最高RH: {max(rh_list):.1f}%')
if t_list and td_list and len(t_list)==len(td_list):
    tds = [t_list[i]-td_list[i] for i in range(min(len(t_list),len(td_list)))]
    print(f'01-06时T-Td范围: {min(tds):.1f}~{max(tds):.1f}°C, 最小(最湿): {min(tds):.1f}°C')

# 查看summary
s = pk.get('summary', {})
print()
print('=== Summary (weather_fetch原始) ===')
print(f'cloud_sea_score: {s.get("cloud_sea_score", "?")}%')
print(f'fog_type: {s.get("fog_type", "?")}')

# 读取report_config
try:
    with open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\report_config_2026-06-07.json', 'r', encoding='utf-8') as f:
        rc = json.load(f)
    peaks = rc.get('peaks', {})
    mf = peaks.get('妙峰山', {})
    print()
    print('=== Report Config (analyzer修正后) ===')
    print(f'score: {mf.get("score", "?")}%')
    print(f'fog_type: {mf.get("fog_type", "?")}')
    print(f'cc_low_original: {mf.get("cc_low_original", "?")}')
    print(f'cc_low_adjusted: {mf.get("cc_low_adjusted", "?")}')
    print(f'summit_diff_m: {mf.get("summit_diff_m", "?")}')
except Exception as e:
    print(f'读取report_config失败: {e}')
