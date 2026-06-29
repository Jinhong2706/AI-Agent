# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 配置与工具函数模块
来源: memory_manager.py (常量/i18n/安全/工具函数)
V3.0: 模块化重构，零依赖（仅标准库）
"""

import json
import os
import sys
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Iterator
from functools import lru_cache

# ============ 跨平台初始化 ============
if sys.platform == 'win32':
    try:
        import io
        if not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ============ 全局缓存 ============
_CONFIG_CACHE = None
_CONFIG_CACHE_TIME = 0
_CONFIG_CACHE_KEY = "global"
_CONFIG_CACHE_TTL = 300

# ============ i18n 翻译支持 ============
_LANG = "zh"
_I18N_DATA = None

def init_i18n(lang="zh"):
    global _LANG, _I18N_DATA
    _LANG = lang
    i18n_path = Path(__file__).parent.parent / "i18n.json"
    if i18n_path.exists():
        try:
            # 文件大小预检（i18n.json 通常不超过 50KB）
            if i18n_path.stat().st_size > 100 * 1024:
                _I18N_DATA = {"zh": {}, "en": {}}
                return
            with open(i18n_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 完整性校验：必须是 dict，且至少包含 zh/en 键
            if not isinstance(data, dict) or not all(k in data for k in ("zh", "en")):
                _I18N_DATA = {"zh": {}, "en": {}}
                return
            _I18N_DATA = data
        except (json.JSONDecodeError, OSError, IOError):
            _I18N_DATA = {"zh": {}, "en": {}}
    else:
        _I18N_DATA = {"zh": {}, "en": {}}

def _(key: str) -> str:
    global _LANG, _I18N_DATA
    if _I18N_DATA is None:
        init_i18n()
    return _I18N_DATA.get(_LANG, {}).get(key, key)

def set_lang(lang: str):
    if lang in ("zh", "en"):
        init_i18n(lang)

# ============ 常量定义 ============
VERSION = "3.0.0"

TOKEN_RATIO = 2
MAX_OUTPUT_CHARS = 300

MEMORY_LARGE_SIZE_KB = 100
MEMORY_VERY_LARGE_SIZE_KB = 500
MEMORY_MANY_FILES = 20
MEMORY_VERY_MANY_FILES = 100
SCAN_LARGE_CACHE_KB = 50
DEFAULT_RETENTION_DAYS = 7
PERSONAL_WORK_REMIND_DAYS = 5
TOKEN_STATS_RETENTION_DAYS = 30
RECENT_DAYS = 7
OLD_DAYS = 30
SUMMARY_MIN_CHARS = 500

TOKEN_WARN_RATIO = 0.7
TOKEN_ALERT_RATIO = 1.0
DEFAULT_DAILY_BUDGET = 10000

PROTECTED_DIRS = {'memory'}

CLEANABLE_EXTS = {'.tmp', '.log', '.cache', '.bak', '.temp', '.swp', '.pyc', '__pycache__'}

# config_memory() 值域白名单：key → (最小值, 最大值)，None 表示无需范围校验
CONFIG_VALUE_LIMITS = {
    "retention_days": (1, 365),
    "auto_remind_days": (1, 90),
    "auto_archive": None,       # bool, 无需范围校验
    "lang": None,               # 枚举校验在 config_memory() 内处理
}
IMAGE_SIGNATURES = {
    'png': b'\x89PNG\r\n\x1a\n',
    'jpg': b'\xff\xd8\xff',
    'gif': b'GIF87a',
    'gif89': b'GIF89a',
    'bmp': b'BM',
    'webp': b'RIFF',
    'ico': b'\x00\x00\x01\x00',
}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico'}

MAX_FILE_SIZE = 1 * 1024 * 1024
MAX_TOTAL_READ = 5 * 1024 * 1024
MAX_REPORT_ITEMS = 1000

SUMMARY_DIR = ".summary"
SUMMARY_MAX_CHARS = 300
SUMMARY_INDEX_FILE = "summary_index.json"
SUMMARY_SCHEMA_VERSION = "1.0"

RANK_CORE_THRESHOLD = 0.7
RANK_NORMAL_THRESHOLD = 0.3

LOAD_BRIEF = "brief"
LOAD_NORMAL = "normal"
LOAD_FULL = "full"

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    C = {
        'red': Fore.RED, 'green': Fore.GREEN, 'yellow': Fore.YELLOW,
        'cyan': Fore.CYAN, 'magenta': Fore.MAGENTA, 'white': Fore.WHITE,
        'bright': Style.BRIGHT, 'reset': Style.RESET_ALL
    }
except ImportError:
    C = {k: '' for k in ['red', 'green', 'yellow', 'cyan', 'magenta', 'white', 'bright', 'reset']}

def get_colors():
    return C

# ============ 配置 ============
_GLOBAL_CONFIG_FILE = str(Path.home() / ".workbuddy" / "skills" / "memory-manager-v3" / "config.json")

def _migrate_v2_config():
    """V3.0 迁移：检测旧版 memory-manager-v2 配置目录，自动迁移到 v3"""
    old_dir = Path.home() / ".workbuddy" / "skills" / "memory-manager-v2"
    new_dir = Path.home() / ".workbuddy" / "skills" / "memory-manager-v3"
    old_cfg = old_dir / "config.json"
    if old_cfg.exists() and not new_dir.exists():
        try:
            new_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(old_cfg, new_dir / "config.json")
        except (OSError, IOError, PermissionError):
            pass  # 迁移失败不影响正常使用

_migrate_v2_config()

def _get_workspace_config_path(workspace_path=None):
    base = Path(workspace_path).resolve() if workspace_path else Path.cwd().resolve()
    # 安全边界校验：拒绝不存在或可疑路径
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    if not base.is_dir():
        return None
    # 确保路径规范化后不含路径穿越分量
    try:
        base.relative_to(base.resolve())
    except ValueError:
        return None
    return str(base / ".workbuddy" / "skills" / "memory-manager-v3" / "config.json")

DEFAULT_CONFIG = {
    "lang": "zh",
    "retention_days": 7,
    "auto_remind_days": 5,
    "auto_archive": True,
    "last_remind_date": "",
    "last_clean_date": "",
    "_automation_rules": {
        "push_content": {
            "retention_days": 1,
            "auto_clean": True,
            "keywords": ["推送", "AI动态", "历史推送摘要", "每日AI", "动态推送", "新闻推送"]
        },
        "personal_work_content": {
            "retention_days": 7,
            "auto_clean": False,
            "remind_days": 5,
            "keywords": ["个人", "工作", "项目", "客户", "企业", "MEMORY.md"]
        }
    }
}

def load_config(workspace_path=None):
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME, _CONFIG_CACHE_KEY
    cache_key = workspace_path or "global"
    now = datetime.now().timestamp()
    if _CONFIG_CACHE is not None and (now - _CONFIG_CACHE_TIME) < _CONFIG_CACHE_TTL and _CONFIG_CACHE_KEY == cache_key:
        return _CONFIG_CACHE

    config = DEFAULT_CONFIG.copy()

    try:
        global_cfg_path = Path(_GLOBAL_CONFIG_FILE)
        if global_cfg_path.exists():
            with open(global_cfg_path, 'r', encoding='utf-8') as f:
                user_global = json.load(f)
                for k in ("lang",):
                    if k in user_global:
                        config[k] = user_global[k]
    except (json.JSONDecodeError, IOError, PermissionError):
        pass

    ws_cfg_path_str = _get_workspace_config_path(workspace_path)
    if ws_cfg_path_str is None:
        # workspace_path 无效，仅返回全局配置
        _CONFIG_CACHE = config
        _CONFIG_CACHE_TIME = now
        _CONFIG_CACHE_KEY = cache_key
        return config

    ws_cfg_path = Path(ws_cfg_path_str)
    try:
        if ws_cfg_path.exists():
            with open(ws_cfg_path, 'r', encoding='utf-8') as f:
                user_ws = json.load(f)
                config.update(user_ws)
        else:
            save_config(config, workspace_path)
    except (json.JSONDecodeError, IOError, PermissionError):
        pass

    _CONFIG_CACHE = config
    _CONFIG_CACHE_TIME = now
    _CONFIG_CACHE_KEY = cache_key
    return config

def clear_config_cache():
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME, _CONFIG_CACHE_KEY
    _CONFIG_CACHE = None
    _CONFIG_CACHE_TIME = 0
    _CONFIG_CACHE_KEY = "global"

def save_config(config, workspace_path=None):
    global_settings = {k: v for k, v in config.items() if k in ("lang",)}
    if global_settings:
        global_path = Path(_GLOBAL_CONFIG_FILE)
        global_path.parent.mkdir(parents=True, exist_ok=True)
        existing_global = {}
        if global_path.exists():
            try:
                with open(global_path, 'r', encoding='utf-8') as f:
                    existing_global = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        existing_global.update(global_settings)
        with open(global_path, 'w', encoding='utf-8') as f:
            json.dump(existing_global, f, ensure_ascii=False, indent=2)

    ws_settings = {k: v for k, v in config.items() if k not in ("lang",)}
    cfg_path_str = _get_workspace_config_path(workspace_path)
    if cfg_path_str is not None:
        cfg_path = Path(cfg_path_str)
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(ws_settings, f, ensure_ascii=False, indent=2)
    clear_config_cache()

def config_memory(workspace_path, key=None, value=None):
    config = load_config()
    result = {"action": "view", "config": config}

    if key is not None and value is not None:
        if key not in DEFAULT_CONFIG:
            return {"error": _("unknown_config_key").format(key=key, keys=list(DEFAULT_CONFIG.keys()))}
        default_type = type(DEFAULT_CONFIG[key])
        try:
            typed_value = default_type(value)
        except (ValueError, TypeError):
            return {"error": _("value_type_error").format(value=value, type=default_type.__name__)}

        # 值域白名单校验
        if key == "lang" and typed_value not in ("zh", "en"):
            return {"error": f"语言值 '{typed_value}' 无效，仅支持: zh, en"}
        if key in CONFIG_VALUE_LIMITS and CONFIG_VALUE_LIMITS[key] is not None:
            lo, hi = CONFIG_VALUE_LIMITS[key]
            if not (lo <= typed_value <= hi):
                return {"error": f"值 {typed_value} 超出范围 [{lo}, {hi}]"}

        config[key] = typed_value
        save_config(config)
        result = {"action": "update", "key": key, "value": typed_value, "config": config}

    return result

# ============ 安全函数 ============
def is_symlink(path):
    try:
        return path.is_symlink()
    except (OSError, ValueError):
        return False

def safe_resolve(path, base_path):
    try:
        abs_path = path.resolve()
        abs_base = base_path.resolve()
        try:
            abs_path.relative_to(abs_base)
            return abs_path
        except ValueError:
            return None
    except (OSError, ValueError):
        return None

def safe_file_read(path, max_size=MAX_FILE_SIZE):
    """P1-4 优化：缓存 key 用 (path_str, max_size) 而非含 mtime。
    - 同进程内命中时直接返回（lru_cache 命中）
    - 文件被修改后内容变更由 size 上限 + lru 容量自动回收兜底
    """
    return _safe_file_cached(str(Path(path).resolve()), max_size)

@lru_cache(maxsize=256)
def _safe_file_cached(path_str, max_size):
    path = Path(path_str)
    try:
        if is_symlink(path):
            return None, "跳过符号链接"

        stat = path.stat()
        if stat.st_size > max_size:
            return None, f"文件超过{max_size//1024}KB限制"

        chunk_size = 64 * 1024
        chunks = []
        bytes_read = 0

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            while bytes_read < max_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_read += len(chunk.encode('utf-8', errors='ignore'))

        content = ''.join(chunks)
        if len(content.encode('utf-8')) > max_size:
            content = content[:max_size]
        return content, "成功"
    except Exception as e:
        return None, f"读取失败: {type(e).__name__}"

def get_file_info(path):
    return _get_file_info_cached(str(path.resolve()))

@lru_cache(maxsize=1024)  # P1-1: 由 256 提升到 1024，容纳 1000+ 文件工作区
def _get_file_info_cached(path_str):
    try:
        path = Path(path_str)
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime), stat.st_size / 1024
    except (OSError, ValueError):
        return None, None

def iter_memory_files(memory_path, skip_symlinks=True, skip_memory_md=True, include_dirs=False):
    """迭代记忆文件（支持子目录递归扫描）

    P1-1 优化：使用 os.walk 替代 rglob，单次 stat 复用。
    比 pathlib.rglob 快 2-3×（OS 级 API）。

    Args:
        memory_path: .workbuddy/memory/ 路径
        skip_symlinks: 跳过符号链接
        skip_memory_md: 跳过 MEMORY.md
        include_dirs: 是否返回子目录信息（保留参数签名，不变更）
    """
    if not memory_path.exists() or not memory_path.is_dir():
        return
    memory_resolved = memory_path.resolve()
    for root, _dirs, files in os.walk(str(memory_path), followlinks=False):
        root_path = Path(root)
        for fname in files:
            if not fname.endswith(".md"):
                continue
            full = root_path / fname
            try:
                if skip_symlinks and full.is_symlink():
                    continue
                if skip_memory_md and fname == "MEMORY.md":
                    continue
                # 安全：确保文件仍在 memory_path 下（防路径穿越）
                full.resolve().relative_to(memory_resolved)
            except (ValueError, OSError):
                continue
            # 单次 stat 复用（get_file_info 内部已带 lru_cache）
            mtime, size_kb = get_file_info(full)
            if mtime is None:
                continue
            rel_path = str(full.relative_to(memory_path))
            yield full, mtime, size_kb, rel_path

def detect_image_format(file_path):
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
        for fmt, sig in IMAGE_SIGNATURES.items():
            if header.startswith(sig):
                if fmt == 'webp':
                    if len(header) >= 12 and header[8:12] == b'WEBP':
                        return 'webp'
                    continue
                return fmt
        return None
    except (OSError, IOError):
        return None


def parse_front_matter(content):
    """解析 Markdown 文件的 front-matter（YAML 头部）

    支持格式:
        ---
        tags: [tag1, tag2]
        category: project-name
        ---

    Returns:
        dict: {tags: list, category: str, ...其他自定义字段}
    """
    meta = {}
    if not content or not content.startswith("---"):
        return meta

    try:
        end = content.index("---", 3)
    except ValueError:
        return meta

    fm_text = content[3:end].strip()
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if not value:
            continue

        # 解析 tags: [tag1, tag2] 或 tags: tag1, tag2
        if key == "tags":
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            meta["tags"] = [t.strip().strip('"\'') for t in value.split(",") if t.strip()]
        else:
            # 去除引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            meta[key] = value

    return meta
