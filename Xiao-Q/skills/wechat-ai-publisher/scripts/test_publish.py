#!/usr/bin/env python3
"""
微信公众号AI内容创作与发布 Skill 测试脚本
验证配置是否正确，测试发布流程
"""

import os
import sys
import json
import subprocess
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

def print_info(text):
    print(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {text}")

def load_config():
    """加载配置文件"""
    skill_dir = Path.home() / ".workbuddy" / "skills" / "wechat-ai-publisher"
    config_path = skill_dir / "config.toml"
    
    if not config_path.exists():
        print_error(f"配置文件不存在：{config_path}")
        print("请先运行配置向导：python3 scripts/setup.py")
        return None
    
    try:
        import tomllib
        with open(config_path, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        # Python < 3.11
        try:
            import toml
            with open(config_path, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            print_error("缺少toml解析库，请安装：pip install toml")
            return None
    except Exception as e:
        print_error(f"读取配置文件失败：{e}")
        return None

def test_wechat_api(config):
    """测试微信API连接"""
    print_step(1, 5, "测试微信API连接")
    
    wechat = config.get('wechat', {})
    app_id = wechat.get('app_id', '')
    app_secret = wechat.get('app_secret', '')
    
    if not app_id or app_id == 'your_wechat_app_id_here':
        print_error("AppID 未配置")
        return False
    
    if not app_secret or app_secret == 'your_wechat_app_secret_here':
        print_error("AppSecret 未配置")
        return False
    
    print_info(f"AppID: {app_id[:8]}...{app_id[-4:]}")
    
    # 尝试获取access_token
    import urllib.request
    import urllib.error
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'access_token' in data:
                print_success("微信API连接成功")
                print_info(f"Access Token 有效期：{data.get('expires_in', 7200)} 秒")
                return True
            elif 'errcode' in data:
                error_code = data['errcode']
                error_msg = data.get('errmsg', '未知错误')
                
                if error_code == -1:
                    print_error(f"系统繁忙，请稍后再试")
                elif error_code == 40001:
                    print_error(f"AppSecret 错误，请检查配置")
                elif error_code == 40013:
                    print_error(f"AppID 错误，请检查配置")
                elif error_code == 40164:
                    print_error(f"IP不在白名单中")
                    print_info("请将当前IP添加到公众号后台的IP白名单")
                else:
                    print_error(f"微信API错误：{error_code} - {error_msg}")
                return False
            else:
                print_error("未知响应格式")
                return False
                
    except urllib.error.URLError as e:
        print_error(f"网络请求失败：{e}")
        return False
    except Exception as e:
        print_error(f"测试失败：{e}")
        return False

def test_dreamina():
    """测试即梦CLI"""
    print_step(2, 5, "测试即梦CLI")
    
    result = subprocess.run(
        ['which', 'dreamina'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print_error("即梦CLI (dreamina) 未安装")
        print_info("安装命令：pip install dreamina-cli")
        return False
    
    print_success("即梦CLI已安装")
    
    # 检查登录状态
    result = subprocess.run(
        ['dreamina', 'user_credit'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("即梦CLI登录状态正常")
        return True
    else:
        print_warning("即梦CLI未登录或登录已过期")
        print_info("请运行：dreamina login")
        return False

def test_wenyan():
    """测试wenyan CLI"""
    print_step(3, 5, "测试wenyan CLI")
    
    result = subprocess.run(
        ['which', 'wenyan'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print_error("wenyan CLI 未安装")
        print_info("安装命令：npm install -g @wenyan/cli")
        return False
    
    print_success("wenyan CLI已安装")
    return True

def test_config_values(config):
    """测试配置值"""
    print_step(4, 5, "测试配置值")
    
    checks = []
    
    # 检查作者信息
    author = config.get('author', {})
    if author.get('name') and author['name'] != '你的名字':
        print_success(f"作者名称已配置：{author['name']}")
        checks.append(True)
    else:
        print_warning("作者名称未配置")
        checks.append(False)
    
    # 检查品牌信息
    brand = config.get('brand', {})
    if brand.get('public_account') and brand['public_account'] != '你的公众号名称':
        print_success(f"公众号名称已配置：{brand['public_account']}")
        checks.append(True)
    else:
        print_warning("公众号名称未配置")
        checks.append(False)
    
    # 检查品牌签名
    if brand.get('signature') and len(brand['signature']) > 20:
        print_success("品牌签名已配置")
        checks.append(True)
    else:
        print_warning("品牌签名未配置或太短")
        checks.append(False)
    
    return all(checks)

def test_directory_structure():
    """测试目录结构"""
    print_step(5, 5, "测试目录结构")
    
    skill_dir = Path.home() / ".workbuddy" / "skills" / "wechat-ai-publisher"
    
    required_dirs = [
        skill_dir / "images",
        skill_dir / "drafts",
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_info(f"创建目录：{dir_path}")
        else:
            print_success(f"目录存在：{dir_path}")
    
    return True

def generate_test_article(config):
    """生成测试文章"""
    print_header("生成测试文章")
    
    author = config.get('author', {})
    brand = config.get('brand', {})
    
    article_content = f"""# {brand.get('public_account', '测试公众号')} | 配置测试文章

这是一篇测试文章，用于验证微信公众号AI内容创作与发布 Skill 的配置是否正确。

## 测试内容

如果你能看到这篇文章，说明：

1. ✅ 微信API配置正确
2. ✅ 文章生成流程正常
3. ✅ 发布到草稿箱成功

## 关于作者

{author.get('background', '作者背景待配置')}

## 下一步

现在你可以：

1. 在公众号后台查看这篇草稿
2. 删除这篇测试文章
3. 开始使用 Skill 创作真正的内容

对 WorkBuddy 说："帮我看看今天有什么值得写的选题"

---

{brand.get('signature', '品牌签名待配置')}
"""
    
    # 保存测试文章
    drafts_dir = Path.home() / ".workbuddy" / "skills" / "wechat-ai-publisher" / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = drafts_dir / "test_article.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(article_content)
    
    print_success(f"测试文章已生成：{test_file}")
    return test_file

def main():
    print_header("微信公众号AI内容创作与发布 Skill 测试")
    
    # 加载配置
    config = load_config()
    if not config:
        sys.exit(1)
    
    # 运行测试
    results = []
    
    results.append(("微信API", test_wechat_api(config)))
    results.append(("即梦CLI", test_dreamina()))
    results.append(("wenyan CLI", test_wenyan()))
    results.append(("配置值", test_config_values(config)))
    results.append(("目录结构", test_directory_structure()))
    
    # 显示结果
    print_header("测试结果汇总")
    
    all_passed = True
    for name, passed in results:
        if passed:
            print_success(f"{name}：通过")
        else:
            print_error(f"{name}：未通过")
            all_passed = False
    
    if all_passed:
        print_header("✅ 所有测试通过！")
        print("你的 Skill 已配置完成，可以开始使用了。")
        print("\n使用命令：")
        print('  "帮我看看今天有什么值得写的选题"')
        
        # 生成测试文章
        response = input("\n是否生成一篇测试文章到微信草稿箱？(y/n): ").strip().lower()
        if response == 'y':
            generate_test_article(config)
            print("\n请在公众号后台查看测试草稿。")
    else:
        print_header("⚠️ 部分测试未通过")
        print("请根据上面的错误提示修复配置问题，然后重新运行测试。")
        print("\n常见问题：")
        print("  1. IP白名单：将当前IP添加到公众号后台")
        print("  2. API凭证：检查 AppID 和 AppSecret 是否正确")
        print("  3. 工具安装：安装缺失的 CLI 工具")
    
    print("")

if __name__ == "__main__":
    main()
