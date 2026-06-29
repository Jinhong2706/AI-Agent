#!/usr/bin/env python3
"""
按序号重命名照片
支持多种命名规则
"""
import os
import shutil
from pathlib import Path
import argparse
from datetime import datetime

def get_sort_key(image_path, sort_by='name'):
    """获取排序键"""
    if sort_by == 'name':
        return os.path.basename(image_path).lower()
    elif sort_by == 'date':
        return os.path.getmtime(image_path)
    elif sort_by == 'size':
        return os.path.getsize(image_path)
    return 0

def rename_photos(source_dir, output_dir, prefix='photo', start_num=1, digits=3, sort_by='name'):
    """
    按序号重命名照片
    prefix: 文件名前缀
    start_num: 起始编号
    digits: 编号位数（补零）
    sort_by: 排序方式 name/date/size
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic', '.cr2', '.nef'}
    
    # 收集所有图片
    images = []
    for img_file in source_path.rglob('*'):
        if img_file.is_file() and img_file.suffix.lower() in image_extensions:
            images.append(img_file)
    
    # 排序
    images.sort(key=lambda x: get_sort_key(x, sort_by))
    
    renamed = 0
    name_mapping = []
    
    for idx, img_file in enumerate(images, start=start_num):
        try:
            # 生成新文件名
            num = str(idx).zfill(digits)
            new_name = f"{prefix}_{num}{img_file.suffix.lower()}"
            target_file = output_path / new_name
            
            # 如果文件已存在，添加后缀
            counter = 1
            while target_file.exists():
                new_name = f"{prefix}_{num}_{counter}{img_file.suffix.lower()}"
                target_file = output_path / new_name
                counter += 1
            
            shutil.copy2(img_file, target_file)
            renamed += 1
            name_mapping.append((img_file.name, new_name))
            
        except Exception as e:
            print(f"⚠️ 重命名失败: {img_file.name} - {e}")
    
    return renamed, name_mapping

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='按序号重命名照片')
    parser.add_argument('source', help='源目录')
    parser.add_argument('-o', '--output', default='./renamed_photos', help='输出目录')
    parser.add_argument('-p', '--prefix', default='photo', help='文件名前缀')
    parser.add_argument('-s', '--start', type=int, default=1, help='起始编号')
    parser.add_argument('-d', '--digits', type=int, default=3, help='编号位数')
    parser.add_argument('--sort-by', choices=['name', 'date', 'size'], default='name', help='排序方式')
    
    args = parser.parse_args()
    
    renamed, mapping = rename_photos(
        args.source, 
        args.output, 
        args.prefix, 
        args.start, 
        args.digits,
        args.sort_by
    )
    
    print(f"✅ 已重命名 {renamed} 张照片")
    print("\n重命名对照:")
    for old, new in mapping[:10]:
        print(f"  {old} → {new}")
    if len(mapping) > 10:
        print(f"  ... 还有 {len(mapping) - 10} 个文件")
