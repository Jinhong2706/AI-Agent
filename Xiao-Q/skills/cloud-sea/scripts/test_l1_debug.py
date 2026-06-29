#!/usr/bin/env python3
"""Debug weather_fetch L1 failure"""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Simulate what weather_fetch does for 2026-06-07
from datetime import datetime

target_date = '2026-06-07'
today_str = datetime.now().strftime('%Y-%m-%d')
days_ahead = (datetime.strptime(target_date, '%Y-%m-%d') - datetime.strptime(today_str, '%Y-%m-%d')).days
needed_days = max(7, days_ahead + 2)
print(f'Today: {today_str}, Target: {target_date}, days_ahead={days_ahead}, needed_days={needed_days}')

# Build 16-peak batch request
peaks = [
    {"name": "海坨山", "latitude": 40.57, "longitude": 115.78, "summit_elev": 2198},
    {"name": "东灵山", "latitude": 40.03, "longitude": 115.47, "summit_elev": 2303},
    {"name": "雾灵山", "latitude": 40.60, "longitude": 117.44, "summit_elev": 2116},
    {"name": "百花山", "latitude": 39.85, "longitude": 115.57, "summit_elev": 1991},
    {"name": "云蒙山", "latitude": 40.53, "longitude": 116.78, "summit_elev": 1414},
    {"name": "妙峰山", "latitude": 40.03, "longitude": 116.0, "summit_elev": 1291},
    {"name": "黄草梁", "latitude": 40.05, "longitude": 115.60, "summit_elev": 1737},
    {"name": "长峪城", "latitude": 40.12, "longitude": 115.68, "summit_elev": 1400},
    {"name": "东指壶", "latitude": 40.40, "longitude": 117.20, "summit_elev": 1242},
    {"name": "燕羽山", "latitude": 40.52, "longitude": 116.25, "summit_elev": 1180},
    {"name": "北灵山", "latitude": 40.05, "longitude": 115.42, "summit_elev": 1915},
    {"name": "西南灵山", "latitude": 39.97, "longitude": 115.37, "summit_elev": 1847},
    {"name": "箭扣长城", "latitude": 40.42, "longitude": 116.46, "summit_elev": 1100},
    {"name": "金山岭长城", "latitude": 40.68, "longitude": 117.23, "summit_elev": 1080},
    {"name": "白石山", "latitude": 39.03, "longitude": 114.58, "summit_elev": 2099},
    {"name": "白草畔", "latitude": 39.73, "longitude": 115.38, "summit_elev": 1983},
]

lats = ",".join(str(p["latitude"]) for p in peaks)
lons = ",".join(str(p["longitude"]) for p in peaks)

params = {
    "latitude": lats,
    "longitude": lons,
    "hourly": "temperature_2m,dew_point_2m,relative_humidity_2m,temperature_2m_max,temperature_2m_min,precipitation_probability,precipitation,surface_pressure,cloud_cover,cloud_cover_low,wind_speed_10m,wind_direction_10m,weather_code",
    "models": "ecmwf_ifs025",
    "forecast_days": needed_days,
    "timezone": "Asia/Shanghai",
}

print(f'\nRequesting {needed_days} forecast_days for 16 peaks...')
try:
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=120)
    print(f'Status: {r.status_code}')
    if r.status_code != 200:
        print(f'Error: {r.text[:500]}')
    else:
        data = r.json()
        if isinstance(data, list):
            print(f'OK: {len(data)} responses')
            for i, d in enumerate(data):
                err = d.get('error', False)
                rsn = d.get('reason', '')
                print(f'  [{i}] {peaks[i]["name"]}: elev={d.get("elevation")}, hourly={len(d.get("hourly",{}).get("time",[]))}, error={err}, reason={rsn[:100] if rsn else ""}')
        else:
            print(f'Single response: error={data.get("error")}, reason={data.get("reason","")[:200]}')
except Exception as e:
    print(f'Exception: {e}')
