#!/usr/bin/env python3
"""Detect whether a workspace is a supported Backend Forge project root."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def visible_entries(root: Path) -> list[Path]:
    return [path for path in root.iterdir() if not path.name.startswith(".")]


def file_contains(path: Path, needles: tuple[str, ...]) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(needle in text for needle in needles)


def detect(root: Path) -> dict[str, object]:
    if not root.exists() or not root.is_dir():
        return {"root_type": "missing", "forge_enabled": False, "evidence": []}

    entries = visible_entries(root)
    if not entries:
        return {"root_type": "empty_new", "forge_enabled": True, "evidence": ["empty directory"]}

    evidence: list[str] = []

    pom = root / "pom.xml"
    gradle = root / "build.gradle"
    gradle_kts = root / "build.gradle.kts"
    if pom.exists() and file_contains(pom, ("spring-boot", "org.springframework.boot")):
        evidence.append("pom.xml contains Spring Boot dependency")
        return {"root_type": "spring_boot_existing", "forge_enabled": True, "evidence": evidence}
    if (gradle.exists() and file_contains(gradle, ("spring-boot", "org.springframework.boot"))) or (
        gradle_kts.exists() and file_contains(gradle_kts, ("spring-boot", "org.springframework.boot"))
    ):
        evidence.append("Gradle file contains Spring Boot dependency")
        return {"root_type": "spring_boot_existing", "forge_enabled": True, "evidence": evidence}

    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    if (pyproject.exists() and file_contains(pyproject, ("fastapi",))) or (
        requirements.exists() and file_contains(requirements, ("fastapi",))
    ):
        evidence.append("Python dependency file contains FastAPI")
        return {"root_type": "fastapi_existing", "forge_enabled": True, "evidence": evidence}
    if any((root / path).exists() for path in ("main.py", "app/main.py")) and file_contains(
        root / "main.py" if (root / "main.py").exists() else root / "app/main.py",
        ("fastapi", "app = fastapi", "from fastapi"),
    ):
        evidence.append("FastAPI entrypoint detected")
        return {"root_type": "fastapi_existing", "forge_enabled": True, "evidence": evidence}

    if (root / "manage.py").exists():
        evidence.append("manage.py detected")
        return {"root_type": "django_existing", "forge_enabled": True, "evidence": evidence}

    if pom.exists() or gradle.exists() or gradle_kts.exists() or pyproject.exists() or requirements.exists():
        evidence.append("backend-like dependency file detected")
        return {"root_type": "backend_other", "forge_enabled": True, "evidence": evidence}

    return {"root_type": "non_backend", "forge_enabled": False, "evidence": ["no backend project markers"]}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print(json.dumps(detect(root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
