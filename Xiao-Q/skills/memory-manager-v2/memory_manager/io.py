# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - 导入导出备份恢复
来源: memory_manager.py (export/import/backup/restore)
V3.0: 模块化重构
"""

import json
import shutil
import gzip
from datetime import datetime
from pathlib import Path

from .config import (
    VERSION, _, get_colors,
    MAX_FILE_SIZE,
    load_config,
    is_symlink, get_file_info,
)
from .token import compute_content_hash

# ZIP 安全限制常量
MAX_IMPORT_SINGLE_FILE_SIZE = MAX_FILE_SIZE          # 单文件 1MB 上限
MAX_IMPORT_TOTAL_SIZE = 50 * 1024 * 1024             # 解压总大小 50MB 上限
MAX_IMPORT_ENTRIES = 1000                             # ZIP 条目数上限


def export_memories(workspace_path, output_file, encrypt=False, password=None):
    workspace = Path(workspace_path).resolve()
    memory_dir = workspace / ".workbuddy" / "memory"
    output_path = Path(output_file)

    if not memory_dir.exists():
        return {"error": _("memory_dir_not_exist_detail")}

    error_note = _("export_failed") if _("export_failed") != "export_failed" else "Export failed"

    try:
        import zipfile

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for md_file in memory_dir.glob("*.md"):
                if is_symlink(md_file):
                    continue
                safe_name = md_file.relative_to(memory_dir).as_posix()
                zf.write(md_file, arcname=safe_name)

            summary_dir = workspace / ".workbuddy" / ".summary"
            if summary_dir.exists():
                for sum_file in summary_dir.glob("*.summary"):
                    if is_symlink(sum_file):
                        continue
                    safe_name = (".summary/" + sum_file.name)
                    zf.write(sum_file, arcname=safe_name)

        file_size = output_path.stat().st_size

        # P2-6: AES-256-GCM 加密支持
        if encrypt:
            if not password:
                import os as _os
                password = _os.environ.get("MEMORY_MANAGER_PASSWORD", "")
            if not password:
                return {"error": _("encrypt_password_required")}

            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                from cryptography.hazmat.primitives import hashes
                import os as _os

                # 读取原始 ZIP 内容
                with open(output_path, 'rb') as _f:
                    plaintext = _f.read()

                # 生成随机 salt + nonce
                salt = _os.urandom(16)
                nonce = _os.urandom(12)

                # PBKDF2 密钥派生
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,  # AES-256
                    salt=salt,
                    iterations=100000,
                )
                key = kdf.derive(password.encode('utf-8'))

                # AES-256-GCM 加密
                aesgcm = AESGCM(key)
                ciphertext = aesgcm.encrypt(nonce, plaintext, None)

                # 写入 .enc 文件: salt(16) + nonce(12) + ciphertext
                enc_path = output_path.with_suffix(output_path.suffix + ".enc")
                with open(enc_path, 'wb') as _f:
                    _f.write(salt)
                    _f.write(nonce)
                    _f.write(ciphertext)

                # 删除原始未加密 ZIP
                output_path.unlink()

                enc_size = enc_path.stat().st_size
                return {
                    "exported_file": str(enc_path),
                    "size_kb": round(enc_size / 1024, 2),
                    "encrypted": True,
                    "message": _("export_encrypted_success")
                }
            except ImportError:
                return {"error": _("encrypt_dependency_missing")}

        return {
            "exported_file": str(output_path),
            "size_kb": round(file_size / 1024, 2),
            "message": _("export_success")
        }
    except ImportError:
        return {"error": error_note}


def import_memories(workspace_path, input_file):
    workspace = Path(workspace_path).resolve()
    memory_dir = workspace / ".workbuddy" / "memory"
    summary_dir = workspace / ".workbuddy" / ".summary"
    input_path = Path(input_file)

    if not input_path.exists():
        return {"error": _("import_file_not_exist")}

    error_note = _("import_failed") if _("import_failed") != "import_failed" else "Import failed"

    # P2-6: 检测 .enc 加密文件，自动解密
    actual_path = input_path
    temp_decrypted = None
    if input_path.suffix == ".enc":
        password = __import__('os').environ.get("MEMORY_MANAGER_PASSWORD", "")
        if not password:
            return {"error": _("encrypt_password_required")}
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            import tempfile as _tempfile

            with open(input_path, 'rb') as _f:
                data = _f.read()

            if len(data) < 28:  # salt(16) + nonce(12) = 28
                return {"error": _("import_encrypted_corrupted")}

            salt = data[:16]
            nonce = data[16:28]
            ciphertext = data[28:]

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode('utf-8'))
            aesgcm = AESGCM(key)

            try:
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            except Exception:
                return {"error": _("import_decrypt_failed")}

            # 写入临时文件
            temp_decrypted = _tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            temp_decrypted.write(plaintext)
            temp_decrypted.close()
            actual_path = Path(temp_decrypted.name)
        except ImportError:
            return {"error": _("encrypt_dependency_missing")}

    memory_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    try:
        import zipfile

        result = {"imported_files": 0, "imported_summaries": 0, "errors": []}

        with zipfile.ZipFile(str(actual_path), 'r') as zf:
            # ---- ZIP Bomb 防御：预检 ----
            total_compressed = 0
            total_uncompressed = 0
            entry_count = 0
            for member in zf.infolist():
                entry_count += 1
                total_compressed += member.compress_size
                total_uncompressed += member.file_size
                # 单文件大小预检
                if member.file_size > MAX_IMPORT_SINGLE_FILE_SIZE:
                    result["errors"].append(
                        f"安全拒绝: {member.filename} (解压后 {member.file_size // 1024}KB 超过单文件上限)")
            # 总条目数预检
            if entry_count > MAX_IMPORT_ENTRIES:
                return {**result, "error": f"安全拒绝: ZIP 包含 {entry_count} 个条目，超过 {MAX_IMPORT_ENTRIES} 上限"}
            # 解压总大小预检
            if total_uncompressed > MAX_IMPORT_TOTAL_SIZE:
                return {**result, "error":
                    f"安全拒绝: 解压总大小 {total_uncompressed // (1024*1024)}MB 超过 {MAX_IMPORT_TOTAL_SIZE // (1024*1024)}MB 上限"}

            extracted_total = 0  # 实际写入字节数追踪

            for member in zf.infolist():
                raw_name = member.filename

                # V3.0 ZIP Slip 严格防护：多重黑名单检查
                # 1) 拒绝包含路径穿越分量的条目（支持 Unix 和 Windows 路径）
                parts = raw_name.replace('\\', '/').split('/')
                if any(p in ('..', '') and i > 0 for i, p in enumerate(parts)):
                    result["errors"].append(f"安全拒绝: {raw_name} (包含路径穿越分量)")
                    continue
                # 2) 拒绝绝对路径（Unix: 以 / 开头; Windows: 以 X:\ 或 \\ 开头）
                if raw_name.startswith('/') or raw_name.startswith('\\') or (len(raw_name) >= 2 and raw_name[1] == ':'):
                    result["errors"].append(f"安全拒绝: {raw_name} (绝对路径)")
                    continue
                # 3) 规范化分隔符，去除开头斜杠
                safe_path = raw_name.replace('\\', '/').lstrip('/')
                # 4) 拒绝空路径
                if not safe_path or safe_path in ('.', '..'):
                    continue

                # 6) 文件类型白名单：仅允许 .md 和 .summary
                if not (safe_path.endswith('.md') or safe_path.endswith('.summary')):
                    result["errors"].append(f"安全拒绝: {safe_path} (不允许的文件类型)")
                    continue

                if safe_path.startswith('.summary/'):
                    target_dir = summary_dir
                    target_name = safe_path[len('.summary/'):]
                else:
                    target_dir = memory_dir
                    target_name = safe_path

                target_path = target_dir / target_name

                # 5) 最终边界校验：解析后路径必须在工作空间内（防御符号链接逃逸）
                try:
                    resolved = target_path.resolve()
                    resolved.relative_to(workspace)
                except (ValueError, OSError):
                    result["errors"].append(f"安全拒绝: {safe_path} (路径超出工作空间)")
                    continue

                target_path = resolved  # 使用已解析路径
                try:
                    with zf.open(member) as source:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(target_path, 'wb') as dest:
                            # 安全写入 + 字节数追踪（ZIP Bomb 防御）
                            while True:
                                chunk = source.read(64 * 1024)
                                if not chunk:
                                    break
                                extracted_total += len(chunk)
                                if extracted_total > MAX_IMPORT_TOTAL_SIZE:
                                    # 超限：删除已写入的部分文件
                                    try:
                                        target_path.unlink()
                                    except OSError:
                                        pass
                                    result["errors"].append(
                                        f"安全拒绝: 解压总大小超过 {MAX_IMPORT_TOTAL_SIZE // (1024*1024)}MB 限制，导入中断")
                                    return result
                                dest.write(chunk)

                    if target_dir == summary_dir:
                        result["imported_summaries"] += 1
                    else:
                        result["imported_files"] += 1
                except Exception as e:
                    result["errors"].append(f"{target_name}: {str(e)}")

        return result
    except ImportError:
        return {"error": error_note}
    finally:
        # 清理临时解密文件
        if temp_decrypted:
            try:
                Path(temp_decrypted.name).unlink()
            except OSError:
                pass


def backup_memory(workspace_path, backup_path=None, dry_run=True, incremental=True):
    config = load_config()
    bp_cfg = config.get("_backup_config", {})
    if backup_path is None:
        backup_path = bp_cfg.get("local_path", "")
    if not backup_path:
        return {"error": _("backup_config_missing")}
    backup_path = Path(backup_path).resolve()
    base_path = Path(workspace_path).resolve()
    memory_path = base_path / ".workbuddy" / "memory"
    result = {"backup_path": str(backup_path), "files_copied": 0, "files_updated": 0, "total_size_kb": 0}
    if not memory_path.exists():
        result["error"] = _("memory_dir_not_exist")
        return result
    if not dry_run:
        backup_path.mkdir(parents=True, exist_ok=True)
    manifest_file = backup_path / ".backup_manifest.json"
    last_backup = {}
    if manifest_file.exists():
        try:
            last_backup = json.loads(manifest_file.read_text(encoding="utf-8")).get("files", {})
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    # ===== P0-3 优化：在主循环累计 manifest 复用，二次 glob/hash 收敛到 0 =====
    manifest_files = {}  # {rel: {"hash": ..., "size_kb": ...}}
    for md_file in memory_path.glob("*.md"):
        if is_symlink(md_file):
            continue
        mtime, size_kb = get_file_info(md_file)
        if mtime is None:
            continue
        rel = md_file.relative_to(memory_path)
        backup_file = backup_path / rel
        current_hash = compute_content_hash(md_file)
        file_key = str(rel)

        # 写 manifest 时直接复用（不再二次 hash / stat / glob）
        manifest_files[file_key] = {"hash": current_hash, "size_kb": size_kb}

        should_backup = not incremental or file_key not in last_backup or last_backup.get(file_key, {}).get(
            "hash") != current_hash
        if should_backup:
            if dry_run:
                result["files_copied" if file_key not in last_backup else "files_updated"] += 1
                result["total_size_kb"] += size_kb
            else:
                try:
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(md_file, backup_file)
                    result["files_copied" if file_key not in last_backup else "files_updated"] += 1
                    result["total_size_kb"] += size_kb
                except (OSError, IOError, PermissionError):
                    pass
    if not dry_run:
        manifest_file.write_text(
            json.dumps(
                {"last_backup": datetime.now().isoformat(), "files": manifest_files},
                ensure_ascii=False, indent=2
            ),
            encoding="utf-8"
        )
    return result


def restore_backup(workspace_path, backup_path=None, dry_run=True):
    config = load_config()
    bp_cfg = config.get("_backup_config", {})
    if backup_path is None:
        backup_path = bp_cfg.get("local_path", "")
    if not backup_path:
        return {"error": _("backup_config_missing")}
    backup_path = Path(backup_path).resolve()
    manifest_file = backup_path / ".backup_manifest.json"
    if not manifest_file.exists():
        return {"error": _("backup_record_not_exist")}
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {"error": _("backup_record_corrupted")}
    result = {"files_restored": 0}
    for file_key in manifest.get("files", {}):
        src = backup_path / file_key
        dst = Path(workspace_path).resolve() / ".workbuddy" / "memory" / file_key
        if src.exists():
            if dry_run:
                result["files_restored"] += 1
            else:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    result["files_restored"] += 1
                except (OSError, IOError, PermissionError):
                    pass
    return result
