---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Create PDFs

#### Basic PDF Creation
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Add text
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add a line
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Create PDF with Multiple Pages
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build PDF
doc.build(story)
```

#### Add Images with `canvas.drawImage`
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

c = canvas.Canvas("image-demo.pdf", pagesize=letter)
page_w, page_h = letter

img = ImageReader("chart.png")  # drawImage accepts a filename or ImageReader
img_w, img_h = img.getSize()

target_w = 4.5 * inch
target_h = target_w * (img_h / img_w)  # Preserve aspect ratio

# PDF canvas coordinates use a bottom-left origin.
# To place the image 1 inch below the top edge, subtract the image height.
x = inch
y = page_h - inch - target_h

c.drawImage(img, x, y, width=target_w, height=target_h)
c.save()
```

#### Fit an Image into a Fixed Box
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

c = canvas.Canvas("boxed-image.pdf", pagesize=letter)
page_w, page_h = letter

box_x = inch
box_y = page_h - 5 * inch
box_w = 4 * inch
box_h = 3 * inch

c.drawImage(
    "photo.jpg",
    box_x,
    box_y,
    width=box_w,
    height=box_h,
    preserveAspectRatio=True,
    anchor="c",
)
c.save()
```

#### Add Images in Platypus
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()

img = ImageReader("logo.png")
img_w, img_h = img.getSize()
target_w = 2 * inch
target_h = target_w * (img_h / img_w)

story = [
    Paragraph("Quarterly Update", styles["Title"]),
    Spacer(1, 12),
    Image("logo.png", width=target_w, height=target_h, hAlign="CENTER"),
]

doc.build(story)
```

#### Image Rules

- **Preserve aspect ratio** - compute the missing dimension from the source image size, or use `preserveAspectRatio=True` when fitting into a fixed box
- **Canvas coordinates are bottom-left based** - `x` and `y` are measured from the lower-left corner of the page
- **Platypus images are flowables** - they flow with the document layout and do not use absolute page coordinates
- **Prefer `drawImage` over `drawInlineImage`** - it reuses external image objects and is usually smaller/faster for repeated images

#### Subscripts and Superscripts

**IMPORTANT**: Never use Unicode subscript/superscript characters (₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹) in ReportLab PDFs. The built-in fonts do not include these glyphs, causing them to render as solid black boxes.

Instead, use ReportLab's XML markup tags in Paragraph objects:
```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# Subscripts: use <sub> tag
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# Superscripts: use <super> tag
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

For canvas-drawn text (not Paragraph objects), manually adjust font the size and position rather than using Unicode subscripts/superscripts.

#### Create Tables

**Always wrap table cell text in `Paragraph` objects.** Plain strings inside `Table` cells do not wrap — long content overflows the cell, overlaps neighbors, or pushes off the page. Wrapping every cell (including headers and short values) in a `Paragraph` keeps wrapping behavior consistent and lets you use inline markup like `<b>`, `<i>`, `<sub>`, and `<super>`.

**Size columns proportionally to expected content length.** Uniform column widths produce squished columns with excessive wrapping when content sizes differ. Give wide-text columns most of the available width and keep narrow columns (IDs, numbers, short labels) small.

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

doc = SimpleDocTemplate("table.pdf", pagesize=letter)
styles = getSampleStyleSheet()
cell = styles["BodyText"]

# Wrap every cell value in a Paragraph so it wraps within the column width.
data = [
    [Paragraph("<b>ID</b>", cell),
     Paragraph("<b>Name</b>", cell),
     Paragraph("<b>Description</b>", cell)],
    [Paragraph("1", cell),
     Paragraph("Widget", cell),
     Paragraph("A long description that needs to wrap across multiple lines without overflowing the cell.", cell)],
]

# Allocate column widths proportional to expected content length.
# Letter is 8.5" wide; with 1" margins, total <= 6.5".
col_widths = [0.5 * inch, 1.5 * inch, 4.5 * inch]

table = Table(data, colWidths=col_widths, repeatRows=1)
table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
]))

doc.build([table])
```

**Rules:**
- Wrap **every** cell value in a `Paragraph` — even headers and short strings — so wrapping is uniform and inline markup works.
- Always pass explicit `colWidths` sized in proportion to the longest expected content per column. Columns that hold paragraphs of prose should get the bulk of the width; columns holding short labels or numbers should be narrow.
- Total `colWidths` must fit the printable area (e.g., letter with 1" margins ~= 6.5"; landscape letter ~= 9").
- Set `("VALIGN", (0, 0), (-1, -1), "TOP")` so wrapped rows align cleanly at the top instead of floating in the middle of the cell.
- Use `repeatRows=1` so the header row is repeated when the table breaks across pages.
- For very wide content, switch the page to `landscape(letter)` rather than shrinking columns into illegibility.

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Extraction vs. Rasterization

- **Use `pdfimages` for extraction** - this pulls out original embedded bitmap assets from the PDF without rendering the page
- **Use `pdftoppm` or `pdf2image` for rasterization** - this renders the full page appearance to pixels, including text, vector graphics, annotations, and layout
- **Rendered pages are not extracted images** - converting a PDF page to PNG/JPG gives you a screenshot of the page, not the original embedded image objects

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Add tables to PDFs | reportlab | Wrap cells in `Paragraph`; size `colWidths` to content |
| Add images to PDFs | reportlab | `canvas.drawImage(...)` or Platypus `Image(...)` |
| Extract embedded images | pdfimages | `pdfimages -all input.pdf prefix` |
| Render pages to images | `pdftoppm` / `pdf2image` | Page snapshots for QA, OCR, or previews |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see forms.md) | See forms.md |

## Visual Verification with pdftoppm

After filling PDF form fields or making any modifications, always render each page to a PNG screenshot and visually verify the result. Field name mappings are often wrong, so visual checks are essential.

```bash
# Render page 1 at 300 DPI
pdftoppm -png -r 300 -f 1 -l 1 output.pdf /tmp/verify
```

Then use `read_file` on `/tmp/verify-1.png` to see the rendered page. Check that each value appears next to its correct label. Repeat for each page:

```bash
# Render page 2
pdftoppm -png -r 300 -f 2 -l 2 output.pdf /tmp/verify_p2
# Then read_file /tmp/verify_p2-2.png
```

This catches misplaced values, overlapping text, and incorrect field mappings that are invisible when only inspecting the raw PDF structure.

## Tax Form Preparation

Fill the official blank PDF tax forms in `forms/`. Do NOT create summary documents, Word files, or custom PDFs. The deliverable must be the actual filled-in official form(s).

**Round all dollar amounts to the nearest whole dollar.** Do not enter cents on any line.

Steps:
1. Read forms.md for the fillable-fields workflow.
2. Use the helper scripts in `scripts/`:
   - check_fillable_fields.py <form.pdf> — verify the form is fillable
   - extract_form_field_info.py <form.pdf> <output.json> — get field names
   - fill_pdf_fields.py — fill fields programmatically (see forms.md)
   - convert_pdf_to_images.py <form.pdf> <outdir> — render for verification
3. Find the correct blank form(s) in `forms/`.
4. Fill each form using the extracted field names and the values you compute.
5. Visually verify your filled forms by rendering them to images.

## Next Steps

- For advanced pypdfium2 usage, see REFERENCE.md
- For JavaScript libraries (pdf-lib), see REFERENCE.md
- If you need to fill out a PDF form, follow the instructions in forms.md
- For troubleshooting guides, see REFERENCE.md
