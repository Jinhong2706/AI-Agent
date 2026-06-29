#!/bin/bash
# PDF Fast Handler Skill - 依赖安装脚本
# 支持 Linux/macOS/Windows (Git Bash)

set -e

echo "============================================="
echo "    PDF Fast Handler Skill - 依赖安装"
echo "============================================="

# 检测 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo "[信息] 使用 Python: $PYTHON_CMD"

# 升级 pip
echo "[步骤 1/2] 升级 pip..."
$PYTHON_CMD -m pip install --upgrade pip -q

# 安装 Python 依赖
echo "[步骤 2/2] 安装 Python 依赖包..."
$PYTHON_CMD -m pip install \
    PyPDF2>=3.0.1 \
    pdf2docx>=0.5.6 \
    pdf2image>=1.17.0 \
    pytesseract>=0.3.10 \
    pillow>=10.0.0 \
    docx2pdf>=0.8.2 \
    -q

echo ""
echo "============================================="
echo "    Python 依赖安装完成！"
echo "============================================="

# 检测操作系统并提示安装系统依赖
detect_os() {
    case "$(uname -s)" in
        Linux*)
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                echo "$ID"
            else
                echo "linux"
            fi
            ;;
        Darwin*)    echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

OS=$(detect_os)
echo ""
echo "[系统] 检测到操作系统: $OS"
echo ""

case "$OS" in
    ubuntu|debian)
        echo "[提示] 请运行以下命令安装系统依赖:"
        echo "       sudo apt update"
        echo "       sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-chi-sim"
        ;;
    centos|fedora|rhel)
        echo "[提示] 请运行以下命令安装系统依赖:"
        echo "       sudo yum install -y poppler-utils tesseract tesseract-langpack-chi_sim"
        ;;
    macos)
        echo "[提示] 请运行以下命令安装系统依赖:"
        echo "       brew install poppler tesseract tesseract-lang"
        ;;
    windows)
        echo "[提示] Windows 需要手动安装以下组件:"
        echo ""
        echo "       1. Poppler (PDF 渲染):"
        echo "          https://github.com/oschwartz10612/poppler-windows/releases"
        echo "          下载后解压，将 bin 目录添加到系统 PATH"
        echo ""
        echo "       2. Tesseract OCR (文字识别):"
        echo "          https://github.com/UB-Mannheim/tesseract/wiki"
        echo "          安装时勾选中文语言包 (chi_sim)"
        echo ""
        echo "       3. 验证安装:"
        echo "          tesseract --version"
        echo "          pdftoppm -v"
        ;;
    *)
        echo "[提示] 请根据您的系统安装 poppler 和 tesseract"
        ;;
esac

echo ""
echo "============================================="
echo "    安装验证"
echo "============================================="
echo ""

# 验证 Python 包
$PYTHON_CMD -c "
import sys
packages = ['PyPDF2', 'pdf2docx', 'pdf2image', 'pytesseract', 'PIL', 'docx2pdf']
all_ok = True
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  [OK] {pkg}')
    except ImportError:
        print(f'  [MISSING] {pkg}')
        all_ok = False
sys.exit(0 if all_ok else 1)
" && echo "" && echo "[成功] 所有 Python 依赖已就绪！" || echo "[警告] 部分依赖安装失败"

echo ""
echo "============================================="
echo "    使用示例"
echo "============================================="
echo ""
echo "  python pdf_fast_handler_skill.py info input.pdf"
echo "  python pdf_fast_handler_skill.py to-word input.pdf -o output.docx"
echo "  python pdf_fast_handler_skill.py merge file1.pdf file2.pdf -o merged.pdf"
echo ""
echo "=============================================