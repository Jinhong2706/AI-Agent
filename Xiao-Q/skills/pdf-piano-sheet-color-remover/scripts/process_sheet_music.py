#!/usr/bin/env python3
"""
Complete pipeline for processing piano sheet music PDFs
Removes red (right hand) and blue (left hand) numbered musical notation
while preserving black finger position markings

Usage: python3 process_sheet_music.py <input_pdf> [output_pdf]
Example: python3 process_sheet_music.py input.pdf output.pdf
"""

import os
import sys
import tempfile
import shutil

# Import step modules
from split_pdf import split_pdf
from pdf_to_images import pdf_to_images
from remove_color_notes import process_images
from images_to_pdf import images_to_pdf
from merge_pdfs import merge_pdfs


def process_sheet_music(input_pdf, output_pdf=None):
    """
    Complete processing pipeline:
    1. Split PDF → 2. Convert to images → 3. Remove colors → 4. Convert to PDFs → 5. Merge
    """
    if output_pdf is None:
        # 使用原文件名 + _黑白版本.pdf
        base_name = os.path.splitext(input_pdf)[0]
        output_pdf = f"{base_name}_黑白版本.pdf"
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="sheet_music_")
    pdf_pages_dir = os.path.join(temp_dir, "pdf-pages")
    pdf_images_dir = os.path.join(temp_dir, "pdf-images")
    pdf_processed_images_dir = os.path.join(temp_dir, "pdf-processed-images")
    pdf_processed_pdfs_dir = os.path.join(temp_dir, "pdf-processed-pdfs")
    
    try:
        print("=" * 60)
        print("PDF Piano Sheet Music Processor")
        print("=" * 60)
        print(f"Input: {input_pdf}")
        print(f"Output: {output_pdf}")
        print()
        
        # Step 1: Split PDF
        print("[Step 1/5] Splitting PDF into pages...")
        split_pdf(input_pdf, pdf_pages_dir)
        print()
        
        # Step 2: Convert PDFs to images
        print("[Step 2/5] Converting PDF pages to images...")
        pdf_to_images(pdf_pages_dir, pdf_images_dir)
        print()
        
        # Step 3: Remove red/blue notation
        print("[Step 3/5] Removing red and blue numbered notation...")
        process_images(pdf_images_dir, pdf_processed_images_dir)
        print()
        
        # Step 4: Convert images to PDFs
        print("[Step 4/5] Converting processed images to PDF...")
        images_to_pdf(pdf_processed_images_dir, pdf_processed_pdfs_dir)
        print()
        
        # Step 5: Merge PDFs
        print("[Step 5/5] Merging all PDF pages...")
        merge_pdfs(pdf_processed_pdfs_dir, output_pdf)
        print()
        
        print("=" * 60)
        print("Processing complete!")
        print(f"Final output: {output_pdf}")
        print("=" * 60)
        
    finally:
        # Clean up temporary directories
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_sheet_music.py <input_pdf> [output_pdf]")
        print("Example: python3 process_sheet_music.py input.pdf output.pdf")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_sheet_music(input_pdf, output_pdf)
