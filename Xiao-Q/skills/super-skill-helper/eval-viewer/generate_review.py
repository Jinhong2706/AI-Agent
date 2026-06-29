#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成评估审查查看器

用法:
    python generate_review.py <workspace>/iteration-N --skill-name <name> [--benchmark <benchmark.json>] [--previous-workspace <path>]

示例:
    python generate_review.py my-skill-workspace/iteration-1 --skill-name my-skill
    python generate_review.py my-skill-workspace/iteration-1 --skill-name my-skill --benchmark my-skill-workspace/iteration-1/benchmark.json
"""

import os
import sys
import json
import argparse
import webbrowser
import http.server
import socketserver
import threading
from pathlib import Path
from datetime import datetime


def load_eval_data(workspace):
    """加载工作区的评估数据"""
    evals = []
    
    # 查找所有 eval 目录
    for eval_dir in sorted(workspace.glob('eval-*')):
        if not eval_dir.is_dir():
            continue
        
        eval_name = eval_dir.name
        
        # 加载 with_skill 运行
        with_skill_dir = eval_dir / 'with_skill'
        if with_skill_dir.exists():
            eval_item = {
                'eval_id': len(evals),
                'eval_name': eval_name,
                'with_skill': load_run_data(with_skill_dir)
            }
            
            # 加载 baseline 运行
            baseline_dir = eval_dir / 'without_skill'
            if baseline_dir.exists():
                eval_item['baseline'] = load_run_data(baseline_dir)
            
            evals.append(eval_item)
    
    return evals


def load_run_data(run_dir):
    """加载运行数据"""
    data = {
        'output': '',
        'grading': None,
        'timing': None,
        'passed': False
    }
    
    # 查找输出文件
    outputs_dir = run_dir / 'outputs'
    if outputs_dir.exists():
        output_files = list(outputs_dir.iterdir())
        if output_files:
            # 读取第一个文本文件
            for output_file in output_files:
                if output_file.suffix in ['.txt', '.md', '.json']:
                    try:
                        data['output'] = output_file.read_text(encoding='utf-8')
                        break
                    except:
                        continue
            
            # 如果没有文本文件，列出文件名
            if not data['output']:
                data['output'] = '\n'.join([f.name for f in output_files])
    
    # 加载评分
    grading_path = run_dir / 'grading.json'
    if grading_path.exists():
        with open(grading_path, 'r', encoding='utf-8') as f:
            data['grading'] = json.load(f)
        
        # 计算是否通过
        if 'summary' in data['grading']:
            summary = data['grading']['summary']
            total = summary.get('total', 0)
            passed = summary.get('passed', 0)
            data['passed'] = (passed == total) if total > 0 else False
    
    # 加载时序
    timing_path = run_dir / 'timing.json'
    if timing_path.exists():
        with open(timing_path, 'r', encoding='utf-8') as f:
            data['timing'] = json.load(f)
    
    return data


def load_benchmark(benchmark_path):
    """加载基准测试数据"""
    if not benchmark_path or not os.path.exists(benchmark_path):
        return None
    
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_viewer_html(evals, skill_name, benchmark=None):
    """生成查看器 HTML"""
    # 读取模板
    template_path = Path(__file__).parent / 'assets' / 'eval_review.html'
    
    if not template_path.exists():
        # 尝试备用路径
        template_path = Path(__file__).parent.parent / 'assets' / 'eval_review.html'
    
    if not template_path.exists():
        print("❌ 未找到评估审查模板")
        sys.exit(1)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 准备评估数据
    eval_data = []
    for eval_item in evals:
        # 简化数据用于前端
        simplified = {
            'eval_id': eval_item['eval_id'],
            'eval_name': eval_item['eval_name'],
            'prompt': eval_item.get('prompt', 'N/A'),
            'output': eval_item['with_skill']['output'] if 'with_skill' in eval_item else '',
            'passed': eval_item['with_skill']['passed'] if 'with_skill' in eval_item else False,
            'assertions': []
        }
        
        # 添加断言
        if 'with_skill' in eval_item and eval_item['with_skill'].get('grading'):
            grading = eval_item['with_skill']['grading']
            if 'expectations' in grading:
                simplified['assertions'] = grading['expectations']
        
        eval_data.append(simplified)
    
    # 替换占位符
    html = template
    html = html.replace('__SKILL_NAME_PLACEHOLDER__', skill_name)
    html = html.replace('__SKILL_DESCRIPTION_PLACEHOLDER__', f'技能 {skill_name} 的评估审查')
    html = html.replace('__EVAL_DATA_PLACEHOLDER__', json.dumps(eval_data, ensure_ascii=False))
    
    return html


def start_server(html_content, port=8000):
    """启动 HTTP 服务器"""
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-length', len(html_content.encode('utf-8')))
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            # 静默日志
            pass
    
    # 尝试多个端口
    for p in range(port, port + 10):
        try:
            with socketserver.TCPServer(("", p), CustomHandler) as httpd:
                print(f"\n🌐 评估查看器已启动")
                print(f"URL: http://localhost:{p}")
                print(f"按 Ctrl+C 关闭服务器")
                
                # 在后台线程运行服务器
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                
                # 打开浏览器
                webbrowser.open(f"http://localhost:{p}")
                
                return httpd
        except OSError as e:
            if "Address already in use" in str(e):
                continue
            raise
    
    print("❌ 无法启动服务器（所有端口都被占用）")
    return None


def save_static_html(html_content, output_path):
    """保存为静态 HTML 文件"""
    output_file = Path(output_path)
    output_file.write_text(html_content, encoding='utf-8')
    print(f"\n✅ 静态 HTML 已保存：{output_file}")
    print(f"在浏览器中打开：file://{output_file.absolute()}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='生成评估审查查看器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python generate_review.py my-skill-workspace/iteration-1 --skill-name my-skill
  python generate_review.py my-skill-workspace/iteration-1 --skill-name my-skill --static /tmp/review.html
        '''
    )
    
    parser.add_argument('workspace', help='工作区路径（iteration-N 目录）')
    parser.add_argument('--skill-name', required=True, help='技能名称')
    parser.add_argument('--benchmark', help='benchmark.json 文件路径')
    parser.add_argument('--previous-workspace', help='上一次迭代的工作区路径')
    parser.add_argument('--static', help='输出静态 HTML 文件路径（而非启动服务器）')
    parser.add_argument('--port', type=int, default=8000, help='HTTP 服务器端口（默认：8000）')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    
    if not workspace.exists():
        print(f"❌ 工作区不存在：{workspace}")
        sys.exit(1)
    
    print(f"📊 生成评估审查查看器")
    print(f"工作区：{workspace}")
    print(f"技能：{args.skill_name}")
    print("=" * 60)
    
    # 加载评估数据
    print("\n📋 加载评估数据...")
    evals = load_eval_data(workspace)
    
    if not evals:
        print("❌ 未找到评估数据")
        sys.exit(1)
    
    print(f"✓ 找到 {len(evals)} 个评估用例")
    
    # 加载基准数据
    benchmark = None
    if args.benchmark:
        print("\n📊 加载基准数据...")
        benchmark = load_benchmark(args.benchmark)
        if benchmark:
            print(f"✓ 加载基准数据")
    
    # 生成 HTML
    print("\n🎨 生成查看器...")
    html_content = generate_viewer_html(evals, args.skill_name, benchmark)
    
    # 输出
    if args.static:
        # 保存为静态文件
        save_static_html(html_content, args.static)
    else:
        # 启动服务器
        httpd = start_server(html_content, args.port)
        
        if httpd and not args.no_browser:
            # 保持运行
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n👋 关闭服务器...")
                httpd.shutdown()
        elif not httpd:
            # 服务器启动失败，保存为静态文件
            static_path = workspace.parent / 'eval_review.html'
            save_static_html(html_content, static_path)


if __name__ == '__main__':
    main()
