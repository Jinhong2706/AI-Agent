# -*- coding: utf-8 -*-
"""
LCL V2.0 — Three-Layer Architecture, Phase 1+2 (Layer 1 + Layer 2 + Layer 3)

Layer 1: ecmwf_ifs025  — Baseline LCL (Open-Meteo free)
Layer 2: cma_grapes_global — Height Correction via Magnus (Open-Meteo free)
Layer 3: ECMWF ENS — Ensemble verification (ecmwf-opendata, Phase 2)
"""
import json, math, sys, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import requests

# ================================================================
# Layer 3: ECMWF ENS Integration (Phase 2)
# ================================================================
try:
    from fetch_ecmwf_ens import fetch_ens_single_peak, EnsembleResult
    ENS_AVAILABLE = True
except ImportError:
    ENS_AVAILABLE = False
    print("[LCL V2.0] WARNING: fetch_ecmwf_ens not available, Layer 3 disabled")

# ================================================================
# Constants
# ================================================================
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

LCL_FACTOR = 125.0  # LCL(m) = 125 * (T - Td) at sea level

# Pressure correction: LCL increases at higher altitudes
# Factor = (1013.25 / P) ** 0.5, where P = 1013.25 * exp(-elev / 8500)
def _lcl_pressure_factor(station_elev):
    """Pressure correction factor for LCL at altitude."""
    if station_elev is None or station_elev <= 0:
        return 1.0
    pressure = 1013.25 * math.exp(-station_elev / 8500.0)
    return (1013.25 / pressure) ** 0.5

MAGNUS_ALPHA = 17.27
MAGNUS_BETA  = 237.7

# Disagreement threshold (meters)
DISAGREEMENT_THRESHOLD = 200.0

# Default forecast days
FORECAST_DAYS = 3

# ================================================================
# Data Classes
# ================================================================
@dataclass
class HourlyData:
    """One hour of data from a single source"""
    hour: int
    temperature: Optional[float]
    dewpoint: Optional[float]      # Layer 1 direct; Layer 2 via Magnus
    relative_humidity: Optional[float] = None  # Layer 2 only
    t_max: Optional[float] = None       # ensemble stat (Layer 1 only)
    t_min: Optional[float] = None       # ensemble stat (Layer 1 only)
    precip_prob: Optional[float] = None
    lcl: Optional[float] = None        # computed
    station_elev: Optional[float] = None  # API elevation field
    # Extended fields for triple-verify integration (2026-05-15)
    cloud_cover: Optional[float] = None         # total cloud cover %
    cloud_cover_low: Optional[float] = None     # low cloud cover %
    wind_speed: Optional[float] = None          # wind speed km/h
    wind_direction: Optional[float] = None      # wind direction degrees
    # BUG-6 FIX: date fields for multi-day forecast filtering
    date: Optional[str] = None                  # "YYYY-MM-DD"
    day_offset: int = 0                         # 0=today, 1=tomorrow, 2=day after


@dataclass
class SourceResult:
    """Result from one data source for one peak"""
    source_name: str
    model_id: str
    station_elev: Optional[float]
    hourly: Dict[int, HourlyData] = field(default_factory=dict)
    status: str = "ok"  # ok | error | partial
    error_msg: str = ""
    # Raw API response for unified-layer integration (2026-05-15)
    # Set by fetch_layer1_batch when used as unified data source
    _raw_response: Optional[dict] = None


@dataclass
class FusionResult:
    """Fused LCL result for one peak"""
    peak_name: str
    latitude: float
    longitude: float
    summit_elev: float
    lcl_final: float
    lcl_range: Tuple[float, float]   # (lo, hi)
    confidence: str                   # HIGH | MEDIUM | LOW
    confidence_score: float           # 0.0-1.0
    mode: str                         # NORMAL | DISAGREEMENT | DISAGREEMENT_ENS | FALLBACK
    layer1_lcl: Optional[float]
    layer2_lcl: Optional[float]
    layer2_weight_used: float
    uncertainty_spread: float
    # Layer 3 fields (Phase 2)
    layer3_lcl: Optional[float] = None
    layer3_std: Optional[float] = None
    layer3_members: int = 0
    ensemble_result: Optional[dict] = None
    # Other
    sources_used: List[str] = field(default_factory=list)
    terrain_analysis: Dict = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


# ================================================================
# Layer 1: ecmwf_ifs025 — Baseline LCL
# ================================================================


# ================================================================
# Layer 2: cma_grapes_global — Height Correction
# ================================================================
def magnus_td(T: float, RH: float) -> Optional[float]:
    """
    Magnus formula: T + RH → Dew Point
    Returns None if RH <= 0 or formula fails.
    """
    if RH <= 0 or RH > 100:
        return None
    try:
        gamma = math.log(RH / 100.0) + (MAGNUS_ALPHA * T) / (MAGNUS_BETA + T)
        denom = MAGNUS_ALPHA - gamma
        if denom == 0:
            return None
        Td = MAGNUS_BETA * gamma / denom
        return Td
    except (ValueError, ZeroDivisionError):
        return None




# ================================================================
# Fusion Engine
# ================================================================
def compute_terrain_weights(
    ecmwf_elev: Optional[float],
    cma_elev: Optional[float],
    summit_elev: float,
) -> Tuple[float, float, bool, dict]:
    """
    Compute dynamic weights based on terrain fidelity.
    CMA gets a boost when its station elevation is closer to the real summit.

    Returns: (w_ecmwf, w_cma, cma_closer, analysis_dict)
    """
    analysis = {
        "ecmwf_station_elev": ecmwf_elev,
        "cma_station_elev": cma_elev,
        "summit_elev": summit_elev,
    }

    if ecmwf_elev is None or cma_elev is None:
        # Can't compare — use defaults
        analysis["reason"] = "missing elevation data"
        return 1.5, 1.0, False, analysis

    diff_ecmwf = abs(ecmwf_elev - summit_elev)
    diff_cma = abs(cma_elev - summit_elev)
    cma_closer = diff_cma < diff_ecmwf

    analysis["diff_ecmwf"] = round(diff_ecmwf, 0)
    analysis["diff_cma"] = round(diff_cma, 0)
    analysis["cma_closer"] = cma_closer

    w_ecmwf = 1.5  # always the anchor
    w_cma = 1.3 if cma_closer else 1.0

    return w_ecmwf, w_cma, cma_closer, analysis


def fuse_single_hour(
    l1_data: Optional[HourlyData],
    l2_data: Optional[HourlyData],
    w_ecmwf: float,
    w_cma: float,
    ens_result: Optional[EnsembleResult] = None,
) -> Tuple[float, float, str, float, Optional[EnsembleResult]]:
    """
    Fuse LCL for a single hour.
    Phase 2: When DISAGREEMENT, use Layer 3 ensemble if available.
    
    Returns: (lcl_final, uncertainty_spread, mode, confidence_score, ens_result_used)
    """
    l1_lcl = l1_data.lcl if l1_data else None
    l2_lcl = l2_data.lcl if l2_data else None

    # Both available
    if l1_lcl is not None and l2_lcl is not None:
        diff = abs(l1_lcl - l2_lcl)

        if diff < DISAGREEMENT_THRESHOLD:
            # NORMAL mode — weighted average
            total_w = w_ecmwf + w_cma
            lcl_final = (l1_lcl * w_ecmwf + l2_lcl * w_cma) / total_w
            mode = "NORMAL"
            conf = 0.85 if diff < 100 else 0.75
            ens_used = None
        else:
            # DISAGREEMENT mode
            # If L1-L2 diff > 5x threshold, L2 is an extreme outlier (e.g. CMA GRAPES
            # dry bias in mountain areas). Don't let L2 contaminate the result.
            L2_EXTREME_FACTOR = 5.0
            l2_is_extreme = diff > (DISAGREEMENT_THRESHOLD * L2_EXTREME_FACTOR)

            if l2_is_extreme:
                # L2 outlier: use L1 as anchor, ENS as validation if available
                if ens_result is not None and ens_result.status == "ok":
                    # If ENS agrees with L1 (within 2x threshold), trust L1-ENS blend
                    if abs(ens_result.lcl_mean - l1_lcl) < DISAGREEMENT_THRESHOLD * 2:
                        lcl_final = (l1_lcl * 1.5 + ens_result.lcl_mean) / 2.5
                        mode = "DISAGREEMENT_L1_ENS"
                        conf = 0.70
                    else:
                        # ENS also disagrees with L1 — use L1 alone (it's the most
                        # reliable single source for mountain cloud sea)
                        lcl_final = l1_lcl
                        mode = "DISAGREEMENT_L1"
                        conf = 0.50
                    spread = ens_result.lcl_p90 - ens_result.lcl_p10
                    ens_used = ens_result
                else:
                    lcl_final = l1_lcl
                    mode = "DISAGREEMENT_L1"
                    conf = 0.50
                    ens_used = None
            elif ens_result is not None and ens_result.status == "ok":
                # Normal disagreement (< 1000m): use median of 3 sources
                all_vals = sorted([l1_lcl, l2_lcl, ens_result.lcl_mean])
                lcl_final = all_vals[len(all_vals) // 2]  # median
                spread = ens_result.lcl_p90 - ens_result.lcl_p10
                mode = "DISAGREEMENT_ENS"
                conf = 0.65 if ens_result.agreement_rate > 0.7 else 0.50
                ens_used = ens_result
            else:
                # No Layer 3 — use median of 2
                vals = sorted([l1_lcl, l2_lcl])
                lcl_final = vals[len(vals) // 2]
                mode = "DISAGREEMENT"
                conf = 0.55 if diff < 500 else 0.40
                ens_used = None

        # Uncertainty: use T_max-T_min from Layer 1, or ensemble spread if available
        if ens_used is not None:
            spread = ens_used.lcl_p90 - ens_used.lcl_p10
        elif l1_data and l1_data.t_max is not None and l1_data.t_min is not None:
            spread = LCL_FACTOR * (l1_data.t_max - l1_data.t_min)
        else:
            spread = diff if mode.startswith("DISAGREEMENT") else abs(l1_lcl - l2_lcl)

        return lcl_final, spread, mode, conf, ens_used

    # Only Layer 1
    if l1_lcl is not None:
        spread = 0
        if l1_data and l1_data.t_max is not None and l1_data.t_min is not None:
            spread = LCL_FACTOR * (l1_data.t_max - l1_data.t_min)
        return l1_lcl, spread, "FALLBACK_L1", 0.60, None

    # Only Layer 2
    if l2_lcl is not None:
        return l2_lcl, 0, "FALLBACK_L2", 0.45, None

    # Neither
    return 500.0, 0, "NO_DATA", 0.10, None


def _hourly_for_date(
    src: SourceResult,
    target_date: Optional[str] = None,
    day_offset: int = 0,
) -> Dict[int, HourlyData]:
    """
    Get hourly data filtered to a specific date.
    BUG-6 FIX: hourly keys are now sequential indices (0,1,...,71),
    not hour-of-day (0-23). This function returns a dict keyed by hour-of-day
    for backward compatibility with fuse_peak.
    
    Args:
        src: SourceResult with hourly data
        target_date: If provided, filter to this date string "YYYY-MM-DD"
        day_offset: If target_date is None, use day_offset (0=today, 1=tomorrow)
    
    Returns:
        Dict[int, HourlyData] keyed by hour-of-day (0-23)
    """
    if not src.hourly:
        return {}
    
    filtered = {}
    for idx, hd in src.hourly.items():
        if target_date:
            if hd.date and hd.date != target_date:
                continue
        else:
            if hd.day_offset != day_offset:
                continue
        filtered[hd.hour] = hd
    
    # Fallback: if no date info in HourlyData, use old behavior (raw hour keys)
    if not filtered and src.hourly:
        first_hd = next(iter(src.hourly.values()))
        if first_hd.date is None:
            # Old-format data, keys are already hour-of-day
            return dict(src.hourly)
    
    return filtered


def fuse_peak(
    peak_name: str,
    lat: float,
    lon: float,
    summit_elev: float,
    l1: SourceResult,
    l2: SourceResult,
    target_hours: Optional[List[int]] = None,
    target_date: Optional[str] = None,
) -> FusionResult:
    """
    Fuse Layer 1 + Layer 2 + Layer 3 for one peak.
    By default targets hours 0-8 (night through morning).
    Phase 2: Fetch Layer 3 ensemble when L1-L2 disagree.
    
    Args:
        target_date: If provided, filter hourly data to this date.
    """
    if target_hours is None:
        target_hours = list(range(0, 9))  # 00:00 - 08:00

    # BUG-6 FIX: Filter hourly data to target date
    l1_hr = _hourly_for_date(l1, target_date=target_date)
    l2_hr = _hourly_for_date(l2, target_date=target_date)

    # Terrain weight computation
    w_ecmwf, w_cma, cma_closer, terrain = compute_terrain_weights(
        l1.station_elev, l2.station_elev, summit_elev
    )

    # First pass: check if any hour has DISAGREEMENT
    needs_ens = False
    for hr in target_hours:
        h1 = l1_hr.get(hr)
        h2 = l2_hr.get(hr)
        if h1 and h2 and h1.lcl is not None and h2.lcl is not None:
            if abs(h1.lcl - h2.lcl) >= DISAGREEMENT_THRESHOLD:
                needs_ens = True
                break

    # Fetch Layer 3 ensemble if needed and available
    ens_result = None
    if needs_ens and ENS_AVAILABLE:
        try:
            print(f"[LCL V2.0] {peak_name}: L1-L2 disagreement detected, fetching ENS Layer 3...")
            ens_result = fetch_ens_single_peak(lat, lon, peak_name)
            if ens_result.status == "ok":
                print(f"[LCL V2.0] {peak_name}: ENS mean={ens_result.lcl_mean:.1f}m, std={ens_result.lcl_std:.1f}m")
            else:
                print(f"[LCL V2.0] {peak_name}: ENS fetch failed: {ens_result.error_msg}")
                ens_result = None
        except Exception as e:
            print(f"[LCL V2.0] {peak_name}: ENS exception: {e}")
            ens_result = None

    # Fuse each target hour
    results = []
    for hr in target_hours:
        h1 = l1_hr.get(hr)
        h2 = l2_hr.get(hr)
        lcl, spread, mode, conf, ens_used = fuse_single_hour(h1, h2, w_ecmwf, w_cma, ens_result)
        results.append((hr, lcl, spread, mode, conf, h1, h2, ens_used))

    # Use minimum LCL in 04-06 range as the "peak" hour for cloud sea
    # (lowest LCL = best cloud sea chance)
    cloud_sea_hours = [r for r in results if 4 <= r[0] <= 6 and r[1] is not None]
    if cloud_sea_hours:
        best = min(cloud_sea_hours, key=lambda x: x[1])
        best_hr, best_lcl, best_spread, best_mode, best_conf, best_h1, best_h2, best_ens = best
    else:
        # Fallback: min LCL across all hours
        valid = [r for r in results if r[1] is not None]
        if valid:
            best = min(valid, key=lambda x: x[1])
        else:
            best = results[0] if results else (0, 500, 0, "NO_DATA", 0.1, None, None, None)
        best_hr, best_lcl, best_spread, best_mode, best_conf, best_h1, best_h2, best_ens = best

    # Confidence label
    if best_conf >= 0.80:
        conf_label = "HIGH"
    elif best_conf >= 0.55:
        conf_label = "MEDIUM"
    else:
        conf_label = "LOW"

    # LCL range (uncertainty)
    lcl_lo = max(0, best_lcl - best_spread)
    lcl_hi = best_lcl + best_spread

    # Source attribution
    sources = []
    if best_h1 and best_h1.lcl is not None:
        sources.append(l1.model_id)
    if best_h2 and best_h2.lcl is not None:
        sources.append(l2.model_id)
    if best_ens is not None:
        sources.append("ecmwf_ens")

    # Layer 3 fields
    layer3_lcl = None
    layer3_std = None
    layer3_members = 0
    ensemble_dict = None
    
    if best_ens is not None:
        layer3_lcl = round(best_ens.lcl_mean, 1)
        layer3_std = round(best_ens.lcl_std, 1)
        layer3_members = best_ens.member_count
        ensemble_dict = {
            "lcl_mean": best_ens.lcl_mean,
            "lcl_std": best_ens.lcl_std,
            "lcl_p10": best_ens.lcl_p10,
            "lcl_p90": best_ens.lcl_p90,
            "member_count": best_ens.member_count,
            "agreement_rate": best_ens.agreement_rate,
        }

    notes = []
    if best_mode.startswith("DISAGREEMENT"):
        diff = abs((best_h1.lcl or 0) - (best_h2.lcl or 0))
        if best_ens is not None:
            notes.append(f"L1-L2差{diff:.0f}m超阈值，ENS Layer3介入验证（均值{layer3_lcl:.0f}m，中位数融合）")
        else:
            notes.append(f"L1-L2差{diff:.0f}m超阈值，启用中位数模式（Layer3未获取或失败）")
    if cma_closer:
        notes.append(f"CMA地形更优（差{terrain.get('diff_cma',0):.0f}m vs ECMWF差{terrain.get('diff_ecmwf',0):.0f}m），权重提升至1.3")

    return FusionResult(
        peak_name=peak_name,
        latitude=lat,
        longitude=lon,
        summit_elev=summit_elev,
        lcl_final=round(best_lcl, 1),
        lcl_range=(round(lcl_lo, 1), round(lcl_hi, 1)),
        confidence=conf_label,
        confidence_score=round(best_conf, 3),
        mode=best_mode,
        layer1_lcl=round(best_h1.lcl, 1) if best_h1 and best_h1.lcl else None,
        layer2_lcl=round(best_h2.lcl, 1) if best_h2 and best_h2.lcl else None,
        layer2_weight_used=w_cma,
        uncertainty_spread=round(best_spread, 1),
        layer3_lcl=layer3_lcl,
        layer3_std=layer3_std,
        layer3_members=layer3_members,
        ensemble_result=ensemble_dict,
        sources_used=sources,
        terrain_analysis=terrain,
        notes=notes,
    )


# ================================================================
# Batch API: Fetch all 16 peaks in one call per layer
# ================================================================
def _parse_l1_responses(responses: list, peaks: List[dict], results: Dict[str, SourceResult]):
    """Parse L1 batch API responses into SourceResult objects."""
    for i, p in enumerate(peaks):
        if i >= len(responses):
            results[p["name"]] = SourceResult(
                source_name="ECMWF IFS 0.25",
                model_id="ecmwf_ifs025",
                station_elev=None,
                status="error",
                error_msg="missing in batch response",
            )
            continue

        resp = responses[i]
        # Check for per-location error
        if resp.get('error', False):
            results[p["name"]] = SourceResult(
                source_name="ECMWF IFS 0.25",
                model_id="ecmwf_ifs025",
                station_elev=None,
                status="error",
                error_msg=resp.get('reason', 'API error')[:200],
            )
            continue

        station_elev = resp.get("elevation")
        h = resp.get("hourly", {})
        times = h.get("time", [])
        temps = h.get("temperature_2m", [])
        dews = h.get("dew_point_2m", [])
        tmaxs = h.get("temperature_2m_max", [])
        tmins = h.get("temperature_2m_min", [])
        rhs_raw = h.get("relative_humidity_2m", [])
        ccs = h.get("cloud_cover", [])
        cc_lows = h.get("cloud_cover_low", [])
        winds = h.get("wind_speed_10m", [])
        wind_dirs = h.get("wind_direction_10m", [])

        hourly = {}
        for j, t_str in enumerate(times):
            hour = int(t_str[11:13])
            date_str = t_str[:10]
            day_offset = j // 24
            T = temps[j] if j < len(temps) else None
            Td = dews[j] if j < len(dews) else None
            Tmx = tmaxs[j] if j < len(tmaxs) else None
            Tmn = tmins[j] if j < len(tmins) else None
            RH = rhs_raw[j] if j < len(rhs_raw) else None
            cc = ccs[j] if j < len(ccs) else None
            cc_low = cc_lows[j] if j < len(cc_lows) else None
            ws = winds[j] if j < len(winds) else None
            wd = wind_dirs[j] if j < len(wind_dirs) else None
            lcl = None
            if T is not None and Td is not None and T >= Td:
                pf = _lcl_pressure_factor(station_elev)
                lcl = LCL_FACTOR * (T - Td) * pf
            hourly[j] = HourlyData(
                hour=hour, temperature=T, dewpoint=Td,
                relative_humidity=RH,
                t_max=Tmx, t_min=Tmn, lcl=lcl, station_elev=station_elev,
                cloud_cover=cc, cloud_cover_low=cc_low,
                wind_speed=ws, wind_direction=wd,
                date=date_str, day_offset=day_offset,
            )

        sr = SourceResult(
            source_name="ECMWF IFS 0.25",
            model_id="ecmwf_ifs025",
            station_elev=station_elev,
            hourly=hourly,
            status="ok" if hourly else "error",
        )
        sr._raw_response = resp
        results[p["name"]] = sr


def fetch_layer1_batch(
    peaks: List[dict], forecast_days: int = FORECAST_DAYS
) -> Dict[str, SourceResult]:
    """
    Batch fetch Layer 1 for all peaks.
    Splits into chunks of 4 peaks to avoid API timeout.
    2026-06-02 FIX: 16 peaks × 13 vars × 7+ days causes timeout;
    chunked approach keeps each request under ~30KB.
    """
    CHUNK_SIZE = 4  # 4 peaks per request to avoid timeout
    results = {}

    for chunk_start in range(0, len(peaks), CHUNK_SIZE):
        chunk = peaks[chunk_start:chunk_start + CHUNK_SIZE]
        lats = ",".join(str(p["latitude"]) for p in chunk)
        lons = ",".join(str(p["longitude"]) for p in chunk)

        params = {
            "latitude": lats,
            "longitude": lons,
            "hourly": (
                "temperature_2m,dew_point_2m,relative_humidity_2m,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability,precipitation,surface_pressure,"
                "cloud_cover,cloud_cover_low,wind_speed_10m,wind_direction_10m,weather_code"
            ),
            "models": "ecmwf_ifs025",
            "forecast_days": forecast_days,
            "timezone": "Asia/Shanghai",
        }

        try:
            r = requests.get(OPEN_METEO_BASE, params=params, timeout=90)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            for p in chunk:
                results[p["name"]] = SourceResult(
                    source_name="ECMWF IFS 0.25",
                    model_id="ecmwf_ifs025",
                    station_elev=None,
                    status="error",
                    error_msg=f"chunk batch failed: {e}",
                )
            continue

        responses = data if isinstance(data, list) else [data]
        _parse_l1_responses(responses, chunk, results)

    return results

    for i, p in enumerate(peaks):
        if i >= len(responses):
            results[p["name"]] = SourceResult(
                source_name="ECMWF IFS 0.25",
                model_id="ecmwf_ifs025",
                station_elev=None,
                status="error",
                error_msg="missing in batch response",
            )
            continue

        resp = responses[i]
        station_elev = resp.get("elevation")
        h = resp.get("hourly", {})
        times = h.get("time", [])
        temps = h.get("temperature_2m", [])
        dews = h.get("dew_point_2m", [])
        tmaxs = h.get("temperature_2m_max", [])
        tmins = h.get("temperature_2m_min", [])
        rhs_raw = h.get("relative_humidity_2m", [])
        ccs = h.get("cloud_cover", [])
        cc_lows = h.get("cloud_cover_low", [])
        winds = h.get("wind_speed_10m", [])
        wind_dirs = h.get("wind_direction_10m", [])

        hourly = {}
        for j, t_str in enumerate(times):
            hour = int(t_str[11:13])
            date_str = t_str[:10]  # "YYYY-MM-DD"
            day_offset = j // 24   # 0=today, 1=tomorrow, 2=day after
            T = temps[j] if j < len(temps) else None
            Td = dews[j] if j < len(dews) else None
            Tmx = tmaxs[j] if j < len(tmaxs) else None
            Tmn = tmins[j] if j < len(tmins) else None
            RH = rhs_raw[j] if j < len(rhs_raw) else None
            cc = ccs[j] if j < len(ccs) else None
            cc_low = cc_lows[j] if j < len(cc_lows) else None
            ws = winds[j] if j < len(winds) else None
            wd = wind_dirs[j] if j < len(wind_dirs) else None
            lcl = None
            if T is not None and Td is not None and T >= Td:
                pf = _lcl_pressure_factor(station_elev)
                lcl = LCL_FACTOR * (T - Td) * pf
            # BUG-6 FIX: Use sequential index as key to avoid overwriting
            # across multiple forecast days (hour=0 appears 3 times)
            hourly[j] = HourlyData(
                hour=hour, temperature=T, dewpoint=Td,
                relative_humidity=RH,
                t_max=Tmx, t_min=Tmn, lcl=lcl, station_elev=station_elev,
                cloud_cover=cc, cloud_cover_low=cc_low,
                wind_speed=ws, wind_direction=wd,
                date=date_str, day_offset=day_offset,
            )

        sr = SourceResult(
            source_name="ECMWF IFS 0.25",
            model_id="ecmwf_ifs025",
            station_elev=station_elev,
            hourly=hourly,
            status="ok" if hourly else "error",
        )
        sr._raw_response = resp  # For unified-layer integration
        results[p["name"]] = sr

    return results


def fetch_layer2_batch(
    peaks: List[dict], forecast_days: int = FORECAST_DAYS
) -> Dict[str, SourceResult]:
    """Batch fetch Layer 2 (CMA GRAPES) for all peaks.
    2026-06-02 FIX: Chunked to avoid API timeout.
    """
    CHUNK_SIZE = 4
    results = {}

    for chunk_start in range(0, len(peaks), CHUNK_SIZE):
        chunk = peaks[chunk_start:chunk_start + CHUNK_SIZE]
        lats = ",".join(str(p["latitude"]) for p in chunk)
        lons = ",".join(str(p["longitude"]) for p in chunk)

        params = {
            "latitude": lats,
            "longitude": lons,
            "hourly": "temperature_2m,relative_humidity_2m",
            "models": "cma_grapes_global",
            "forecast_days": forecast_days,
            "timezone": "Asia/Shanghai",
        }

        try:
            r = requests.get(OPEN_METEO_BASE, params=params, timeout=90)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            for p in chunk:
                results[p["name"]] = SourceResult(
                    source_name="CMA GRAPES Global",
                    model_id="cma_grapes_global",
                    station_elev=None,
                    status="error",
                    error_msg=f"chunk batch failed: {e}",
                )
            continue

        responses = data if isinstance(data, list) else [data]

    for i, p in enumerate(peaks):
        if i >= len(responses):
            results[p["name"]] = SourceResult(
                source_name="CMA GRAPES Global",
                model_id="cma_grapes_global",
                station_elev=None,
                status="error",
                error_msg="missing in batch response",
            )
            continue

        resp = responses[i]
        station_elev = resp.get("elevation")
        h = resp.get("hourly", {})
        times = h.get("time", [])
        temps = h.get("temperature_2m", [])
        rhs = h.get("relative_humidity_2m", [])

        hourly = {}
        for j, t_str in enumerate(times):
            hour = int(t_str[11:13])
            date_str = t_str[:10]
            day_offset = j // 24
            T = temps[j] if j < len(temps) else None
            RH = rhs[j] if j < len(rhs) else None
            Td = magnus_td(T, RH) if T is not None and RH is not None else None
            lcl = None
            if T is not None and Td is not None and T >= Td:
                pf = _lcl_pressure_factor(station_elev)
                lcl = LCL_FACTOR * (T - Td) * pf
            # BUG-6 FIX: Use sequential index as key to avoid overwriting
            hourly[j] = HourlyData(
                hour=hour, temperature=T, dewpoint=Td,
                relative_humidity=RH, lcl=lcl, station_elev=station_elev,
                date=date_str, day_offset=day_offset,
            )

        results[p["name"]] = SourceResult(
            source_name="CMA GRAPES Global",
            model_id="cma_grapes_global",
            station_elev=station_elev,
            hourly=hourly,
            status="ok" if hourly else "error",
        )

    return results


# ================================================================
# ================================================================
# Helper: Build l1_results from unified Open-Meteo response
# Used when Round 1 and LCL V2.0 L1 share a single API call
# ================================================================


# Main: Run full 16-peak LCL V2.0
# ================================================================
def run_lcl_v2(
    peaks: List[dict],
    target_hours: Optional[List[int]] = None,
    forecast_days: int = FORECAST_DAYS,
    l1_data: Optional[Dict[str, SourceResult]] = None,
    l2_data: Optional[Dict[str, SourceResult]] = None,
    target_date: Optional[str] = None,
) -> Tuple[List[FusionResult], Dict[str, SourceResult]]:
    """
    Run LCL V2.0 for all peaks.
    Returns (list of FusionResult sorted by lcl_final, l1_results dict).
    
    Phase 2: Layer 3 ensemble verification for disagreement cases.
    
    Args:
        l1_data: Pre-fetched L1 SourceResult dict. If None, fetches automatically.
        l2_data: Pre-fetched L2 SourceResult dict. If None, fetches automatically.
                 Pass a dict (from fetch_layer2_batch) or None for auto-fetch.
        target_date: If provided, filter hourly data to this date "YYYY-MM-DD".
    """
    if target_hours is None:
        target_hours = list(range(0, 9))

    # Phase 1: Batch fetch (skip if pre-fetched)
    if l1_data is None:
        print("[LCL V2.0] Fetching Layer 1 (ecmwf_ifs025)...")
        t0 = time.time()
        l1_results = fetch_layer1_batch(peaks, forecast_days)
        print(f"  Done in {time.time()-t0:.1f}s — {sum(1 for v in l1_results.values() if v.status=='ok')}/{len(peaks)} OK")
    else:
        l1_results = l1_data
        print(f"[LCL V2.0] Using pre-fetched Layer 1 data ({sum(1 for v in l1_results.values() if v.status=='ok')}/{len(peaks)} OK)")

    if l2_data is None:
        print("[LCL V2.0] Fetching Layer 2 (cma_grapes_global)...")
        t0 = time.time()
        l2_results = fetch_layer2_batch(peaks, forecast_days)
        print(f"  Done in {time.time()-t0:.1f}s — {sum(1 for v in l2_results.values() if v.status=='ok')}/{len(peaks)} OK")
    else:
        l2_results = l2_data
        print(f"[LCL V2.0] Using pre-fetched Layer 2 data ({sum(1 for v in l2_results.values() if v.status=='ok')}/{len(peaks)} OK)")

    # Phase 2: Fuse per peak (with Layer 3 if needed)
    fused = []
    for peak in peaks:
        name = peak["name"]
        l1 = l1_results.get(name)
        l2 = l2_results.get(name)
        if l1 is None:
            l1 = SourceResult("L1", "ecmwf_ifs025", None, status="error", error_msg="not fetched")
        if l2 is None:
            l2 = SourceResult("L2", "cma_grapes_global", None, status="error", error_msg="not fetched")
        result = fuse_peak(name, peak["latitude"], peak["longitude"], peak["summit_elev"], l1, l2, target_hours, target_date=target_date)
        fused.append(result)

    # Sort: lowest LCL first (best cloud sea chance)
    fused.sort(key=lambda r: r.lcl_final)
    # Return L1 results alongside for triple-verify integration
    return fused, l1_results


def print_fusion_table(results: List[FusionResult]):
    """Print a formatted summary table. Phase 2: Include Layer 3 column."""
    print()
    print("=" * 140)
    print(f"{'#':>2} {'Peak':<10} {'Elev':>5} {'L1_LCL':>7} {'L2_LCL':>7} {'L3_LCL':>7} {'L2_W':>5} {'Fused':>7} {'Range':>14} {'Spread':>7} {'Conf':>6} {'Mode':<15} {'Notes'}")
    print("-" * 140)
    for i, r in enumerate(results, 1):
        l1 = f"{r.layer1_lcl:.0f}m" if r.layer1_lcl else "---"
        l2 = f"{r.layer2_lcl:.0f}m" if r.layer2_lcl else "---"
        l3 = f"{r.layer3_lcl:.0f}m" if r.layer3_lcl else "---"
        rng = f"[{r.lcl_range[0]:.0f}, {r.lcl_range[1]:.0f}]"
        notes = "; ".join(r.notes[:1]) if r.notes else ""
        print(f"{i:>2} {r.peak_name:<10} {r.summit_elev:>5} {l1:>7} {l2:>7} {l3:>7} {r.layer2_weight_used:>5.1f} {r.lcl_final:>7.1f} {rng:>14} {r.uncertainty_spread:>7.1f} {r.confidence:>6} {r.mode:<15} {notes}")
    print("=" * 140)




# ================================================================
# Entry Point
# ================================================================

def extract_verify_data(l1_results: dict, target_date: str) -> dict:
    """
    Extract verification data from L1 results for target_date.
    Returns dict with "sample_peaks" key.
    """
    if not l1_results:
        return None
    
    sample_peaks = {}
    for peak_name, sr in l1_results.items():
        if sr.status != "ok" or not sr.hourly:
            continue
        
        # Filter hourly data for target_date
        date_hours = [h for h in sr.hourly 
                      if hasattr(h, 'date') and h.date == target_date]
        
        if not date_hours:
            continue
        
        # Compute averages
        t_vals   = [h.temperature for h in date_hours if h.temperature is not None]
        td_vals  = [h.dewpoint for h in date_hours if h.dewpoint is not None]
        rh_vals  = [h.relative_humidity for h in date_hours if h.relative_humidity is not None]
        cc_vals  = [h.cloud_cover for h in date_hours if h.cloud_cover is not None]
        ws_vals  = [h.wind_speed for h in date_hours if h.wind_speed is not None]
        lcl_vals = [h.lcl for h in date_hours if h.lcl is not None]
        
        if not t_vals:
            continue
        
        sample_peaks[peak_name] = {
            "T_avg":   sum(t_vals)   / len(t_vals),
            "Td_avg":  sum(td_vals)  / len(td_vals)  if td_vals  else None,
            "RH_avg":  sum(rh_vals)  / len(rh_vals)  if rh_vals  else None,
            "cc_avg":  sum(cc_vals)  / len(cc_vals)  if cc_vals  else None,
            "wind_avg": sum(ws_vals)  / len(ws_vals)  if ws_vals  else None,
            "LCL_avg": sum(lcl_vals) / len(lcl_vals) if lcl_vals else None,
        }
    
    if not sample_peaks:
        return None
    
    return {"sample_peaks": sample_peaks}


if __name__ == "__main__":
    # Load peaks from peaks.json
    import os
    peaks_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "references", "peaks.json"
    )
    with open(peaks_path, encoding="utf-8") as f:
        peaks_data = json.load(f)
    peaks = peaks_data["peaks"]

    print(f"LCL V2.0 — Three-Layer Architecture (Phase 1+2: L1+L2+L3)")
    print(f"Peaks: {len(peaks)} | Time: {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Layer 3 (ENS) Available: {ENS_AVAILABLE}")
    print()

    results, _ = run_lcl_v2(peaks)
    print_fusion_table(results)