#!/usr/bin/env python3
"""
MarkItDown 技能执行脚本
将各种文件格式转换为 Markdown
"""

import sys
import json
import os
import subprocess
from pathlib import Path

def install_markitdown():
    """安装 MarkItDown 及其依赖"""
    try:
        import markitdown
        return True
    except ImportError:
        pass
    
    print("首次使用，正在安装 MarkItDown...", file=sys.stderr)
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "markitdown[pdf,docx,pptx,xlsx]", "-q"
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {e}", file=sys.stderr)
        return False

def convert_file(file_path, output_path=None, return_content=False):
    """转换单个文件为 Markdown"""
    try:
        from markitdown import MarkItDown
    except ImportError:
        return {
            "status": "failed",
            "result": {
                "error_code": "IMPORT_ERROR",
                "error_message": "MarkItDown 库未安装"
            }
        }
    
    if not os.path.exists(file_path):
        return {
            "status": "failed",
            "result": {
                "error_code": "FILE_NOT_FOUND",
                "error_message": f"文件不存在：{file_path}"
            }
        }
    
    try:
        md = MarkItDown()
        result = md.convert(file_path)
        content = result.text_content
        
        if return_content:
            return {
                "status": "success",
                "result": {
                    "message": "转换完成",
                    "content": content
                }
            }
        else:
            if not output_path:
                # 默认输出路径：原文件名 + .md
                input_path = Path(file_path)
                output_path = str(input_path.parent / f"{input_path.stem}.md")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "result": {
                    "message": "转换完成",
                    "output_path": output_path
                }
            }
    except Exception as e:
        return {
            "status": "failed",
            "result": {
                "error_code": "CONVERSION_ERROR",
                "error_message": f"转换失败：{str(e)}"
            }
        }

def batch_convert(file_paths, output_dir=None):
    """批量转换文件"""
    if not output_dir:
        output_dir = "/sandbox/workspace/outputs/"
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            results.append({
                "input": file_path,
                "output": None,
                "status": "failed",
                "error": "文件不存在"
            })
            fail_count += 1
            continue
        
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert(file_path)
            content = result.text_content
            
            # 生成输出文件名
            input_name = Path(file_path).stem
            output_path = os.path.join(output_dir, f"{input_name}.md")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            results.append({
                "input": file_path,
                "output": output_path,
                "status": "success"
            })
            success_count += 1
        except Exception as e:
            results.append({
                "input": file_path,
                "output": None,
                "status": "failed",
                "error": str(e)
            })
            fail_count += 1
    
    return {
        "status": "success",
        "result": {
            "message": f"批量转换完成：{success_count} 成功，{fail_count} 失败",
            "files": results
        }
    }

def main():
    """主函数：解析参数并执行转换"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "failed",
            "result": {
                "error_code": "MISSING_PARAMETERS",
                "error_message": "缺少参数，请使用 --parameters '...'"
            }
        }))
        sys.exit(1)
    
    # 解析参数
    params_str = None
    for i, arg in enumerate(sys.argv):
        if arg == "--parameters" and i + 1 < len(sys.argv):
            params_str = sys.argv[i + 1]
            break
    
    if not params_str:
        print(json.dumps({
            "status": "failed",
            "result": {
                "error_code": "MISSING_PARAMETERS",
                "error_message": "未找到 --parameters 参数"
            }
        }))
        sys.exit(1)
    
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "failed",
            "result": {
                "error_code": "INVALID_PARAMETERS",
                "error_message": f"参数解析失败：{str(e)}"
            }
        }))
        sys.exit(1)
    
    # 安装依赖
    if not install_markitdown():
        print(json.dumps({
            "status": "failed",
            "result": {
                "error_code": "INSTALL_FAILED",
                "error_message": "MarkItDown 安装失败"
            }
        }))
        sys.exit(1)
    
    # 执行转换
    file_path = params.get("file_path")
    file_paths = params.get("file_paths", [])
    return_content = params.get("return_content", False)
    output_path = params.get("output_path")
    output_dir = params.get("output_dir")
    upload_to_kb = params.get("upload_to_kb", False)
    kb_id = params.get("kb_id")
    
    # 批量转换
    if file_paths:
        result = batch_convert(file_paths, output_dir)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    
    # 单个文件转换
    if not file_path:
        print(json.dumps({
            "status": "failed",
            "result": {
                "error_code": "MISSING_FILE",
                "error_message": "未指定文件路径（file_path 或 file_paths）"
            }
        }))
        sys.exit(1)
    
    result = convert_file(file_path, output_path, return_content)
    
    # 如果需要上传到知识库（暂未实现，返回提示）
    if upload_to_kb:
        if not kb_id:
            result = {
                "status": "failed",
                "result": {
                    "error_code": "MISSING_KB_ID",
                    "error_message": "upload_to_kb=true 时需要提供 kb_id"
                }
            }
        else:
            # TODO: 实现知识库上传逻辑
            result["result"]["upload_status"] = "知识库上传功能暂未实现"
    
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
