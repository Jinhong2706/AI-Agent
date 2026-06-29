"""
测试 UnityOpsListener 的 Manual 命令
通过 TCP 连接到 Unity 编辑器的 UnityOpsListener 服务，发送 Manual 命令并打印结果。
"""

import socket
import json
import argparse


def send_command(command: dict[str, str], host: str = "127.0.0.1", port: int = 8888) -> str:
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


def test_manual(full: bool = False):
    """测试 Manual 命令：获取所有可用 API 的 Markdown 手册

    Args:
        full: 是否请求完整手册（包含详细说明）
    """
    command = {
        "action": "CoreOperations.Manual",
        "full": "true" if full else "false"
    }

    response = send_command(command=command)

    # 解析响应
    try:
        result = json.loads(response)
        if result.get("status") == "success":
            print("\n[成功] Manual 命令执行成功！")
            print("=" * 60)
            # 还原转义的 Markdown 内容
            manual = result.get("manual", "").replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
            print(manual)
            print("=" * 60)
        else:
            print(f"\n[失败] {result}")
    except json.JSONDecodeError:
        print(f"\n[响应] 无法解析 JSON：{response}")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="测试 CoreOperations 的 Manual 命令")
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        default=False,
        help="请求完整手册（包含详细说明）"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  CoreOperations - Manual 命令测试")
    print("  确保已启动 Unity 编辑器并运行 UnityOpsListener 服务器")
    print(f"  默认连接: 127.0.0.1:8888")
    if args.full:
        print("  模式: 完整手册 (full)")
    else:
        print("  模式: 精简手册")
    print("=" * 60)
    print()

    try:
        test_manual(full=args.full)
    except ConnectionRefusedError:
        print("[错误] 连接被拒绝！请确认:")
        print("  1. Unity 编辑器已打开")
        print("  2. 已在 Unity 中启动 UnityOpsListener 服务器 (Tools -> UnityOpsListener)")
        print("  3. 端口 8888 未被占用")
    except TimeoutError:
        print("[错误] 连接超时！服务器可能未响应。")
    except Exception as e:
        print(f"[错误] {type(e).__name__}: {e}")
