"""网页内容提取工具。支持微信公众号文章和普通网页。

用法:
    from web_fetcher import fetch_web_content
    title, content = fetch_web_content("https://mp.weixin.qq.com/s/xxxx")
"""

from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_web_content(url: str) -> tuple[str, str]:
    """抓取网页内容，返回 (title, content)。

    微信公众号文章使用专门提取逻辑（h1#activity-name + div#js_content）。
    普通网页使用 BeautifulSoup 提取正文（article/main/.content 等选择器）。

    Args:
        url: 网页链接

    Returns:
        (title, content) 元组。失败时抛出 requests.RequestException。
    """
    if "mp.weixin.qq.com" in url:
        return _extract_wechat_article(url)
    return _extract_generic_page(url)


def _extract_wechat_article(url: str) -> tuple[str, str]:
    """提取微信公众号文章。"""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # 提取标题（可能在 h1 > span.js_title_inner 内）
    title = ""
    title_tag = soup.find("h1", id="activity-name")
    if title_tag:
        title_inner = title_tag.find("span", class_="js_title_inner")
        if title_inner:
            title = title_inner.get_text(strip=True)
        else:
            title = title_tag.get_text(strip=True)

    # 提取正文
    content_div = soup.find("div", id="js_content")
    content = ""
    if content_div:
        paragraphs = content_div.find_all("p")
        content = "\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )
        if not content:
            content = content_div.get_text(separator="\n", strip=True)

    return title, content


def _extract_generic_page(url: str) -> tuple[str, str]:
    """提取普通网页。"""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    content = ""
    for selector in [
        "article", "main", "[role='main']",
        ".post-content", ".entry-content", ".content", "#content",
    ]:
        tag = soup.select_one(selector)
        if tag:
            content = tag.get_text(separator="\n", strip=True)
            break

    if not content:
        texts = [
            tag.get_text(strip=True)
            for tag in soup.find_all(["p", "div", "section"])
            if len(tag.get_text(strip=True)) > 100
        ]
        if texts:
            content = max(texts, key=len)

    return title, content
