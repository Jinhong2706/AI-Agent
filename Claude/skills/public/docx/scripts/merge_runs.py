"""Merge adjacent identically-formatted runs in a DOCX.

Word fragments paragraph text across many <w:r> elements (revision ids,
spell-check markers, editing history), which makes find-and-replace on
word/document.xml unreliable — the string you're looking for is split
across runs. This coalesces adjacent runs whose formatting (<w:rPr>) is
identical, strips rsid attributes and proofErr markers, and consolidates
<w:t> elements. Text content and rendering are unchanged.

Only word/document.xml is processed (not headers, footers, or footnotes).

Usage:
    python merge_runs.py unpacked/                  # after unzip, before editing
    python merge_runs.py document.docx              # rewrite in place
    python merge_runs.py document.docx -o out.docx
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

from office.helpers import rezip, safe_extract
from office.helpers.merge_runs import merge_runs


def _merge_or_die(path: Path) -> str:
    _, msg = merge_runs(str(path))
    if msg.startswith("Error"):
        print(msg, file=sys.stderr)
        sys.exit(1)
    return msg


def main() -> None:
    p = argparse.ArgumentParser(
        description="Merge adjacent identically-formatted runs in a DOCX (directory or .docx file)."
    )
    p.add_argument("input", help="Unpacked DOCX directory OR a .docx/.dotx file")
    p.add_argument(
        "-o", "--output",
        help="Output .docx path (only valid when input is a .docx; default: overwrite input)",
    )
    args = p.parse_args()

    src = Path(args.input)

    try:
        if src.is_dir():
            if args.output:
                p.error("--output is only valid for .docx input; directory input is modified in place")
            print(_merge_or_die(src))
        elif src.is_file() and src.suffix.lower() in (".docx", ".dotx"):
            out = Path(args.output) if args.output else src
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                with zipfile.ZipFile(src) as zf:
                    safe_extract(zf, tmp_path)
                msg = _merge_or_die(tmp_path)
                rezip(tmp_path, out)
            print(f"{msg}; wrote {out}")
        else:
            print(f"Error: {src} is neither a directory nor a .docx/.dotx file", file=sys.stderr)
            sys.exit(1)
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
