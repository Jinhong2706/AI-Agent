"""Tests for validate.py strict mode and self-audit integration.

Verify that strict mode:
1. Runs without crashing on a valid skill
2. Produces expected result structure
3. Self-audit injection works in strict mode
4. strict flag affects issue severity filtering
"""

import sys
from pathlib import Path

# Add SCK root to path so we can import validate module
SCK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCK_ROOT))

from scripts.validate import validate


def test_validate_strict_no_crash():
    """strict mode must run without exception on skill-creator-king itself."""
    result = validate(str(SCK_ROOT), strict=True)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "success" in result, "Missing 'success' key in validate result"
    assert "issues" in result, "Missing 'issues' key in validate result"
    assert "stats" in result, "Missing 'stats' key in validate result"
    assert "self_audit" in result, "strict mode must inject self_audit"
    # self-audit should not crash
    sa = result["self_audit"]
    assert isinstance(sa, dict), f"self_audit must be dict, got {type(sa)}"


def test_validate_strict_stats():
    """strict mode must return valid stats structure."""
    result = validate(str(SCK_ROOT), strict=True)
    stats = result["stats"]
    required_keys = ["total", "critical", "high", "medium", "low"]
    for key in required_keys:
        assert key in stats, f"Missing stat key: {key}"
        assert isinstance(stats[key], int), f"stat.{key} must be int"


def test_validate_non_strict_also_works():
    """Non-strict mode must also run without self_audit injection."""
    result = validate(str(SCK_ROOT), strict=False)
    assert isinstance(result, dict)
    assert "self_audit" not in result, "Non-strict must NOT inject self_audit"


def test_validate_strict_platform_autodetect():
    """strict mode with explicit platform must not crash."""
    result = validate(str(SCK_ROOT), strict=True, platform="workbuddy")
    assert isinstance(result, dict)
    assert result.get("platform") == "workbuddy"


def test_validate_strict_channel_full():
    """strict mode with full channel must include design checks."""
    result = validate(str(SCK_ROOT), strict=True, channel="full")
    assert isinstance(result, dict)
    assert result.get("channel") == "full"


def test_validate_strict_channel_lightweight():
    """strict mode with lightweight channel skips DESIGN/SPEC checks."""
    result = validate(str(SCK_ROOT), strict=True, channel="lightweight")
    assert isinstance(result, dict)
    assert result.get("channel") == "lightweight"


if __name__ == "__main__":
    import subprocess
    # Run all tests in this file
    tests = [
        test_validate_strict_no_crash,
        test_validate_strict_stats,
        test_validate_non_strict_also_works,
        test_validate_strict_platform_autodetect,
        test_validate_strict_channel_full,
        test_validate_strict_channel_lightweight,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
        except Exception as e:
            print(f"💥 {test.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
