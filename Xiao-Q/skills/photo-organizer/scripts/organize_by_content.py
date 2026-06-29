#!/usr/bin/env python3
"""
按内容类型整理照片（风景/人像/截图等）
使用简单的图像特征识别
"""
import os
import shutil
from pathlib import Path
import argparse
from PIL import Image
import imagehash

def classify_photo(image_path):
    """
    简单的照片分类逻辑
    返回: ('类别', 置信度)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        aspect_ratio = width / height if height > 0 else 1
        
        # 读取EXIF信息判断是否为截图
        has_screenshot_indicators = False
        if 'screenshot' in image_path.lower() or width == 1920 or width == 2560 or width == 3840:
            has_screenshot_indicators = True
        
        # 简单的启发式分类
        if has_screenshot_indicators or (width == 1366 and height == 768) or (width == 1920 and height == 1080):
            return '截图', 0.8
        
        # 读取图片特征
        img_hash = imagehash.average_hash(img)
        
        # 根据比例和特征判断
        if aspect_ratio > 2.5:
            return '全景/风景', 0.7
        elif aspect_ratio < 0.6:
            return '人像/竖拍', 0.7
        else:
            # 默认分类为风景或日常
            return '风景/日常', 0.6
            
    except Exception as e:
        return '未分类', 0.0

def organize_by_content(source_dir, output_dir):
    """按内容类型整理照片"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic'}
    
    organized = 0
    classification = {}
    
    for img_file in source_path.rglob('*'):
        if img_file.is_file() and img_file.suffix.lower() in image_extensions:
            try:
                category, confidence = classify_photo(img_file)
                
                target_dir = output_path / category
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_file = target_dir / img_file.name
                if not target_file.exists():
                    shutil.copy2(img_file, target_file)
                    organized += 1
                    
                    if category not in classification:
                        classification[category] = 0
                    classification[category] += 1
                    
            except Exception as e:
                print(f"⚠️ 处理失败: {img_file.name} - {e}")
    
    return organized, classification

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='按内容整理照片')
    parser.add_argument('source', help='源目录')
    parser.add_argument('-o', '--output', default='./organized_by_content', help='输出目录')
    
    args = parser.parse_args()
    
    organized, classification = organize_by_content(args.source, args.output)
    
    print(f"✅ 已整理 {organized} 张照片")
    print("\n分类统计:")
    for category, count in sorted(classification.items()):
        print(f"  {category}: {count} 张")
