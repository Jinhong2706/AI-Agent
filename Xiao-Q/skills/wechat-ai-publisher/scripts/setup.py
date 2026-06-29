#!/usr/bin/env python3
"""
微信公众号AI内容创作与发布 Skill 配置向导
引导用户完成初始配置
"""

import os
import sys
import json
from pathlib import Path

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_step(step, total, text):
    print(f"{Colors.OKCYAN}[步骤 {step}/{total}]{Colors.ENDC} {text}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {text}")

def print_error(text):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")

def input_required(prompt):
    while True:
        value = input(f"{Colors.OKBLUE}?{Colors.ENDC} {prompt}: ").strip()
        if value:
            return value
        print_error("此项不能为空，请重新输入")

def input_optional(prompt, default=""):
    value = input(f"{Colors.OKBLUE}?{Colors.ENDC} {prompt} [{default}]: ").strip()
    return value if value else default

def check_prerequisites():
    """检查前置条件"""
    print_header("检查前置条件")
    
    checks = []
    
    # 检查即梦CLI
    result = os.system("which dreamina > /dev/null 2>&1")
    if result == 0:
        print_success("即梦CLI (dreamina) 已安装")
        checks.append(True)
    else:
        print_error("即梦CLI (dreamina) 未安装")
        print("  安装命令: pip install dreamina-cli")
        checks.append(False)
    
    # 检查wenyan
    result = os.system("which wenyan > /dev/null 2>&1")
    if result == 0:
        print_success("wenyan CLI 已安装")
        checks.append(True)
    else:
        print_error("wenyan CLI 未安装")
        print("  安装命令: npm install -g @wenyan/cli")
        checks.append(False)
    
    # 检查WorkBuddy
    wb_dir = Path.home() / ".workbuddy"
    if wb_dir.exists():
        print_success("WorkBuddy 目录已存在")
        checks.append(True)
    else:
        print_warning("WorkBuddy 目录不存在，将自动创建")
        checks.append(True)
    
    if all(checks):
        print_success("所有前置条件已满足！")
        return True
    else:
        print_warning("部分前置条件未满足，请先安装缺失的工具")
        return False

def setup_wechat_config():
    """配置微信公众号"""
    print_step(1, 4, "配置微信公众号API")
    
    print("\n请从微信公众号后台获取以下信息：")
    print("  路径：设置与开发 → 基本配置 → 开发者ID")
    
    app_id = input_required("微信公众号 AppID")
    app_secret = input_required("微信公众号 AppSecret")
    
    print("\n" + "="*60)
    print("重要提示：")
    print("  1. 需要在公众号后台配置IP白名单")
    print("  2. 当前IP地址将在配置完成后显示")
    print("  3. 如果IP变动，需要重新配置白名单")
    print("="*60 + "\n")
    
    return {"app_id": app_id, "app_secret": app_secret}

def setup_author_info():
    """配置作者信息"""
    print_step(2, 4, "配置作者信息")
    
    print("\n这些信息将用于文章署名和品牌签名\n")
    
    name = input_required("你的名字（用于署名）")
    title = input_required("你的称号（如：AI实战派、技术博主）")
    
    print("\n个人背景介绍（支持多行，输入空行结束）：")
    print("示例：清华本科，腾讯10年老员工，AI创业者...")
    background_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        background_lines.append(line)
    background = "\n".join(background_lines)
    
    expertise = input_required("你擅长的AI领域（如：AI落地、企业培训、工具测评）")
    
    return {
        "name": name,
        "title": title,
        "background": background,
        "expertise": expertise
    }

def setup_brand_info(author_name):
    """配置品牌信息"""
    print_step(3, 4, "配置品牌信息")
    
    print("\n公众号品牌信息\n")
    
    public_account = input_required("公众号名称")
    slogan = input_optional("公众号口号", f"{author_name}说AI，每天带你读懂AI圈")
    
    print("\n品牌签名文字（显示在每篇文章末尾，支持多行，输入空行结束）：")
    print("示例：")
    print(f"我是{author_name}，[你的背景]")
    print("[你的成就/项目]")
    print("对AI感兴趣？欢迎关注本公众号。")
    print("")
    
    signature_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        signature_lines.append(line)
    signature = "\n".join(signature_lines)
    
    print("\n引导关注图片：")
    print("  建议尺寸：900x386（21:9），小于2MB")
    footer_image = input_optional("引导关注图片路径", "images/footer-guide.png")
    
    return {
        "public_account": public_account,
        "slogan": slogan,
        "signature": signature,
        "footer_image": footer_image
    }

def setup_content_strategy():
    """配置内容策略"""
    print_step(4, 4, "配置内容策略")
    
    print("\n内容策略设置\n")
    
    print("文章类型（可多选，用逗号分隔）：")
    print("  1. 深度解读")
    print("  2. 工具推荐")
    print("  3. 观点专栏")
    print("  4. 实战案例")
    
    types_input = input_optional("选择文章类型", "1,2,3,4")
    type_map = {
        "1": "深度解读",
        "2": "工具推荐",
        "3": "观点专栏",
        "4": "实战案例"
    }
    article_types = [type_map.get(t.strip(), t.strip()) for t in types_input.split(",")]
    
    daily_limit = int(input_optional("每日发布上限", "1"))
    min_words = int(input_optional("最少字数要求", "800"))
    
    return {
        "article_types": article_types,
        "daily_limit": daily_limit,
        "min_word_count": min_words
    }

def generate_config(wechat, author, brand, content):
    """生成配置文件"""
    skill_dir = Path.home() / ".workbuddy" / "skills" / "wechat-ai-publisher"
    config_path = skill_dir / "config.toml"
    
    config_content = f'''# 微信公众号AI内容创作与发布 Skill 配置
# 生成时间：自动生成

[wechat]
app_id = "{wechat['app_id']}"
app_secret = "{wechat['app_secret']}"

[author]
name = "{author['name']}"
title = "{author['title']}"
background = """
{author['background']}
"""
expertise = "{author['expertise']}"

[brand]
public_account = "{brand['public_account']}"
slogan = "{brand['slogan']}"
signature = """
{brand['signature']}
"""
footer_image = "{brand['footer_image']}"

[content]
article_types = {json.dumps(content['article_types'], ensure_ascii=False)}
daily_limit = {content['daily_limit']}
min_word_count = {content['min_word_count']}
depth_min_word_count = 1500

[image]
ratio = "21:9"
resolution = "2k"
max_size_kb = 600

[publish]
author_name = "{author['name']}"
theme = "orange"
auto_append_signature = true
auto_append_footer_image = true

[news]
primary_sources = ["腾讯科技"]
secondary_sources = ["36氪", "品玩", "Solidot"]
tech_sources = ["GitHub Trending", "Hacker News"]
excluded_sources = ["知乎"]

[quality]
forbidden_words = ["登顶", "碾压", "颠覆", "跪求", "震惊", "绝了"]
max_lines_per_paragraph = 4
checklist = [
    "标题符合规范",
    "有实战视角板块",
    "品牌签名已追加",
    "没有敏感词",
    "段落不超过4行"
]
'''
    
    # 确保目录存在
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入配置
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    return config_path

def show_current_ip():
    """显示当前IP地址"""
    import socket
    try:
        # 获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "无法获取"

def main():
    print_header("微信公众号AI内容创作与发布 Skill 配置向导")
    
    # 检查前置条件
    if not check_prerequisites():
        response = input("\n是否继续配置？(y/n): ").strip().lower()
        if response != 'y':
            print("配置已取消")
            return
    
    # 收集配置信息
    wechat = setup_wechat_config()
    author = setup_author_info()
    brand = setup_brand_info(author["name"])
    content = setup_content_strategy()
    
    # 生成配置文件
    print_header("生成配置文件")
    config_path = generate_config(wechat, author, brand, content)
    print_success(f"配置文件已生成：{config_path}")
    
    # 显示当前IP
    current_ip = show_current_ip()
    print(f"\n{Colors.WARNING}重要：请将以下IP添加到微信公众号白名单{Colors.ENDC}")
    print(f"当前IP地址：{Colors.BOLD}{current_ip}{Colors.ENDC}")
    print("添加路径：公众号后台 → 设置与开发 → 基本配置 → IP白名单")
    
    # 下一步提示
    print_header("配置完成！")
    print("下一步：")
    print("  1. 在公众号后台添加IP白名单")
    print("  2. 准备引导关注图片并放到配置的路径")
    print("  3. 运行测试脚本验证配置：")
    print(f"     python3 {Path.home() / '.workbuddy' / 'skills' / 'wechat-ai-publisher' / 'scripts' / 'test_publish.py'}")
    print("\n使用 Skill：")
    print("  对 WorkBuddy 说：\"帮我看看今天有什么值得写的选题\"")
    print("")

if __name__ == "__main__":
    main()
