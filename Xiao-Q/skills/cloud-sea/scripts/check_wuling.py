"""Check Wuling Mountain 06-06 data for validation"""
import json, os

with open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-07.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

peaks = data['peaks']

# Load peaks.json for summit elev
skills_dir = r'C:\Users\86139\.qclaw\skills\cloud-sea'
with open(os.path.join(skills_dir, 'references', 'peaks.json'), 'r', encoding='utf-8') as pf:
    pk_data = json.load(pf)
pk_list = pk_data['peaks']
# Build name->summit map
summit_map = {}
for p in pk_list:
    summit_map[p['name']] = p.get('summit_elev', p.get('elevation', 0))

for k, v in peaks.items():
    if '雾灵' in k:
        name = k
        api_elev = v.get('elevation', 0)
        summit = summit_map.get(name, '?')
        print(f"=== {name} ===")
        print(f"API elevation: {api_elev}m")
        print(f"Summit elevation: {summit}m")
        if isinstance(summit, (int,float)):
            diff = summit - api_elev
            print(f"Elev diff: {diff:.0f}m")
        
        hourly = v.get('hourly', [])
        print("\n06-06 data (00-14):")
        for h in hourly:
            t = str(h.get('time', ''))
            if '2026-06-06' in t:
                hr = int(t[11:13])
                if hr <= 14:
                    ccl = h.get('cloud_cover_low', h.get('cc_low', '?'))
                    rh = h.get('RH_pct', '?')
                    tmp = h.get('T_C', '?')
                    tdp = h.get('Td_C', '?')
                    rp = h.get('precipitation', '?')
                    print(f"  {hr:02d}:00 T={tmp} Td={tdp} RH={rh}% cc_low={ccl} rain={rp}mm")
        
        # Compute 01-06 averages
        print("\n01-06 window:")
        cc_vals, rh_vals = [], []
        for h in hourly:
            t = str(h.get('time', ''))
            if '2026-06-06' in t:
                hr = int(t[11:13])
                if 1 <= hr <= 6:
                    ccl = h.get('cloud_cover_low', h.get('cc_low', None))
                    r = h.get('RH_pct', None)
                    if ccl is not None: cc_vals.append(ccl)
                    if r is not None: rh_vals.append(r)
        
        if cc_vals:
            cc_avg = sum(cc_vals)/len(cc_vals)
            rh_avg = sum(rh_vals)/len(rh_vals) if rh_vals else 0
            print(f"  cc_low avg: {cc_avg:.1f}%")
            print(f"  RH avg: {rh_avg:.1f}%")
            
            if isinstance(summit, (int,float)):
                diff = summit - api_elev
                trigger = (diff > 500) and (cc_avg < 10)
                print(f"  Elev diff: {diff:.0f}m -> correction trigger: {trigger}")
                if trigger and rh_avg >= 85:
                    new_cc = max(cc_avg, rh_avg - 50)
                    capped = min(new_cc, 50)
                    floor = max(capped, 20) if api_elev < 600 else (max(capped, 15) if api_elev < 1000 else capped)
                    print(f"  CORRECTED cc_low: {floor}% (was {cc_avg:.1f}%)")
                elif trigger:
                    print(f"  NO correction: RH={rh_avg:.1f}% < 85% threshold")
        
        # Summary
        s = v.get('summary', {})
        score = s.get('cloud_sea_score', '?')
        fog_type = s.get('fog_type', '?')
        print(f"\nSummary: score={score}% fog_type={fog_type}")
