#!/usr/bin/env python3
"""
RSDK Mod Packager
Package RSDK mod for distribution.
"""

import os
import sys
import zipfile
import shutil
from datetime import datetime

def package_mod(mod_dir, output_dir=None):
    """Package an RSDK mod directory into a distributable zip."""
    
    if not os.path.isdir(mod_dir):
        print(f"Error: Mod directory not found: {mod_dir}")
        return False
    
    # Check for mod.ini
    mod_ini = os.path.join(mod_dir, 'mod.ini')
    if not os.path.exists(mod_ini):
        print(f"Warning: No mod.ini found in {mod_dir}")
        print("Mod may not load correctly without configuration.")
    
    # Determine output file name
    mod_name = os.path.basename(os.path.normpath(mod_dir))
    if not output_dir:
        output_dir = '.'
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f"{mod_name}_{timestamp}.zip")
    
    print(f"\n{'='*50}")
    print(f"Packaging RSDK Mod: {mod_name}")
    print(f"{'='*50}\n")
    
    # Create zip file
    files_added = 0
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(mod_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, mod_dir)
                
                print(f"  Adding: {arcname}")
                zipf.write(file_path, arcname)
                files_added += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Mod packaged successfully!")
    print(f"   Output: {output_file}")
    print(f"   Files added: {files_added}")
    print(f"{'='*50}\n")
    
    print("Installation instructions:")
    print("  1. Extract the zip file to your game's mods/ directory")
    print("  2. Enable the mod in RSDK Mod Loader")
    print("  3. Configure load order if needed")
    
    return output_file

def main():
    if len(sys.argv) < 2:
        print("RSDK Mod Packager")
        print("\nUsage:")
        print("  python package_mod.py <mod_directory> [output_directory]")
        print("\nExample:")
        print("  python package_mod.py ./MyMod ./dist")
        print("  python package_mod.py C:/Games/SonicMania/mods/MyMod")
        sys.exit(1)
    
    mod_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = package_mod(mod_dir, output_dir)
    
    if output_file:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
