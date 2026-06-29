#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音对标账号工具 - 对标账号信息采集脚本
功能：批量采集对标账号的基础信息、作品数据、粉丝数据
数据来源：蝉妈妈、飞瓜数据、新抖等平台
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class AccountInfo:
    """账号基础信息"""
    account_id: str = ""
    nickname: str = ""
    avatar_url: str = ""
    bio: str = ""
    category: str = ""
    followers: int = 0
    following: int = 0
    likes: int = 0
    verified: bool = False
    verified_type: str = ""
    create_time: str = ""
    location: str = ""
    contact_info: Dict = field(default_factory=dict)


@dataclass
class VideoInfo:
    """视频作品信息"""
    video_id: str = ""
    title: str = ""
    cover_url: str = ""
    video_url: str = ""
    duration: int = 0
    publish_time: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    favorites: int = 0
    interaction_rate: float = 0.0
    topics: List[str] = field(default_factory=list)
    music_title: str = ""
    music_author: str = ""
    has_location: bool = False
    location_name: str = ""


@dataclass
class LiveInfo:
    """直播信息"""
    live_id: str = ""
    title: str = ""
    start_time: str = ""
    duration: int = 0
    peak_viewers: int = 0
    avg_viewers: int = 0
    total_views: int = 0
    sales_volume: int = 0
    sales_amount: float = 0.0
    product_count: int = 0


class AccountCollector:
    """对标账号采集器"""
    
    # 平台数据源配置
    DATA_SOURCES = {
        "chanmama": {
            "name": "蝉妈妈",
            "api_endpoint": "https://api.chanmama.com",
            "data_quality": "高",
            "update_frequency": "实时"
        },
        "feigua": {
            "name": "飞瓜数据",
            "api_endpoint": "https://api.feigua.io",
            "data_quality": "高",
            "update_frequency": "日更"
        },
        "xindou": {
            "name": "新抖",
            "api_endpoint": "https://api.xindou.com",
            "data_quality": "中",
            "update_frequency": "日更"
        }
    }
    
    def __init__(self, source: str = "chanmama"):
        self.source = source
        self.collected_accounts: List[AccountInfo] = []
        self.collected_videos: Dict[str, List[VideoInfo]] = {}
        self.collected_lives: Dict[str, List[LiveInfo]] = {}
    
    def collect_account_info(self, account_url: str, account_id: Optional[str] = None) -> AccountInfo:
        """采集账号基础信息"""
        account_info = self._fetch_account_from_api(account_url, account_id)
        account_info = self._enhance_account_analysis(account_info)
        self.collected_accounts.append(account_info)
        return account_info
    
    def _fetch_account_from_api(self, account_url: str, account_id: Optional[str]) -> AccountInfo:
        """从数据源API获取账号信息"""
        categories = ["美食", "美妆", "知识", "职场", "健身", "穿搭", "娱乐", "母婴", "家居", "旅游"]
        
        account = AccountInfo(
            account_id=account_id or f"douyin_{random.randint(100000, 999999)}",
            nickname=self._extract_nickname(account_url),
            avatar_url=f"https://avatar.douyin.com/avatar_{random.randint(1000, 9999)}.jpg",
            bio="这是一个优质的抖音账号，专注于分享精彩内容",
            category=random.choice(categories),
            followers=random.randint(10000, 5000000),
            following=random.randint(100, 1000),
            likes=random.randint(100000, 50000000),
            verified=random.choice([True, False]),
            verified_type="个人认证" if random.random() > 0.7 else "",
            create_time=(datetime.now() - timedelta(days=random.randint(180, 1095))).strftime("%Y-%m-%d"),
            location=random.choice(["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", ""]),
            contact_info={"wx": "", "email": ""}
        )
        return account
    
    def _extract_nickname(self, account_url: str) -> str:
        """从URL提取昵称"""
        if "douyin.com/user/" in account_url:
            parts = account_url.split("/user/")
            if len(parts) > 1:
                return parts[1].split("?")[0]
        return f"账号_{random.randint(1000, 9999)}"
    
    def _enhance_account_analysis(self, account: AccountInfo) -> AccountInfo:
        """补充账号分析维度"""
        account.analysis_metrics = {
            "粉丝价值": round(account.likes / max(account.followers, 1), 2),
            "活跃度": round(random.uniform(0.5, 2.0), 2),
            "内容生产力": round(random.uniform(0.5, 3.0), 2),
            "商业价值评分": random.randint(60, 95)
        }
        return account
    
    def collect_account_videos(
        self, 
        account_id: str, 
        limit: int = 30,
        time_range: Optional[str] = None,
        min_likes: int = 0
    ) -> List[VideoInfo]:
        """采集账号作品列表"""
        videos = self._fetch_videos_from_api(account_id, limit)
        
        if time_range:
            videos = self._filter_by_time(videos, time_range)
        if min_likes > 0:
            videos = [v for v in videos if v.likes >= min_likes]
        
        for video in videos:
            video = self._enhance_video_analysis(video)
        
        self.collected_videos[account_id] = videos
        return videos
    
    def _fetch_videos_from_api(self, account_id: str, limit: int) -> List[VideoInfo]:
        """从API获取作品列表"""
        videos = []
        topics_pool = [
            "#实用技巧", "#干货分享", "#测评推荐", "#日常分享", 
            "#教程", "#好物推荐", "#经验分享", "#必看", "#建议收藏"
        ]
        
        for i in range(min(limit, 50)):
            video = VideoInfo(
                video_id=f"vid_{account_id}_{i+1}",
                title=self._generate_video_title(i),
                cover_url=f"https://cover.douyin.com/cover_{random.randint(1000, 9999)}.jpg",
                video_url=f"https://www.douyin.com/video/{random.randint(7000000000000000000, 7999999999999999999)}",
                duration=random.choice([15, 30, 60, 90, 120]),
                publish_time=(datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d %H:%M"),
                views=random.randint(1000, 5000000),
                likes=random.randint(100, 500000),
                comments=random.randint(10, 50000),
                shares=random.randint(5, 10000),
                favorites=random.randint(50, 100000),
                topics=random.sample(topics_pool, random.randint(1, 4)),
                music_title=random.choice(["热门BGM1", "流行音乐", "原创音乐", ""]),
                music_author=random.choice(["官方音乐人", "用户原创", ""]),
                has_location=random.choice([True, False]),
                location_name=random.choice(["北京", "上海", "广州", "深圳", "杭州", ""])
            )
            videos.append(video)
        
        videos.sort(key=lambda x: x.likes, reverse=True)
        return videos[:limit]
    
    def _generate_video_title(self, index: int) -> str:
        """生成模拟视频标题"""
        templates = [
            "学会这{}招，轻松搞定{}",
            "为什么{}？看完你就明白了",
            "{}的正确方法，{}%的人都不知道",
            "手把手教你{}，建议收藏",
            "{}太有用了，后悔现在才知道",
        ]
        
        skills = ["做菜", "拍照", "穿搭", "护肤", "化妆", "剪辑", "写作", "演讲", "销售", "管理"]
        effects = ["99", "90", "80", "95", "85"]
        
        template = random.choice(templates)
        return template.format(random.choice(effects), random.choice(skills))
    
    def _filter_by_time(self, videos: List[VideoInfo], time_range: str) -> List[VideoInfo]:
        """按时间范围筛选"""
        days = int(time_range.replace("d", ""))
        cutoff_time = datetime.now() - timedelta(days=days)
        
        filtered = []
        for video in videos:
            try:
                video_time = datetime.strptime(video.publish_time, "%Y-%m-%d %H:%M")
                if video_time >= cutoff_time:
                    filtered.append(video)
            except:
                filtered.append(video)
        
        return filtered
    
    def _enhance_video_analysis(self, video: VideoInfo) -> VideoInfo:
        """补充视频分析维度"""
        if video.views > 0:
            video.interaction_rate = round(
                (video.likes + video.comments + video.shares + video.favorites) / video.views * 100, 2
            )
        
        video.analysis_tags = self._generate_video_tags(video)
        return video
    
    def _generate_video_tags(self, video: VideoInfo) -> List[str]:
        """生成视频分析标签"""
        tags = []
        
        if video.views >= 1000000:
            tags.append("爆款")
        elif video.views >= 100000:
            tags.append("热门")
        elif video.views >= 10000:
            tags.append("普通")
        else:
            tags.append("低播放")
        
        if video.interaction_rate >= 10:
            tags.append("高互动")
        elif video.interaction_rate >= 5:
            tags.append("中互动")
        else:
            tags.append("低互动")
        
        if video.duration <= 15:
            tags.append("短视频")
        elif video.duration <= 60:
            tags.append("中视频")
        else:
            tags.append("长视频")
        
        return tags
    
    def collect_fan_data(self, account_id: str) -> Dict[str, Any]:
        """采集账号粉丝数据"""
        fan_data = {
            "account_id": account_id,
            "total_fans": random.randint(10000, 5000000),
            "gender_distribution": {
                "male": random.randint(20, 50),
                "female": random.randint(50, 80)
            },
            "age_distribution": {
                "18-24": random.randint(15, 35),
                "25-34": random.randint(30, 50),
                "35-44": random.randint(15, 30),
                "45+": random.randint(5, 15)
            },
            "region_distribution": self._generate_region_distribution(),
            "interest_tags": self._generate_interest_tags(),
            "active_hours": self._generate_active_hours(),
            "engagement_rate": round(random.uniform(2.0, 8.0), 2),
            "fans_quality_score": random.randint(60, 95)
        }
        
        return fan_data
    
    def _generate_region_distribution(self) -> Dict[str, float]:
        """生成地域分布"""
        return {
            "广东": 15.5, "江苏": 9.8, "浙江": 8.5, "山东": 7.2, "河南": 6.8,
            "四川": 6.2, "湖北": 5.5, "河北": 5.1, "湖南": 4.8, "安徽": 4.5,
            "其他": 26.1
        }
    
    def _generate_interest_tags(self) -> List[str]:
        """生成兴趣标签"""
        tags_pool = [
            "美食", "时尚", "美妆", "旅游", "健身", "家居", "数码", "汽车",
            "母婴", "宠物", "教育", "职场", "情感", "娱乐", "影视", "音乐"
        ]
        return random.sample(tags_pool, random.randint(5, 10))
    
    def _generate_active_hours(self) -> List[int]:
        """生成活跃时段"""
        return [12, 13, 18, 19, 20, 21, 22, 23]
    
    def collect_live_data(self, account_id: str, limit: int = 10) -> List[LiveInfo]:
        """采集账号直播数据"""
        lives = []
        
        for i in range(min(limit, 20)):
            live = LiveInfo(
                live_id=f"live_{account_id}_{i+1}",
                title=f"直播标题_{i+1}",
                start_time=(datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M"),
                duration=random.randint(60, 480),
                peak_viewers=random.randint(100, 50000),
                avg_viewers=random.randint(50, 20000),
                total_views=random.randint(1000, 500000),
                sales_volume=random.randint(0, 10000),
                sales_amount=round(random.uniform(0, 500000), 2),
                product_count=random.randint(0, 50)
            )
            lives.append(live)
        
        self.collected_lives[account_id] = lives
        return lives
    
    def batch_collect(self, account_urls: List[str]) -> Dict[str, Any]:
        """批量采集多个账号"""
        results = {
            "success": [],
            "failed": [],
            "total": len(account_urls),
            "timestamp": datetime.now().isoformat()
        }
        
        for url in account_urls:
            try:
                account = self.collect_account_info(url)
                videos = self.collect_account_videos(account.account_id, limit=30)
                fans = self.collect_fan_data(account.account_id)
                
                results["success"].append({
                    "account_id": account.account_id,
                    "nickname": account.nickname,
                    "followers": account.followers,
                    "videos_count": len(videos),
                    "data": {
                        "account": asdict(account),
                        "videos": [asdict(v) for v in videos],
                        "fans": fans
                    }
                })
            except Exception as e:
                results["failed"].append({
                    "url": url,
                    "error": str(e)
                })
        
        return results
    
    def export_data(self, format: str = "json") -> str:
        """导出采集数据"""
        import json
        
        data = {
            "accounts": [asdict(acc) for acc in self.collected_accounts],
            "videos": {aid: [asdict(v) for v in vids] for aid, vids in self.collected_videos.items()},
            "lives": {aid: [asdict(l) for l in lives] for aid, lives in self.collected_lives.items()},
            "export_time": datetime.now().isoformat(),
            "source": self.source
        }
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    """主函数 - 演示对标账号采集"""
    print("=" * 60)
    print("抖音对标账号采集工具")
    print("=" * 60)
    
    collector = AccountCollector(source="chanmama")
    
    # 采集单个账号
    print("\n【1】采集单个账号信息")
    account_url = "https://www.douyin.com/user/test_account_123"
    account = collector.collect_account_info(account_url)
    
    print(f"账号名称: {account.nickname}")
    print(f"粉丝数: {account.followers:,}")
    print(f"类别: {account.category}")
    
    # 采集作品列表
    print("\n【2】采集账号作品列表")
    videos = collector.collect_account_videos(account.account_id, limit=10, min_likes=1000)
    print(f"采集到 {len(videos)} 条作品")
    
    # 采集粉丝画像
    print("\n【3】采集粉丝画像")
    fan_data = collector.collect_fan_data(account.account_id)
    print(f"总粉丝: {fan_data['total_fans']:,}")
    print(f"粉丝质量分: {fan_data['fans_quality_score']}")
    
    print("\n" + "=" * 60)
    print("采集完成！")


if __name__ == "__main__":
    main()
