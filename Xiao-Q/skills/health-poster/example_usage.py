#!/usr/bin/env python3
"""
健康海报生成器使用示例
"""

import os
import sys
from pathlib import Path

def example_basic_usage():
    """基本使用示例"""
    print("📋 基本使用示例")
    print("=" * 60)
    
    print("\n1. 生成随机主题的海报:")
    print("   python3 scripts/generate_health_poster_pro.py")
    
    print("\n2. 生成指定主题的海报:")
    print("   python3 scripts/generate_health_poster_pro.py --theme '口腔健康'")
    
    print("\n3. 设置组织名称后生成:")
    print("   python3 scripts/generate_health_poster_pro.py \\")
    print("     --org-name '广东省江西青原商会' \\")
    print("     --theme '感冒预防'")
    
    print("\n4. 自定义输出目录:")
    print("   python3 scripts/generate_health_poster_pro.py \\")
    print("     --output-dir '~/my_health_posters'")

def example_configure_skill():
    """配置技能示例"""
    print("\n⚙️ 配置技能示例")
    print("=" * 60)
    
    print("\n1. 进入配置界面:")
    print("   python3 scripts/generate_health_poster_pro.py --configure")
    
    print("\n2. 设置组织名称（如'广东省江西青原商会'）")
    print("   选择选项 1，输入组织名称")
    
    print("\n3. 设置输出目录:")
    print("   选择选项 2，输入目录路径（如 ~/health_posters）")
    
    print("\n4. 查看当前配置:")
    print("   python3 scripts/generate_health_poster_pro.py --show-config")

def example_integration():
    """集成到其他系统的示例"""
    print("\n🔧 集成到其他系统示例")
    print("=" * 60)
    
    print("""
# 在Python代码中调用
import sys
from pathlib import Path

# 添加技能路径
skill_dir = Path("/path/to/health-poster-generator-pro")
sys.path.insert(0, str(skill_dir / "scripts"))

from generate_health_poster_pro import generate_poster

# 生成海报
result = generate_poster(
    theme="口腔健康",
    org_name="广东省江西青原商会",
    output_dir="~/output/posters"
)

if result:
    print(f"✅ 海报生成成功!")
    print(f"   图片: {result['image_path']}")
    print(f"   内容: {result['content_file']}")
    
    # 使用生成的图片
    # ... 你的业务逻辑 ...
else:
    print("❌ 海报生成失败")
""")

def example_error_handling():
    """错误处理示例"""
    print("\n🚨 常见错误处理示例")
    print("=" * 60)
    
    print("\n1. seedream技能未安装:")
    print("   错误: ❌ 依赖检查失败")
    print("   解决: clawhub install seedream-image-generation")
    
    print("\n2. 火山引擎API key未配置:")
    print("   错误: ❌ 导入seedream模块失败")
    print("   解决: 配置seedream技能的API key")
    
    print("\n3. API余额不足:")
    print("   错误: ❌ 图片生成失败: 余额不足")
    print("   解决: 登录火山引擎控制台充值")
    
    print("\n4. 主题不存在:")
    print("   错误: ❌ 主题 'XXX' 不存在")
    print("   解决: 使用 --list-themes 查看可用主题")

def main():
    """主函数"""
    print("健康海报生成器使用示例")
    print("=" * 60)
    
    example_basic_usage()
    example_configure_skill()
    example_integration()
    example_error_handling()
    
    print("\n🎯 快速开始:")
    print("-" * 40)
    print("1. 安装依赖: clawhub install seedream-image-generation")
    print("2. 配置火山引擎API key")
    print("3. 测试生成: python3 scripts/generate_health_poster_pro.py")
    print("4. 配置组织名称: python3 scripts/generate_health_poster_pro.py --configure")
    print("-" * 40)
    
    print("\n📞 获取帮助:")
    print("python3 scripts/generate_health_poster_pro.py --help")

if __name__ == "__main__":
    main()