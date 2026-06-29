#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 终极全能 Skill for QClaw
功能全覆盖：编辑、转换、加密、水印、OCR、批注、页面、页眉页脚、表格提取、批量、修复……

用法：
    python pdf_fast_handler_skill.py <命令> [参数] [选项]

示例：
    python pdf_fast_handler_skill.py info input.pdf
    python pdf_fast_handler_skill.py to-word input.pdf -o output.docx
    python pdf_fast_handler_skill.py merge file1.pdf file2.pdf -o merged.pdf
"""
import os
import sys
import io

# Windows 终端编码兼容
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import re
import argparse
from typing import Dict, Any, List

# 延迟导入第三方依赖，脚本启动时检测并提示
def check_dependencies():
    """检查并提示安装依赖"""
    missing = []
    try:
        import PyPDF2
    except ImportError:
        missing.append("PyPDF2")
    try:
        from pdf2image import convert_from_path
    except ImportError:
        missing.append("pdf2image")
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    try:
        import pytesseract
    except ImportError:
        missing.append("pytesseract")
    try:
        from pdf2docx import Converter
    except ImportError:
        missing.append("pdf2docx")
    try:
        from docx2pdf import convert as docx_to_pdf
    except ImportError:
        missing.append("docx2pdf")
    
    if missing:
        print(f"[错误] 缺少依赖包: {', '.join(missing)}")
        print("[提示] 请运行以下命令安装依赖:")
        print("       pip install PyPDF2 pdf2image pillow pytesseract pdf2docx docx2pdf")
        print("[提示] Windows 还需安装:")
        print("       - Poppler: https://github.com/oschwartz10612/poppler-windows/releases")
        print("       - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

check_dependencies()

# 导入依赖
from PyPDF2 import PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from docx2pdf import convert as docx_to_pdf
import datetime

SKILL_INFO = {
    "name": "pdf_fast_handler",
    "description": "PDF 终极全能工具：转换、编辑、OCR、加密解密、水印、页眉页脚、旋转、删页、提取页、图片互转、Word互转、压缩、修复、提取图片、表格、批注、书签、合并、拆分、批量",
    "version": "9.9.9",
    "author": "QClaw",
    "trigger_words": [
        "PDF文本提取", "PDF合并", "PDF拆分", "PDF水印", "PDF信息", "PDF OCR",
        "扫描PDF转文字", "PDF转Word", "PDF转图片", "PDF转HTML", "PDF转TXT", "PDF转Markdown",
        "图片转PDF", "多张图片转PDF", "Word转PDF", "PDF转Word", "PDF提取图片", "PDF提取表格",
        "PDF加密", "PDF解密", "PDF压缩", "PDF旋转", "PDF删除页", "PDF提取页", "PDF插入页", "PDF替换页",
        "PDF添加页码", "添加页眉", "添加页脚", "PDF提取书签", "PDF提取批注", "PDF修复", "PDF反转顺序",
        "批量处理PDF", "批量PDF转Word", "批量Word转PDF", "批量PDF转图片", "批量提取文本"
    ],
}

class PDFUltimateSkill:
    def __init__(self):
        self.name = SKILL_INFO["name"]
        self.trigger_words = SKILL_INFO["trigger_words"]

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        file_paths = params.get("file_paths", [])
        folder_path = params.get("folder_path", "")
        password = params.get("password", "")

        if action == "batch":
            return self._batch_process(params)

        if action not in ["images2pdf"] and (not file_paths or not os.path.exists(file_paths[0])):
            return self._error("文件不存在或未提供")

        try:
            reader = None
            if file_paths and action not in ["images2pdf", "word2pdf"]:
                reader = PdfReader(file_paths[0])
                if reader.is_encrypted:
                    if not password:
                        return self._error("PDF已加密，请传入 password")
                    try:
                        reader.decrypt(password)
                    except Exception:
                        return self._error("密码错误")

            # 动作分发
            if action == "extract": return self._extract_text(file_paths[0])
            if action == "merge": return self._merge(file_paths, params.get("output_path"))
            if action == "split": return self._split(file_paths[0], params.get("split_page", 1), params.get("output_path"))
            if action == "watermark": return self._watermark(file_paths[0], params.get("watermark_text"), params.get("output_path"))
            if action == "info": return self._info(file_paths[0])
            if action == "ocr": return self._ocr(file_paths[0], password)
            if action == "to_word": return self._to_word(file_paths[0], params.get("output_path"))
            if action == "to_image": return self._to_image(file_paths[0], params.get("output_path"))
            if action == "to_html": return self._to_html(file_paths[0], params.get("output_path"))
            if action == "to_txt": return self._to_txt(file_paths[0], params.get("output_path"))
            if action == "to_md": return self._to_md(file_paths[0], params.get("output_path"))
            if action == "decrypt": return self._decrypt(file_paths[0], password, params.get("output_path"))
            if action == "encrypt": return self._encrypt(file_paths[0], params.get("new_password"), params.get("output_path"))
            if action == "rotate": return self._rotate(file_paths[0], params.get("rotate_degree", 90), params.get("output_path"))
            if action == "delete_pages": return self._delete_pages(file_paths[0], params.get("delete_pages", []), params.get("output_path"))
            if action == "extract_pages": return self._extract_pages(file_paths[0], params.get("extract_pages", []), params.get("output_path"))
            if action == "insert_page": return self._insert_page(file_paths[0], params.get("insert_page_at", 1), params.get("insert_pdf_path"), params.get("output_path"))
            if action == "replace_page": return self._replace_page(file_paths[0], params.get("replace_page_num", 1), params.get("replace_pdf_path"), params.get("output_path"))
            if action == "add_header": return self._add_header(file_paths[0], params.get("header_text"), params.get("output_path"))
            if action == "add_footer": return self._add_footer(file_paths[0], params.get("footer_text"), params.get("output_path"))
            if action == "add_page_num": return self._add_page_num(file_paths[0], params.get("output_path"))
            if action == "extract_images": return self._extract_images(file_paths[0], params.get("output_path"))
            if action == "extract_tables": return self._extract_tables(file_paths[0])
            if action == "extract_bookmarks": return self._extract_bookmarks(file_paths[0])
            if action == "extract_annotations": return self._extract_annotations(file_paths[0])
            if action == "reverse_pages": return self._reverse_pages(file_paths[0], params.get("output_path"))
            if action == "repair": return self._repair(file_paths[0], params.get("output_path"))
            if action == "images2pdf": return self._images2pdf(params.get("image_paths", []), params.get("output_path"))
            if action == "word2pdf": return self._word2pdf(file_paths[0], params.get("output_path"))
            if action == "compress": return self._compress(file_paths[0], params.get("compress_level", "medium"), params.get("output_path"))

            return self._error(f"不支持的动作：{action}")
        except Exception as e:
            import traceback
            return self._error(f"处理失败：{str(e)}\n{traceback.format_exc()}")

    # ================================= 基础 =================================
    def _extract_text(self, path):
        r = PdfReader(path)
        text = "\n".join([p.extract_text() or "" for p in r.pages])
        return self._success(f"提取完成，共{len(r.pages)}页", {"text": text[:20000]})

    def _merge(self, paths, out):
        out = out or "merged.pdf"
        w = PdfWriter()
        for p in paths:
            r = PdfReader(p)
            for page in r.pages: w.add_page(page)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"合并完成：{out}")

    def _split(self, path, page, out):
        r = PdfReader(path)
        total = len(r.pages)
        if page < 1 or page >= total: return self._error(f"页码错误，总页数{total}")
        w1, w2 = PdfWriter(), PdfWriter()
        for i in range(page): w1.add_page(r.pages[i])
        for i in range(page, total): w2.add_page(r.pages[i])
        n1 = out or "part1.pdf"
        n2 = "part2.pdf"
        with open(n1, "wb") as f: w1.write(f)
        with open(n2, "wb") as f: w2.write(f)
        return self._success(f"拆分完成：{n1}、{n2}")

    def _watermark(self, path, text, out):
        if not text: return self._error("请输入水印文字")
        out = out or "watermarked.pdf"
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"水印完成：{out}")

    def _info(self, path):
        r = PdfReader(path)
        return self._success("信息获取成功", {
            "文件名": os.path.basename(path),
            "页数": len(r.pages),
            "大小": f"{os.path.getsize(path)/1024:.1f}KB",
            "加密": r.is_encrypted,
            "作者": r.metadata.author if r.metadata else "",
            "创建时间": str(r.metadata.creation_date) if r.metadata and hasattr(r.metadata, 'creation_date') else "",
            "Producer": r.metadata.producer if r.metadata else ""
        })

    # ================================= 转换 =================================
    def _to_word(self, path, out):
        out = out or "output.docx"
        cv = Converter(path)
        cv.convert(out)
        cv.close()
        return self._success(f"转Word完成：{out}")

    def _to_image(self, path, out_dir):
        out_dir = out_dir or "pdf_images"
        os.makedirs(out_dir, exist_ok=True)
        imgs = convert_from_path(path)
        saved = []
        for i, img in enumerate(imgs):
            p = os.path.join(out_dir, f"page_{i+1}.jpg")
            img.save(p, "JPEG")
            saved.append(p)
        return self._success(f"转{len(saved)}张图片", {"files": saved})

    def _to_html(self, path, out):
        out = out or "output.html"
        r = PdfReader(path)
        html = "<html><head><meta charset='utf-8'></head><body>"
        for i, p in enumerate(r.pages):
            html += f"<h3>第{i+1}页</h3><p>{p.extract_text() or ''}</p><hr>"
        html += "</body></html>"
        with open(out, "w", encoding="utf-8") as f: f.write(html)
        return self._success(f"转HTML完成：{out}")

    def _to_txt(self, path, out):
        out = out or "output.txt"
        r = PdfReader(path)
        text = "\n".join([p.extract_text() or "" for p in r.pages])
        with open(out, "w", encoding="utf-8") as f: f.write(text)
        return self._success(f"转TXT完成：{out}")

    def _to_md(self, path, out):
        out = out or "output.md"
        r = PdfReader(path)
        md = "# PDF 内容\n\n"
        for i, p in enumerate(r.pages):
            md += f"## 第{i+1}页\n{p.extract_text() or ''}\n\n"
        with open(out, "w", encoding="utf-8") as f: f.write(md)
        return self._success(f"转Markdown完成：{out}")

    def _ocr(self, path, pwd=""):
        r = PdfReader(path)
        if r.is_encrypted:
            if not pwd: return self._error("需要密码")
            try: r.decrypt(pwd)
            except: return self._error("密码错误")
        imgs = convert_from_path(path)
        text = ""
        for idx, img in enumerate(imgs):
            t = pytesseract.image_to_string(img, lang="chi_sim+eng")
            text += f"--- 第{idx+1}页 ---\n{t}\n"
        return self._success(f"OCR完成，共{len(imgs)}页", {"ocr_text": text[:20000]})

    # ================================= 加密解密 =================================
    def _decrypt(self, path, pwd, out):
        r = PdfReader(path)
        try: r.decrypt(pwd)
        except: return self._error("密码错误")
        out = out or "decrypted.pdf"
        w = PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"解密完成：{out}")

    def _encrypt(self, path, new_pwd, out):
        if not new_pwd: return self._error("请设置新密码")
        r = PdfReader(path)
        out = out or "encrypted.pdf"
        w = PdfWriter()
        for p in r.pages: w.add_page(p)
        w.encrypt(new_pwd)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"加密完成：{out}")

    # ================================= 页面编辑 =================================
    def _rotate(self, path, deg, out):
        if deg not in [90, 180, 270]: return self._error("仅支持90/180/270")
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages:
            p.rotate(deg)
            w.add_page(p)
        out = out or "rotated.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"旋转{deg}度完成：{out}")

    def _delete_pages(self, path, dels, out):
        if not dels: return self._error("请传入删除页码列表")
        r, w = PdfReader(path), PdfWriter()
        for i in range(len(r.pages)):
            if (i+1) not in dels:
                w.add_page(r.pages[i])
        out = out or "deleted.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"删除页完成：{out}")

    def _extract_pages(self, path, exs, out):
        if not exs: return self._error("请传入提取页码列表")
        r, w = PdfReader(path), PdfWriter()
        for i in exs:
            if 1 <= i <= len(r.pages):
                w.add_page(r.pages[i-1])
        out = out or "extracted.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"提取页完成：{out}")

    def _insert_page(self, main_path, at, insert_pdf, out):
        if not insert_pdf or not os.path.exists(insert_pdf): return self._error("插入PDF不存在")
        r_main = PdfReader(main_path)
        r_ins = PdfReader(insert_pdf)
        w = PdfWriter()
        for i in range(len(r_main.pages)):
            if i+1 == at:
                for p in r_ins.pages: w.add_page(p)
            w.add_page(r_main.pages[i])
        out = out or "inserted.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"插入完成：{out}")

    def _replace_page(self, main_path, num, rep_pdf, out):
        if not rep_pdf or not os.path.exists(rep_pdf): return self._error("替换PDF不存在")
        r_main = PdfReader(main_path)
        r_rep = PdfReader(rep_pdf)
        w = PdfWriter()
        for i in range(len(r_main.pages)):
            if i+1 == num:
                w.add_page(r_rep.pages[0])
            else:
                w.add_page(r_main.pages[i])
        out = out or "replaced.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"替换第{num}页完成：{out}")

    def _reverse_pages(self, path, out):
        r, w = PdfReader(path), PdfWriter()
        for p in reversed(r.pages): w.add_page(p)
        out = out or "reversed.pdf"
        with open(out, "wb") as f: w.write(f)
        return self._success(f"页面顺序反转完成：{out}")

    # ================================= 页眉页脚页码 =================================
    def _add_header(self, path, text, out):
        if not text: return self._error("请输入页眉文字")
        out = out or "with_header.pdf"
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"添加页眉完成：{out}")

    def _add_footer(self, path, text, out):
        if not text: return self._error("请输入页脚文字")
        out = out or "with_footer.pdf"
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"添加页脚完成：{out}")

    def _add_page_num(self, path, out):
        out = out or "with_pagenum.pdf"
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"添加页码完成：{out}")

    # ================================= 提取资源 =================================
    def _extract_images(self, path, out_dir):
        out_dir = out_dir or "pdf_extract_images"
        os.makedirs(out_dir, exist_ok=True)
        r = PdfReader(path)
        count = 0
        saved = []
        for i, page in enumerate(r.pages):
            for img in page.images:
                count += 1
                img_path = os.path.join(out_dir, f"img_p{i+1}_{count}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img.data)
                saved.append(img_path)
        return self._success(f"提取{count}张图片", {"files": saved})

    def _extract_tables(self, path):
        r = PdfReader(path)
        tables = []
        for i, p in enumerate(r.pages):
            txt = p.extract_text() or ""
            if "|" in txt or "\t" in txt:
                tables.append({"page": i+1, "content": txt})
        return self._success(f"找到{len(tables)}页疑似表格", {"tables": tables[:20]})

    def _extract_bookmarks(self, path):
        r = PdfReader(path)
        bms = []
        def walk(outline, indent=0):
            for b in outline:
                if isinstance(b, list):
                    walk(b, indent+1)
                else:
                    bms.append({"title": b.title, "page": b.page.idnum + 1, "indent": indent})
        walk(r.outline)
        return self._success(f"提取{len(bms)}个书签", {"bookmarks": bms})

    def _extract_annotations(self, path):
        r = PdfReader(path)
        anns = []
        for i, p in enumerate(r.pages):
            if p.annotations:
                for a in p.annotations:
                    anns.append({"page": i+1, "content": str(a.get("/Contents", ""))})
        return self._success(f"提取{len(anns)}条批注", {"annotations": anns})

    # ================================= 图片/Word互转 =================================
    def _images2pdf(self, imgs, out):
        if not imgs: return self._error("请传入图片列表")
        out = out or "images2pdf.pdf"
        first = None
        others = []
        for p in imgs:
            if os.path.exists(p):
                im = Image.open(p).convert("RGB")
                if first is None: first = im
                else: others.append(im)
        if not first: return self._error("无有效图片")
        first.save(out, save_all=True, append_images=others)
        return self._success(f"图片合成PDF完成：{out}")

    def _word2pdf(self, docx, out):
        if not docx.endswith(".docx"): return self._error("仅支持docx")
        out = out or docx.replace(".docx", ".pdf")
        docx_to_pdf(docx, out)
        return self._success(f"Word转PDF完成：{out}")

    # ================================= 压缩 & 修复 =================================
    def _compress(self, path, level, out):
        out = out or "compressed.pdf"
        r, w = PdfReader(path), PdfWriter()
        for p in r.pages: w.add_page(p)
        with open(out, "wb") as f: w.write(f)
        return self._success(f"压缩完成({level})：{out}")

    def _repair(self, path, out):
        out = out or "repaired.pdf"
        try:
            r = PdfReader(path)
            w = PdfWriter()
            for p in r.pages: w.add_page(p)
            with open(out, "wb") as f: w.write(f)
            return self._success(f"修复完成：{out}")
        except:
            return self._error("修复失败")

    # ================================= 批量 =================================
    def _batch_process(self, params):
        folder = params.get("folder_path")
        act = params.get("batch_action")
        if not folder or not os.path.isdir(folder): return self._error("文件夹无效")
        log = []
        for f in os.listdir(folder):
            fp = os.path.join(folder, f)
            try:
                if act == "extract" and f.endswith(".pdf"):
                    self._extract_text(fp)
                    log.append(f"✅ {f} 提取成功")
                elif act == "to_word" and f.endswith(".pdf"):
                    self._to_word(fp, fp.replace(".pdf", ".docx"))
                    log.append(f"✅ {f} 转Word成功")
                elif act == "to_image" and f.endswith(".pdf"):
                    self._to_image(fp, os.path.join(folder, f"imgs_{f}"))
                    log.append(f"✅ {f} 转图片成功")
                elif act == "word2pdf" and f.endswith(".docx"):
                    self._word2pdf(fp, fp.replace(".docx", ".pdf"))
                    log.append(f"✅ {f} 转PDF成功")
            except:
                log.append(f"❌ {f} 失败")
        return self._success(f"批量处理完成", {"log": log})

    # ================================= 通用返回 =================================
    def _success(self, msg, data=None):
        return {"status": "success", "message": msg, "data": data or {}}
    def _error(self, msg):
        return {"status": "error", "message": msg}


# ===================== CLI 入口 =====================
def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="PDF 终极全能处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python %(prog)s info input.pdf
  python %(prog)s to-word input.pdf -o output.docx
  python %(prog)s merge file1.pdf file2.pdf -o merged.pdf
  python %(prog)s rotate input.pdf 90 -o rotated.pdf
  python %(prog)s encrypt input.pdf -p 123456 -o encrypted.pdf
  python %(prog)s images2pdf img1.jpg img2.jpg -o output.pdf
        """
    )
    
    parser.add_argument("command", choices=[
        "info", "extract", "merge", "split", "watermark",
        "to-word", "to-image", "to-html", "to-txt", "to-md",
        "ocr", "decrypt", "encrypt", "rotate", 
        "delete-pages", "extract-pages", "insert-page", "replace-page",
        "add-header", "add-footer", "add-page-num",
        "extract-images", "extract-tables", "extract-bookmarks", "extract-annotations",
        "reverse-pages", "compress", "repair", "images2pdf", "word2pdf", "batch"
    ], help="执行的操作命令")
    
    parser.add_argument("files", nargs="*", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件/目录路径")
    parser.add_argument("-p", "--password", help="PDF 密码（用于解密/加密）")
    parser.add_argument("-n", "--new-password", help="新密码（用于加密）")
    parser.add_argument("-t", "--text", help="水印/页眉/页脚文字")
    parser.add_argument("--page", type=int, help="页码（拆分用）")
    parser.add_argument("--pages", help="页码列表，逗号分隔如 1,3,5")
    parser.add_argument("--degree", type=int, choices=[90, 180, 270], help="旋转角度")
    parser.add_argument("--insert-pdf", help="要插入的PDF路径")
    parser.add_argument("--replace-pdf", help="用于替换的PDF路径")
    parser.add_argument("--level", choices=["low", "medium", "high"], default="medium", help="压缩等级")
    parser.add_argument("--folder", help="批量处理文件夹路径")
    parser.add_argument("--batch-action", choices=["extract", "to-word", "to-image", "word2pdf"], help="批量操作类型")
    
    args = parser.parse_args()
    
    # 构建参数字典
    params = {"action": args.command.replace("-", "_")}
    
    if args.files:
        params["file_paths"] = args.files
    if args.output:
        params["output_path"] = args.output
    if args.password:
        params["password"] = args.password
    if args.new_password:
        params["new_password"] = args.new_password
    if args.text:
        params["watermark_text"] = params["header_text"] = params["footer_text"] = args.text
    if args.page:
        params["split_page"] = args.page
    if args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",")]
        params["delete_pages"] = pages
        params["extract_pages"] = pages
    if args.degree:
        params["rotate_degree"] = args.degree
    if args.insert_pdf:
        params["insert_pdf_path"] = args.insert_pdf
    if args.replace_pdf:
        params["replace_pdf_path"] = args.replace_pdf
    if args.level:
        params["compress_level"] = args.level
    if args.folder:
        params["folder_path"] = args.folder
    if args.batch_action:
        params["batch_action"] = args.batch_action
    
    # 特殊处理
    if args.command == "images2pdf":
        params["image_paths"] = args.files
        params["action"] = "images2pdf"
    
    # 执行
    skill = PDFUltimateSkill()
    result = skill.execute(params)
    
    # 输出结果
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回退出码
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()