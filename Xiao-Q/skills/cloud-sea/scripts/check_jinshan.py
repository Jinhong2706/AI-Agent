"""Check Jinshanling 06-06 data in detail"""
import json

with open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-07.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

peaks = data['peaks']
for k, v in peaks.items():
    if '金山' in k:
        name = k
        api_elev = v.get('elevation', 0)
        print(f"=== {name} ===")
        print(f"API elevation: {api_elev}m")
        print(f"Elev diff (summit~1100 - API): {1100 - api_elev:.0f}m")
        
        hourly = v.get('hourly', [])
        # hourly is a list of dicts
        print(f"\nHourly type: {type(hourly)}, count: {len(hourly)}")
        if hourly and isinstance(hourly, list):
            print(f"First entry keys: {list(hourly[0].keys())}")
            print("\n06-06 data (00-12):")
            for h in hourly:
                t = str(h.get('time', ''))
                if '2026-06-06' in t:
                    hr = t[11:13]
                    if int(hr) <= 12:
                        ccl = h.get('cloud_cover_low', h.get('cc_low', '?'))
                        r = h.get('RH_pct', h.get('relative_humidity_2m', '?'))
                        tmp = h.get('T_C', '?')
                        tdp = h.get('Td_C', '?')
                        rp = h.get('precipitation', h.get('rain', '?'))
                        ft = h.get('fog_type', '?')
                        print(f"  {hr}:00 T={tmp} Td={tdp} RH={r}% cc_low={ccl} rain={rp}mm fog={ft}")
            
            # Compute 01-06
            print("\n01-06 window:")
            cc_vals, rh_vals = [], []
            for h in hourly:
                t = str(h.get('time', ''))
                if '2026-06-06' in t:
                    hr = int(t[11:13])
                    if 1 <= hr <= 6:
                        ccl = h.get('cloud_cover_low', h.get('cc_low', None))
                        r = h.get('RH_pct', h.get('relative_humidity_2m', None))
                        if ccl is not None: cc_vals.append(ccl)
                        if r is not None: rh_vals.append(r)
            
            if cc_vals:
                cc_avg = sum(cc_vals)/len(cc_vals)
                rh_avg = sum(rh_vals)/len(rh_vals) if rh_vals else 0
                print(f"  cc_low avg: {cc_avg:.1f}%")
                print(f"  RH avg: {rh_avg:.1f}%")
                diff = 1100 - api_elev
                trigger = (diff > 500) and (cc_avg < 10)
                print(f"  Elev diff: {diff:.0f}m -> correction trigger: {trigger}")
                if trigger and rh_avg >= 85:
                    new_cc = max(cc_avg, rh_avg - 50)
                    capped = min(new_cc, 50)
                    floor = max(capped, 20) if api_elev < 600 else max(capped, 15)
                    print(f"  CORRECTED cc_low: {floor}% (was {cc_avg:.1f}%)")
                elif trigger:
                    print(f"  NO correction: RH={rh_avg:.1f}% < 85% threshold")
