#!/usr/bin/env python3
"""
九马AI图片生成简单版
输入提示词，生成图片并返回URL
"""
import argparse
import json
import requests

SUBMIT_API = "https://api.jiuma.com/api/textImage/add"
CHECK_STATUS_API = "https://api.jiuma.com/api/textImage/status"


def output_result(json_data):
    """输出JSON格式结果"""
    print(json.dumps(json_data, ensure_ascii=False, indent=2))


def submit_text2image(text, width, height):
    """
    返回结构
    status: 状态
    message: 返回消息
    data: 数据结构体
    task_id: 任务ID(根据此任务ID查询制作进度)
    示例
    {
      "status": "success",
      "message": "文生图任务提交成功",
      "data": {
        "task_id": "202603263844232132"
      }
    }
    """
    if not text:
        output_result({
            "status": "error",
            "message": "请输入需要生成的图片的描述",
            "data": {}
        })
        return

    if width > 832 or height > 832:
        output_result({
            "status": "error",
            "message": "输出图片最大尺寸限制在832以内",
            "data": {}
        })
        return

    # 1. 提交生成请求
    try:
        response = requests.post(SUBMIT_API, {"text": text, "width": width, "height": height}, timeout=30)
        if response.status_code != 200:
            output_result({
                "status": "error",
                "message": f"请求远程API失败，状态码: {response.status_code}",
                "data": {}
            })
            return

        json_result = response.json()

        # 检查API返回结构 - 根据实际返回的JSON结构调整
        # API返回格式: {"code": 200, "message": "成功", "data": {"task_id": "xxx"}}
        if json_result.get("code") != 200:
            output_result({
                "status": "error",
                "message": f"API返回错误: {json_result.get('message', '未知错误')}",
                "data": json_result
            })
            return

        task_id = json_result.get("data", {}).get("task_id")

        if not task_id:
            output_result({
                "status": "error",
                "message": "API未返回任务ID",
                "data": json_result
            })
            return

        output_result({
            "status": "success",
            "message": "文生图任务提交成功",
            "data": {
                "task_id": task_id,
                "width": width,
                "height": height,
                "text": text
            }
        })
        return
    except requests.exceptions.Timeout:
        output_result({
            "status": "error",
            "message": "请求超时，请检查网络连接",
            "data": {}
        })
        return
    except requests.exceptions.RequestException as e:
        output_result({
            "status": "error",
            "message": f"请求异常: {str(e)}",
            "data": {}
        })
        return
    except json.JSONDecodeError as e:
        output_result({
            "status": "error",
            "message": f"API返回格式错误: {str(e)}",
            "data": {}
        })
        return


def check_task_status(task_id):
    """
    返回结构
    status: 处理结果，success|pending|running|failed
    message: 返回消息
    data: 数据结构体
    task_id: 任务ID
    image_url: 图片链接(如status为success)
    示例
    {
      "status": "success",
      "message": "图片生成成功",
      "data": {
        "image_url": "https://cache.jiuma.com/static/uploads/20260326/69c4cc0c043e1.png",
        "task_id": "20260326486039011"
      }
    }
    """
    if not task_id:
        output_result({
            "status": "error",
            "message": "任务ID不能为空",
            "data": {}
        })
        return None

    try:
        task_response = requests.post(CHECK_STATUS_API, {"task_id": task_id}, timeout=30)

        if task_response.status_code != 200:
            output_result({
                "status": "error",
                "message": f"请求远程API失败，状态码: {task_response.status_code}",
                "data": {}
            })
            return None

        task_detail = task_response.json()

        # 检查API返回状态 - 根据实际返回的JSON结构调整
        # API返回格式: {"code": 200, "message": "成功", "data": {"task_status": "xxx", "image_url": "xxx"}}
        if task_detail.get("code") != 200:
            output_result({
                "status": "error",
                "message": f"API返回错误: {task_detail.get('message', '未知错误')}",
                "data": task_detail
            })
            return None

        data = task_detail.get("data", {})
        task_status = data.get("task_status", "").upper()

        if task_status == 'SUCCEEDED':
            image_url = data.get('image_url')
            if not image_url:
                output_result({
                    "status": "error",
                    "message": "API未返回图片URL",
                    "data": data
                })
                return None

            output_result({
                "status": "success",
                "message": "图片生成成功",
                "data": {
                    "image_url": image_url,
                    "task_id": task_id,
                    "download_link": image_url
                }
            })
        elif task_status == 'PENDING':
            output_result({
                "status": "pending",
                "message": "文生图任务排队中，请耐心等待",
                "data": {
                    "task_id": task_id,
                    "status": "pending"
                }
            })
        elif task_status == 'RUNNING':
            output_result({
                "status": "pending",
                "message": "文生图任务执行中，请耐心等待",
                "data": {
                    "task_id": task_id,
                    "status": "running"
                }
            })
        else:
            output_result({
                "status": "failed",
                "message": f"图片生成失败: {task_detail.get('message', '未知错误')}",
                "data": {
                    "task_id": task_id,
                    "status": "failed"
                }
            })
    except requests.exceptions.Timeout:
        output_result({
            "status": "error",
            "message": "请求超时，请检查网络连接",
            "data": {
                "task_id": task_id
            }
        })
        return None
    except requests.exceptions.RequestException as e:
        output_result({
            "status": "error",
            "message": f"请求异常: {str(e)}",
            "data": {
                "task_id": task_id
            }
        })
        return None
    except json.JSONDecodeError as e:
        output_result({
            "status": "error",
            "message": f"API返回格式错误: {str(e)}",
            "data": {
                "task_id": task_id
            }
        })
        return None
    except Exception as e:
        output_result({
            "status": "error",
            "message": f"未知错误: {str(e)}",
            "data": {
                "task_id": task_id
            }
        })
        return None


def main():
    parser = argparse.ArgumentParser(description="九马AI免费文生图工具",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # 主要参数组
    parser.add_argument('--text', type=str, default="", help="文生图提示词，对图片的描述")
    parser.add_argument('--width', type=int, default=832, help="输出图片的宽，最大832")
    parser.add_argument('--height', type=int, default=480, help="输出图片的高，最大832")
    parser.add_argument('--task_id', type=str, default='', help="文生图执行任务ID")

    # 操作参数
    parser.add_argument('--check', action='store_true', help="检查生成状态")
    parser.add_argument('--submit', action='store_true', help="提交文生图制作")

    args = parser.parse_args()

    if args.submit:
        submit_text2image(args.text, args.width, args.height)
    elif args.check:
        check_task_status(args.task_id)
    else:
        print("""
九马AI免费文生图工具 v1.0
==========================

使用方法:
1. 提交图片生成任务:
   python3 agent.py --submit --text "图片描述" --width 512 --height 512

2. 查询任务状态:
   python3 agent.py --check --task_id "任务ID"

参数说明:
--submit        提交图片生成任务
--text          图片描述文本（必需）
--width         图片宽度（可选，默认832，最大832）
--height        图片高度（可选，默认480，最大832）
--check         查询任务生成状态
--task_id       任务ID（与--check一起使用）

示例:
python3 agent.py --submit --text "一只可爱的小猫在草地上玩耍" --width 512 --height 512
python3 agent.py --check --task_id "202603263844232132"

注意:
- 最大图片尺寸为832x832
- 图片生成可能需要等待，请使用--check参数查询状态
- 生成的图片URL可以直接在浏览器中打开下载
        """.strip())


if __name__ == '__main__':
    main()