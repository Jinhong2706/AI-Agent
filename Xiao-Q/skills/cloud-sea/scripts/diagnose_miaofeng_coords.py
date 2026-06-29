#!/usr/bin/env python3
"""诊断妙峰山坐标偏差问题 - 对比多个坐标点的气象数据"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

# Windy截图显示：妙峰山森林公园玫瑰谷 06-06 08:00 = 20°C 晴天 RH≈11-26%
# 我们系统预测：RH=97% cc_low=77% 有雾
# 假设：坐标点定位在山谷而非山顶

coords = [
    ('peaks.json当前', 40.03, 116.0),       # 当前使用
    ('偏东北(近山顶)', 40.05, 116.02),      # 可能更接近山顶
    ('偏西南(山谷?)', 39.98, 115.95),       # 可能在山谷
    ('偏东', 40.04, 116.05),
]

for name, lat, lon in coords:
    url = ('https://api.open-meteo.com/v1/forecast'
           f'?latitude={lat}&longitude={lon}'
           '&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,weather_code,cloud_cover_low'
           '&timezone=Asia/Shanghai'
           '&start_date=2026-06-06&end_date=2026-06-06')
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.load(resp)
    h = data['hourly']
    elev = data.get('elevation')
    
    print(f'=== {name} ({lat},{lon}) API海拔={elev}m ===')
    print(f'{"时间":>8s} | {"T":>5s} | {"Td":>5s} | {"RH":>4s} | {"cc_low":>6s} | {"wmo":>3s}')
    for i, t in enumerate(h['time']):
        hour = t[11:16]
        if hour in ['05:00', '06:00', '07:00', '08:00']:
            T = h['temperature_2m'][i]
            Td = h['dew_point_2m'][i]
            RH = h['relative_humidity_2m'][i]
            ccl = h['cloud_cover_low'][i]
            wmo = h['weather_code'][i]
            print(f'{hour:>8s} | {T:>5.1f} | {Td:>5.1f} | {RH:>4.0f}% | {ccl:>6.0f} | {wmo:>3.0f}')
    print()
