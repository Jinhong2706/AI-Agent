#!/usr/bin/env python3
"""
健康科普海报生成器（专业版）
基于现有技能修改，符合技能市场要求：
1. 不包含定时设置
2. 不包含固定通道配置
3. 商会文字可配置
4. 依赖火山生图技能
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ==================== 配置管理 ====================

class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        "organization_name": "深圳市微康网络科技有限公司",  # 左上角商会/组织名称，默认为空
        "output_base": "~/health_posters",  # 输出目录
        "knowledge_file": None,  # 知识库文件路径，None表示使用默认
    }
    
    CONFIG_DIR = Path.home() / ".config" / "health-poster"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    @classmethod
    def load(cls):
        """加载配置"""
        config = cls.DEFAULT_CONFIG.copy()
        
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载配置文件失败，使用默认配置: {e}")
        
        # 展开路径
        if config["output_base"].startswith("~"):
            config["output_base"] = os.path.expanduser(config["output_base"])
        
        return config
    
    @classmethod
    def save(cls, config):
        """保存配置"""
        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    @classmethod
    def show_current(cls):
        """显示当前配置"""
        config = cls.load()
        print("\n📋 当前配置:")
        print("-" * 40)
        for key, value in config.items():
            print(f"  {key}: {value}")
        print("-" * 40)

# ==================== 核心功能 ====================

def load_health_knowledge(knowledge_file=None):
    """加载健康知识库"""
    if knowledge_file and os.path.exists(knowledge_file):
        knowledge_path = knowledge_file
    else:
        # 使用技能自带的默认知识库（修复后的版本）
        skill_dir = Path(__file__).parent.parent
        knowledge_path = skill_dir / "references" / "health_knowledge_enhanced_fixed.json"
    
    try:
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
        
        # 确保知识库格式正确
        if "全年通用" not in knowledge:
            knowledge = {"全年通用": knowledge}
        
        print(f"✅ 加载知识库: {knowledge_path}")
        return knowledge
    except Exception as e:
        print(f"❌ 加载知识库失败: {e}")
        # 返回最小示例知识库
        return {
            "全年通用": {
                "健康科普": {
                    "title": "健康科普",
                    "subtitle": "每日健康小知识",
                    "description": "关注健康，预防疾病，提高生活质量。",
                    "points": [
                        "保持良好生活习惯，均衡饮食，适量运动。",
                        "定期体检，早发现早治疗。",
                        "保持良好心态，积极面对生活。",
                        "注意个人卫生，预防疾病传播。"
                    ],
                    "colors": "清新的蓝色、绿色调，健康元素"
                }
            }
        }

def check_seedream_dependency():
    """检查seedream技能依赖"""
    seedream_skill_path = Path("/root/.openclaw/workspace/skills/seedream-image-generation")
    
    if not seedream_skill_path.exists():
        print("\n⚠️ **依赖检查失败**")
        print("=" * 60)
        print("本技能需要依赖 'seedream-image-generation' 技能")
        print("\n请执行以下步骤:")
        print("1. 安装seedream技能:")
        print("   clawhub install seedream-image-generation")
        print("\n2. 配置火山引擎API key:")
        print("   a. 访问 https://www.volcengine.com/")
        print("   b. 注册并登录火山引擎控制台")
        print("   c. 进入「人工智能」->「智能创作」->「Seedream」")
        print("   d. 创建API Key并获取Access Key和Secret Key")
        print("   e. 在seedream技能中配置API key")
        print("\n3. 确保账户有足够余额:")
        print("   a. 在火山引擎控制台充值")
        print("   b. 查看Seedream服务余额")
        print("=" * 60)
        return False
    
    # 检查seedream模块是否可导入
    try:
        sys.path.insert(0, str(seedream_skill_path))
        from seedream import generate_image as seedream_generate
        print("✅ seedream技能可用")
        return True
    except ImportError as e:
        print(f"❌ 导入seedream模块失败: {e}")
        print("请确保seedream技能已正确安装和配置")
        return False
    except Exception as e:
        print(f"❌ seedream技能检查失败: {e}")
        return False

def get_daily_theme(knowledge, history_file=None):
    """获取随机主题（每次运行都不同）"""
    all_themes = list(knowledge["全年通用"].keys())
    if not all_themes:
        return "健康科普", knowledge["全年通用"].get("健康科普", {})
    
    # 每次运行都是真正的随机选择
    import random
    theme_index = random.randint(0, len(all_themes) - 1)
    
    theme_key = all_themes[theme_index]
    theme_data = knowledge["全年通用"][theme_key]
    
    return theme_key, theme_data

def get_optimal_image_size(content):
    """根据内容长度选择最优图片尺寸"""
    description = content.get('description', '')
    points = content.get('points', [])
    title = content.get('title', '')
    subtitle = content.get('subtitle', '')

    # 计算内容复杂度评分
    desc_length = len(description)
    title_length = len(title) + len(subtitle)
    points_text_length = sum(len(str(p)) for p in points)

    # 复杂度评分 (0-100)
    complexity_score = min(100, (desc_length * 0.5 + points_text_length * 0.3 + title_length * 0.2))

    # 根据复杂度选择尺寸（宽度固定1440px，高度动态调整）
    if complexity_score < 40:
        # 内容简单，使用标准手机尺寸
        return "1440x2560", "2304x4096"  # 9:16 比例
    elif complexity_score < 70:
        # 内容中等，使用稍高尺寸
        return "1440x2880", "2304x4608"  # 10:16 比例
    else:
        # 内容丰富，使用最高尺寸
        return "1440x3200", "2304x5120"  # 11:16 比例

def create_image_prompt(content, org_name="", size_hint="2304x4096"):
    """创建图片生成提示"""
    title = content['title']
    subtitle = content['subtitle']
    description = content.get('description', '')
    points = content.get('points', [])
    colors = content.get('colors', '清新的蓝色、绿色调，健康元素')
    
    # 构建提示
    prompt_parts = []
    
    # 基本描述
    prompt_parts.append(f"生成一张健康科普海报图片。")
    prompt_parts.append(f"主题: {title}")
    prompt_parts.append(f"副标题: {subtitle}")
    
    if description:
        prompt_parts.append(f"")
        prompt_parts.append(f"{description}")
    
    if points:
        prompt_parts.append(f"")
        prompt_parts.append(f"核心知识点:")
        for i, point in enumerate(points[:4], 1):
            prompt_parts.append(f"{i}. {point}")
    
def create_image_prompt(content, org_name="", size_hint="2304x4096"):
    """创建图片生成提示"""
    title = content['title']
    subtitle = content['subtitle']
    description = content.get('description', '')
    points = content.get('points', [])
    colors = content.get('colors', '清新的蓝色、绿色调，健康元素')
    
    # 构建提示
    prompt_parts = []
    
    # 基本描述
    prompt_parts.append(f"生成一张健康科普海报图片。")
    prompt_parts.append(f"主题: {title}")
    prompt_parts.append(f"副标题: {subtitle}")
    
    if description:
        prompt_parts.append(f"")
        prompt_parts.append(f"{description}")
    
    if points:
        prompt_parts.append(f"")
        prompt_parts.append(f"核心知识点:")
        for i, point in enumerate(points[:4], 1):
            prompt_parts.append(f"{i}. {point}")
    
    # 设计要求
    prompt_parts.append(f"")
    prompt_parts.append(f"设计要求:")
    prompt_parts.append(f"- 图片尺寸: {size_hint} (手机竖屏比例，宽度固定适合手机查看)")
    prompt_parts.append(f"- 配色方案: {colors}")
    
    if org_name:
        prompt_parts.append(f"- 左上角添加\"{org_name}\"字样")
    
    prompt_parts.append(f"- 底部添加\"{content['date']} {content['weekday']}\"字样（字体稍小，颜色稍淡）")
    prompt_parts.append(f"- 布局: 模块化卡片式设计，简洁明了，根据内容多少自动调整布局")
    prompt_parts.append(f"- 风格: 现代、专业、清晰易读")
    prompt_parts.append(f"- 字体: 使用清晰易读的中文字体")
    prompt_parts.append(f"- 元素: 包含相关健康图标或插图")
    prompt_parts.append(f"- 整体效果: 适合社交媒体分享的健康教育海报")
    
    prompt_parts.append(f"")
    prompt_parts.append(f"请生成高质量的健康科普海报图片，确保文字清晰可读，设计专业美观。如果内容较多，请合理利用纵向空间。")
    
    return "\n".join(prompt_parts)

def generate_image(content, output_dir, org_name=""):
    """生成海报图片"""
    try:
        # 检查依赖
        if not check_seedream_dependency():
            return None
        
        # 导入seedream模块
        seedream_skill_path = Path("/root/.openclaw/workspace/skills/seedream-image-generation")
        sys.path.insert(0, str(seedream_skill_path))
        from seedream import generate_image as seedream_generate
        
        # 根据内容选择最优尺寸
        actual_size, size_hint = get_optimal_image_size(content)
        
        # 创建提示
        prompt = create_image_prompt(content, org_name, size_hint)
        
        print(f"🖼️ 生成海报: {content['title']}")
        print(f"📐 使用尺寸: {actual_size} (宽度固定，高度自适应)")
        
        # 调用seedream生成图片
        result = seedream_generate(
            prompt=prompt,
            model="doubao-seedream-4-5-251128",  # 使用指定的4.5版本模型
            size=actual_size,  # 使用动态选择的尺寸
            watermark=False,
            download_dir=output_dir
        )
        
        if 'error' in result:
            error_msg = str(result.get('error', ''))
            error_details = str(result.get('message', ''))
            
            print(f"❌ 图片生成失败: {error_msg}")
            
            # 检查是否为余额不足错误
            error_lower = (error_msg + error_details).lower()
            balance_keywords = ['余额', 'insufficient', 'quota', 'credit', '额度', 'balance', 'exceeded', 'limit']
            
            if any(keyword in error_lower for keyword in balance_keywords):
                print("\n⚠️ **API余额不足**")
                print("=" * 60)
                print("火山引擎Seedream API余额不足，请按以下步骤处理:")
                print("\n1. 登录火山引擎控制台:")
                print("   https://www.volcengine.com/")
                print("\n2. 检查Seedream服务余额:")
                print("   a. 进入「人工智能」->「智能创作」->「Seedream」")
                print("   b. 查看账户余额和使用情况")
                print("\n3. 充值:")
                print("   a. 在控制台找到「费用中心」")
                print("   b. 选择「充值」")
                print("   c. 选择充值金额并完成支付")
                print("\n4. 重新尝试生成海报")
                print("=" * 60)
            
            return None
        
        if 'data' in result and result['data']:
            image_data = result['data'][0]
            if 'local_path' in image_data:
                image_path = image_data['local_path']
                print(f"✅ 图片生成成功: {image_path}")
                return image_path
        
        return None
        
    except Exception as e:
        print(f"❌ 生成图片时出错: {e}")
        return None

def save_content(content, image_path, output_dir):
    """保存内容到文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 更新内容
    content['image_path'] = image_path
    
    # 保存JSON
    json_file = os.path.join(output_dir, "content.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    # 保存文本
    text_file = os.path.join(output_dir, "poster.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"标题: {content['title']}\n")
        f.write(f"副标题: {content['subtitle']}\n")
        f.write(f"日期: {content['date']} {content['weekday']}\n")
        f.write(f"主题: {content['theme']}\n")
        f.write(f"图片: {image_path}\n\n")
        if 'description' in content:
            f.write(f"描述: {content['description']}\n\n")
        f.write("知识点:\n")
        for i, point in enumerate(content.get('points', []), 1):
            f.write(f"{i}. {point}\n")
    
    return json_file, text_file

def generate_poster(theme=None, org_name="", output_dir=None, knowledge_file=None):
    """生成海报主函数"""
    
    # 加载配置
    config = Config.load()
    if not org_name:
        org_name = config.get("organization_name", "")
    
    if not output_dir:
        output_dir = config.get("output_base", "~/health_posters")
        if output_dir.startswith("~"):
            output_dir = os.path.expanduser(output_dir)
    
    print("=" * 60)
    print("健康科普海报生成器（专业版）")
    print("=" * 60)
    
    if org_name:
        print(f"🏢 组织名称: {org_name}")
    else:
        print(f"🏢 组织名称: 未设置（左上角将不显示组织名称）")
    
    today = datetime.now()
    date_folder = today.strftime("%Y%m%d")
    final_output_dir = os.path.join(output_dir, date_folder)
    
    print(f"📅 日期: {today.strftime('%Y年%m月%d日 %A')}")
    print(f"📁 输出目录: {final_output_dir}")
    
    # 加载知识库
    print("\n📚 加载健康知识库...")
    knowledge = load_health_knowledge(knowledge_file)
    
    # 获取主题
    if theme:
        if theme in knowledge["全年通用"]:
            theme_key = theme
            theme_data = knowledge["全年通用"][theme]
            print(f"🎯 使用指定主题: {theme_key}")
        else:
            print(f"❌ 主题 '{theme}' 不存在，使用随机主题")
            theme_key, theme_data = get_daily_theme(knowledge)
    else:
        theme_key, theme_data = get_daily_theme(knowledge)
        print(f"🎲 使用随机主题: {theme_key}")
    
    # 生成内容
    content = {
        "title": theme_data.get("title", theme_key),
        "subtitle": theme_data.get("subtitle", "健康知识"),
        "description": theme_data.get("description", ""),
        "points": theme_data.get("points", theme_data.get("prevention_points", [])),
        "colors": theme_data.get("colors", "清新的蓝色、绿色调，健康元素"),
        "theme": theme_key,
        "date": today.strftime("%Y年%m月%d日"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
        "generated_at": today.isoformat()
    }
    
    print(f"📌 标题: {content['title']}")
    print(f"📝 副标题: {content['subtitle']}")
    if content.get('description'):
        print(f"📋 描述: {content['description'][:50]}...")
    
    # 生成图片
    print("\n🖼️ 生成海报图片...")
    image_path = generate_image(content, final_output_dir, org_name)
    
    if not image_path:
        print("❌ 图片生成失败")
        return None
    
    # 保存内容
    print("\n💾 保存内容文件...")
    json_file, text_file = save_content(content, image_path, final_output_dir)
    print(f"✅ JSON文件: {json_file}")
    print(f"✅ 文本文件: {text_file}")
    
    print("\n🎉 海报生成完成!")
    print(f"📷 图片路径: {image_path}")
    print(f"📄 内容文件: {json_file}")
    
    return {
        "image_path": image_path,
        "content_file": json_file,
        "text_file": text_file,
        "content": content
    }

# ==================== 命令行接口 ====================

def list_themes(knowledge_file=None):
    """列出所有可用主题"""
    knowledge = load_health_knowledge(knowledge_file)
    
    print("\n📚 可用健康主题列表:")
    print("=" * 60)
    
    themes = list(knowledge["全年通用"].keys())
    themes.sort()
    
    for i, theme in enumerate(themes, 1):
        theme_data = knowledge["全年通用"][theme]
        title = theme_data.get("title", theme)
        print(f"{i:3d}. {title} ({theme})")
    
    print(f"\n总计: {len(themes)} 个主题")
    return themes

def configure_skill():
    """配置技能"""
    print("\n⚙️ 健康海报生成器配置")
    print("=" * 60)
    
    config = Config.load()
    
    print("\n当前配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n配置选项:")
    print("1. 设置组织/商会名称（左上角显示的文字）")
    print("2. 设置输出目录")
    print("3. 设置知识库文件路径")
    print("4. 显示当前配置")
    print("5. 恢复默认配置")
    print("0. 返回")
    
    choice = input("\n请选择 (0-5): ").strip()
    
    if choice == "1":
        org_name = input("请输入组织/商会名称（留空则不显示）: ").strip()
        config["organization_name"] = org_name
        if Config.save(config):
            print(f"✅ 组织名称已设置为: '{org_name if org_name else '空'}'")
    
    elif choice == "2":
        output_dir = input("请输入输出目录（支持~路径）: ").strip()
        if output_dir:
            config["output_base"] = output_dir
            if Config.save(config):
                print(f"✅ 输出目录已设置为: {output_dir}")
    
    elif choice == "3":
        knowledge_file = input("请输入知识库文件路径（留空使用默认）: ").strip()
        if knowledge_file:
            if os.path.exists(knowledge_file):
                config["knowledge_file"] = knowledge_file
                if Config.save(config):
                    print(f"✅ 知识库文件路径已设置为: {knowledge_file}")
            else:
                print(f"❌ 文件不存在: {knowledge_file}")
        else:
            config["knowledge_file"] = None
            if Config.save(config):
                print("✅ 已恢复使用默认知识库")
    
    elif choice == "4":
        Config.show_current()
    
    elif choice == "5":
        config = Config.DEFAULT_CONFIG.copy()
        if Config.save(config):
            print("✅ 已恢复默认配置")
    
    elif choice == "0":
        print("返回主菜单")
    
    else:
        print("❌ 无效选择")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='健康科普海报生成器（专业版）')
    parser.add_argument('--theme', type=str, help='指定主题（不指定则随机选择）')
    parser.add_argument('--org-name', type=str, help='组织/商会名称（左上角显示）')
    parser.add_argument('--output-dir', type=str, help='输出目录')
    parser.add_argument('--knowledge-file', type=str, help='知识库文件路径')
    parser.add_argument('--list-themes', action='store_true', help='列出所有可用主题')
    parser.add_argument('--configure', action='store_true', help='配置技能')
    parser.add_argument('--show-config', action='store_true', help='显示当前配置')
    
    args = parser.parse_args()
    
    if args.configure:
        configure_skill()
        return
    
    if args.show_config:
        Config.show_current()
        return
    
    if args.list_themes:
        list_themes(args.knowledge_file)
        return
    
    # 生成海报
    result = generate_poster(
        theme=args.theme,
        org_name=args.org_name,
        output_dir=args.output_dir,
        knowledge_file=args.knowledge_file
    )
    
    if result:
        print("\n🎯 使用说明:")
        print("-" * 40)
        print("生成的图片和内容文件已保存，路径如上所示")
        print("\n📋 后续操作建议:")
        print("1. 查看生成的内容: cat", result["text_file"])
        print("2. 配置技能（设置组织名称等）:")
        print("   python3", __file__, "--configure")
        print("3. 列出所有可用主题:")
        print("   python3", __file__, "--list-themes")
        print("4. 再次生成（指定主题）:")
        print("   python3", __file__, "--theme '口腔健康'")
        print("-" * 40)
    else:
        print("\n❌ 海报生成失败，请检查错误信息")

if __name__ == "__main__":
    main()