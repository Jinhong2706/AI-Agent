#!/usr/bin/env python3
"""
generate_audio.py - 根据演讲稿生成语音
"""
import sys
import os
import subprocess

def generate_audio_from_script(script_md, output_dir, voice="zh-CN-XiaoxiaoNeural"):
    """
    根据演讲稿markdown生成语音文件
    
    Args:
        script_md: 演讲稿markdown文本
        output_dir: 音频输出目录
        voice: TTS语音角色
    
    Returns:
        生成的音频文件列表
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 解析markdown，提取每页的讲解内容
    pages = []
    current_page = None
    current_content = []
    
    for line in script_md.split('\n'):
        if line.startswith('## 第'):
            if current_page:
                pages.append({
                    'title': current_page,
                    'content': '\n'.join(current_content)
                })
            current_page = line.strip('# ').strip()
            current_content = []
        elif line.strip() and current_page:
            # 移除markdown格式
            clean_line = line.replace('**', '').replace('*', '')
            if clean_line and not clean_line.startswith('#'):
                current_content.append(clean_line)
    
    # 添加最后一页
    if current_page and current_content:
        pages.append({
            'title': current_page,
            'content': '\n'.join(current_content)
        })
    
    # 为每页生成语音
    audio_files = []
    for i, page in enumerate(pages):
        if not page['content'].strip():
            continue
            
        output_file = os.path.join(output_dir, f"page_{i+1:02d}.mp3")
        
        # 使用 edge-tts 生成语音
        try:
            cmd = [
                'edge-tts',
                '--text', page['content'],
                '--voice', voice,
                '--write-media', output_file
            ]
            
            print(f"正在生成第 {i+1} 页语音: {page['title']}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_file):
                audio_files.append(output_file)
                print(f"✓ 生成成功: {output_file}")
            else:
                print(f"✗ 生成失败: {result.stderr}")
                
        except Exception as e:
            print(f"✗ 生成语音时出错: {e}")
    
    return audio_files

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_audio.py <script.md file> <output_dir> [voice]")
        sys.exit(1)
    
    script_file = sys.argv[1]
    output_dir = sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "zh-CN-XiaoxiaoNeural"
    
    # 读取演讲稿
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 生成语音
    audio_files = generate_audio_from_script(script_content, output_dir, voice)
    
    print(f"\n总共生成了 {len(audio_files)} 个音频文件")
    for audio_file in audio_files:
        print(f"  - {audio_file}")
