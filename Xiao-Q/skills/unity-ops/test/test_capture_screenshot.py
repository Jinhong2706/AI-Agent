"""
测试 UnityOpsListener 的 CaptureScreenshot 命令
流程：
  1. 调用 test_create_model.py 在场景中生成多个几何体
  2. 使用不同视角预设（iso / top / front）对场景截图
  3. 验证截图文件是否成功保存
"""

import socket
import json
import argparse
import subprocess
import sys
import os


def send_command(command: dict, host: str = "127.0.0.1", port: int = 8888) -> str:
    """
    通过 TCP 发送命令到 UnityOpsListener 并返回响应。

    Args:
        host: UnityOpsListener 服务地址
        port: UnityOpsListener 监听端口
        command: 要发送的 JSON 命令字典

    Returns:
        服务器返回的原始字符串响应
    """
    message = json.dumps(command, ensure_ascii=False)
    print(f"[发送] {message}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(message.encode("utf-8"))
        response = s.recv(65536).decode("utf-8")

    return response


# ────────────────── 截图测试用例 ──────────────────

SCREENSHOT_TEST_CASES = [
    {
        "name": "等距视角截图 (iso)",
        "command": {
            "action": "CoreOperations.CaptureScreenshot",
            "angle_preset": "iso",
            "screenshot_width": 1920,
            "screenshot_height": 1080,
        },
    },
    {
        "name": "俯视视角截图 (top)",
        "command": {
            "action": "CoreOperations.CaptureScreenshot",
            "angle_preset": "top",
            "screenshot_width": 1280,
            "screenshot_height": 720,
        },
    },
    {
        "name": "正视视角截图 (front)",
        "command": {
            "action": "CoreOperations.CaptureScreenshot",
            "angle_preset": "front",
            "screenshot_width": 1280,
            "screenshot_height": 720,
        },
    },
    {
        "name": "自定义分辨率截图 (4K)",
        "command": {
            "action": "CoreOperations.CaptureScreenshot",
            "angle_preset": "iso",
            "screenshot_width": 3840,
            "screenshot_height": 2160,
            "fov": 45.0,
        },
    },
]


def run_create_model_script(host: str, port: int) -> bool:
    """调用 test_create_model.py 生成场景内容。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    create_model_script = os.path.join(script_dir, "test_create_model.py")
    
    if not os.path.exists(create_model_script):
        print(f"[错误] 找不到脚本: {create_model_script}")
        return False

    print(f"\n{'='*60}")
    print(f"  步骤 1/2: 调用 test_create_model.py 生成场景内容...")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, create_model_script, "--host", host, "--port", str(port)],
        capture_output=True,
        text=True,
    )

    # 输出子进程日志
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  [create_model] {line}")
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            print(f"  [create_model ERR] {line}")

    if result.returncode == 0:
        print(f"\n  ✓ 场景内容生成完成")
        return True
    else:
        print(f"\n  ✗ 场景内容生成失败 (退出码: {result.returncode})")
        return False


def test_capture_screenshot(
    host: str = "127.0.0.1",
    port: int = 8888,
    skip_setup: bool = False,
):
    """运行截图测试流程。

    Args:
        host: UnityOpsListener 服务地址
        port: UnityOpsListener 监听端口
        skip_setup: 跳过创建模型步骤，直接执行截图测试
    """
    # ── Step 1: 生成场景内容 ──
    if not skip_setup:
        if not run_create_model_script(host=host, port=port):
            print("\n[终止] 场景内容准备失败，无法继续截图测试。")
            return False
    else:
        print(f"\n{'='*60}")
        print(f"  已跳过模型创建步骤 (--skip-setup)")
        print(f"{'='*60}")

    # ── Step 2: 执行截图测试 ──
    passed = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"  步骤 2/2: 执行截图测试...")
    print(f"{'='*60}")

    for idx, case in enumerate(SCREENSHOT_TEST_CASES, start=1):
        name = case["name"]
        print(f"\n{'-'*60}")
        print(f"  截图测试 [{idx}/{len(SCREENSHOT_TEST_CASES)}]：{name}")
        print(f"{'-'*60}")

        response_str = send_command(command=case["command"], host=host, port=port)
        print(f"[接收] {response_str[:200]}...")

        try:
            result = json.loads(response_str)

            if result.get("status") == "success":
                path = result.get("path", "?")
                width = result.get("width", "?")
                height = result.get("height", "?")
                print(f"  ✓ 截图成功！")
                print(f"    路径: {path}")
                print(f"    尺寸: {width}x{height}")
                passed += 1
            else:
                msg = result.get("message", "未知原因")
                print(f"  ✗ 截图失败: {msg}")
                failed += 1

        except json.JSONDecodeError:
            print(f"  ✗ 响应无法解析为 JSON")
            failed += 1

    # 汇总
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  截图测试完成: {passed}/{total} 通过, {failed} 失败")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试 UnityOpsListener 的 CaptureScreenshot 命令")
    parser.add_argument("--host", default="127.0.0.1", help="UnityOpsListener 服务地址 (默认 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8888, help="UnityOpsListener 监听端口 (默认 8888)")
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="跳过调用 test_create_model.py 的场景准备步骤"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  UnityOpsListener - CaptureScreenshot 命令测试")
    print("  流程: 先生成场景内容 → 再多角度截图验证")
    print(f"  默认连接: {args.host}:{args.port}")
    if args.skip_setup:
        print("  模式: 跳过场景准备，直接截图")
    print("=" * 60)

    try:
        ok = test_capture_screenshot(host=args.host, port=args.port, skip_setup=args.skip_setup)
        exit(0 if ok else 1)
    except ConnectionRefusedError:
        print("\n[错误] 连接被拒绝！请确认:")
        print("  1. Unity 编辑器已打开")
        print("  2. 已在 Unity 中启动 UnityOpsListener 服务器 (Tools -> UnityOpsListener)")
        print("  3. 端口未占用")
        exit(2)
    except TimeoutError:
        print("\n[错误] 连接超时！服务器可能未响应。")
        exit(3)
    except Exception as e:
        print(f"\n[错误] {type(e).__name__}: {e}")
        exit(4)
