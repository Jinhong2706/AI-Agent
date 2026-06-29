---
name: audio-compress
slug: audio-compress
displayName: 音频压缩工具
description: 将音频文件压缩到指定大小（2-3MB），保持人声清晰度，输出到原文件夹
version: 1.0.0
author: UU的盒子
tags: [audio, compress, ffmpeg, mp3]
---

# 音频压缩工具 (audio-compress)

## 功能
将大体积音频文件压缩到目标大小（默认 2-3MB），保持人声清晰度，自动输出到原文件夹。

## 使用场景
- 飞书语音消息文件过大需要压缩再使用
- 音频文件需要减小体积便于传输
- 保持人声清晰度的同时大幅降低文件大小

## 压缩参数
| 参数 | 值 | 说明 |
|:----|:---|:------|
| 声道 | 单声道 (mono) | 人声足够，体积减半 |
| 采样率 | 22050 Hz | 人声频段完整保留 |
| 码率 | 64 kbps | 平衡体积与清晰度 |
| 格式 | MP3 | 兼容性最佳 |

## 压缩效果参考
| 原文件 | 压缩后 | 压缩比 |
|:------|:------|:------:|
| 11 MB / 4分28秒 / 320kbps立体声 | **2.1 MB / 4分28秒 / 64kbps单声道** | **~5:1** |

## 使用方法

### 方式一：终端命令
```bash
# 基本压缩（单声道 22050Hz 64kbps）
ffmpeg -y -i /path/to/input.mp3 -ac 1 -ar 22050 -b:a 64k /path/to/output.mp3
```

### 方式二：Python 脚本
```python
import subprocess
from pathlib import Path

def compress_audio(input_path, output_path=None):
    """压缩音频到约2-3MB"""
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_compressed{p.suffix}")
    
    result = subprocess.run([
        'ffmpeg', '-y',
        '-i', input_path,
        '-ac', '1',
        '-ar', '22050',
        '-b:a', '64k',
        output_path
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        orig_size = Path(input_path).stat().st_size
        comp_size = Path(output_path).stat().st_size
        ratio = orig_size / comp_size
        return {"success": True, "output": output_path, "ratio": f"{ratio:.1f}:1"}
    else:
        return {"success": False, "error": result.stderr}
```

### 方式三：Hermes 直接调用
让 Hermes Agent 执行：
```
帮我压缩这个音频到2-3MB，输出到原文件夹
```

## 依赖
- ffmpeg
- Python 3

## 验证方法
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 compressed.mp3
ffmpeg -v error -i compressed.mp3 -f null - 2>&1
ls -lh compressed.mp3
```

## 注意事项
- 压缩后时长与原始时长完全一致
- 音乐类音频建议用 96kbps 以上保持音质
- 立体声会合并为单声道（人声无影响）
