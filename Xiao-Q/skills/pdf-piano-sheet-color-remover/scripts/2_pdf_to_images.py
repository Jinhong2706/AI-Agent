#!/usr/bin/env python3
"""
Step 2: Convert PDF pages to PNG images
Usage: python3 2_pdf_to_images.py <input_dir> <output_dir>
"""

from pdf2image import convert_from_path
import os
import sys


def pdf_to_images(input_dir, output_dir):
    """Convert PDF files to PNG images"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PDF files and sort
    pdf_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.pdf')])
    print(f"Found {len(pdf_files)} PDF files, converting to images...")
    
    for pdf_file in pdf_files:
        # Extract page number
        page_num = pdf_file.replace('page_', '').replace('.pdf', '')
        pdf_path = os.path.join(input_dir, pdf_file)
        
        # Convert to image
        images = convert_from_path(pdf_path, dpi=200)
        
        # Save image
        for i, image in enumerate(images):
            output_filename = f"page_{page_num}.png"
            output_path = os.path.join(output_dir, output_filename)
            image.save(output_path, 'PNG')
            print(f"Converted: {pdf_file} -> {output_filename}")
    
    print(f"\nConversion complete! All images saved to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 2_pdf_to_images.py <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    pdf_to_images(input_dir, output_dir)
