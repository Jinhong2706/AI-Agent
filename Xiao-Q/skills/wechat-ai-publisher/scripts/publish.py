#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号自动发布脚本
一键发布 Markdown/HTML 文章到微信公众号草稿箱
支持自动上传封面图、Markdown转HTML、UTF-8编码

用法：
  python3 publish.py --app_id "xxx" --app_secret "xxx" \
    --title "标题" --article "draft.md" --cover "cover.jpg"

  # 使用HTML文件（跳过MD转HTML）
  python3 publish.py --app_id "xxx" --app_secret "xxx" \
    --title "标题" --html_file "draft.html" --cover "cover.jpg"

  # 使用环境变量 WECHAT_APPID / WECHAT_APPSECRET
  python3 publish.py --title "标题" --article "draft.md" --cover "cover.jpg"
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests 未安装，请执行: pip install requests")
    sys.exit(1)


class WeChatPublisher:
    """微信公众号发布器"""

    API_BASE = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.token = None

    def get_token(self):
        """获取 access_token"""
        url = f"{self.API_BASE}/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json()
        if "access_token" in result:
            self.token = result["access_token"]
            return self.token
        err = result.get("errcode", "unknown")
        msg = result.get("errmsg", "unknown error")
        print(f"ERROR: 获取token失败 [{err}] {msg}")
        return None

    def _ensure_token(self):
        if not self.token:
            return self.get_token()
        return self.token

    def upload_thumb(self, image_path):
        """上传封面图，返回 thumb_media_id"""
        token = self._ensure_token()
        if not token:
            return None, None

        url = f"{self.API_BASE}/material/add_material"
        params = {"access_token": token, "type": "image"}

        path = Path(image_path)
        if not path.exists():
            print(f"ERROR: 图片不存在: {image_path}")
            return None, None

        with open(path, "rb") as f:
            resp = requests.post(url, params=params, files={"media": f}, timeout=30)

        result = resp.json()
        media_id = result.get("media_id")
        url_val = result.get("url")
        if media_id:
            print(f"封面上传成功: media_id={media_id}")
            return media_id, url_val
        else:
            err = result.get("errcode", "unknown")
            msg = result.get("errmsg", "unknown error")
            print(f"ERROR: 封面上传失败 [{err}] {msg}")
            return None, None

    def markdown_to_html(self, content):
        """Markdown 转微信公众号兼容 HTML"""
        lines = content.split("\n")
        html = []
        in_code = False
        code_lang = ""
        code_lines = []

        for line in lines:
            stripped = line.strip()

            # 代码块
            if stripped.startswith("```"):
                if not in_code:
                    in_code = True
                    code_lang = stripped[3:].strip()
                    code_lines = []
                else:
                    in_code = False
                    code_content = "\n".join(code_lines)
                    if code_content:
                        html.append(
                            f'<pre style="background:#f6f8fa;padding:16px;border-radius:6px;'
                            f'overflow-x:auto;font-size:14px;line-height:1.6;">'
                            f'<code>{self._escape_html(code_content)}</code></pre>'
                        )
                    code_lines = []
                continue

            if in_code:
                code_lines.append(line if line.strip() else " ")
                continue

            # 空行
            if not stripped:
                continue

            # 标题
            if stripped.startswith("# "):
                html.append(f'<h2 style="font-size:20px;font-weight:bold;margin:24px 0 12px;">{self._process_inline(stripped[2:])}</h2>')
            elif stripped.startswith("## "):
                html.append(f'<h3 style="font-size:18px;font-weight:bold;margin:20px 0 10px;">{self._process_inline(stripped[3:])}</h3>')
            elif stripped.startswith("### "):
                html.append(f'<h4 style="font-size:16px;font-weight:bold;margin:16px 0 8px;">{self._process_inline(stripped[4:])}</h4>')
            # 分隔线
            elif stripped == "---" or stripped == "***":
                html.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0;">')
            # 无序列表
            elif stripped.startswith("- ") or stripped.startswith("* "):
                html.append(f'<p style="margin:8px 0;padding-left:16px;">• {self._process_inline(stripped[2:])}</p>')
            # 有序列表
            elif re.match(r"^\d+\. ", stripped):
                text = re.sub(r"^\d+\. ", "", stripped)
                html.append(f'<p style="margin:8px 0;padding-left:16px;">{self._process_inline(text)}</p>')
            # 引用
            elif stripped.startswith("> "):
                html.append(f'<blockquote style="border-left:3px solid #d0d0d0;padding-left:12px;color:#666;margin:12px 0;">{self._process_inline(stripped[2:])}</blockquote>')
            # 普通段落
            else:
                html.append(f'<p style="font-size:16px;line-height:1.75;letter-spacing:1px;margin:12px 0;">{self._process_inline(stripped)}</p>')

        return "\n".join(html)

    def _process_inline(self, text):
        """处理行内格式：加粗、斜体、行内代码、链接"""
        text = self._escape_html(text)
        # 加粗
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # 斜体
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # 行内代码
        text = re.sub(r"`(.+?)`", r'<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;font-size:14px;">\1</code>', text)
        # 链接
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" style="color:#576b95;">\1</a>', text)
        return text

    def _escape_html(self, text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def create_draft(self, title, content_html, thumb_media_id, digest="", author=""):
        """创建草稿"""
        token = self._ensure_token()
        if not token:
            return None

        url = f"{self.API_BASE}/draft/add"
        params = {"access_token": token}

        draft_data = {
            "articles": [
                {
                    "title": title,
                    "content": content_html,
                    "author": author,
                    "digest": digest,
                    "thumb_media_id": thumb_media_id,
                    "show_cover_pic": 1,
                    "content_source_url": "",
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }
            ]
        }

        json_data = json.dumps(draft_data, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        resp = requests.post(url, params=params, data=json_data, headers=headers, timeout=30)

        result = resp.json()
        media_id = result.get("media_id")
        if media_id:
            print(f"草稿创建成功: media_id={media_id}")
            return media_id
        else:
            err = result.get("errcode", "unknown")
            msg = result.get("errmsg", "unknown error")
            print(f"ERROR: 草稿创建失败 [{err}] {msg}")
            return None

    def publish(self, title, article_path=None, html_content=None,
                cover_path=None, digest="", author=""):
        """
        发布文章到公众号草稿箱

        Args:
            title: 文章标题
            article_path: Markdown 文件路径（与 html_content 二选一）
            html_content: HTML 字符串（与 article_path 二选一）
            cover_path: 封面图路径
            digest: 摘要（50字以内）
            author: 作者名

        Returns:
            dict: {"media_id": str, "cover_url": str} 或 None
        """
        print(f"\n{'='*50}")
        print(f"微信公众号自动发布")
        print(f"{'='*50}")
        print(f"标题: {title}")
        print(f"作者: {author or '(未设置)'}")

        # Step 1: 上传封面
        if cover_path:
            print(f"\n[1/3] 上传封面: {cover_path}")
            thumb_media_id, cover_url = self.upload_thumb(cover_path)
            if not thumb_media_id:
                return None
        else:
            print("\n[1/3] 跳过封面上传（未提供封面图）")
            thumb_media_id = None
            cover_url = None

        # Step 2: 获取内容
        print(f"\n[2/3] 准备内容")
        if html_content:
            content_html = html_content
            print("  使用传入的HTML内容")
        elif article_path:
            path = Path(article_path)
            if not path.exists():
                print(f"ERROR: 文章不存在: {article_path}")
                return None
            md_content = path.read_text(encoding="utf-8")
            print(f"  读取Markdown: {article_path} ({len(md_content)} 字符)")
            content_html = self.markdown_to_html(md_content)
            print(f"  转换HTML完成 ({len(content_html)} 字符)")
        else:
            print("ERROR: 必须提供 --article 或 --html_file")
            return None

        # Step 3: 创建草稿
        print(f"\n[3/3] 创建草稿")
        media_id = self.create_draft(
            title=title,
            content_html=content_html,
            thumb_media_id=thumb_media_id,
            digest=digest,
            author=author,
        )

        if media_id:
            print(f"\n{'='*50}")
            print(f"发布成功!")
            print(f"  草稿 media_id: {media_id}")
            if cover_url:
                print(f"  封面图URL: {cover_url}")
            print(f"  前往 https://mp.weixin.qq.com 查看草稿箱")
            print(f"{'='*50}")
            return {"media_id": media_id, "cover_url": cover_url}
        return None


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号自动发布 - 一键发布文章到草稿箱"
    )
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--article", help="Markdown文章路径")
    parser.add_argument("--html_file", help="HTML文件路径（跳过MD转HTML）")
    parser.add_argument("--cover", help="封面图路径（JPG/PNG，建议<600KB）")
    parser.add_argument("--digest", default="", help="文章摘要（50字以内）")
    parser.add_argument("--author", default="", help="作者名")
    parser.add_argument("--app_id", default="", help="微信公众号AppID（或环境变量WECHAT_APPID）")
    parser.add_argument("--app_secret", default="", help="微信公众号AppSecret（或环境变量WECHAT_APPSECRET）")

    args = parser.parse_args()

    # 读取凭据：参数 > 环境变量
    app_id = args.app_id or os.environ.get("WECHAT_APPID", "")
    app_secret = args.app_secret or os.environ.get("WECHAT_APPSECRET", "")

    if not app_id or not app_secret:
        print("ERROR: 缺少微信API凭据")
        print("  方式1: --app_id 和 --app_secret 参数")
        print("  方式2: 环境变量 WECHAT_APPID 和 WECHAT_APPSECRET")
        sys.exit(1)

    # 获取HTML内容
    html_content = None
    article_path = args.article
    if args.html_file:
        html_content = Path(args.html_file).read_text(encoding="utf-8")

    publisher = WeChatPublisher(app_id, app_secret)
    result = publisher.publish(
        title=args.title,
        article_path=article_path,
        html_content=html_content,
        cover_path=args.cover,
        digest=args.digest,
        author=args.author,
    )

    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
