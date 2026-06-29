#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker 镜像搜索 CLI
数据源: docker.aityp.com
支持搜索镜像列表和获取拉取地址
"""

import argparse
import json
import sys

import requests
from parsel import Selector


def find_images(key: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    url = "https://docker.aityp.com/i/search"
    params = {"search": key}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return parse_results(response.text)


def parse_results(response_text: str):
    data = Selector(text=response_text)
    images_data_raw = data.css(".card")
    images = []
    for idx, i in enumerate(images_data_raw):
        images.append({
            "id": idx,
            "name": i.css(".ms-3 .fw-bold a::text").get(),
            "platform": i.css(".text-muted span::text").get(),
            "url": i.css(".ms-3 .fw-bold a::attr(href)").get()
        })
    return images


def get_image_url(url: str):
    """
    获取镜像的拉取地址
    :param url: 镜像详情页相对路径，如 /i/library/nginx
    :return: 拉取地址（docker pull 后面的镜像名）
    """
    full_url = "https://docker.aityp.com" + url
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(full_url, headers=headers, timeout=15)
    response.raise_for_status()
    data = Selector(response.text)
    image = data.css("tr span.badge.bg-success::text").get()
    return image


def print_table(images, limit=None):
    if limit:
        images = images[:limit]
    if not images:
        print("[!] 未找到结果")
        return
    id_w = max(4, len(str(len(images) - 1)))
    name_w = max(20, max(len(str(img.get("name", ""))) for img in images))
    plat_w = max(10, max(len(str(img.get("platform", ""))) for img in images))
    url_w = max(40, max(len(str(img.get("url", ""))) for img in images))
    sep = "+" + "-" * (id_w + 2) + "+" + "-" * (name_w + 2) + "+" + "-" * (plat_w + 2) + "+" + "-" * (url_w + 2) + "+"
    print(sep)
    print(f"| {'ID':^{id_w}} | {'镜像名称':^{name_w}} | {'平台':^{plat_w}} | {'链接':^{url_w}} |")
    print(sep)
    for img in images:
        name = str(img.get("name", "") or "")[:name_w]
        plat = str(img.get("platform", "") or "")[:plat_w]
        url = str(img.get("url", "") or "")[:url_w]
        print(f"| {img['id']:^{id_w}} | {name:{name_w}} | {plat:{plat_w}} | {url:{url_w}} |")
    print(sep)
    print(f"\n共找到 {len(images)} 条结果")


def main():
    parser = argparse.ArgumentParser(
        prog="docker-search",
        description="从 docker.aityp.com 搜索 Docker 镜像并获取拉取地址",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s search nginx                    # 搜索 nginx 镜像
  %(prog)s search redis --limit 5          # 只显示前 5 条
  %(prog)s search mysql --format json      # JSON 格式输出
  %(prog)s detail /i/library/nginx         # 获取镜像拉取地址
  %(prog)s pull nginx                      # 搜索并获取第一个结果的拉取地址
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # search 子命令
    search_parser = subparsers.add_parser("search", help="搜索镜像")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("-l", "--limit", type=int, default=None, help="限制返回数量")
    search_parser.add_argument("-f", "--format", choices=["table", "json", "csv"], default="table", help="输出格式")
    search_parser.add_argument("-o", "--output", default=None, help="输出到文件")

    # detail 子命令
    detail_parser = subparsers.add_parser("detail", help="获取镜像详情（拉取地址）")
    detail_parser.add_argument("url", help="镜像详情页路径，如 /i/library/nginx")

    # pull 子命令（搜索+自动获取拉取地址）
    pull_parser = subparsers.add_parser("pull", help="搜索镜像并输出 docker pull 命令")
    pull_parser.add_argument("keyword", help="搜索关键词")
    pull_parser.add_argument("-l", "--limit", type=int, default=1, help="获取前 N 个结果的拉取地址")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "search":
        if args.output:
            sys.stdout = open(args.output, "w", encoding="utf-8")
        try:
            print(f"[*] 正在搜索: {args.keyword} ...")
            images = find_images(args.keyword)
            if not images:
                print("[!] 未找到任何镜像")
                sys.exit(1)
            if args.format == "table":
                print_table(images, args.limit)
            elif args.format == "json":
                out = images[:args.limit] if args.limit else images
                print(json.dumps(out, ensure_ascii=False, indent=2))
            elif args.format == "csv":
                out = images[:args.limit] if args.limit else images
                print("id,name,platform,url")
                for img in out:
                    name = (img.get("name") or "").replace(",", " ")
                    plat = (img.get("platform") or "").replace(",", " ")
                    url = (img.get("url") or "").replace(",", " ")
                    print(f'{img["id"]},{name},{plat},{url}')
        except Exception as e:
            print(f"[!] 发生错误: {e}")
            sys.exit(1)
        finally:
            if args.output:
                sys.stdout.close()

    elif args.command == "detail":
        try:
            print(f"[*] 正在获取镜像详情: {args.url}")
            image_url = get_image_url(args.url)
            if image_url:
                print(f"[+] 拉取地址: {image_url}")
                print(f"[+] 拉取命令: docker pull {image_url}")
            else:
                print("[!] 未找到拉取地址")
                sys.exit(1)
        except Exception as e:
            print(f"[!] 发生错误: {e}")
            sys.exit(1)

    elif args.command == "pull":
        try:
            print(f"[*] 正在搜索: {args.keyword}")
            images = find_images(args.keyword)
            if not images:
                print("[!] 未找到任何镜像")
                sys.exit(1)

            limit = args.limit or 1
            for img in images[:limit]:
                print(f"[*] 获取 [{img['name']}] 的拉取地址...")
                image_url = get_image_url(img["url"])
                if image_url:
                    print(f"  [+] docker pull {image_url}")
                else:
                    print(f"  [!] 未能获取拉取地址")
        except Exception as e:
            print(f"[!] 发生错误: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
