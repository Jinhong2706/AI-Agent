#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装艺术作品解读技能所需的依赖
"""

import subprocess
import sys


def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
        print(f"✅ 已安装: {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ 安装失败: {package}")
        return False


def main():
    """主函数"""
    print("正在安装艺术作品解读技能依赖...")
    print("-" * 50)
    
    packages = [
        "python-docx",
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("-" * 50)
    print(f"安装完成: {success_count}/{len(packages)} 个包")
    
    if success_count == len(packages):
        print("✅ 所有依赖安装成功！")
    else:
        print("⚠️ 部分依赖安装失败，请手动安装")


if __name__ == '__main__':
    main()
