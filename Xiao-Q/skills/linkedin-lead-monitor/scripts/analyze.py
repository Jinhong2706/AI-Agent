#!/usr/bin/env python3
"""
LinkedIn 潜客监控 - 商机分析模块
AI 分析动态的商机价值，生成跟进建议
"""

import json
from datetime import datetime
from typing import Optional


# 商机识别规则库
OPPORTUNITY_RULES = {
    'high': {
        'keywords': [
            '采购经理', '采购总监', '决策者', 'director', 'vp', 'vice president',
            'head of', 'chief', 'founder', 'co-founder', 'ceo', 'cto', 'cmo',
            '融资', 'funding', 'investment', 'series', '扩张', 'expansion',
            '招聘', 'hiring', 'growing', 'team', 'launch', '新产品'
        ],
        'position_changes': True,  # 职位变动
        'company_changes': True,   # 公司变动
    },
    'medium': {
        'keywords': [
            '经理', 'manager', 'lead', 'senior', '视频营销', 'video marketing',
            '获客', 'lead generation', '转化', 'conversion', '营销', 'marketing',
            '销售', 'sales', '业务', 'business', '增长', 'growth'
        ],
        'content_mentions': True,  # 内容提及关键词
    },
    'low': {
        'keywords': [
            '分享', 'share', '文章', 'article', '活动', 'event',
            '会议', 'conference', '学习', 'learn', '证书', 'certificate'
        ],
        'daily_activities': True,  # 日常活动
    }
}

# 跟进话术模板
ACTION_TEMPLATES = {
    'job_change': [
        "祝贺{ name} 履新！这是一个建立联系的好时机，可以发送祝贺消息并介绍 Kingsway 如何帮助新团队提升视频营销效果。",
        "职位变动后的前 30 天是最佳接触期，建议发送个性化祝贺 + 价值主张。"
    ],
    'company_funding': [
        "公司获得融资后通常有预算扩大营销，建议介绍 Kingsway 的企业级视频托管方案。",
        "融资后 1-3 个月是采购决策高峰期，建议主动联系演示产品。"
    ],
    'company_expansion': [
        "公司扩张意味着需要更多营销工具，建议介绍 Kingsway 的规模化视频获客方案。",
        "新市场拓展需要本地化视频内容，Kingsway 的视频翻译功能可以派上用场。"
    ],
    'content_mention': [
        "潜客提及视频营销相关话题，可以在评论区提供有价值见解，建立专业形象。",
        "针对潜客提到的痛点，分享 Kingsway 相关案例或解决方案。"
    ],
    'default': [
        "保持关注，等待更好的接触时机。",
        "可以通过点赞/评论保持互动，建立弱联系。"
    ]
}


def analyze_opportunity(activity: dict, lead_info: dict) -> dict:
    """
    分析商机的优先级和价值
    
    Args:
        activity: 动态信息 {type, content, timestamp}
        lead_info: 潜客信息 {name, company, position, priority}
    
    Returns:
        分析结果 {score, level, analysis, suggested_action}
    """
    content = activity.get('content', '').lower()
    activity_type = activity.get('type', 'unknown')
    
    # 计算商机分数
    score = calculate_score(content, activity_type, lead_info)
    
    # 确定优先级
    if score >= 70:
        level = 'high'
    elif score >= 40:
        level = 'medium'
    else:
        level = 'low'
    
    # 生成 AI 分析
    analysis = generate_analysis(activity, lead_info, score)
    
    # 生成跟进建议
    suggested_action = generate_action(activity_type, lead_info)
    
    return {
        'score': score,
        'level': level,
        'analysis': analysis,
        'suggested_action': suggested_action,
        'analyzed_at': datetime.now().isoformat()
    }


def calculate_score(content: str, activity_type: str, lead_info: dict) -> int:
    """计算商机分数 (0-100)"""
    score = 0
    
    # 基础分数：根据潜客优先级
    base_scores = {'high': 30, 'medium': 20, 'low': 10}
    score += base_scores.get(lead_info.get('priority', 'medium'), 20)
    
    # 活动类型分数
    type_scores = {
        'job_change': 40,      # 职位变动
        'company_update': 35,  # 公司动态
        'post': 15,            # 内容发布
        'interaction': 10      # 互动行为
    }
    score += type_scores.get(activity_type, 10)
    
    # 关键词匹配分数
    for level, rules in OPPORTUNITY_RULES.items():
        for keyword in rules['keywords']:
            if keyword.lower() in content:
                multiplier = {'high': 3, 'medium': 2, 'low': 1}[level]
                score += 5 * multiplier
    
    # 职位分数 (如果潜客是决策者)
    position = lead_info.get('position', '').lower()
    decision_keywords = ['director', 'vp', 'head', 'chief', 'manager', '决策', '采购']
    if any(kw in position for kw in decision_keywords):
        score += 15
    
    # 限制在 0-100 范围
    return min(100, max(0, score))


def generate_analysis(activity: dict, lead_info: dict, score: int) -> str:
    """生成 AI 分析文本"""
    activity_type = activity.get('type', 'unknown')
    content = activity.get('content', '')
    
    analyses = {
        'job_change': (
            f"职位变动是最佳接触时机。{lead_info.get('name')} 的新职位可能带来新的采购决策权，"
            f"建议在 24 小时内发送祝贺消息并介绍 Kingsway 的核心价值。"
        ),
        'company_update': (
            f"公司动态表明业务正在发展。融资/扩张通常伴随营销预算增加，"
            f"Kingsway 的企业级视频解决方案可以帮助{lead_info.get('company')}提升获客效率。"
        ),
        'post': (
            f"内容发布显示{lead_info.get('name')}对{extract_topic(content)}感兴趣。"
            f"可以通过评论互动建立联系，分享 Kingsway 相关案例。"
        ),
        'interaction': (
            f"互动行为表明{lead_info.get('name')}在关注行业动态。"
            f"保持适度互动，等待更好的接触时机。"
        )
    }
    
    base_analysis = analyses.get(activity_type, "发现新的动态，值得持续关注。")
    
    # 根据分数调整语气
    if score >= 70:
        urgency = "【高优先级】建议立即跟进。"
    elif score >= 40:
        urgency = "【中优先级】建议 48 小时内联系。"
    else:
        urgency = "【低优先级】保持关注即可。"
    
    return f"{base_analysis} {urgency}"


def generate_action(activity_type: str, lead_info: dict) -> str:
    """生成跟进建议"""
    templates = ACTION_TEMPLATES.get(activity_type, ACTION_TEMPLATES['default'])
    template = templates[0]  # 选择第一个模板
    
    return template.format(
        name=lead_info.get('name', '潜客'),
        company=lead_info.get('company', '该公司'),
        position=lead_info.get('position', '新职位')
    )


def extract_topic(content: str) -> str:
    """从内容中提取主题关键词"""
    topics = []
    
    topic_keywords = {
        '视频营销': ['video', '营销', '内容'],
        '获客': ['lead', '获客', '转化'],
        '跨境电商': ['cross-border', '电商', '独立站'],
        'B2B 外贸': ['b2b', '外贸', '出口'],
    }
    
    content_lower = content.lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in content_lower for kw in keywords):
            topics.append(topic)
    
    return ', '.join(topics) if topics else '行业相关话题'


if __name__ == '__main__':
    # 测试示例
    test_activity = {
        'type': 'job_change',
        'content': 'Excited to announce my new role as Marketing Director at TechCorp!',
        'timestamp': '2026-03-31T10:00:00'
    }
    
    test_lead = {
        'name': 'John Doe',
        'company': 'TechCorp',
        'position': 'Marketing Director',
        'priority': 'high'
    }
    
    result = analyze_opportunity(test_activity, test_lead)
    print(json.dumps(result, indent=2, ensure_ascii=False))
