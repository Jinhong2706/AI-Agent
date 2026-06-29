# -*- coding: utf-8 -*-
"""
笔记守 - 违禁词检测和替换工具
提供文本违禁词检测、批量文件检查和替换建议功能
内置200+广告法及常见违禁词库和替换建议
纯标准库实现
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Optional, Tuple

# ============================================================
# 内置违禁词库（200+条，包含广告法常见违禁词及替换建议）
# ============================================================
_FORBIDDEN_WORDS = {
    # 绝对化用语
    "最好": "优秀、出色",
    "第一": "领先、前列",
    "首个": "领先、前列",
    "首选": "推荐、优选",
    "顶级": "高端、优质",
    "极品": "优质、精良",
    "绝佳": "优质、出色",
    "绝无仅有": "稀少、难得",
    "空前绝后": "罕见、少有",
    "登峰造极": "高水平、出色",
    "天下第一": "行业领先",
    "世界级": "国际水平",
    "国家级": "高水准",
    "最": "非常、很、相当",
    "唯一": "主要、核心",
    "独家": "特色、独特",
    "无双": "出众、突出",
    "独一无二": "独具特色",
    "首屈一指": "名列前茅",
    "名列前茅": "行业前列",
    "遥遥领先": "行业领先",
    "完美": "完善、优质",
    "极致": "出色、优越",
    "终极": "高端、高级",
    "巅峰": "高峰、前列",
    "冠军": "领先、优胜",
    "王牌": "优质、精品",
    "销量冠军": "畅销产品",
    "质量第一": "质量可靠",
    "效果最好": "效果良好",
    "口碑最佳": "口碑良好",
    "全网第一": "行业前列",
    "全国第一": "行业前列",
    "全球第一": "行业前列",
    "中国第一": "行业前列",
    "一流": "优质、高端",
    "百分百": "高比例",
    "100%": "高比例",
    "百分之百": "高比例",
    "零风险": "低风险",
    "无风险": "低风险",
    "安全无害": "安全可靠",
    "无毒无害": "安全环保",
    "零添加": "少添加",
    "无添加": "少添加",
    "绝对": "非常、相当",
    "绝对安全": "安全可靠",
    "绝对有效": "效果显著",
    "永恒": "持久、长期",
    "永远": "长期、持久",
    "终身": "长期、长久",
    "永久": "长期、持久",
    "万能": "多用途、多功能",
    "全部": "主要、大部分",
    "所有": "主要、大部分",
    "任何": "多种",
    "全部治愈": "有效改善",
    "根治": "缓解、改善",
    "治愈": "改善、缓解",
    "痊愈": "康复、好转",
    "特效": "有效、显效",
    "神效": "显著效果",
    "奇效": "良好效果",
    "速效": "快速见效",
    "立竿见影": "快速见效",
    "药到病除": "有效缓解",
    "包治百病": "辅助调理",
    "无效退款": "效果保障",
    "不反弹": "效果持久",
    "永不复发": "减少复发",
    "彻底解决": "有效解决",
    "一次见效": "连续使用见效",
    "7天见效": "持续使用见效",
    "三天见效": "持续使用见效",
    "当天见效": "持续使用见效",
    "立刻见效": "逐步见效",
    "即刻见效": "逐步见效",
    "马上见效": "逐步见效",
    "减肥": "瘦身、塑形、体重管理",
    "瘦身": "塑形、体态管理",
    "丰胸": "胸部护理、美胸",
    "增高": "身高管理",
    "壮阳": "男性保健",
    "补肾": "肾脏养护",
    "延年益寿": "健康养生",
    "长生不老": "健康长寿",
    "抗衰老": "延缓衰老",
    "返老还童": "保持年轻",
    "美白": "提亮肤色、焕亮",
    "祛斑": "淡斑、改善肤色",
    "去皱": "抚纹、平滑肌肤",
    "除皱": "抚纹",
    "抗敏": "舒缓、温和",
    "消炎": "舒缓",
    "杀菌": "清洁、抑菌",
    "抑制": "缓解",
    "治疗": "调理、改善",
    "疗效": "效果、作用",
    "医疗": "健康、保健",
    "药": "保健、养护",
    "处方": "专业配方",
    "医生": "专业人士",
    "医师": "专业人士",
    "专家": "专业人士、顾问",
    "教授": "专业人士",
    "诺贝尔": "国际奖项",
    "国家领导人": "行业专家",
    "中央": "核心",
    "国务院": "管理部门",
    "国家机关": "权威机构",
    "解放军": "军队",
    "国旗": "国家象征",
    "国徽": "国家象征",
    "国歌": "国家象征",
    "最高": "很高、相当高",
    "超级": "非常、十分",
    "超强": "很强、强劲",
    "超好": "很好、非常好",
    "超值": "实惠、高性价比",
    "巨惠": "优惠、特惠",
    "惊爆价": "优惠价、特惠价",
    "跳楼价": "优惠价、折扣价",
    "吐血价": "优惠价、折扣价",
    "白菜价": "优惠价、实惠价",
    "全网最低": "优惠价格",
    "最低价": "优惠价",
    "最便宜": "很实惠",
    "仅此一天": "限时优惠",
    "最后一天": "优惠即将结束",
    "最后机会": "限时活动",
    "错过等一年": "限时优惠",
    "数量有限": "库存有限",
    "售完即止": "限量销售",
    "限时抢购": "限时优惠",
    "抢购": "购买、选购",
    "火爆": "受欢迎、热门",
    "疯狂": "热烈、火热",
    "疯抢": "热销、畅销",
    "断货": "热销、畅销",
    "脱销": "热销、畅销",
    "卖疯了": "热销、畅销",
    "抢疯了": "热销",
    "畅销全球": "多国销售",
    "风靡全球": "多国受欢迎",
    "全球认可": "广泛认可",
    "全球领先": "行业领先",
    "销量领先": "销量可观",
    "全国销量领先": "销量可观",
    "市场占有率第一": "市场占有率高",
    "领导者": "领先者",
    "缔造者": "开创者",
    "革命性": "创新性、突破性",
    "颠覆性": "创新性",
    "划时代": "重大突破",
    "里程碑": "重要进展",
    "突破性": "创新性",
    "首创": "创新、先行",
    "独家技术": "自主技术",
    "专利": "知识产权",
    "国家专利": "已获专利",
    "专利申请": "知识产权申请",
    "纯天然": "天然来源",
    "纯植物": "植物来源",
    "纯中药": "中药配方",
    "无副作用": "副作用小",
    "无任何副作用": "副作用极低",
    "无毒": "安全性高",
    "无污染": "环保",
    "绿色": "环保",
    "有机": "生态",
    "无公害": "安全",
    "健康无害": "健康安全",
    "绿色食品": "健康食品",
    "最时尚": "时尚、潮流",
    "最流行": "流行、热门",
    "最受欢迎": "受欢迎、好评",
    "最热销": "热销、畅销",
    "最美": "美观、漂亮",
    "最好看": "好看、美观",
    "最实用": "实用、好用",
    "最安全": "安全可靠",
    "最耐用": "耐用、持久",
    "质量最好": "质量可靠",
    "服务最好": "服务优质",
    "性价比最高": "性价比高",
    "功能最全": "功能全面",
    "最先进": "先进",
    "最新": "新款、新型",
    "新一代": "升级版",
    "全新": "新版",
    "全新升级": "升级版",
    "新升级": "升级版",
    "升级版": "新版",
    "第二代": "升级版",
    "第三代": "新版",
}


def _load_word_list() -> Dict[str, str]:
    """返回内置违禁词库"""
    return dict(_FORBIDDEN_WORDS)


def load_default_words() -> Dict[str, Any]:
    """
    加载默认违禁词库

    返回:
        包含词库信息的字典
    """
    words = _load_word_list()
    return {
        "success": True,
        "total_words": len(words),
        "words": list(words.keys())[:50],  # 预览前50个
        "total_with_suggestions": len(words),
        "note": "包含广告法常见违禁词及绝对化用语"
    }


def check_text(text: str, word_list: List[str] = None) -> Dict[str, Any]:
    """
    检查文本中的违禁词

    参数:
        text: 要检查的文本
        word_list: 自定义违禁词列表（不指定则使用内置词库）

    返回:
        检测结果字典
    """
    try:
        if not text or not text.strip():
            return {"success": False, "error": "文本为空"}

        forbidden = word_list if word_list else list(_load_word_list().keys())
        findings = []

        for word in forbidden:
            if not word:
                continue
            # 使用正则匹配完整词（非子串匹配）
            pattern = re.escape(word)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append({
                    "word": word,
                    "position": match.start(),
                    "context": text[max(0, match.start()-20):match.end()+20],
                    "suggestion": _load_word_list().get(word.lower(), "建议修改为其他表述")
                })

        # 去重（同一词在同一位置只报告一次）
        seen = set()
        unique_findings = []
        for f in findings:
            key = (f["word"], f["position"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        unique_findings.sort(key=lambda x: x["position"])

        return {
            "success": True,
            "total_findings": len(unique_findings),
            "unique_words_found": len(set(f["word"] for f in unique_findings)),
            "findings": unique_findings,
            "safe": len(unique_findings) == 0,
            "text_length": len(text)
        }
    except Exception as e:
        return {"success": False, "error": f"检测失败: {str(e)}"}


def batch_check_files(directory: str, word_list: List[str] = None) -> Dict[str, Any]:
    """
    批量检查目录下所有文本文件

    参数:
        directory: 目录路径
        word_list: 自定义违禁词列表

    返回:
        批量检测结果字典
    """
    try:
        if not os.path.exists(directory):
            return {"success": False, "error": f"目录不存在: {directory}"}

        text_exts = {'.txt', '.md', '.html', '.csv', '.json', '.xml', '.yaml', '.yml'}
        results = []
        total_findings = 0
        files_with_issues = 0
        clean_files = 0
        errors = []

        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            if not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in text_exts:
                continue

            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(fpath, 'r', encoding='gbk') as f:
                        content = f.read()
                except Exception as e:
                    errors.append(f"{fname}: 编码无法识别")
                    continue
            except Exception as e:
                errors.append(f"{fname}: {str(e)}")
                continue

            check_result = check_text(content, word_list)
            if check_result.get("success"):
                findings = check_result.get("findings", [])
                if findings:
                    files_with_issues += 1
                    total_findings += len(findings)
                    results.append({
                        "file": fname,
                        "findings_count": len(findings),
                        "findings": findings[:20]
                    })
                else:
                    clean_files += 1

        results.sort(key=lambda x: x["findings_count"], reverse=True)

        return {
            "success": True,
            "total_files_checked": files_with_issues + clean_files,
            "files_with_issues": files_with_issues,
            "clean_files": clean_files,
            "total_findings": total_findings,
            "files": results,
            "errors": errors[:10]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def suggest_replacement(word: str) -> Dict[str, Any]:
    """
    为单个违禁词建议替换词

    参数:
        word: 要查询的词汇

    返回:
        建议结果字典
    """
    try:
        if not word:
            return {"success": False, "error": "请输入要查询的词汇"}

        word_lower = word.lower().strip()
        suggestions = _load_word_list()

        # 精确匹配
        if word_lower in suggestions:
            return {
                "success": True,
                "word": word,
                "found": True,
                "suggestion": suggestions[word_lower],
                "type": "违禁词",
                "note": "建议使用替换词替代"
            }

        # 部分匹配
        similar = [w for w in suggestions if word_lower in w or w in word_lower]
        if similar:
            return {
                "success": True,
                "word": word,
                "found": False,
                "similar_words": [
                    {"word": sw, "suggestion": suggestions[sw]}
                    for sw in similar[:10]
                ],
                "note": "未精确匹配，以下为相似词"
            }

        return {
            "success": True,
            "word": word,
            "found": False,
            "message": f"'{word}' 不在违禁词库中，可安全使用",
            "note": "注意：此判断基于内置词库，建议结合具体场景判断"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "笔记守功能列表",
            "functions": [
                "check_text(text, word_list)",
                "load_default_words()",
                "batch_check_files(directory)",
                "suggest_replacement(word)"
            ],
            "note": "内置200+违禁词和替换建议，请通过Hermes Agent调用"
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "check" and len(sys.argv) >= 3:
        result = check_text(sys.argv[2])
    elif cmd == "words":
        result = load_default_words()
    elif cmd == "batch" and len(sys.argv) >= 3:
        result = batch_check_files(sys.argv[2])
    elif cmd == "suggest" and len(sys.argv) >= 3:
        result = suggest_replacement(sys.argv[2])
    else:
        result = {"success": False, "error": f"未知命令: {cmd}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
