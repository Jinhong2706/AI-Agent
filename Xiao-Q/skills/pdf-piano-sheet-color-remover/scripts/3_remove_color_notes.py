#!/usr/bin/env python3
"""
Step 3: Remove red and blue numbered musical notation from sheet music images
Usage: python3 3_remove_color_notes.py <input_dir> <output_dir>

This script uses a two-stage approach:
1. Aggressively remove red/blue colors (may accidentally remove some black numbers)
2. Restore accidentally removed black finger position numbers
"""

from PIL import Image
import numpy as np
import os
import sys
from scipy import ndimage


def remove_red_blue_notes(input_path, output_path):
    """
    Remove red and blue numbered notation from sheet music image
    Uses aggressive parameters to ensure complete removal of colored notation
    """
    img = Image.open(input_path).convert('RGB')
    data = np.array(img)
    result = data.copy()
    
    # Aggressive red detection - relaxed thresholds to catch all red shades
    red_mask = (
        (data[:, :, 0] > 130) &
        (data[:, :, 1] < 150) &
        (data[:, :, 2] < 150) &
        (data[:, :, 0] > data[:, :, 1] + 15) &
        (data[:, :, 0] > data[:, :, 2] + 15)
    )
    
    # Aggressive blue detection - relaxed thresholds to catch all blue shades
    blue_mask = (
        (data[:, :, 2] > 100) &
        (data[:, :, 0] < 140) &
        (data[:, :, 1] < 160) &
        (data[:, :, 2] > data[:, :, 0] + 15) &
        (data[:, :, 2] > data[:, :, 1] + 5)
    )
    
    color_mask = red_mask | blue_mask
    # Dilate mask to ensure complete removal
    color_mask_dilated = ndimage.binary_dilation(color_mask, iterations=4)
    
    white_color = np.array([255, 255, 255])
    result[color_mask_dilated] = white_color
    
    result_img = Image.fromarray(result)
    result_img.save(output_path, 'PNG')


def restore_black_numbers(original_path, processed_path, output_path):
    """
    Restore black finger position numbers that were accidentally removed
    """
    original_img = Image.open(original_path).convert('RGB')
    processed_img = Image.open(processed_path).convert('RGB')
    
    original_data = np.array(original_img)
    processed_data = np.array(processed_img)
    result = processed_data.copy()
    
    # Detect dark pixels in original (black numbers)
    black_mask = (
        (original_data[:, :, 0] < 120) &
        (original_data[:, :, 1] < 120) &
        (original_data[:, :, 2] < 120) &
        (original_data[:, :, 0] + original_data[:, :, 1] + original_data[:, :, 2] < 300)
    )
    
    # Detect white pixels in processed (removed areas)
    white_mask = (
        (processed_data[:, :, 0] > 200) &
        (processed_data[:, :, 1] > 200) &
        (processed_data[:, :, 2] > 200)
    )
    
    # Restore black numbers that were removed
    restore_mask = black_mask & white_mask
    restore_mask_dilated = ndimage.binary_dilation(restore_mask, iterations=1)
    
    result[restore_mask_dilated] = original_data[restore_mask_dilated]
    
    result_img = Image.fromarray(result)
    result_img.save(output_path, 'PNG')


def process_images(input_dir, output_dir):
    """Process all images in input directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create temporary directory for intermediate files
    temp_dir = os.path.join(output_dir, '_temp_removed')
    os.makedirs(temp_dir, exist_ok=True)
    
    image_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
    print(f"Found {len(image_files)} images, processing...")
    
    for filename in image_files:
        input_path = os.path.join(input_dir, filename)
        temp_path = os.path.join(temp_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        print(f"Processing: {filename}")
        
        # Step 1: Remove red/blue colors
        remove_red_blue_notes(input_path, temp_path)
        
        # Step 2: Restore black numbers
        restore_black_numbers(input_path, temp_path, output_path)
        
        print(f"  Complete: {filename}")
    
    # Clean up temp directory
    import shutil
    shutil.rmtree(temp_dir)
    
    print(f"\nProcessing complete! All images saved to {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 3_remove_color_notes.py <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    process_images(input_dir, output_dir)
