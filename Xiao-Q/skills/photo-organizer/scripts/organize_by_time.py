#!/usr/bin/env python3
"""
按时间整理照片
支持按年/月/日分组
"""
import os
import shutil
import exifread
from datetime import datetime
from pathlib import Path
import argparse

def get_photo_date(image_path):
    """获取照片拍摄日期"""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', details=False)
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except:
        pass
    
    # 如果没有EXIF信息，使用文件修改时间
    return datetime.fromtimestamp(os.path.getmtime(image_path))

def organize_by_time(source_dir, output_dir, group_by='month'):
    """
    按时间整理照片
    group_by: 'year', 'month', 'day'
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic', '.cr2', '.nef'}
    
    organized = 0
    errors = []
    
    for img_file in source_path.rglob('*'):
        if img_file.is_file() and img_file.suffix.lower() in image_extensions:
            try:
                photo_date = get_photo_date(img_file)
                
                if group_by == 'year':
                    folder_name = photo_date.strftime('%Y')
                elif group_by == 'month':
                    folder_name = photo_date.strftime('%Y-%m')
                else:  # day
                    folder_name = photo_date.strftime('%Y-%m-%d')
                
                target_dir = output_path / folder_name
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_file = target_dir / img_file.name
                if not target_file.exists():
                    shutil.copy2(img_file, target_file)
                    organized += 1
                    
            except Exception as e:
                errors.append((img_file.name, str(e)))
    
    return organized, errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='按时间整理照片')
    parser.add_argument('source', help='源目录')
    parser.add_argument('-o', '--output', default='./organized_by_time', help='输出目录')
    parser.add_argument('-g', '--group-by', choices=['year', 'month', 'day'], default='month', help='分组方式')
    
    args = parser.parse_args()
    
    organized, errors = organize_by_time(args.source, args.output, args.group_by)
    
    print(f"✅ 已整理 {organized} 张照片")
    if errors:
        print(f"⚠️ {len(errors)} 张照片处理失败")
