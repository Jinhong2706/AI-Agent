#!/usr/bin/env python3
"""
浏览器自动化发布脚本
使用 Playwright 控制浏览器发布视频
"""

import asyncio
import argparse
import os
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser


class VideoPublisher:
    """视频发布器"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=["--start-maximized"]
        )
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            storage_state="browser_state.json"  # 保存登录状态
        )
        self.page = await context.new_page()
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def publish_to_xiaohongshu(
        self, 
        video_path: str, 
        title: str, 
        tags: List[str],
        description: str = ""
    ) -> Dict:
        """
        发布到小红书
        
        Args:
            video_path: 视频文件路径
            title: 标题
            tags: 标签列表
            description: 描述
        
        Returns:
            发布结果
        """
        print("\n📱 发布到小红书...")
        
        try:
            # 打开小红书创作者中心
            await self.page.goto("https://creator.xiaohongshu.com/publish/publish")
            await self.page.wait_for_load_state("networkidle")
            
            # 检查是否需要登录
            if "login" in self.page.url:
                print("⚠️  需要登录小红书，请在浏览器中完成登录")
                await self.page.wait_for_url("**/publish/publish", timeout=300000)
            
            # 点击上传视频
            upload_btn = await self.page.query_selector('text="上传视频"')
            if upload_btn:
                await upload_btn.click()
            
            # 上传视频文件
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
            
            # 等待上传完成
            print("⏳ 上传视频中...")
            await asyncio.sleep(5)  # 简单等待，实际应该监控上传进度
            
            # 填写标题
            title_input = await self.page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
            
            # 填写描述
            if description:
                desc_input = await self.page.query_selector('textarea[placeholder*="描述"]')
                if desc_input:
                    await desc_input.fill(description)
            
            # 添加标签
            for tag in tags:
                tag_input = await self.page.query_selector('input[placeholder*="标签"]')
                if tag_input:
                    await tag_input.fill(tag)
                    await tag_input.press("Enter")
                    await asyncio.sleep(0.5)
            
            # 点击发布
            publish_btn = await self.page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()
            
            # 等待发布完成
            await asyncio.sleep(3)
            
            print("✅ 小红书发布成功")
            return {
                "platform": "xiaohongshu",
                "status": "success",
                "title": title,
                "tags": tags
            }
            
        except Exception as e:
            print(f"❌ 小红书发布失败: {e}")
            return {
                "platform": "xiaohongshu",
                "status": "failed",
                "error": str(e)
            }
    
    async def publish_to_douyin(
        self, 
        video_path: str, 
        title: str, 
        tags: List[str]
    ) -> Dict:
        """
        发布到抖音
        """
        print("\n🎵 发布到抖音...")
        
        try:
            # 打开抖音创作者中心
            await self.page.goto("https://creator.douyin.com/creator-micro/content/upload")
            await self.page.wait_for_load_state("networkidle")
            
            # 检查登录
            if "login" in self.page.url:
                print("⚠️  需要登录抖音，请在浏览器中完成登录")
                await self.page.wait_for_url("**/content/upload", timeout=300000)
            
            # 上传视频
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
            
            print("⏳ 上传视频中...")
            await asyncio.sleep(5)
            
            # 填写标题
            title_input = await self.page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
            
            # 添加标签
            for tag in tags:
                tag_input = await self.page.query_selector('input[placeholder*="话题"]')
                if tag_input:
                    await tag_input.fill(tag)
                    await tag_input.press("Enter")
                    await asyncio.sleep(0.5)
            
            # 发布
            publish_btn = await self.page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()
            
            await asyncio.sleep(3)
            
            print("✅ 抖音发布成功")
            return {
                "platform": "douyin",
                "status": "success",
                "title": title,
                "tags": tags
            }
            
        except Exception as e:
            print(f"❌ 抖音发布失败: {e}")
            return {
                "platform": "douyin",
                "status": "failed",
                "error": str(e)
            }
    
    async def publish_to_shipinhao(
        self, 
        video_path: str, 
        title: str, 
        tags: List[str]
    ) -> Dict:
        """
        发布到视频号
        """
        print("\n📹 发布到视频号...")
        
        try:
            # 视频号需要通过微信网页版
            await self.page.goto("https://channels.weixin.qq.com/")
            await self.page.wait_for_load_state("networkidle")
            
            print("⚠️  视频号需要扫码登录微信")
            print("   请在浏览器中扫码登录，然后手动上传视频")
            
            # 视频号发布较复杂，暂时只打开页面
            return {
                "platform": "shipinhao",
                "status": "manual",
                "message": "请手动完成发布"
            }
            
        except Exception as e:
            print(f"❌ 视频号发布失败: {e}")
            return {
                "platform": "shipinhao",
                "status": "failed",
                "error": str(e)
            }
    
    async def publish_to_kuaishou(
        self, 
        video_path: str, 
        title: str, 
        tags: List[str]
    ) -> Dict:
        """
        发布到快手
        """
        print("\n⚡ 发布到快手...")
        
        try:
            await self.page.goto("https://cp.kuaishou.com/article/publish/video")
            await self.page.wait_for_load_state("networkidle")
            
            if "login" in self.page.url:
                print("⚠️  需要登录快手，请在浏览器中完成登录")
                await self.page.wait_for_url("**/publish/video", timeout=300000)
            
            # 上传视频
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
            
            print("⏳ 上传视频中...")
            await asyncio.sleep(5)
            
            # 填写标题
            title_input = await self.page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
            
            # 添加标签
            for tag in tags:
                tag_input = await self.page.query_selector('input[placeholder*="标签"]')
                if tag_input:
                    await tag_input.fill(tag)
                    await tag_input.press("Enter")
                    await asyncio.sleep(0.5)
            
            # 发布
            publish_btn = await self.page.query_selector('button:has-text("发布")')
            if publish_btn:
                await publish_btn.click()
            
            await asyncio.sleep(3)
            
            print("✅ 快手发布成功")
            return {
                "platform": "kuaishou",
                "status": "success",
                "title": title,
                "tags": tags
            }
            
        except Exception as e:
            print(f"❌ 快手发布失败: {e}")
            return {
                "platform": "kuaishou",
                "status": "failed",
                "error": str(e)
            }


async def main():
    parser = argparse.ArgumentParser(description="浏览器自动化发布")
    parser.add_argument("--video", type=str, required=True)
    parser.add_argument("--platform", type=str, required=True)
    parser.add_argument("--title", type=str, required=True)
    parser.add_argument("--tags", type=str, required=True)
    parser.add_argument("--description", type=str, default="")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    
    args = parser.parse_args()
    
    publisher = VideoPublisher(headless=args.headless)
    
    try:
        await publisher.init_browser()
        
        tags = [t.strip() for t in args.tags.split(",")]
        
        if args.platform == "xiaohongshu":
            result = await publisher.publish_to_xiaohongshu(
                args.video, args.title, tags, args.description
            )
        elif args.platform == "douyin":
            result = await publisher.publish_to_douyin(
                args.video, args.title, tags
            )
        elif args.platform == "shipinhao":
            result = await publisher.publish_to_shipinhao(
                args.video, args.title, tags
            )
        elif args.platform == "kuaishou":
            result = await publisher.publish_to_kuaishou(
                args.video, args.title, tags
            )
        else:
            print(f"❌ 不支持的平台: {args.platform}")
            return
        
        print(f"\n📋 发布结果: {result}")
        
    finally:
        await publisher.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
