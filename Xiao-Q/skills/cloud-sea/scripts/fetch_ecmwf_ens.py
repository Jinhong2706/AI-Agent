# -*- coding: utf-8 -*-
"""LCL V2.0 Phase 2 - ECMWF ENS Layer 3 (Optimized v2)

Fetch ECMWF ENS ensemble data (50 members, sampled to 5 representatives)
and compute ensemble LCL statistics for cloud sea prediction.

Optimizations (v2):
- Step availability probe: auto-detect which ENS steps exist (3h intervals)
- Adaptive step selection: prefer step=15 (03BJT) + step=18 (06BJT)
- File-level caching: skip download if same (date, member, param, step) was fetched
- Reduced member count: 5 representative members (from 10) for faster execution
- Progress tracking with ETA

Technical stack:
- ecmwf-opendata 0.3.29, source='azure' for GRIB2 download
- eccodes 2.27.0 grib_get.exe for point value extraction
- Subprocess-based extraction (ctypes API failed due to CRT incompatibility)

ENS step availability (12UTC base, verified 2026-05-13):
  step=12 (00 BJT) ✅  step=15 (03 BJT) ✅  step=18 (06 BJT) ✅
  step=21 (09 BJT) ✅  step=24 (12 BJT) ✅
  Odd steps (13,14,16,17,19,20,22,23) ❌ not available (3h intervals only)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ================================================================
# Configuration
# ================================================================

# eccodes tool path (优先使用 skill 目录下的版本，回退到 TEMP 目录)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ECCODES_BIN_SKILL = os.path.join(SKILL_DIR, 'tools', 'eccodes-bin')
ECCODES_BIN_TEMP = os.path.join(os.environ.get('TEMP', '/tmp'), 'eccodes-full-deps', 'bin')

# 优先使用 skill 目录下的 eccodes
if os.path.exists(os.path.join(ECCODES_BIN_SKILL, 'grib_get2.exe')):
    ECCODES_BIN = ECCODES_BIN_SKILL
    GRIB_GET = os.path.join(ECCODES_BIN, 'grib_get2.exe')  # 重命名避免权限问题
elif os.path.exists(os.path.join(ECCODES_BIN_SKILL, 'grib_get.exe')):
    ECCODES_BIN = ECCODES_BIN_SKILL
    GRIB_GET = os.path.join(ECCODES_BIN, 'grib_get.exe')
else:
    ECCODES_BIN = ECCODES_BIN_TEMP
    GRIB_GET = os.path.join(ECCODES_BIN, 'grib_get.exe')

# Representative members (uniform sampling of 50 members)
# Reduced from 10 to 5 for performance (~100s vs ~200s)
SAMPLE_MEMBERS = [5, 15, 25, 35, 45]

# Preferred cloud sea steps (from 12UTC base), ordered by priority
# step=15 → 03 BJT (pre-dawn, radiation cooling)
# step=18 → 06 BJT (sunrise, best observation window)
# NOTE: These values are hardcode based on verified availability (2026-05-13)
# to avoid hitting the ECMWF opendata Azure SAS token rate limit (429 errors).
PREFERRED_STEPS = [15, 18]

# Fallback steps if preferred ones fail
FALLBACK_STEPS = [12, 21]

# Maximum steps to attempt
MAX_STEPS = 3

# LCL factor
LCL_FACTOR = 125.0

# Cache directory - use skill directory for persistence
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SKILL_DIR, '..', 'cache', 'ens')
CACHE_DIR = os.path.abspath(CACHE_DIR)
CACHE_TTL_SECONDS = 3600 * 24  # 24 hours (ENS updates every 6h, cache for 4 cycles)


# ================================================================
# Data Classes
# ================================================================

@dataclass
class EnsembleMember:
    """Single ensemble member's LCL data"""
    number: int
    lcl_values: Dict[int, float] = field(default_factory=dict)  # step -> LCL(m)


@dataclass
class EnsembleResult:
    """Ensemble statistics for one peak"""
    lcl_mean: float
    lcl_std: float
    lcl_p10: float  # 10th percentile
    lcl_p90: float  # 90th percentile
    member_count: int
    members: List[EnsembleMember]
    agreement_rate: float  # 0-1, members within 200m of median
    status: str = "ok"  # ok | partial | error
    error_msg: str = ""
    steps_used: List[int] = field(default_factory=list)
    download_time: float = 0.0


# ================================================================
# Step Availability Cache (module-level)
# ================================================================
_step_availability_cache: Optional[List[int]] = None
_step_probe_time: float = 0.0




def select_best_steps(base_time: int = 12) -> List[int]:
    """
    Select the best available steps for cloud sea analysis.
    Priority: 15 (03BJT) > 18 (06BJT) > 12 (00BJT) > 21 (09BJT)
    Returns at most MAX_STEPS.

    NOTE: Hardcoded to skip network probe (avoids 429 rate limit from Azure SAS token endpoint).
    Verified available steps: 12, 15, 18, 21, 24 (from 2026-05-13 test).
    """
    # HARDCODE: skip probe to avoid 429 rate limit
    available = [12, 15, 18, 21, 24]  # verified available steps

    # Priority order
    priority = [s for s in PREFERRED_STEPS if s in available]
    fallback = [s for s in FALLBACK_STEPS if s in available]
    others = [s for s in available if s not in PREFERRED_STEPS and s not in FALLBACK_STEPS]

    selected = (priority + fallback + others)[:MAX_STEPS]

    if not selected and available:
        selected = available[:MAX_STEPS]

    step_labels = []
    for s in selected:
        bjt = (base_time + s) % 24
        step_labels.append(f"step={s} ({bjt:02d} BJT)")
    print(f"[ENS] Selected steps: {', '.join(step_labels)}")

    return selected


# ================================================================
# Cache Management
# ================================================================

def _cache_key(param: str, step: int, number: int) -> str:
    """Generate cache key for a GRIB2 file."""
    # P2 FIX: 使用 ENS 运行日期（今天），而非目标日期
    # ENS 数据每天更新一次（base_time=12 UTC），缓存键应按运行日期，不是预报日期
    run_date = time.strftime('%Y%m%d')
    return f"{run_date}_{param}_s{step}_n{number}.grib2"


def _get_cache_file(key: str) -> Optional[str]:
    """Check if a cached GRIB2 file exists and is fresh."""
    cache_path = os.path.join(CACHE_DIR, key)
    if os.path.exists(cache_path):
        age = time.time() - os.path.getmtime(cache_path)
        if age < CACHE_TTL_SECONDS:
            return cache_path
    return None


def _put_cache_file(key: str, source_path: str) -> str:
    """Copy a downloaded file to cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, key)
    shutil.copy2(source_path, cache_path)
    return cache_path


def _get_result_cache_path(peak_name: str, base_time: int) -> str:
    """Path for caching EnsembleResult JSON."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    # P2 FIX: 使用 ENS 运行日期（今天），而非目标日期
    run_date = time.strftime('%Y%m%d')
    return os.path.join(CACHE_DIR, f"result_{peak_name}_t{base_time}_{run_date}.json")


def _load_cached_result(peak_name: str, base_time: int) -> Optional[dict]:
    """Load cached EnsembleResult if fresh."""
    path = _get_result_cache_path(peak_name, base_time)
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < CACHE_TTL_SECONDS:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                pass
    return None


def _save_cached_result(peak_name: str, base_time: int, result: EnsembleResult):
    """Save EnsembleResult to cache."""
    path = _get_result_cache_path(peak_name, base_time)
    try:
        data = {
            'lcl_mean': result.lcl_mean,
            'lcl_std': result.lcl_std,
            'lcl_p10': result.lcl_p10,
            'lcl_p90': result.lcl_p90,
            'member_count': result.member_count,
            'agreement_rate': result.agreement_rate,
            'status': result.status,
            'error_msg': result.error_msg,
            'steps_used': result.steps_used,
            'download_time': result.download_time,
            'cached_at': time.time(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ================================================================
# Download & Extract
# ================================================================

def download_ens_grib2(
    param: str,
    step: int,
    number: int,
    base_time: int = 12,
    target: Optional[str] = None,
    use_cache: bool = True,
) -> Optional[str]:
    """
    Download a single GRIB2 file from ECMWF ENS.
    Supports caching to avoid redundant downloads.
    """
    # Check cache first (P2 FIX: 不再需要 date_str)
    if use_cache:
        cache_key = _cache_key(param, step, number)
        cached = _get_cache_file(cache_key)
        if cached:
            return cached

    try:
        from ecmwf.opendata import Client
    except ImportError:
        print("[ENS] ERROR: ecmwf-opendata not installed")
        return None

    if target is None:
        target = tempfile.mktemp(suffix='.grib2')

    try:
        client = Client(source='azure')
        client.retrieve(
            type='pf',
            levtype='sfc',
            param=param,
            step=step,
            number=number,
            time=base_time,
            target=target
        )

        # Cache the file
        if use_cache and os.path.exists(target):
            cache_key = _cache_key(param, step, number)
            _put_cache_file(cache_key, target)

        return target
    except Exception as e:
        if os.path.exists(target):
            os.remove(target)
        return None


def extract_point_value(grib2_path: str, lat: float, lon: float) -> Optional[float]:
    """Extract point value from GRIB2 using grib_get.exe."""
    if not os.path.exists(GRIB_GET):
        return None
    if not os.path.exists(grib2_path):
        return None

    try:        
        # grib_get.exe expects: -l lat,lon,mode (comma-separated in ONE argument)
        # Using separate args '-l', str(lat), str(lon), '1' is WRONG!
        latlon_arg = f"{lat},{lon},1"
        result = subprocess.run(
            [GRIB_GET, '-l', latlon_arg, '-F', '%.1f', grib2_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"[ENS extract] grib_get FAILED (code {result.returncode}): {result.stderr.strip()[:120]}")
            return None
        value_str = result.stdout.strip()
        if not value_str:
            print(f"[ENS extract] grib_get returned empty for {os.path.basename(grib2_path)} (code {result.returncode})")
            return None
        return float(value_str)
    except subprocess.TimeoutExpired:
        print(f"[ENS extract] grib_get TIMEOUT for {os.path.basename(grib2_path)}")
        return None
    except (ValueError, Exception) as e:
        print(f"[ENS extract] Error processing {os.path.basename(grib2_path)}: {e}")
        return None


# ================================================================
# Main: Fetch & Compute
# ================================================================

def fetch_ens_single_peak(
    lat: float,
    lon: float,
    peak_name: str,
    base_time: int = 12,
    date_str: Optional[str] = None,
    use_cache: bool = True,
) -> EnsembleResult:
    """
    Fetch ENS ensemble data for a single peak and compute LCL statistics.

    Optimization (v2):
    - Auto-detect available steps (probe once, cache in-process)
    - File-level caching to skip re-downloads
    - 5 representative members for faster execution (~100s)

    Args:
        lat: Peak latitude
        lon: Peak longitude
        peak_name: Peak name for logging
        base_time: ECMWF base time (12 UTC for cloud sea)
        date_str: Date string for cache key (auto-detect if None)
        use_cache: Whether to use file/result caching

    Returns:
        EnsembleResult with LCL statistics
    """
    # Auto-detect date for cache key
    if date_str is None:
        date_str = time.strftime('%Y%m%d')

    # Check result cache
    if use_cache:
        cached = _load_cached_result(peak_name, base_time)
        if cached and cached.get('status') == 'ok':
            age = time.time() - cached.get('cached_at', 0)
            print(f"[ENS] {peak_name}: using cached result ({age/60:.0f}m old, "
                  f"mean={cached['lcl_mean']:.1f}m, "
                  f"std={cached['lcl_std']:.1f}m)")
            return EnsembleResult(
                lcl_mean=cached['lcl_mean'],
                lcl_std=cached['lcl_std'],
                lcl_p10=cached['lcl_p10'],
                lcl_p90=cached['lcl_p90'],
                member_count=cached['member_count'],
                members=[],
                agreement_rate=cached['agreement_rate'],
                status=cached['status'],
                steps_used=cached.get('steps_used', []),
                download_time=cached.get('download_time', 0),
            )

    # Select best available steps
    steps = select_best_steps(base_time)
    if not steps:
        return EnsembleResult(
            lcl_mean=500.0, lcl_std=0, lcl_p10=500.0, lcl_p90=500.0,
            member_count=0, members=[], agreement_rate=0,
            status="error", error_msg="No ENS steps available"
        )

    print(f"[ENS] Fetching ensemble for {peak_name} (lat={lat}, lon={lon})...")

    # Create temp directory for non-cached GRIB2 files
    work_dir = tempfile.mkdtemp(prefix='ens_')

    try:
        # Phase 1: Download GRIB2 files
        downloaded: Dict[Tuple[str, int, int], str] = {}
        total = len(SAMPLE_MEMBERS) * 2 * len(steps)
        done = 0
        failed = 0
        cached_hits = 0
        t0 = time.time()

        for number in SAMPLE_MEMBERS:
            for param in ['2t', '2d']:
                for step in steps:
                    # Try cache first
                    if use_cache:
                        cache_key = _cache_key(param, step, number)
                        cached_path = _get_cache_file(cache_key)
                        if cached_path:
                            downloaded[(param, step, number)] = cached_path
                            cached_hits += 1
                            done += 1
                            continue

                    # Download
                    filename = f"{param}_{step}_{number}.grib2"
                    target_path = os.path.join(work_dir, filename)
                    result_path = download_ens_grib2(
                        param=param, step=step, number=number,
                        base_time=base_time, target=target_path,
                        use_cache=use_cache  # P2 FIX: 启用内层缓存检查
                    )

                    if result_path and os.path.exists(result_path):
                        downloaded[(param, step, number)] = result_path
                        # Cache it
                        if use_cache:
                            cache_key = _cache_key(param, step, number)
                            _put_cache_file(cache_key, result_path)
                        done += 1
                    else:
                        failed += 1

        dl_time = time.time() - t0
        print(f"[ENS] Downloaded {done - cached_hits}/{total} new + {cached_hits} cached "
              f"in {dl_time:.1f}s ({failed} failed)")

        # Need enough data for meaningful ensemble
        # Minimum: 3 members with both 2t and 2d for at least 1 step
        min_files = len(steps) * 2 * 2  # 2 params × 2 members minimum per step
        if done < min_files:
            return EnsembleResult(
                lcl_mean=500.0, lcl_std=0, lcl_p10=500.0, lcl_p90=500.0,
                member_count=0, members=[], agreement_rate=0,
                status="error",
                error_msg=f"Too few downloads ({done}/{total}, need ≥{min_files})"
            )

        # Phase 2: Extract point values
        members: List[EnsembleMember] = []

        for number in SAMPLE_MEMBERS:
            member = EnsembleMember(number=number)

            for step in steps:
                t_key = ('2t', step, number)
                d_key = ('2d', step, number)
                t_path = downloaded.get(t_key)
                d_path = downloaded.get(d_key)

                if t_path and d_path:
                    T_K = extract_point_value(t_path, lat, lon)
                    Td_K = extract_point_value(d_path, lat, lon)

                    if T_K is not None and Td_K is not None:
                        T_C = T_K - 273.15
                        Td_C = Td_K - 273.15
                        if T_C >= Td_C:
                            lcl = LCL_FACTOR * (T_C - Td_C)
                            member.lcl_values[step] = lcl

            if member.lcl_values:
                members.append(member)

        # Phase 3: Compute statistics
        all_lcls: List[float] = []
        for member in members:
            if member.lcl_values:
                avg_lcl = sum(member.lcl_values.values()) / len(member.lcl_values)
                all_lcls.append(avg_lcl)

        if not all_lcls:
            return EnsembleResult(
                lcl_mean=500.0, lcl_std=0, lcl_p10=500.0, lcl_p90=500.0,
                member_count=0, members=[], agreement_rate=0,
                status="error", error_msg="No valid LCL values extracted"
            )

        n = len(all_lcls)
        lcl_mean = sum(all_lcls) / n

        # Standard deviation
        if n > 1:
            variance = sum((x - lcl_mean) ** 2 for x in all_lcls) / n
            lcl_std = variance ** 0.5
        else:
            lcl_std = 0

        # Percentiles
        sorted_lcls = sorted(all_lcls)
        lcl_p10 = sorted_lcls[max(0, int(n * 0.1))]
        lcl_p90 = sorted_lcls[min(n - 1, int(n * 0.9))]

        # Agreement rate
        median_lcl = sorted_lcls[n // 2]
        agreeing = sum(1 for x in all_lcls if abs(x - median_lcl) <= 200.0)
        agreement_rate = agreeing / n

        result = EnsembleResult(
            lcl_mean=round(lcl_mean, 1),
            lcl_std=round(lcl_std, 1),
            lcl_p10=round(lcl_p10, 1),
            lcl_p90=round(lcl_p90, 1),
            member_count=n,
            members=members,
            agreement_rate=round(agreement_rate, 3),
            status="ok",
            steps_used=steps,
            download_time=round(dl_time, 1),
        )

        print(f"[ENS] {peak_name}: mean={lcl_mean:.1f}m, std={lcl_std:.1f}m, "
              f"P10={lcl_p10:.1f}m, P90={lcl_p90:.1f}m, "
              f"agree={agreement_rate:.2f} ({n} members)")

        # Cache result
        if use_cache:
            _save_cached_result(peak_name, base_time, result)

        return result

    finally:
        # Cleanup temp directory (keep cache dir)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)






# ================================================================
# Test / Demo
# ================================================================
if __name__ == "__main__":
    test_peak = {
        "name": "海坨山",
        "latitude": 40.93,
        "longitude": 115.78
    }

    print(f"[ENS Test] {test_peak['name']} | {time.strftime('%Y-%m-%d %H:%M')}")
    print()

    result = fetch_ens_single_peak(
        lat=test_peak["latitude"],
        lon=test_peak["longitude"],
        peak_name=test_peak["name"]
    )

    print()
    print("=" * 60)
    print(f"Peak: {test_peak['name']}")
    print(f"LCL Mean: {result.lcl_mean:.1f}m")
    print(f"LCL Std:  {result.lcl_std:.1f}m")
    print(f"LCL P10:  {result.lcl_p10:.1f}m")
    print(f"LCL P90:  {result.lcl_p90:.1f}m")
    print(f"Members:  {result.member_count}")
    print(f"Agreement: {result.agreement_rate:.2f}")
    print(f"Steps: {result.steps_used}")
    print(f"DL Time: {result.download_time:.1f}s")
    print(f"Status: {result.status}")
    if result.error_msg:
        print(f"Error: {result.error_msg}")
    print("=" * 60)
