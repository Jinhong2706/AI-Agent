#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪分析命令行工具 v4.3
修复：英文强调词匹配问题（使用单词边界）
"""

import sys
import re
import json
from collections import Counter

# 情绪词典 v4.3
EMOTION_DICT = {
    'positive': {
        'words': {
            # 高强度正面词 (强度 8-10)
            '优秀': 9, '完美': 10, '太棒了': 9, '最爱': 10, '惊喜': 8,
            'awesome': 9, 'perfect': 10, 'amazing': 9, 'brilliant': 9,
            'yyds': 10, '绝了': 9, '宝藏': 8,
            '🥰': 9, '🎉': 8, '🌟': 8,
            '开心': 6, '快乐': 6, '高兴': 6, '喜悦': 7, '幸福': 7, '美好': 6,
            '棒': 6, '好': 5, '赞': 6, '爱': 7, '喜欢': 6, '满意': 6,
            '舒服': 5, '温暖': 6, '甜蜜': 6, '精彩': 7, '厉害': 7,
            '哈哈': 6, '嘿嘿': 5, '嘻嘻': 5, '愉快': 6, '兴奋': 7, '期待': 6,
            '棒棒': 6, '真棒': 7, '太好了': 8, '非常好': 7, '超级': 8,
            '庆幸': 6, '欣慰': 6, '自豪': 7, '感动': 7,
            'happy': 6, 'good': 5, 'great': 7, 'excellent': 8, 'wonderful': 7,
            'love': 8, 'like': 6, 'best': 9, 'fantastic': 8,
            '666': 7, '牛': 7, '牛逼': 8, '太香了': 7, '真香': 7,
            '😊': 6, '😄': 7, '😃': 6, '😀': 6, '❤️': 8, '♥️': 8, '💕': 7, '✨': 6
        },
        'weight': 1.0,
        'ambiguous': []
    },
    'negative': {
        'words': {
            # 高强度负面词 (强度 8-10)
            '绝望': 10, '崩溃': 9, '心碎': 9, '恨': 9, '恶心': 8,
            'shit': 9, 'fuck': 10, 'hell': 8, 'worst': 9, 'horrible': 9, 'disgusting': 8,
            '智障': 9, '辣鸡': 8, '垃圾': 8, '傻逼': 10, '滚': 8,
            '💀': 9, '🤬': 10, '🖕': 10, '😡': 9, '😤': 8, '😠': 8, '💔': 9, '😢': 8, '😭': 9,
            '难过': 6, '伤心': 6, '悲伤': 7, '痛苦': 7, '失望': 6, '沮丧': 6,
            '郁闷': 6, '烦躁': 6, '生气': 7, '讨厌': 7, '烦': 6, '累': 6,
            '困': 5, '病': 6, '痛': 7, '穷': 6, '坏': 6, '烂': 6,
            '哭': 6, '泪': 6, '孤独': 7, '寂寞': 7, '无聊': 5, '压力': 6,
            '焦虑': 7, '恐惧': 7, '累了': 6, '不会再爱了': 8, '无奈': 6,
            '委屈': 6, '心痛': 7, '心累': 7, '折磨': 7,
            '倒霉': 6, '惨': 7, '可恶': 6, '愤怒': 8, '暴怒': 9, '抓狂': 8,
            'sad': 6, 'bad': 6, 'terrible': 8, 'awful': 7, 'hate': 8, 'angry': 7,
            'depressed': 8, 'pain': 7,
            'sb': 9, 'SB': 9, 'md': 7, '卧槽': 6, '我靠': 6, '坑爹': 7, '服了': 6, '无语': 6, '醉了': 6,
        },
        'weight': 1.2,
        'ambiguous': ['卧槽', '我靠', 'md', '服了', '无语', '醉了']
    },
    'neutral': {
        'words': {
            '还行': 5, '一般': 5, '可以': 5, '还好': 5, '普通': 4, '正常': 5,
            '差不多': 4, '不知道': 3, '随便': 3,
            '嗯': 3, '哦': 3, '额': 3, '好吧': 4, '行吧': 4, '可能': 3,
            '也许': 3, '大概': 3, '似乎': 3,
            'ok': 5, 'OK': 5, 'okay': 5, 'fine': 5, 'so-so': 4, 'average': 4, 'normal': 5, 'maybe': 3
        },
        'weight': 0.6,
        'ambiguous': []
    },
    'surprise': {
        'words': {
            '哇': 7, '天哪': 8, '竟然': 7, '居然': 7, '没想到': 7, '震惊': 9, '意外': 6, '惊喜': 8,
            'wow': 8, 'omg': 9, 'OMG': 9, 'what': 6, 'no way': 8, 'unbelievable': 9, 'incredible': 9
        },
        'weight': 0.8,
        'ambiguous': []
    },
    'question': {
        'words': {
            '吗': 3, '呢': 3, '啊': 3, '怎么': 4, '为什么': 4, '啥': 3, '多少': 4, '哪里': 4,
            'how': 4, 'what': 4, 'why': 4, 'where': 4, 'when': 4, 'who': 4, 'which': 4
        },
        'weight': 0.5,
        'ambiguous': []
    }
}

# 强度修饰词
INTENSIFIERS = {
    'high': {
        '非常': 1.5, '特别': 1.5, '超级': 1.8, '极其': 1.8, '太': 1.5, '真': 1.3,
        '好': 1.3, '很': 1.4, '最': 2.0, '巨': 1.8, '超': 1.6, '贼': 1.7,
        'really': 1.5, 'very': 1.5, 'so': 1.6, 'extremely': 2.0, 'totally': 1.7, 'absolutely': 1.8
    },
    'low': {
        '有点': 0.6, '稍微': 0.5, '略微': 0.5, '一些': 0.6, '一点': 0.6, '还算': 0.7, '挺': 0.8,
        'a bit': 0.6, 'slightly': 0.5, 'somewhat': 0.6, 'kind of': 0.6, 'pretty': 0.7
    }
}

# 上下文规则
POSITIVE_CONTEXT = ['厉害', '牛', '棒', '好', '赞', '666', '绝了', '漂亮', '优秀', 'perfect', 'great', 'awesome', 'happy', 'good', 'excellent', 'love', 'like', 'best', 'fantastic']
NEGATIVE_CONTEXT = ['垃圾', '烂', '坏', '讨厌', '烦', '痛', '惨', '倒霉', 'terrible', 'bad', 'awful', 'shit']

# 英文强调词（作为副词修饰其他词，本身不表达情绪）
# 注意：这些是独立的词，不是其他词的一部分
ENGLISH_INTENSIFIERS = ['fucking', 'fuckin', 'freaking', 'frigging', 'damn', 'damned']

def word_in_text(word, text):
    """检查词是否在文本中（使用单词边界，避免子串匹配）"""
    # 对于中文，直接检查
    if re.search(r'[\u4e00-\u9fff]', word):
        return word in text
    
    # 对于英文，使用单词边界
    pattern = r'\b' + re.escape(word) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def preprocess_text(text):
    """文本预处理"""
    text = text.lower().strip()
    return text

def detect_intensifier(text):
    """检测强度修饰词，返回倍率"""
    intensity_multiplier = 1.0
    for word, multiplier in INTENSIFIERS['high'].items():
        if word_in_text(word, text):
            intensity_multiplier *= multiplier
    for word, multiplier in INTENSIFIERS['low'].items():
        if word_in_text(word, text):
            intensity_multiplier *= multiplier
    return intensity_multiplier

def get_base_intensity(emotion_type, matched_words):
    """计算基础强度"""
    if not matched_words:
        return 5.0
    
    total_intensity = 0
    count = 0
    
    for word in matched_words:
        clean_word = word.replace('(歧义→已修正)', '').replace('(强调)', '').strip()
        if clean_word in EMOTION_DICT[emotion_type]['words']:
            total_intensity += EMOTION_DICT[emotion_type]['words'][clean_word]
            count += 1
    
    if count == 0:
        return 5.0
    
    return total_intensity / count

def calculate_intensity_score(text, emotion_type, matched_words, base_score):
    """计算最终情感强度评分（1-10）"""
    score = base_score
    
    intensity_multiplier = detect_intensifier(text)
    score *= intensity_multiplier
    
    # 英文强调词额外增强
    for word in ENGLISH_INTENSIFIERS:
        if word_in_text(word, text):
            score *= 1.8
            break
    
    exclamation_count = text.count('！') + text.count('!')
    question_count = text.count('？') + text.count('?')
    
    if exclamation_count >= 3:
        score += 1.5
    elif exclamation_count >= 2:
        score += 1.0
    elif exclamation_count >= 1:
        score += 0.5
    
    if question_count >= 2:
        score -= 0.5
    
    repeated_chars = re.findall(r'(.)\1{2,}', text)
    if repeated_chars:
        score += len(repeated_chars) * 0.8
    
    if len(text) < 5:
        score *= 0.8
    elif len(text) > 50:
        score *= 1.1
    
    score = max(1.0, min(10.0, score))
    
    return round(score, 1)

def resolve_ambiguous_words(text, emotion_type, matched_word):
    """解决歧义词问题"""
    has_positive_context = any(word_in_text(ctx, text) for ctx in POSITIVE_CONTEXT)
    has_negative_context = any(word_in_text(ctx, text) for ctx in NEGATIVE_CONTEXT)
    
    if has_positive_context and has_negative_context:
        amb_pos = text.find(matched_word)
        min_dist = float('inf')
        context_type = None
        for ctx in POSITIVE_CONTEXT:
            pos = text.find(ctx)
            if pos != -1:
                dist = abs(pos - amb_pos)
                if dist < min_dist:
                    min_dist = dist
                    context_type = 'positive'
        for ctx in NEGATIVE_CONTEXT:
            pos = text.find(ctx)
            if pos != -1:
                dist = abs(pos - amb_pos)
                if dist < min_dist:
                    min_dist = dist
                    context_type = 'negative'
        return context_type
    
    if has_positive_context:
        return 'positive'
    
    if has_negative_context:
        return 'negative'
    
    if '！' in text or '!' in text:
        return 'positive'
    
    return emotion_type

def analyze_emotion_v4(text):
    """v4.3 增强版情绪分析，修复英文强调词匹配问题"""
    original_text = text
    text = preprocess_text(text)
    
    scores = {emotion: 0 for emotion in EMOTION_DICT.keys()}
    matched_words = {emotion: [] for emotion in EMOTION_DICT.keys()}
    ambiguous_words_found = []
    english_intensifier_used = False
    
    # 第一遍：检测英文强调词，标记它们修饰的词
    intensifier_context = {}  # {强调词: 被修饰的情绪类型}
    for intensifier in ENGLISH_INTENSIFIERS:
        if word_in_text(intensifier, text):
            # 找到强调词的位置
            pattern = r'\b' + re.escape(intensifier) + r'\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                int_pos = match.start()
                # 检查后面是否跟着正面词（在30个字符内）
                following_text = text[int_pos:int_pos + 30]
                for pos_word in POSITIVE_CONTEXT:
                    if word_in_text(pos_word, following_text):
                        intensifier_context[intensifier] = 'positive'
                        english_intensifier_used = True
                        break
                if intensifier not in intensifier_context:
                    intensifier_context[intensifier] = 'negative'
    
    # 第二遍：匹配所有词（排除已标记为强调词的）
    for emotion, data in EMOTION_DICT.items():
        for word, intensity in data['words'].items():
            if word_in_text(word, text):
                # 检查这个词是否是英文强调词，且修饰正面词
                if word in ENGLISH_INTENSIFIERS and word in intensifier_context:
                    if intensifier_context[word] == 'positive':
                        # 跳过，不作为负面词处理
                        continue
                
                count = text.count(word) if not re.search(r'[\u4e00-\u9fff]', word) else text.count(word)
                # 对于英文，使用更精确的计数
                if not re.search(r'[\u4e00-\u9fff]', word):
                    pattern = r'\b' + re.escape(word) + r'\b'
                    count = len(re.findall(pattern, text, re.IGNORECASE))
                
                weight = data['weight']
                scores[emotion] += count * weight * intensity
                matched_words[emotion].extend([word] * count)
                
                if word in data.get('ambiguous', []):
                    ambiguous_words_found.append((word, emotion))
    
    # 为英文强调词添加正面分数（作为强调）
    for intensifier, context in intensifier_context.items():
        if context == 'positive':
            scores['positive'] += 5.0  # 强调词增加正面分数
            matched_words['positive'].append(intensifier + '(强调)')
    
    # 处理歧义词
    for ambiguous_word, original_emotion in ambiguous_words_found:
        resolved_emotion = resolve_ambiguous_words(text, original_emotion, ambiguous_word)
        if resolved_emotion != original_emotion:
            scores[original_emotion] -= 1
            scores[resolved_emotion] += 1.2
            matched_words[original_emotion] = [w for w in matched_words[original_emotion] if w != ambiguous_word]
            matched_words[resolved_emotion].append(ambiguous_word + '(歧义→已修正)')
    
    # 否定检测
    negation = False
    negation_words = ['不', '没', '无', '别', 'not', 'no', 'never', "don't"]
    for neg in negation_words:
        if word_in_text(neg, text):
            negation = True
            break
    
    if negation and scores['positive'] > 0:
        scores['positive'] *= 0.3
        scores['negative'] += 0.5
    
    # 标点分析
    exclamation_count = text.count('！') + text.count('!')
    question_count = text.count('？') + text.count('?')
    
    if exclamation_count > 0:
        scores['positive'] += exclamation_count * 0.2
        scores['negative'] += exclamation_count * 0.1
    
    if question_count > 0:
        scores['question'] += question_count * 0.5
    
    # 重复字符检测
    repeated_chars = re.findall(r'(.)\1{2,}', text)
    if repeated_chars:
        scores['negative'] += len(repeated_chars) * 0.3
        scores['surprise'] += len(repeated_chars) * 0.2
    
    # 应用强度修饰
    intensity_multiplier = detect_intensifier(text)
    for emotion in scores:
        scores[emotion] *= intensity_multiplier
    
    # 确定最终情绪
    total_score = sum(scores.values())
    
    if total_score == 0:
        if len(original_text) < 5:
            final_emotion = '中性'
            confidence = 0.4
        elif exclamation_count > 2:
            final_emotion = '激动'
            confidence = 0.5
        elif question_count > 0:
            final_emotion = '疑问'
            confidence = 0.5
        else:
            final_emotion = '中性'
            confidence = 0.5
    else:
        max_emotion = max(scores, key=scores.get)
        emotion_map = {
            'positive': '正面',
            'negative': '负面',
            'neutral': '中性',
            'surprise': '惊讶',
            'question': '疑问'
        }
        final_emotion = emotion_map.get(max_emotion, '中性')
        confidence = scores[max_emotion] / total_score if total_score > 0 else 0.5
        confidence = min(max(confidence, 0.3), 0.95)
    
    # 计算情感强度评分（1-10）
    emotion_key_map = {
        '正面': 'positive',
        '负面': 'negative',
        '中性': 'neutral',
        '惊讶': 'surprise',
        '疑问': 'question',
        '激动': 'surprise'
    }
    
    emotion_key = emotion_key_map.get(final_emotion, 'neutral')
    base_intensity = get_base_intensity(emotion_key, matched_words.get(emotion_key, []))
    intensity_score = calculate_intensity_score(text, emotion_key, matched_words.get(emotion_key, []), base_intensity)
    
    # 构建结果
    result = {
        'text': original_text,
        'emotion': final_emotion,
        'confidence': round(confidence, 2),
        'intensity_score': intensity_score,
        'scores': {k: round(v, 2) for k, v in scores.items()},
        'matched_words': matched_words,
        'ambiguous_words_resolved': len(ambiguous_words_found) > 0,
        'english_intensifier_detected': english_intensifier_used,
        'details': {
            'intensity_modifier': round(intensity_multiplier, 2),
            'negation_detected': negation,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'repeated_chars': repeated_chars,
            'base_intensity': round(base_intensity, 2)
        }
    }
    
    return result

def print_result(result):
    """美化输出结果"""
    print("\n" + "="*60)
    print("📊 情绪分析结果 v4.3 (修复英文强调词匹配)")
    print("="*60)
    print(f"\n【输入文本】\n{result['text']}\n")
    
    print(f"【情绪类型】{result['emotion']}")
    print(f"【置信度】  {result['confidence']} ({result['confidence']*100:.0f}%)")
    
    # 情感强度评分（1-10分）+ 可视化
    intensity = result['intensity_score']
    bar_length = int(intensity * 2)
    bar = '█' * bar_length + '░' * (20 - bar_length)
    
    if intensity >= 9:
        level = "极强 🔥"
    elif intensity >= 7:
        level = "强烈 💪"
    elif intensity >= 5:
        level = "中等 😐"
    elif intensity >= 3:
        level = "轻微 😕"
    else:
        level = "微弱 🤔"
    
    print(f"\n【情感强度】{intensity}/10 ({level})")
    print(f"            {bar}")
    
    if result.get('ambiguous_words_resolved'):
        print(f"【⚠️  歧义词检测】已自动修正歧义词的情感判断")
    
    if result.get('english_intensifier_detected'):
        print(f"【✨ 英文强调词】检测到强调词（fucking/damn等），已正确处理为正面强调")
    
    print(f"\n【各维度得分】")
    emotion_cn = {
        'positive': '正面',
        'negative': '负面',
        'neutral': '中性',
        'surprise': '惊讶',
        'question': '疑问'
    }
    for emotion, score in result['scores'].items():
        if score > 0:
            bar_length = int(score * 8)
            bar = '█' * min(bar_length, 40)
            print(f"  {emotion_cn.get(emotion, emotion):>6}: {score:>6.2f} {bar}")
    
    print(f"\n【匹配词汇】")
    for emotion, words in result['matched_words'].items():
        if words:
            print(f"  {emotion_cn.get(emotion, emotion)}: {', '.join(set(words))}")
    
    print(f"\n【分析细节】")
    details = result['details']
    print(f"  - 基础强度: {details['base_intensity']}")
    print(f"  - 强度修饰: {details['intensity_modifier']}")
    print(f"  - 否定检测: {'是' if details['negation_detected'] else '否'}")
    print(f"  - 感叹号数: {details['exclamation_count']}")
    print(f"  - 问号数: {details['question_count']}")
    if details['repeated_chars']:
        print(f"  - 重复字符: {', '.join(details['repeated_chars'])}")
    
    print("="*60 + "\n")

def main():
    if len(sys.argv) < 2:
        print("用法: python emotion_analyzer.py <文本>")
        print("示例: python emotion_analyzer.py '今天天气真好！'")
        print("      python emotion_analyzer.py 'fucking happy!'")
        sys.exit(1)
    
    text = ' '.join(sys.argv[1:])
    result = analyze_emotion_v4(text)
    print_result(result)

if __name__ == '__main__':
    main()
