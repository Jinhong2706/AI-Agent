#!/usr/bin/env python3
"""
健康海报生成器技能测试脚本
"""

import os
import sys
from pathlib import Path

def test_configuration():
    """测试配置功能"""
    print("🧪 测试配置功能...")
    
    # 导入主脚本
    skill_dir = Path(__file__).parent
    sys.path.insert(0, str(skill_dir / "scripts"))
    
    try:
        from generate_health_poster_pro import Config
        
        # 测试配置加载
        config = Config.load()
        print(f"✅ 配置加载成功: {len(config)} 个配置项")
        
        # 显示配置
        print("\n📋 当前配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_knowledge_loading():
    """测试知识库加载"""
    print("\n🧪 测试知识库加载...")
    
    skill_dir = Path(__file__).parent
    sys.path.insert(0, str(skill_dir / "scripts"))
    
    try:
        from generate_health_poster_pro import load_health_knowledge
        
        knowledge = load_health_knowledge()
        
        if "全年通用" in knowledge:
            themes = list(knowledge["全年通用"].keys())
            print(f"✅ 知识库加载成功: {len(themes)} 个主题")
            
            # 显示前5个主题
            print("\n📚 前5个主题:")
            for i, theme in enumerate(themes[:5], 1):
                theme_data = knowledge["全年通用"][theme]
                title = theme_data.get("title", theme)
                print(f"  {i}. {title}")
            
            return True
        else:
            print("❌ 知识库格式错误")
            return False
    except Exception as e:
        print(f"❌ 知识库加载测试失败: {e}")
        return False

def test_dependency_check():
    """测试依赖检查"""
    print("\n🧪 测试依赖检查...")
    
    skill_dir = Path(__file__).parent
    sys.path.insert(0, str(skill_dir / "scripts"))
    
    try:
        from generate_health_poster_pro import check_seedream_dependency
        
        # 注意：这个测试可能会失败，如果seedream技能未安装
        # 这是预期的，我们只测试函数是否能运行
        result = check_seedream_dependency()
        print(f"✅ 依赖检查完成: {'通过' if result else '未通过（可能需要安装seedream技能）'}")
        return True
    except Exception as e:
        print(f"❌ 依赖检查测试失败: {e}")
        return False

def test_theme_listing():
    """测试主题列表功能"""
    print("\n🧪 测试主题列表功能...")
    
    skill_dir = Path(__file__).parent
    sys.path.insert(0, str(skill_dir / "scripts"))
    
    try:
        from generate_health_poster_pro import list_themes
        
        themes = list_themes()
        if themes:
            print(f"✅ 主题列表功能正常: {len(themes)} 个主题")
            return True
        else:
            print("❌ 未获取到主题列表")
            return False
    except Exception as e:
        print(f"❌ 主题列表测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("健康海报生成器技能测试")
    print("=" * 60)
    
    tests = [
        ("配置功能", test_configuration),
        ("知识库加载", test_knowledge_loading),
        ("依赖检查", test_dependency_check),
        ("主题列表", test_theme_listing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！技能基本功能正常。")
        print("\n📋 下一步:")
        print("1. 安装seedream技能: clawhub install seedream-image-generation")
        print("2. 配置火山引擎API key")
        print("3. 测试海报生成: python3 scripts/generate_health_poster_pro.py")
    else:
        print("\n⚠️  部分测试失败，请检查问题。")
    
    print("\n🔧 使用说明:")
    print("-" * 40)
    print("1. 配置技能:")
    print("   python3 scripts/generate_health_poster_pro.py --configure")
    print("\n2. 生成海报（随机主题）:")
    print("   python3 scripts/generate_health_poster_pro.py")
    print("\n3. 生成海报（指定主题）:")
    print("   python3 scripts/generate_health_poster_pro.py --theme '口腔健康'")
    print("\n4. 列出所有主题:")
    print("   python3 scripts/generate_health_poster_pro.py --list-themes")
    print("-" * 40)

if __name__ == "__main__":
    main()