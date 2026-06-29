#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF (fitz) is required for PDF screenshot export.", file=sys.stderr)
    sys.exit(1)

def export_pdf_pages_as_images(pdf_path: Path, output_dir: Path, dpi: int = 150) -> bool:
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found.", file=sys.stderr)
        return False
        
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        doc = fitz.open(pdf_path)
        print(f"[*] Extracting {doc.page_count} high-fidelity images from PDF: {pdf_path.name}")
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for i, page in enumerate(doc):
            slide_number = i + 1
            pix = page.get_pixmap(matrix=mat, alpha=False)
            output_file = output_dir / f"slide_{slide_number}.png"
            pix.save(str(output_file))
            print(f"  [+] Saved {output_file.name}")
            
        doc.close()
        return True
    except Exception as e:
        print(f"Error extracting PDF: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Export PDF pages to PNG images.")
    parser.add_argument("pdf_path", type=Path, help="Path to the source PDF file")
    parser.add_argument("--output-dir", type=Path, default=Path("output/screenshots"), help="Output directory for PNGs")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for the output images")
    args = parser.parse_args()
    
    success = export_pdf_pages_as_images(args.pdf_path, args.output_dir, args.dpi)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
