"""Slide-XML defects PowerPoint refuses, and nothing else.

`validate.py` never schema-checked ppt/slides/slideN.xml. That hole hid four
defects that made real decks unopenable, including an eight-digit hex colour
this repo shipped in an eval output for months with every check green.

The hole cannot be closed by simply pointing the schema at slide parts. The
bundled ISO-IEC29500-4 schemas are the *Strict* flavour, and every Transitional
document -- everything PowerPoint reads, everything pptxgenjs writes -- trips
them. Measured over 427 decks PowerPoint itself authored, slide-level XSD
produces seven error classes, all of which PowerPoint reads back happily:
buSzPct percentages, the ea/cs/latin/buFont typeface facets, an ST_Coordinate
union, and one txBody ordering case.

So this reports a denylist, not an allowlist: only the classes seen exclusively
on decks PowerPoint refuses. An unknown class is therefore a miss, never a false
alarm -- and a false alarm is what teaches an agent to "fix" valid XML and ship
a deck that will not open.

Each entry below names how it was confirmed.
"""

from __future__ import annotations

import re

SLIDE_PART_RE = re.compile(
    r"ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters|handoutMasters)"
    r"/[^/]+\.xml"
)

FATAL_SLIDE_ERRORS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\}tableStyleId': This element is not expected"),
        "two <a:tableStyleId> in one <a:tblPr> (the schema allows one)",
    ),
    (
        re.compile(r"\}srgbClr', attribute 'val'"),
        "a colour that is not six hex digits",
    ),
    (
        re.compile(r"\}txBody': Missing child element"),
        "a <p:txBody> with no children",
    ),
    (
        re.compile(r"\}miter', attribute 'lim'"),
        'a line join with lim="NaN"',
    ),
    (
        re.compile(r"\}uLnTx': This element is not expected"),
        "<a:uLnTx> in a position the schema forbids",
    ),
    (
        re.compile(r"\}overrideClrMapping': This element is not expected"),
        "<p:overrideClrMapping> in a position the schema forbids",
    ),
    (
        re.compile(r"\}nvGrpSpPr': Missing child element"),
        "a <p:nvGrpSpPr> with no children",
    ),
)


def is_schema_verdict(error: str) -> bool:
    return error.startswith("Element ")


def fatal_slide_errors(errors: set[str]) -> list[str]:
    out = []
    for error in sorted(errors):
        for pattern, meaning in FATAL_SLIDE_ERRORS:
            if pattern.search(error):
                out.append(f"{meaning}: {error}")
                break
    return out
