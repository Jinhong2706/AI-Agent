#!/bin/bash
# auto_video_generator.sh - 一键内容转视频主脚本
# 用法: ./auto_video_generator.sh "主题" [时长分钟] [输出目录]

set -e  # 遇到错误立即退出

TOPIC="${1:-量子力学基础}"
DURATION="${2:-5}"
OUTPUT_DIR="${3:-./video_output_$(date +%Y%m%d_%H%M%S)}"

echo "=========================================="
echo "🎬 一键内容转视频"
echo "=========================================="
echo "主题: $TOPIC"
echo "目标时长: ${DURATION} 分钟"
echo "输出目录: $OUTPUT_DIR"
echo "=========================================="

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 第一步：生成演讲稿
echo ""
echo "📝 第一步：生成演讲稿..."
python3 scripts/generate_script.py "$TOPIC" "$DURATION" > "$OUTPUT_DIR/script.md"
echo "✓ 演讲稿已生成: $OUTPUT_DIR/script.md"

# 第二步：生成PPT配图
echo ""
echo "🎨 第二步：生成PPT配图..."
if command -v node &> /dev/null; then
    # 检查 ppt-generator-skill 是否存在
    if [ -d "/data/skills/ppt-generator-skill" ]; then
        cd /data/skills/ppt-generator-skill
        node scripts/generate.js \
            --topic "$TOPIC" \
            --pages $((DURATION * 2)) \
            --lang zh \
            --style "教育简约" \
            --output "$OUTPUT_DIR/slides.pptx" || echo "⚠ PPT生成失败，跳过"
        cd - > /dev/null
        
        if [ -f "$OUTPUT_DIR/slides.pptx" ]; then
            echo "✓ PPT已生成: $OUTPUT_DIR/slides.pptx"
        fi
    else
        echo "⚠ ppt-generator-skill 未安装，跳过PPT生成"
    fi
else
    echo "⚠ Node.js 未安装，跳过PPT生成"
fi

# 第三步：转换PPT为PDF（如果PPT存在）
if [ -f "$OUTPUT_DIR/slides.pptx" ]; then
    echo ""
    echo "📄 第三步：转换PPT为PDF..."
    if command -v libreoffice &> /dev/null; then
        libreoffice --headless --convert-to pdf \
            --outdir "$OUTPUT_DIR" "$OUTPUT_DIR/slides.pptx" 2>/dev/null || echo "⚠ PPT转PDF失败"
        
        if [ -f "$OUTPUT_DIR/slides.pdf" ]; then
            echo "✓ PDF已生成: $OUTPUT_DIR/slides.pdf"
        fi
    else
        echo "⚠ LibreOffice 未安装，跳过PDF转换"
    fi
fi

# 第四步：生成语音讲解
echo ""
echo "🎙 第四步：生成语音讲解..."
mkdir -p "$OUTPUT_DIR/audio"
python3 scripts/generate_audio.py "$OUTPUT_DIR/script.md" "$OUTPUT_DIR/audio" || echo "⚠ 语音生成失败"

if [ -d "$OUTPUT_DIR/audio" ] && [ "$(ls -A "$OUTPUT_DIR/audio" 2>/dev/null)" ]; then
    echo "✓ 语音已生成: $OUTPUT_DIR/audio/"
fi

# 第五步：合成视频
echo ""
echo "🎬 第五步：合成最终视频..."

if [ -f "$OUTPUT_DIR/slides.pdf" ] && [ -d "$OUTPUT_DIR/audio" ]; then
    # 使用 ppt-to-video 技能
    if [ -d "/data/skills/ppt-to-video" ]; then
        echo "使用 ppt-to-video 合成视频..."
        python3 /data/skills/ppt-to-video/scripts/run_pipeline.py \
            --speech_md "$OUTPUT_DIR/script.md" \
            --slides_pdf "$OUTPUT_DIR/slides.pdf" \
            --output_dir "$OUTPUT_DIR/video_output" \
            --tts_engine edge || echo "⚠ 视频合成失败"
        
        if [ -f "$OUTPUT_DIR/video_output/final_presentation.mp4" ]; then
            echo "✓ 视频已生成: $OUTPUT_DIR/video_output/final_presentation.mp4"
        fi
    else
        echo "⚠ ppt-to-video 未安装，尝试使用FFmpeg直接合成..."
        
        # 备选方案：使用FFmpeg合成
        if command -v ffmpeg &> /dev/null; then
            echo "使用FFmpeg合成简单视频..."
            # 这里可以添加FFmpeg合成逻辑
            echo "⚠ 需要手动完成视频合成"
        fi
    fi
elif [ -f "$OUTPUT_DIR/slides.pptx" ]; then
    echo "⚠ 缺少PDF或音频，无法合成视频"
    echo "提示：可以手动使用 $OUTPUT_DIR/slides.pptx 和 $OUTPUT_DIR/audio/ 合成视频"
else
    echo "⚠ 缺少必要的文件，无法合成视频"
fi

# 总结
echo ""
echo "=========================================="
echo "✅ 处理完成！"
echo "=========================================="
echo "生成的文件："
echo "  - 演讲稿: $OUTPUT_DIR/script.md"
[ -f "$OUTPUT_DIR/slides.pptx" ] && echo "  - PPT: $OUTPUT_DIR/slides.pptx"
[ -f "$OUTPUT_DIR/slides.pdf" ] && echo "  - PDF: $OUTPUT_DIR/slides.pdf"
[ -d "$OUTPUT_DIR/audio" ] && echo "  - 音频: $OUTPUT_DIR/audio/"
[ -f "$OUTPUT_DIR/video_output/final_presentation.mp4" ] && echo "  - 最终视频: $OUTPUT_DIR/video_output/final_presentation.mp4"
echo "=========================================="
echo ""
echo "💡 提示："
echo "  - 可以直接使用PPT文件: $OUTPUT_DIR/slides.pptx"
echo "  - 或者查看最终视频: $OUTPUT_DIR/video_output/final_presentation.mp4"
echo ""
