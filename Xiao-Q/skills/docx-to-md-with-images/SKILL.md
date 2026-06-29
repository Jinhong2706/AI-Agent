---
name: docx-to-md-with-images
description: Convert Word (.docx) and other document formats to Markdown. Primary focus on .docx with full image extraction, inline formatting, and structure preservation. Also supports PDF, PPTX, XLSX, HTML, CSV, JSON, XML via markitdown fallback.
---

# DOCX to Markdown with Images

Convert Word (.docx) documents to Markdown with proper image extraction, inline formatting preservation, and relative path references. Also supports other document formats via fallback.

## When to Use

- User asks to convert a .docx file to .md / markdown
- User wants images preserved from the document
- User needs high-fidelity conversion with headings, tables, lists, and formatting

## Prerequisites

- **pandoc** (primary, required for high-quality .docx conversion with images)
- **python** with `python-docx` (fallback when pandoc unavailable)
- **uvx markitdown** (fallback for other formats: PDF, PPTX, XLSX, HTML, CSV, JSON, XML)

## Scripts

All scripts are in the `scripts/` directory relative to this skill file. **Always use these scripts instead of writing inline code.**

| Script | Purpose |
|--------|---------|
| `scripts/install_pandoc.py` | Auto-install pandoc on Windows/macOS/Linux |
| `scripts/fix_images.py` | Flatten img/media/ to img/ and fix image paths in markdown |
| `scripts/docx_to_md.py` | Fallback .docx → .md converter using python-docx (no pandoc needed) |

## DOCX Conversion Workflow

### Step 1: Check for Pandoc

```bash
pandoc --version
```

### Step 1b: Auto-Install Pandoc if Missing

If pandoc is not found, run the install script and show a **prominent notice** to the user:

```bash
py scripts/install_pandoc.py
```

After installation, verify:

```bash
pandoc --version
```

> **IMPORTANT**: After successfully installing pandoc, you MUST tell the user explicitly:
>
> "Pandoc has been automatically installed. You may need to restart your terminal for the PATH changes to take effect. If `pandoc --version` still fails, please restart your terminal and try again."

If auto-install fails, show this message:

> "Could not automatically install pandoc. Please install it manually:
> - Windows: Download from https://github.com/jgm/pandoc/releases/latest
> - macOS: `brew install pandoc`
> - Linux: `sudo apt install pandoc`"

### Step 2: Extract Images and Convert with Pandoc

```bash
# Create img directory
mkdir -p ./img

# Convert with image extraction
pandoc input.docx --extract-media="./img" -o output.md -f docx -t gfm
```

### Step 3: Organize Extracted Images and Fix Paths

Run the bundled script — it handles both flattening and path fixing:

```bash
py scripts/fix_images.py output.md
```

This script does:
1. Flattens `./img/media/` → `./img/`
2. Converts `<img>` HTML tags to standard markdown `![](./img/...)`
3. Fixes absolute paths to relative paths
4. Removes stray `<p>` tags and style attributes around images

### Step 4: Verify

```bash
# Should show only ./img/ paths
grep -oP '!\[.*?\]\(.*?\)' output.md

# Should return 0 (no leftover <img> tags)
grep -c '<img src=' output.md
```

## Fallback: python-docx (when pandoc unavailable)

When pandoc cannot be installed, use the bundled python-docx script:

```bash
py scripts/docx_to_md.py input.docx output.md
```

This handles:
- Heading levels (Heading 1/2/3 → `#`/`##`/`###`)
- Bold/italic inline formatting via run detection
- Lists with nesting via `w:numPr` XML elements
- Tables → markdown table format
- TOC entries (style `toc 1`, `toc 2`, etc.) are automatically skipped

Key lessons from real-world conversion:
- `uvx markitdown` may fail on Windows due to `onnxruntime` DLL load errors
- `python-docx` is reliable but does NOT extract images — use pandoc when images matter

## Other Format Conversion (markitdown fallback)

For non-docx formats, use `uvx markitdown` when available:

```bash
# PDF
uvx markitdown input.pdf -o output.md

# PowerPoint
uvx markitdown input.pptx -o output.md

# Excel
uvx markitdown input.xlsx -o output.md

# HTML, CSV, JSON, XML
uvx markitdown input.html -o output.md
uvx markitdown input.csv -o output.md

# With file type hint (for stdin)
cat document | uvx markitdown -x .pdf > output.md

# Use Azure Document Intelligence for difficult PDFs
uvx markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/"
```

Note: `markitdown` may fail on some Windows systems due to `onnxruntime` DLL issues. In that case, use format-specific alternatives (e.g., `python-pptx` for PPTX, `openpyxl` for XLSX).

## Output Structure

```
project/
├── input.docx          # Source document
├── output.md           # Converted markdown
└── img/                # Extracted images (pandoc method only)
    ├── image1.png
    ├── image2.jpeg
    └── ...
```

## Notes

- **Pandoc is strongly preferred** for .docx conversion — it handles headings, tables, lists, code blocks, and formatting far better than manual python-docx parsing
- The `.emf` format (Windows metafile) is not widely supported in markdown viewers; consider converting to PNG if needed
- Image filenames follow Word's internal naming (image1.png, image2.png, etc.)
- Always use `gfm` (GitHub Flavored Markdown) output format for best compatibility
- On Windows, run Python scripts via `py script.py` not inline in PowerShell (escaping issues)
- The python-docx fallback preserves: heading levels, bold/italic formatting, lists with nesting, tables, and skips TOC entries automatically
