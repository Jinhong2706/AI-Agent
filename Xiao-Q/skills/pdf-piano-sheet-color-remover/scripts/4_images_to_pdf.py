#!/usr/bin/env python3
"""
Step 4: Convert PNG images to PDF files
Usage: python3 4_images_to_pdf.py <input_dir> <output_dir>
"""

from PIL import Image
import os
import sys


def images_to_pdf(input_dir, output_dir):
    """Convert PNG images to PDF files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PNG files and sort
    image_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
    print(f"Found {len(image_files)} images, converting to PDF...")
    
    for filename in image_files:
        # Extract page number
        page_num = filename.replace('page_', '').replace('.png', '')
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"page_{page_num}.pdf")
        
        # Open image and convert to PDF
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, 'PDF', resolution=200.0)
        
        print(f"Converted: {filename} -> page_{page_num}.pdf")
    
    print(f"\nConversion complete! All PDFs saved to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 4_images_to_pdf.py <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    images_to_pdf(input_dir, output_dir)
