#!/usr/bin/env python3
"""Test 16-peak batch with minimal hourly to find timeout limit"""
import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8')

lats = "40.57,40.03,40.60,39.85,40.53,40.03,40.05,40.12,40.40,40.52,40.05,39.97,40.42,40.68,39.03,39.73"
lons = "115.78,115.47,117.44,115.57,116.78,116.0,115.60,115.68,117.20,116.25,115.42,115.37,116.46,117.23,114.58,115.38"

# Test with forecast_days=5 first
for fd in [5, 7]:
    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "temperature_2m,dew_point_2m,relative_humidity_2m,cloud_cover,cloud_cover_low,wind_speed_10m,wind_direction_10m,weather_code,surface_pressure,precipitation_probability,precipitation",
        "models": "ecmwf_ifs025",
        "forecast_days": fd,
        "timezone": "Asia/Shanghai",
    }
    print(f"Testing forecast_days={fd}...")
    t0 = time.time()
    try:
        r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=120)
        elapsed = time.time() - t0
        print(f"  Status: {r.status_code}, elapsed: {elapsed:.1f}s, size: {len(r.content)/1024:.0f}KB")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                ok = sum(1 for d in data if not d.get('error', False) and d.get('hourly', {}).get('time'))
                print(f"  OK: {ok}/16 peaks")
        else:
            print(f"  Error: {r.text[:200]}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Exception after {elapsed:.1f}s: {e}")
