#!/bin/bash
# AI视频创作师 - 技能打包脚本

SKILL_NAME="AI视频创作师"
VERSION="1.0.0"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$(pwd)"

echo "=========================================="
echo "🎬 $SKILL_NAME 打包脚本 v$VERSION"
echo "=========================================="

# 清理旧文件
rm -f "$OUTPUT_DIR/${SKILL_NAME}_v${VERSION}.zip"
rm -f "$OUTPUT_DIR/${SKILL_NAME}_v${VERSION}.tar.gz"

# 创建临时目录
TEMP_DIR="/tmp/${SKILL_NAME}_packaging"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# 复制文件（排除 __pycache__ 和 .pyc）
echo "📦 复制文件..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' "$SKILL_DIR/" "$TEMP_DIR/"

# 创建ZIP包
echo "📚 创建ZIP包..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_DIR/${SKILL_NAME}_v${VERSION}.zip" . -x "*.pyc" -x "__pycache__/*" -x ".DS_Store"

# 创建TAR.GZ包
echo "📦 创建TAR.GZ包..."
cd "$TEMP_DIR"
tar -czvf "$OUTPUT_DIR/${SKILL_NAME}_v${VERSION}.tar.gz" . --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store'

# 清理临时目录
cd "$OUTPUT_DIR"
rm -rf "$TEMP_DIR"

# 显示结果
echo ""
echo "=========================================="
echo "✅ 打包完成！"
echo "=========================================="
echo "📁 输出文件："
echo "   - ${SKILL_NAME}_v${VERSION}.zip"
echo "   - ${SKILL_NAME}_v${VERSION}.tar.gz"
echo ""
ls -lh "${SKILL_NAME}_v${VERSION}."* 2>/dev/null || true
