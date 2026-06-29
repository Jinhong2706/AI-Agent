#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能打包和验证脚本

用法:
    python package_skill.py <path/to/skill-folder> [--output <output-directory>]

示例:
    python package_skill.py skills/my-skill
    python package_skill.py skills/my-skill --output ./dist
"""

import os
import sys
import zipfile
import json
import yaml
import argparse
from datetime import datetime
from pathlib import Path

class SkillValidator:
    """技能验证器"""
    
    def __init__(self, skill_path):
        self.skill_path = Path(skill_path)
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate(self):
        """运行所有验证检查"""
        print(f"[CHECK] Verifying skill: {self.skill_path}")
        print("=" * 60)
        
        # 检查目录结构
        self.check_directory_structure()
        
        # 检查 SKILL.md
        self.check_skill_md()
        
        # 检查资源文件
        self.check_resources()
        
        # 检查符号链接（不允许）
        self.check_symlinks()
        
        # 打印结果
        self.print_results()
        
        # 返回是否通过验证
        return len(self.errors) == 0
    
    def check_directory_structure(self):
        """检查目录结构"""
        # 必须存在的文件
        required_files = ['SKILL.md']
        
        for file in required_files:
            if not (self.skill_path / file).exists():
                self.errors.append(f"Missing required file: {file}")
            else:
                self.info.append(f"[OK] Found required file: {file}")
        
        # 检查可选目录
        optional_dirs = ['scripts', 'references', 'assets', 'evals', 'agents']
        
        for dir_name in optional_dirs:
            dir_path = self.skill_path / dir_name
            if dir_path.exists():
                if not dir_path.is_dir():
                    self.errors.append(f"{dir_name} must be a directory")
                else:
                    self.info.append(f"[OK] Found resource directory: {dir_name}/")
    
    def check_skill_md(self):
        """检查 SKILL.md 文件"""
        skill_md_path = self.skill_path / 'SKILL.md'
        
        if not skill_md_path.exists():
            return
        
        try:
            content = skill_md_path.read_text(encoding='utf-8')
            
            # 检查 frontmatter
            if not content.startswith('---'):
                self.errors.append("SKILL.md must start with '---' (YAML frontmatter)")
                return
            
            # 解析 frontmatter
            try:
                # 找到 frontmatter 结束位置
                end_index = content.find('---', 3)
                if end_index == -1:
                    self.errors.append("SKILL.md frontmatter format error (missing closing '---')")
                    return
                
                frontmatter_str = content[3:end_index].strip()
                frontmatter = yaml.safe_load(frontmatter_str)
                
                # 检查必需字段
                if not frontmatter:
                    self.errors.append("SKILL.md frontmatter is empty")
                    return
                
                if 'name' not in frontmatter:
                    self.errors.append("SKILL.md missing required field: name")
                else:
                    name = frontmatter['name']
                    # 检查命名规范
                    if not self.is_valid_skill_name(name):
                        self.warnings.append(f"Skill name '{name}' does not follow naming convention (use lowercase letters, numbers and hyphens)")
                    else:
                        self.info.append(f"[OK] Skill name: {name}")
                
                if 'description' not in frontmatter:
                    self.errors.append("SKILL.md missing required field: description")
                else:
                    desc = frontmatter['description']
                    # 检查描述质量
                    if len(desc) < 20:
                        self.warnings.append(f"Skill description too short ({len(desc)} chars), recommend at least 20 chars")
                    elif len(desc) > 500:
                        self.warnings.append(f"Skill description too long ({len(desc)} chars), recommend max 500 chars")
                    else:
                        self.info.append(f"[OK] Skill description: {len(desc)} chars")
                    
                    # 检查描述是否包含触发条件
                    if not any(keyword in desc.lower() for keyword in ['当', '时', 'use', 'when', 'if']):
                        self.warnings.append("Skill description seems to lack trigger conditions (recommend including '当...时' or 'when')")
                
                # 检查是否有多余字段
                allowed_fields = {'name', 'description'}
                extra_fields = set(frontmatter.keys()) - allowed_fields
                if extra_fields:
                    self.warnings.append(f"SKILL.md frontmatter contains unnecessary fields: {', '.join(extra_fields)}")
                
            except yaml.YAMLError as e:
                self.errors.append(f"SKILL.md YAML frontmatter parse error: {str(e)}")
            
            # 检查正文内容
            body = content[end_index+3:].strip()
            if not body:
                self.errors.append("SKILL.md body is empty")
            else:
                self.info.append(f"[OK] SKILL.md body: {len(body.splitlines())} lines")
                
                # 检查是否包含基本章节
                if len(body) < 100:
                    self.warnings.append("SKILL.md body content is short (<100 chars), may need more detail")
        
        except Exception as e:
            self.errors.append(f"Failed to read SKILL.md: {str(e)}")
    
    def check_resources(self):
        """检查资源文件"""
        # 检查 scripts 目录
        scripts_dir = self.skill_path / 'scripts'
        if scripts_dir.exists():
            py_files = list(scripts_dir.glob('*.py'))
            if py_files:
                self.info.append(f"[OK] Found {len(py_files)} Python scripts")
                
                # 检查脚本语法
                for py_file in py_files:
                    try:
                        compile(py_file.read_text(encoding='utf-8'), py_file, 'exec')
                    except SyntaxError as e:
                        self.errors.append(f"Script syntax error {py_file.name}: {str(e)}")
        
        # 检查 references 目录
        references_dir = self.skill_path / 'references'
        if references_dir.exists():
            md_files = list(references_dir.glob('*.md'))
            if md_files:
                self.info.append(f"[OK] Found {len(md_files)} reference documents")
        
        # 检查 assets 目录
        assets_dir = self.skill_path / 'assets'
        if assets_dir.exists():
            asset_files = list(assets_dir.iterdir())
            if asset_files:
                self.info.append(f"[OK] Found {len(asset_files)} asset files")
        
        # 检查 evals 目录
        evals_dir = self.skill_path / 'evals'
        if evals_dir.exists():
            evals_json = evals_dir / 'evals.json'
            if evals_json.exists():
                try:
                    content = evals_json.read_text(encoding='utf-8')
                    data = json.loads(content)
                    
                    if 'evals' not in data:
                        self.errors.append("evals.json missing 'evals' field")
                    elif not isinstance(data['evals'], list):
                        self.errors.append("evals.json 'evals' must be an array")
                    elif len(data['evals']) == 0:
                        self.warnings.append("evals.json has no test cases")
                    else:
                        self.info.append(f"[OK] Found {len(data['evals'])} test cases")
                        
                        # 检查测试用例格式
                        for i, eval_item in enumerate(data['evals']):
                            if 'prompt' not in eval_item:
                                self.errors.append(f"Test case #{i+1} missing 'prompt' field")
                            if 'expected_output' not in eval_item:
                                self.warnings.append(f"Test case #{i+1} missing 'expected_output' field")
                
                except json.JSONDecodeError as e:
                    self.errors.append(f"evals.json JSON format error: {str(e)}")
    
    def check_symlinks(self):
        """检查符号链接（不允许）"""
        for root, dirs, files in os.walk(self.skill_path):
            # 检查目录
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                if dir_path.is_symlink():
                    self.errors.append(f"Symlink detected (not supported): {dir_path.relative_to(self.skill_path)}")
            
            # 检查文件
            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.is_symlink():
                    self.errors.append(f"Symlink detected (not supported): {file_path.relative_to(self.skill_path)}")
    
    def is_valid_skill_name(self, name):
        """检查技能名称是否符合规范"""
        import re
        # 只允许小写字母、数字和连字符
        return bool(re.match(r'^[a-z0-9-]+$', name))
    
    def print_results(self):
        """打印验证结果"""
        print()
        
        if self.info:
            print("[INFO] Information:")
            for item in self.info:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("[WARN] Warnings:")
            for item in self.warnings:
                print(f"  - {item}")
            print()
        
        if self.errors:
            print("[ERROR] Errors:")
            for item in self.errors:
                print(f"  - {item}")
            print()
        
        print("=" * 60)
        
        if self.errors:
            print(f"[FAIL] Validation failed: {len(self.errors)} errors")
        elif self.warnings:
            print(f"[WARN] Validation passed ({len(self.warnings)} warnings)")
        else:
            print("[OK] Validation passed")


class SkillPackager:
    """技能打包器"""
    
    def __init__(self, skill_path, output_dir=None):
        self.skill_path = Path(skill_path)
        self.output_dir = Path(output_dir) if output_dir else self.skill_path.parent
        self.validator = SkillValidator(skill_path)
    
    def package(self):
        """打包技能"""
        # 首先验证
        if not self.validator.validate():
            print("\n[FAIL] Validation failed, cannot package. Please fix all errors and try again.")
            return None
        
        # 获取技能名称
        skill_md_path = self.skill_path / 'SKILL.md'
        content = skill_md_path.read_text(encoding='utf-8')
        
        # 解析 frontmatter
        end_index = content.find('---', 3)
        frontmatter_str = content[3:end_index].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        
        skill_name = frontmatter.get('name', self.skill_path.name)
        
        # 创建 .skill 文件（zip 格式）
        output_filename = f"{skill_name}.skill"
        output_path = self.output_dir / output_filename
        
        print(f"\n[PACK] Packaging skill: {skill_name}")
        print(f"Output file: {output_path}")
        
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历技能目录
                for root, dirs, files in os.walk(self.skill_path):
                    for file in files:
                        file_path = Path(root) / file
                        
                        # 跳过符号链接
                        if file_path.is_symlink():
                            print(f"  [WARN] Skipping symlink: {file_path.name}")
                            continue
                        
                        # 添加到 zip
                        arcname = file_path.relative_to(self.skill_path)
                        zipf.write(file_path, arcname)
                        print(f"  [OK] Added: {arcname}")
            
            # 获取文件大小
            file_size = output_path.stat().st_size
            file_size_str = self.format_file_size(file_size)
            
            print(f"\n[OK] Package created successfully!")
            print(f"File: {output_path}")
            print(f"Size: {file_size_str}")
            
            return output_path
        
        except Exception as e:
            print(f"\n[FAIL] Packaging failed: {str(e)}")
            return None
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Package and validate skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python package_skill.py skills/my-skill
  python package_skill.py skills/my-skill --output ./dist
        '''
    )
    
    parser.add_argument('skill_path', help='Skill directory path')
    parser.add_argument('--output', '-o', help='Output directory (default: parent of skill directory)')
    
    args = parser.parse_args()
    
    # 检查技能目录是否存在
    if not os.path.exists(args.skill_path):
        print(f"[ERROR] Error: Skill directory does not exist: {args.skill_path}")
        sys.exit(1)
    
    if not os.path.isdir(args.skill_path):
        print(f"[ERROR] Error: Not a directory: {args.skill_path}")
        sys.exit(1)
    
    # 打包技能
    packager = SkillPackager(args.skill_path, args.output)
    output_path = packager.package()
    
    if output_path:
        print(f"\n[TIP] Next steps:")
        print(f"  Install skill: Provide {output_path.name} file to user")
        print(f"  User install: Place file in skills directory and restart")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()