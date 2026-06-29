#!/usr/bin/env python3
"""
Skill Security Audit Scanner
Detects malicious patterns in Claude/OpenClaw skills based on SlowMist threat intelligence.
Pure stdlib implementation — zero external dependencies.
"""

import argparse
import base64
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from pathlib import Path
from typing import Optional


# ─── Severity ────────────────────────────────────────────────────────────────

class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self):
        return self.name


# ─── Finding ─────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    detector: str
    severity: Severity
    category: str
    file_path: str
    line_number: int
    line_content: str
    description: str
    confidence: int  # 0-100

    def to_dict(self):
        d = asdict(self)
        d["severity"] = str(self.severity)
        return d


# ─── IOC Database ────────────────────────────────────────────────────────────

class IOCDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "ioc_database.json")
        self.ips: set[str] = set()
        self.domains: set[str] = set()
        self.url_patterns: list[re.Pattern] = []
        self.hashes: set[str] = set()
        self._load(db_path)

    def _load(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Could not load IOC database ({path}): {e}", file=sys.stderr)
            return
        for entry in data.get("malicious_ips", []):
            self.ips.add(entry["ip"])
        for entry in data.get("malicious_domains", []):
            self.domains.add(entry["domain"])
        for entry in data.get("malicious_url_patterns", []):
            try:
                self.url_patterns.append(re.compile(entry["pattern"]))
            except re.error:
                pass
        for entry in data.get("malicious_hashes", []):
            self.hashes.add(entry["sha256"].lower())


# ─── Skill Discovery ────────────────────────────────────────────────────────

SKIP_DIRS = {"venv", "node_modules", ".git", "__pycache__", ".mypy_cache", ".tox", "dist", "build", ".egg-info"}
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash", ".zsh",
    ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".rb", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
    ".html", ".css", ".xml", ".svg", ".env", ".plist",
    ".ps1", ".bat", ".cmd", ".mjs", ".cjs",
}
MAX_FILE_SIZE = 1_000_000  # 1 MB
MAX_FILES_PER_SKILL = 1000


class SkillDiscovery:
    def __init__(self):
        self.skill_dirs: list[Path] = []

    def discover(self) -> list[dict]:
        """Return list of {'name': str, 'path': Path, 'files': list[Path]}."""
        home = Path.home()

        search_roots = [
            home / ".cursor" / "skills",
            home / ".claude" / "skills",
            home / ".openclaw" / "workspace" / "skills",
        ]

        cwd = Path.cwd()
        for project_dir in [
            cwd / ".cursor" / "skills",
            cwd / ".claude" / "skills",
            cwd / ".agents" / "skills",
            cwd / ".codebuddy" / "skills",
        ]:
            if project_dir.is_dir():
                search_roots.append(project_dir)

        skills = []
        seen_paths = set()

        for root in search_roots:
            if not root.is_dir():
                continue
            # Each immediate subdirectory is a skill
            for child in sorted(root.iterdir()):
                if child.is_dir() and child.resolve() not in seen_paths:
                    seen_paths.add(child.resolve())
                    files = self._collect_files(child)
                    skills.append({
                        "name": child.name,
                        "path": child,
                        "files": files,
                    })

        return skills

    def discover_single(self, path: str) -> list[dict]:
        """Scan a single path as one skill."""
        p = Path(path).resolve()
        if not p.is_dir():
            print(f"[ERROR] Not a directory: {p}", file=sys.stderr)
            return []
        files = self._collect_files(p)
        return [{"name": p.name, "path": p, "files": files}]

    def _collect_files(self, root: Path) -> list[Path]:
        files = []
        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune skipped directories
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if count >= MAX_FILES_PER_SKILL:
                    return files
                fp = Path(dirpath) / fname
                if fp.suffix.lower() in TEXT_EXTENSIONS and fp.stat().st_size <= MAX_FILE_SIZE:
                    files.append(fp)
                    count += 1
        return files


# ─── Detectors ───────────────────────────────────────────────────────────────

class BaseDetector:
    name: str = "BaseDetector"
    category: str = "generic"

    def scan_line(self, line: str, line_num: int, file_path: str) -> list[Finding]:
        return []

    def scan_file(self, content: str, file_path: str) -> list[Finding]:
        """Optional whole-file scan. Default: per-line scan."""
        findings = []
        for i, line in enumerate(content.splitlines(), 1):
            findings.extend(self.scan_line(line, i, file_path))
        return findings


class Base64Detector(BaseDetector):
    name = "Base64Detector"
    category = "obfuscation"
    _pattern = re.compile(r'[A-Za-z0-9+/]{50,}={0,2}')
    _image_prefix = re.compile(r'data:image/')

    # Skip integrity hashes, SHA256 hex strings, and lock files
    _skip_patterns = re.compile(r'"integrity"\s*:|"sha256"\s*:|"sha512-|"sha384-|"sha1-')

    def scan_line(self, line, line_num, file_path):
        findings = []
        if self._image_prefix.search(line):
            return findings
        basename = os.path.basename(file_path)
        if basename in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
            return findings
        if self._skip_patterns.search(line):
            return findings
        for m in self._pattern.finditer(line):
            blob = m.group()
            # Verify it decodes
            try:
                decoded = base64.b64decode(blob)
                # Check if it looks like binary or text with suspicious content
                try:
                    text = decoded.decode("utf-8", errors="strict")
                    suspicious_kw = any(kw in text.lower() for kw in [
                        "exec", "eval", "import", "subprocess", "os.system",
                        "curl", "wget", "bash", "/bin/sh", "socket",
                    ])
                    severity = Severity.HIGH if suspicious_kw else Severity.MEDIUM
                    confidence = 85 if suspicious_kw else 50
                except UnicodeDecodeError:
                    severity = Severity.MEDIUM
                    confidence = 40
            except Exception:
                continue

            findings.append(Finding(
                detector=self.name, severity=severity, category=self.category,
                file_path=file_path, line_number=line_num,
                line_content=line.strip()[:200],
                description=f"Base64-encoded string ({len(blob)} chars) detected",
                confidence=confidence,
            ))
        return findings


class DownloadExecDetector(BaseDetector):
    name = "DownloadExecDetector"
    category = "code_execution"
    _patterns = [
        (re.compile(r'curl\s+.*\|\s*(ba)?sh', re.IGNORECASE), "curl pipe to shell", 95),
        (re.compile(r'wget\s+.*\|\s*(ba)?sh', re.IGNORECASE), "wget pipe to shell", 95),
        (re.compile(r'curl\s+.*-o\s+\S+.*&&\s*(ba)?sh', re.IGNORECASE), "curl download then execute", 90),
        (re.compile(r'wget\s+.*-O\s+\S+.*&&\s*(ba)?sh', re.IGNORECASE), "wget download then execute", 90),
        (re.compile(r'curl\s+.*\|\s*python', re.IGNORECASE), "curl pipe to python", 90),
        (re.compile(r'wget\s+.*\|\s*python', re.IGNORECASE), "wget pipe to python", 90),
        (re.compile(r'fetch\s*\(.*\).*\.then\(.*eval', re.IGNORECASE), "fetch + eval (JS)", 85),
        (re.compile(r'urllib\.request\.urlopen\(.*\).*exec\(', re.IGNORECASE), "urllib + exec (Python)", 85),
    ]

    def scan_line(self, line, line_num, file_path):
        findings = []
        for pat, desc, confidence in self._patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.CRITICAL, category=self.category,
                    file_path=file_path, line_number=line_num,
                    line_content=line.strip()[:200],
                    description=f"Download-and-execute pattern: {desc}",
                    confidence=confidence,
                ))
        return findings


class IOCMatchDetector(BaseDetector):
    name = "IOCMatchDetector"
    category = "threat_intelligence"

    def __init__(self, ioc_db: IOCDatabase):
        self.ioc_db = ioc_db

    def scan_line(self, line, line_num, file_path):
        findings = []
        for ip in self.ioc_db.ips:
            if ip in line:
                findings.append(Finding(
                    detector=self.name, severity=Severity.CRITICAL,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Known malicious IP address: {ip}",
                    confidence=95,
                ))
        for domain in self.ioc_db.domains:
            if domain in line:
                findings.append(Finding(
                    detector=self.name, severity=Severity.CRITICAL,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Known malicious domain: {domain}",
                    confidence=95,
                ))
        for pat in self.ioc_db.url_patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.CRITICAL,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Matches malicious URL pattern: {pat.pattern}",
                    confidence=90,
                ))
        return findings


class ObfuscationDetector(BaseDetector):
    name = "ObfuscationDetector"
    category = "obfuscation"
    _patterns = [
        (re.compile(r'\beval\s*\(\s*[^"\'`\d]'), "eval() with non-literal argument", 80),
        (re.compile(r'(?<!\.)exec\s*\(\s*[^"\'`\d]'), "exec() with non-literal argument", 80),
        (re.compile(r'\\x[0-9a-fA-F]{2}(\\x[0-9a-fA-F]{2}){5,}'), "Hex-encoded string sequence", 70),
        (re.compile(r'chr\s*\(\s*\d+\s*\)\s*\+\s*chr\s*\(\s*\d+\s*\)(\s*\+\s*chr\s*\(\s*\d+\s*\)){3,}'), "chr() chain concatenation", 85),
        (re.compile(r'\[::\s*-1\s*\]'), "String reversal (Python slice)", 45),
        (re.compile(r'\.split\s*\(\s*["\'].*["\']\s*\)\s*\.reverse\s*\(\s*\)\s*\.join'), "String split-reverse-join (JS)", 60),
        (re.compile(r'String\.fromCharCode\s*\(.*,.*,.*,.*\)'), "String.fromCharCode with multiple args", 70),
        (re.compile(r'atob\s*\(\s*[^)]{20,}\s*\)'), "atob() with long encoded string", 65),
    ]

    def scan_line(self, line, line_num, file_path):
        findings = []
        for pat, desc, confidence in self._patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.HIGH,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Obfuscation technique: {desc}",
                    confidence=confidence,
                ))
        return findings


class ExfiltrationDetector(BaseDetector):
    name = "ExfiltrationDetector"
    category = "data_exfiltration"
    _patterns = [
        (re.compile(r'zipfile.*write|ZipFile\(.*,\s*["\']w["\']', re.IGNORECASE), "ZIP archive creation for potential exfiltration", 55),
        (re.compile(r'shutil\.(make_archive|copytree)'), "Archive/copy operations", 40),
        (re.compile(r'(\.ssh|\.aws|\.gnupg|\.config|\.env)', re.IGNORECASE), None, None),  # handled below
        (re.compile(r'glob\.(glob|iglob)\s*\(\s*["\'].*(\*\*|/home|~)'), "Recursive file enumeration of sensitive directories", 60),
    ]
    _sensitive_dir_pattern = re.compile(r'(\.ssh|\.aws|\.gnupg|\.kube|\.config/gcloud|\.npmrc|\.pypirc)')
    _upload_pattern = re.compile(r'(requests\.(post|put)|urllib\.request\.(urlopen|Request)|http\.client|fetch\s*\(|\.upload)', re.IGNORECASE)

    def scan_file(self, content, file_path):
        findings = []
        lines = content.splitlines()
        has_sensitive_dir = False
        has_upload = False
        sensitive_lines = []
        upload_lines = []

        for i, line in enumerate(lines, 1):
            if self._sensitive_dir_pattern.search(line):
                has_sensitive_dir = True
                sensitive_lines.append((i, line))
            if self._upload_pattern.search(line):
                has_upload = True
                upload_lines.append((i, line))

        # ZIP + upload combo
        for i, line in enumerate(lines, 1):
            if re.search(r'zipfile|ZipFile|make_archive', line, re.IGNORECASE):
                if has_upload:
                    findings.append(Finding(
                        detector=self.name, severity=Severity.HIGH,
                        category=self.category, file_path=file_path,
                        line_number=i, line_content=line.strip()[:200],
                        description="ZIP archive creation combined with upload capability — possible data exfiltration",
                        confidence=75,
                    ))
            if re.search(r'glob\.(glob|iglob)\s*\(\s*["\'].*(\*\*|/home|~)', line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.HIGH,
                    category=self.category, file_path=file_path,
                    line_number=i, line_content=line.strip()[:200],
                    description="Recursive file enumeration of sensitive directories",
                    confidence=60,
                ))

        if has_sensitive_dir and has_upload:
            ln, lc = sensitive_lines[0]
            findings.append(Finding(
                detector=self.name, severity=Severity.HIGH,
                category=self.category, file_path=file_path,
                line_number=ln, line_content=lc.strip()[:200],
                description="Access to sensitive directories combined with network upload capability",
                confidence=70,
            ))

        return findings


class CredentialTheftDetector(BaseDetector):
    name = "CredentialTheftDetector"
    category = "credential_theft"
    _patterns = [
        (re.compile(r'osascript.*display\s+dialog.*password', re.IGNORECASE), "macOS password dialog via osascript", 95),
        (re.compile(r'osascript.*display\s+dialog.*hidden\s+answer', re.IGNORECASE), "macOS hidden-input dialog (password phishing)", 95),
        (re.compile(r'security\s+find-(generic|internet)-password', re.IGNORECASE), "macOS Keychain password extraction", 90),
        (re.compile(r'security\s+dump-keychain', re.IGNORECASE), "macOS Keychain dump", 95),
        (re.compile(r'cat\s+.*\.ssh/(id_rsa|id_ed25519|id_ecdsa)', re.IGNORECASE), "SSH private key reading", 90),
        (re.compile(r'(open|cat|read).*\.ssh/id_', re.IGNORECASE), "SSH private key access", 85),
        (re.compile(r'cat\s+.*\.(env|npmrc|pypirc|netrc|aws/credentials)', re.IGNORECASE), "Credential file reading", 85),
        (re.compile(r'Cookies/Cookies\.binarycookies|Login\s*Data|cookies\.sqlite', re.IGNORECASE), "Browser credential/cookie access", 90),
    ]

    def scan_line(self, line, line_num, file_path):
        findings = []
        for pat, desc, confidence in self._patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.CRITICAL,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Credential theft technique: {desc}",
                    confidence=confidence,
                ))
        return findings


class PersistenceDetector(BaseDetector):
    name = "PersistenceDetector"
    category = "persistence"
    _patterns = [
        (re.compile(r'crontab\s+(-[el]|-)'), "crontab modification", 70),
        (re.compile(r'(>>|>)\s*.*crontab|cron\.d/', re.IGNORECASE), "cron job installation", 75),
        (re.compile(r'LaunchAgents|LaunchDaemons|\.plist', re.IGNORECASE), "macOS launchd persistence", 65),
        (re.compile(r'launchctl\s+(load|bootstrap)', re.IGNORECASE), "macOS launchctl loading", 80),
        (re.compile(r'systemctl\s+(enable|start)', re.IGNORECASE), "systemd service enablement", 60),
        (re.compile(r'/etc/systemd/system/.*\.service', re.IGNORECASE), "systemd service file creation", 70),
        (re.compile(r'\.bashrc|\.zshrc|\.profile|\.bash_profile', re.IGNORECASE), None, None),  # context-dependent
        (re.compile(r'HKEY_.*\\Run|CurrentVersion\\Run', re.IGNORECASE), "Windows registry run key persistence", 80),
    ]
    _shell_write_pattern = re.compile(r'(>>|>)\s*.*(\.(bashrc|zshrc|profile|bash_profile))')

    def scan_line(self, line, line_num, file_path):
        findings = []
        for pat, desc, confidence in self._patterns:
            if desc is None:
                continue
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.HIGH,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Persistence mechanism: {desc}",
                    confidence=confidence,
                ))
        if self._shell_write_pattern.search(line):
            findings.append(Finding(
                detector=self.name, severity=Severity.HIGH,
                category=self.category, file_path=file_path,
                line_number=line_num, line_content=line.strip()[:200],
                description="Persistence mechanism: writing to shell profile file",
                confidence=75,
            ))
        return findings


class PostInstallHookDetector(BaseDetector):
    name = "PostInstallHookDetector"
    category = "supply_chain"

    def scan_file(self, content, file_path):
        findings = []
        basename = os.path.basename(file_path)
        lines = content.splitlines()

        # npm package.json postinstall
        if basename == "package.json":
            try:
                pkg = json.loads(content)
                scripts = pkg.get("scripts", {})
                for hook in ("postinstall", "preinstall", "install", "prepare"):
                    if hook in scripts:
                        val = scripts[hook]
                        # Check for suspicious content in hook
                        suspicious = any(kw in val.lower() for kw in [
                            "curl", "wget", "bash", "sh ", "python", "node -e", "eval",
                        ])
                        severity = Severity.CRITICAL if suspicious else Severity.HIGH
                        confidence = 90 if suspicious else 60
                        for i, line in enumerate(lines, 1):
                            if hook in line:
                                findings.append(Finding(
                                    detector=self.name, severity=severity,
                                    category=self.category, file_path=file_path,
                                    line_number=i, line_content=line.strip()[:200],
                                    description=f"npm lifecycle hook '{hook}': {val[:100]}",
                                    confidence=confidence,
                                ))
                                break
            except json.JSONDecodeError:
                pass

        # Python setup.py cmdclass
        if basename == "setup.py":
            for i, line in enumerate(lines, 1):
                if re.search(r'cmdclass\s*=', line):
                    findings.append(Finding(
                        detector=self.name, severity=Severity.HIGH,
                        category=self.category, file_path=file_path,
                        line_number=i, line_content=line.strip()[:200],
                        description="Python setup.py custom command class (potential install hook)",
                        confidence=55,
                    ))

        return findings


class HiddenCharDetector(BaseDetector):
    name = "HiddenCharDetector"
    category = "obfuscation"
    # Zero-width and bidi override characters
    _zwc_pattern = re.compile(r'[\u200b\u200c\u200d\u2060\ufeff]')
    _bidi_pattern = re.compile(r'[\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069]')

    def scan_line(self, line, line_num, file_path):
        findings = []
        if self._zwc_pattern.search(line):
            findings.append(Finding(
                detector=self.name, severity=Severity.MEDIUM,
                category=self.category, file_path=file_path,
                line_number=line_num, line_content=repr(line.strip()[:200]),
                description="Zero-width characters detected (potential code hiding)",
                confidence=60,
            ))
        if self._bidi_pattern.search(line):
            findings.append(Finding(
                detector=self.name, severity=Severity.MEDIUM,
                category=self.category, file_path=file_path,
                line_number=line_num, line_content=repr(line.strip()[:200]),
                description="Unicode bidirectional control characters (Trojan Source attack)",
                confidence=80,
            ))
        return findings


class EntropyDetector(BaseDetector):
    name = "EntropyDetector"
    category = "obfuscation"

    @staticmethod
    def _shannon_entropy(data: str) -> float:
        if not data:
            return 0.0
        freq = {}
        for c in data:
            freq[c] = freq.get(c, 0) + 1
        length = len(data)
        return -sum((count / length) * math.log2(count / length) for count in freq.values())

    def scan_line(self, line, line_num, file_path):
        stripped = line.strip()
        if len(stripped) < 100:
            return []
        # Skip lines that are obviously data URIs or comments
        if stripped.startswith(("data:", "//", "#", "/*", "*")):
            return []
        # Skip lock files entirely (integrity hashes are expected high entropy)
        basename = os.path.basename(file_path)
        if basename in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "Gemfile.lock", "poetry.lock"):
            return []
        # CJK characters and markdown naturally have higher entropy; raise threshold
        ext = os.path.splitext(file_path)[1].lower()
        has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7af' for c in stripped[:50])
        threshold = 6.5 if (has_cjk or ext in ('.md', '.txt')) else 5.5
        entropy = self._shannon_entropy(stripped)
        if entropy > threshold:
            return [Finding(
                detector=self.name, severity=Severity.MEDIUM,
                category=self.category, file_path=file_path,
                line_number=line_num, line_content=stripped[:200],
                description=f"High entropy line (Shannon entropy: {entropy:.2f}) — possible encoded/encrypted payload",
                confidence=max(30, min(80, int((entropy - 5.5) * 40 + 30))),
            )]
        return []


class SocialEngineeringDetector(BaseDetector):
    name = "SocialEngineeringDetector"
    category = "social_engineering"
    _suspicious_names = re.compile(
        r'(crypto[_-]?wallet|airdrop|free[_-]?token|security[_-]?update|urgent[_-]?fix|'
        r'claim[_-]?reward|bonus[_-]?token|wallet[_-]?connect|seed[_-]?phrase|'
        r'private[_-]?key[_-]?recovery|metamask[_-]?fix)',
        re.IGNORECASE,
    )
    _filename_suspicious = re.compile(
        r'(wallet|airdrop|claim|reward|metamask|seed|recovery|token[_-]?gen)',
        re.IGNORECASE,
    )

    def scan_file(self, content, file_path):
        findings = []
        basename = os.path.basename(file_path)
        if self._filename_suspicious.search(basename):
            findings.append(Finding(
                detector=self.name, severity=Severity.MEDIUM,
                category=self.category, file_path=file_path,
                line_number=0, line_content=basename,
                description=f"Suspicious filename associated with social engineering: {basename}",
                confidence=50,
            ))
        for i, line in enumerate(content.splitlines(), 1):
            if self._suspicious_names.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.LOW,
                    category=self.category, file_path=file_path,
                    line_number=i, line_content=line.strip()[:200],
                    description="Social engineering keyword detected (crypto/wallet/airdrop related)",
                    confidence=35,
                ))
                break  # Only report once per file to avoid noise
        return findings


class NetworkCallDetector(BaseDetector):
    name = "NetworkCallDetector"
    category = "network_access"
    _patterns = [
        (re.compile(r'\bsocket\.(socket|connect|create_connection)\b'), "Python socket usage", 50),
        (re.compile(r'\bhttp\.client\.(HTTPConnection|HTTPSConnection)\b'), "Python http.client usage", 40),
        (re.compile(r'\burllib\.request\.(urlopen|Request)\b'), "Python urllib usage", 40),
        (re.compile(r'\brequests\.(get|post|put|delete|patch|head)\s*\('), "Python requests library", 35),
        (re.compile(r'\bfetch\s*\(\s*["\']https?://'), "JavaScript fetch() call", 35),
        (re.compile(r'\bXMLHttpRequest\b'), "XMLHttpRequest usage", 35),
        (re.compile(r'\baxios\.(get|post|put|delete|patch)\s*\('), "axios HTTP call", 35),
        (re.compile(r'\bcurl\s+-'), "curl command invocation", 45),
        (re.compile(r'\bwget\s+'), "wget command invocation", 45),
        (re.compile(r'\bnet\.createConnection\b|require\s*\(\s*["\']net["\']\s*\)'), "Node.js net module", 50),
    ]

    def scan_line(self, line, line_num, file_path):
        findings = []
        for pat, desc, confidence in self._patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.MEDIUM,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Network call detected: {desc}",
                    confidence=confidence,
                ))
        return findings


class PrivilegeEscalationDetector(BaseDetector):
    name = "PrivilegeEscalationDetector"
    category = "privilege_escalation"
    # Only flag in executable files, not docs
    _doc_extensions = {'.md', '.txt', '.rst', '.adoc'}
    _patterns = [
        (re.compile(r'\bsudo\s+'), "sudo invocation", 65),
        (re.compile(r'chmod\s+777\b'), "chmod 777 (world-writable)", 80),
        (re.compile(r'chmod\s+[0-7]*[4-7][0-7]{2}\s'), "chmod with setuid/setgid bit", 70),
        (re.compile(r'chmod\s+\+s\b'), "chmod +s (setuid)", 85),
        (re.compile(r'chown\s+root\b'), "chown to root", 70),
        (re.compile(r'os\.setuid\s*\(|os\.setgid\s*\('), "Python setuid/setgid call", 85),
        (re.compile(r'dscl\s+\.\s+-append\s+/Groups/admin'), "macOS admin group modification", 90),
    ]

    def scan_line(self, line, line_num, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self._doc_extensions:
            return []
        findings = []
        for pat, desc, confidence in self._patterns:
            if pat.search(line):
                findings.append(Finding(
                    detector=self.name, severity=Severity.HIGH,
                    category=self.category, file_path=file_path,
                    line_number=line_num, line_content=line.strip()[:200],
                    description=f"Privilege escalation: {desc}",
                    confidence=confidence,
                ))
        return findings


# ─── Scanner ─────────────────────────────────────────────────────────────────

class SkillScanner:
    def __init__(self, ioc_db: IOCDatabase):
        self.ioc_db = ioc_db
        self.detectors: list[BaseDetector] = [
            Base64Detector(),
            DownloadExecDetector(),
            IOCMatchDetector(ioc_db),
            ObfuscationDetector(),
            ExfiltrationDetector(),
            CredentialTheftDetector(),
            PersistenceDetector(),
            PostInstallHookDetector(),
            HiddenCharDetector(),
            EntropyDetector(),
            SocialEngineeringDetector(),
            NetworkCallDetector(),
            PrivilegeEscalationDetector(),
        ]

    def scan_skill(self, skill: dict) -> list[Finding]:
        all_findings = []
        for fp in skill["files"]:
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError) as e:
                print(f"[WARN] Cannot read {fp}: {e}", file=sys.stderr)
                continue

            # File hash check
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if file_hash in self.ioc_db.hashes:
                all_findings.append(Finding(
                    detector="IOCMatchDetector", severity=Severity.CRITICAL,
                    category="threat_intelligence", file_path=str(fp),
                    line_number=0, line_content="(file hash match)",
                    description=f"File SHA256 matches known malicious hash: {file_hash}",
                    confidence=99,
                ))

            for detector in self.detectors:
                try:
                    findings = detector.scan_file(content, str(fp))
                    all_findings.extend(findings)
                except Exception as e:
                    print(f"[WARN] Detector {detector.name} failed on {fp}: {e}", file=sys.stderr)

        return all_findings


# ─── Report Formatting ───────────────────────────────────────────────────────

SEVERITY_COLORS = {
    Severity.LOW: "\033[90m",       # gray
    Severity.MEDIUM: "\033[33m",    # yellow
    Severity.HIGH: "\033[91m",      # red
    Severity.CRITICAL: "\033[31;1m",  # bold red
}
RESET = "\033[0m"
BOLD = "\033[1m"


def format_text_report(results: dict, use_color: bool = True) -> str:
    lines = []
    total_findings = sum(len(f) for f in results["skills"].values())

    lines.append("")
    lines.append("=" * 70)
    lines.append("  SKILL SECURITY AUDIT REPORT")
    lines.append(f"  Scanned: {results['summary']['skills_scanned']} skills, "
                 f"{results['summary']['files_scanned']} files")
    lines.append("=" * 70)
    lines.append("")

    if total_findings == 0:
        lines.append("  [CLEAN] No security issues detected.")
        lines.append("")
        return "\n".join(lines)

    # Summary counts
    counts = results["summary"]["severity_counts"]
    summary_parts = []
    for sev_name in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        cnt = counts.get(sev_name, 0)
        if cnt > 0:
            if use_color:
                color = SEVERITY_COLORS[Severity[sev_name]]
                summary_parts.append(f"{color}{sev_name}: {cnt}{RESET}")
            else:
                summary_parts.append(f"{sev_name}: {cnt}")
    lines.append("  Summary: " + "  |  ".join(summary_parts))
    lines.append("")

    for skill_name, findings in sorted(results["skills"].items()):
        if not findings:
            continue
        lines.append(f"  {'─' * 66}")
        lines.append(f"  Skill: {BOLD}{skill_name}{RESET}" if use_color else f"  Skill: {skill_name}")
        lines.append(f"  Findings: {len(findings)}")
        lines.append("")

        for f in sorted(findings, key=lambda x: -x["severity_value"]):
            sev = f["severity"]
            if use_color:
                color = SEVERITY_COLORS.get(Severity[sev], "")
                sev_str = f"{color}[{sev}]{RESET}"
            else:
                sev_str = f"[{sev}]"

            rel_path = f["file_path"]
            try:
                rel_path = os.path.relpath(f["file_path"])
            except ValueError:
                pass

            lines.append(f"    {sev_str} {f['detector']}")
            lines.append(f"      File: {rel_path}:{f['line_number']}")
            lines.append(f"      {f['description']}")
            lines.append(f"      Confidence: {f['confidence']}%")
            if f["line_content"]:
                content_preview = f["line_content"][:120]
                lines.append(f"      > {content_preview}")
            lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Skill Security Audit Scanner — detect malicious patterns in Claude/OpenClaw skills",
    )
    parser.add_argument("--path", "-p", help="Scan a single skill directory instead of auto-discovery")
    parser.add_argument("--json", "-j", action="store_true", dest="json_output", help="Output results as JSON")
    parser.add_argument("--severity", "-s",
                        choices=["low", "medium", "high", "critical"],
                        help="Minimum severity level to report")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--ioc-db", help="Path to custom IOC database JSON")
    args = parser.parse_args()

    # Min severity filter
    min_severity = Severity.LOW
    if args.severity:
        min_severity = Severity[args.severity.upper()]

    # Load IOC database
    ioc_db = IOCDatabase(args.ioc_db)

    # Discover skills
    discovery = SkillDiscovery()
    if args.path:
        skills = discovery.discover_single(args.path)
    else:
        skills = discovery.discover()

    if not skills:
        print("[INFO] No skills found to scan.", file=sys.stderr)
        sys.exit(0)

    # Scan
    scanner = SkillScanner(ioc_db)
    results = {
        "skills": {},
        "summary": {
            "skills_scanned": len(skills),
            "files_scanned": 0,
            "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        },
    }

    max_severity = Severity.LOW

    for skill in skills:
        results["summary"]["files_scanned"] += len(skill["files"])
        findings = scanner.scan_skill(skill)

        # Filter by min severity
        findings = [f for f in findings if f.severity >= min_severity]

        # Deduplicate: same detector + file + line
        seen = set()
        deduped = []
        for f in findings:
            key = (f.detector, f.file_path, f.line_number)
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        results["skills"][skill["name"]] = [
            {**f.to_dict(), "severity_value": int(f.severity)}
            for f in deduped
        ]

        for f in deduped:
            results["summary"]["severity_counts"][str(f.severity)] += 1
            if f.severity > max_severity:
                max_severity = f.severity

    # Output
    if args.json_output:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        use_color = not args.no_color and sys.stdout.isatty()
        print(format_text_report(results, use_color=use_color))

    # Exit code
    if max_severity >= Severity.CRITICAL:
        sys.exit(3)
    elif max_severity >= Severity.HIGH:
        sys.exit(2)
    elif max_severity >= Severity.MEDIUM:
        sys.exit(1)
    else:
        total = sum(len(f) for f in results["skills"].values())
        sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Scanner error: {e}", file=sys.stderr)
        sys.exit(4)
