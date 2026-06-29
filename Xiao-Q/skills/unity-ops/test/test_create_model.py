"""
测试 UnityOpsListener 的 CreateModel 命令
通过 TCP 连接到 Unity 编辑器的 UnityOpsListener 服务，
发送 CoreOperations.CreateModel 命令并验证响应。
"""

import socket
import json
import argparse


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


# ────────────────── 测试用例定义 ──────────────────

TEST_CASES = [
    {
        "name": "创建默认 Cube",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
        },
    },
    # ── Cube 参数变体测试 ──
    {
        "name": "Cube - 正位置 (x=3, y=1, z=2)",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_Pos",
            "position": {"x": 3.0, "y": 1.0, "z": 2.0},
        },
    },
    {
        "name": "Cube - 负位置与零分量",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_NegPos",
            "position": {"x": -5.0, "y": 0.0, "z": -2.5},
        },
    },
    {
        "name": "Cube - 仅 X 轴旋转 90 度",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_RotX",
            "rotation": {"x": 90.0, "y": 0.0, "z": 0.0},
        },
    },
    {
        "name": "Cube - 三轴旋转 (30, 60, 45)",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_RotAll",
            "position": {"x": 1.0, "y": 2.0, "z": 0.0},
            "rotation": {"x": 30.0, "y": 60.0, "z": 45.0},
        },
    },
    {
        "name": "Cube - 均匀放大 scale(2,2,2)",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_ScaleUniform",
            "scale": {"x": 2.0, "y": 2.0, "z": 2.0},
        },
    },
    {
        "name": "Cube - 非均匀缩放 (0.5, 3, 0.5) 扁平高体",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_ScaleNonUniform",
            "position": {"x": -1.0, "y": 1.5, "z": 0.0},
            "scale": {"x": 0.5, "y": 3.0, "z": 0.5},
        },
    },
    {
        "name": "Cube - 全部变换参数组合",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cube",
            "name": "Cube_FullTransform",
            "position": {"x": 4.0, "y": 0.5, "z": -3.0},
            "rotation": {"x": 15.0, "y": -30.0, "z": 10.0},
            "scale": {"x": 1.2, "y": 2.5, "z": 0.8},
        },
    },
    {
        "name": "创建 Sphere 并指定名称与位置",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Sphere",
            "name": "MySphere",
            "position": {"x": 2.0, "y": 1.0, "z": 0.0},
        },
    },
    {
        "name": "创建 Cylinder 并设置旋转和缩放",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Cylinder",
            "name": "MyCylinder",
            "position": {"x": -2.0, "y": 0.5, "z": 0.0},
            "rotation": {"x": 0.0, "y": 45.0, "z": 0.0},
            "scale": {"x": 1.5, "y": 1.0, "z": 1.5},
        },
    },
    {
        "name": "创建 Capsule",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Capsule",
            "name": "MyCapsule",
            "position": {"x": 0.0, "y": 2.0, "z": 3.0},
        },
    },
    {
        "name": "创建 Plane",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Plane",
            "name": "Ground",
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scale": {"x": 10.0, "y": 1.0, "z": 10.0},
        },
    },
    {
        "name": "传入不支持的类型（预期返回 error）",
        "command": {
            "action": "CoreOperations.CreateModel",
            "type": "Pyramid",
            "name": "BadType",
        },
        "expect_error": True,
    },
]


def test_create_model(
    host: str = "127.0.0.1",
    port: int = 8888,
    case_filter: str | None = None,
):
    """运行所有（或指定的）CreateModel 测试用例。

    Args:
        host: UnityOpsListener 服务地址
        port: UnityOpsListener 监听端口
        case_filter: 仅执行名称包含该字符串的测试用例（大小写不敏感）
    """
    passed = 0
    failed = 0

    for idx, case in enumerate(TEST_CASES, start=1):
        name = case["name"]
        # 支持按名称过滤
        if case_filter and case_filter.lower() not in name.lower():
            print(f"\n[跳过] [{idx}] {name}")
            continue

        expect_error = case.get("expect_error", False)
        print(f"\n{'='*60}")
        print(f"  测试 [{idx}/{len(TEST_CASES)}]：{name}")
        print(f"{'='*60}")

        response_str = send_command(command=case["command"], host=host, port=port)
        print(f"[接收] {response_str}")

        try:
            result = json.loads(response_str)

            if expect_error:
                if result.get("status") == "error":
                    print(f"  ✓ 预期错误，实际返回 error: {result.get('message', '')}")
                    passed += 1
                else:
                    print(f"  ✗ 预期 error 但得到 success")
                    failed += 1
            else:
                if result.get("status") == "success":
                    created_name = result.get("name", "?")
                    print(f"  ✓ 创建成功！对象名: {created_name}")
                    passed += 1
                else:
                    msg = result.get("message", "未知原因")
                    print(f"  ✗ 创建失败: {msg}")
                    failed += 1

        except json.JSONDecodeError:
            print(f"  ✗ 响应无法解析为 JSON")
            failed += 1

    # 汇总
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  测试完成: {passed}/{total} 通过, {failed} 失败")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试 UnityOpsListener 的 CreateModel 命令")
    parser.add_argument("--host", default="127.0.0.1", help="UnityOpsListener 服务地址 (默认 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8888, help="UnityOpsListener 监听端口 (默认 8888)")
    parser.add_argument(
        "--filter", "-f",
        default=None,
        help="仅执行名称包含该字符串的测试用例（大小写不敏感）"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  UnityOpsListener - CreateModel 命令测试")
    print("  确保已启动 Unity 编辑器并运行 UnityOpsListener 服务器")
    print(f"  默认连接: {args.host}:{args.port}")
    if args.filter:
        print(f"  过滤条件: {args.filter}")
    print("=" * 60)

    try:
        ok = test_create_model(host=args.host, port=args.port, case_filter=args.filter)
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
