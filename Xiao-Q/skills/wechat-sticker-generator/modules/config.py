import os
import sys
import json

CONFIG_FILE = os.path.expanduser("~/.sticker_generator_config.json")

DEFAULT_CONFIG = {
    "default_provider": "gemini",
    "providers": {
        "gemini": {
            "api_key_env": "GEMINI_API_KEY",
            "alt_env_keys": ["GOOGLE_API_KEY"],
            "model": "gemini-3.1-flash-image-preview",
            "text_model": "gemini-2.5-flash",
            "description": "Google Gemini - 推荐，效果好速度快"
        },
        "qwen": {
            "api_key_env": "DASHSCOPE_API_KEY",
            "alt_env_keys": ["QWEN_API_KEY"],
            "model": "qwen-image-2.0-pro",
            "text_model": "qwen-max",
            "description": "阿里千问 - 国内访问稳定"
        }
    }
}

def load_config():
    """加载配置文件，不存在则返回默认配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置（确保新增的 provider 也能用）
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                for provider, settings in DEFAULT_CONFIG["providers"].items():
                    if provider not in config["providers"]:
                        config["providers"][provider] = settings
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"[✓] 配置已保存到: {CONFIG_FILE}")

def get_api_key(provider_name=None):
    """
    获取指定 provider 的 API Key
    """
    config = load_config()
    provider = provider_name or config.get("default_provider", "gemini")
    provider_config = config["providers"].get(provider)

    if not provider_config:
        print(f"[!] 未知的 provider: {provider}", file=sys.stderr)
        print(f"[*] 可用的 providers: {list(config['providers'].keys())}", file=sys.stderr)
        return None, provider

    # 1. 检查配置文件中的 api_key
    if provider_config.get("api_key"):
        return provider_config["api_key"], provider

    # 2. 检查主环境变量
    main_env = provider_config.get("api_key_env", f"{provider.upper()}_API_KEY")
    api_key = os.environ.get(main_env)
    if api_key:
        return api_key, provider

    # 3. 检查备选环境变量
    for alt_env in provider_config.get("alt_env_keys", []):
        api_key = os.environ.get(alt_env)
        if api_key:
            return api_key, provider

    # 没有 key，给出提示
    print("\n" + "="*60, file=sys.stderr)
    print(f"❌ 缺少 {provider.upper()} API Key", file=sys.stderr)
    print("="*60, file=sys.stderr)

    if provider == "gemini":
        print("\n获取 Gemini API Key:", file=sys.stderr)
        print("  1. 访问: https://aistudio.google.com/app/apikey", file=sys.stderr)
        print("  2. 登录 Google 账号并创建 API Key", file=sys.stderr)
    elif provider == "qwen":
        print("\n获取千问 API Key:", file=sys.stderr)
        print("  1. 访问: https://dashscope.console.aliyun.com/", file=sys.stderr)
        print("  2. 开通服务并获取 API Key", file=sys.stderr)

    print(f"\n配置方式（三选一）：", file=sys.stderr)
    print(f"  方式A - 环境变量：", file=sys.stderr)
    print(f'    export {main_env}="你的API_Key"', file=sys.stderr)
    print(f"\n  方式B - 配置文件（交互式）：", file=sys.stderr)
    print(f'    python sticker_utils.py config set {provider}', file=sys.stderr)
    print(f"\n  方式C - 切换到其他 provider：", file=sys.stderr)
    print(f'    python sticker_utils.py config default qwen', file=sys.stderr)
    print("\n" + "="*60 + "\n", file=sys.stderr)

    return None, provider

def show_config():
    """显示当前配置"""
    config = load_config()
    print("\n" + "="*60)
    print("📋 Sticker Generator 配置")
    print("="*60)
    print(f"\n默认 Provider: {config.get('default_provider', 'gemini')}")
    print(f"配置文件: {CONFIG_FILE}")
    print("\n可用的 Providers:")
    for name, settings in config["providers"].items():
        has_key = "✅" if settings.get("api_key") or os.environ.get(settings.get("api_key_env", "")) else "❌"
        print(f"  {has_key} {name}: {settings.get('description', '')}")
    print("\n" + "="*60)

def config_command(args):
    """处理 config 子命令"""
    if not args:
        show_config()
        return

    cmd = args[0]
    config = load_config()

    if cmd == "set" and len(args) >= 2:
        provider = args[1]
        if provider not in config["providers"]:
            print(f"[!] 未知的 provider: {provider}")
            print(f"[*] 可用的: {list(config['providers'].keys())}")
            return

        if len(args) >= 3:
            api_key = args[2]
        else:
            import getpass
            api_key = getpass.getpass(f"请输入 {provider} API Key: ")

        config["providers"][provider]["api_key"] = api_key
        save_config(config)

    elif cmd == "default" and len(args) >= 2:
        provider = args[1]
        if provider not in config["providers"]:
            print(f"[!] 未知的 provider: {provider}")
            return
        config["default_provider"] = provider
        save_config(config)
        print(f"[✓] 默认 provider 已设置为: {provider}")

    elif cmd == "list":
        show_config()

    else:
        print("用法:")
        print("  config              - 显示当前配置")
        print("  config list         - 显示当前配置")
        print("  config set <provider> [key]  - 设置 API Key")
        print("  config default <provider>    - 设置默认 provider")
