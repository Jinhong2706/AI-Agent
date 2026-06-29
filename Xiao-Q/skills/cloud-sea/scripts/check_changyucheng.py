#!/usr/bin/env python3
"""检查长峪城05-30预测数据，核实是否与Windy矛盾"""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"

def main():
    target_date = "2026-05-30"
    peak_name = "长峪城"
    
    # 读取天气数据
    weather_file = DATA_DIR / f"weather_data_{target_date}.json"
    if not weather_file.exists():
        print(f"❌ 文件不存在: {weather_file}")
        return 1
    
    with open(weather_file, 'r', encoding='utf-8') as f:
        weather_data = json.load(f)
    
    if peak_name not in weather_data.get("peaks", {}):
        print(f"❌ {peak_name} 不在天气数据中")
        return 1
    
    peak_data = weather_data["peaks"][peak_name]
    hourly = peak_data.get("hourly", [])
    
    print(f"=== {peak_name} {target_date} 核实 ===\n")
    print(f"坐标: ({peak_data.get('latitude')}, {peak_data.get('longitude')})")
    print(f"站海拔: {peak_data.get('elevation')}m")
    print(f"峰海拔: 1400m")
    print(f"小时数: {len(hourly)}\n")
    
    # 打印关键时段数据
    print("时段        T(°C)  Td(°C)  RH(%)  风速(km/h)  LCL(m)  雾顶MSL(m)  险差(m)  CC(%)  降水  status")
    print("-" * 120)
    
    morning_hours = ["2026-05-30T03:00", "2026-05-30T04:00", "2026-05-30T05:00",
                     "2026-05-30T06:00", "2026-05-30T07:00", "2026-05-30T08:00",
                     "2026-05-30T09:00"]
    
    for hour_data in hourly:
        time_str = hour_data.get("time", "")
        if time_str not in morning_hours:
            continue
        
        t = hour_data.get("T_C", 0)
        td = hour_data.get("Td_C", 0)
        rh = hour_data.get("RH_pct", 0)
        wind = hour_data.get("wind_kmh", 0)
        lcl = hour_data.get("lcl_ag_m", 0)
        fog_top = hour_data.get("fog_top_msl", 0)
        diff = hour_data.get("summit_diff_m", 0)
        above = hour_data.get("above_fog", False)
        cc = hour_data.get("cloud_cover", 0)
        rain = hour_data.get("precipitation", 0)
        
        status = "above" if above else "below"
        print(f"{time_str}  {t:5.1f}   {td:5.1f}   {rh:5d}   {wind:10.1f}  {lcl:7.1f}  {fog_top:10.1f}  {diff:8.1f}  {cc:5d}  {rain:6.1f}  {status}")
    
    print("\n=== 关键指标检查 ===")
    
    # 检查03-06点平均条件
    morning_data = [h for h in hourly if h.get("time", "") in morning_hours[:4]]
    if morning_data:
        avg_rh = sum(h.get("RH_pct", 0) for h in morning_data) / len(morning_data)
        avg_wind = sum(h.get("wind_kmh", 0) for h in morning_data) / len(morning_data)
        avg_cc = sum(h.get("cloud_cover", 0) for h in morning_data) / len(morning_data)
        min_diff = min(h.get("summit_diff_m", 0) for h in morning_data)
        
        print(f"03-06点平均RH: {avg_rh:.1f}%")
        print(f"03-06点平均风速: {avg_wind:.1f} km/h")
        print(f"03-06点平均云量: {avg_cc:.1f}%")
        print(f"03-06点最小险差: {min_diff:.1f}m")
        
        print("\n=== 矛盾分析 ===")
        if avg_cc > 50:
            print(f"[WARN] 03-06点平均云量{avg_cc:.1f}% > 50%，阴天不利于云海可见")
        else:
            print(f"[OK] 03-06点平均云量{avg_cc:.1f}% < 50%，有利于云海可见")
        
        if avg_rh < 70:
            print(f"[WARN] 03-06点平均RH{avg_rh:.1f}% < 70%，湿度不足")
        else:
            print(f"[OK] 03-06点平均RH{avg_rh:.1f}% >= 70%，湿度充足")
        
        if min_diff < 200:
            print(f"[WARN] 最小险差{min_diff:.1f}m < 200m，山顶可能进入雾中")
        else:
            print(f"[OK] 最小险差{min_diff:.1f}m >= 200m，山顶安全高于雾顶")
    
    # 读取report config对比
    config_file = DATA_DIR / f"report_config_{target_date}.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print("\n=== report_config.json 对比 ===")
        top_peak = config_data.get("ranked", [{}])[0]
        print(f"报告中的cc: {config_data.get('fog_data', {}).get('cc')}%")
        print(f"报告中的RH: {config_data.get('fog_data', {}).get('rh')}%")
        print(f"报告中的wind: {config_data.get('fog_data', {}).get('wind')} km/h")
        print(f"长峪城diff: {top_peak.get('diff')}m")
        print(f"长峪城prob: {top_peak.get('score')}%")
        
        # 检查cc字段来源
        cc_value = config_data.get('fog_data', {}).get('cc')
        print(f"\n[BUG] 报告顶层cc={cc_value}%，但逐时数据显示03-06点cc=0-2%")
        print(f"      这可能意味着cc字段读取了错误的时间点或计算方式有问题")
        print(f"      建议：检查analyzer.py中build_report_config()如何设置cc字段")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
