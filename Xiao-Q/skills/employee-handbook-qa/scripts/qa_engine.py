#!/usr/bin/env python3
"""
问答检索引擎 - 基于 TF-IDF 的多策略语义检索，精准定位制度文档段落。

检索策略:
  1. TF-IDF 余弦相似度 — 主策略，计算 query 向量与所有 chunk 向量的相似度
  2. 关键词精确匹配 — 加分策略，query 中的关键词在 chunk 中精确命中加分
  3. 章节标题匹配 — 加分策略，query 中的词命中章节标题加权
  4. 最近导入文档加权 — 时间衰减策略，较新文档小幅加分

用法:
  python qa_engine.py --query "陪产假怎么休？" --top_k 5
  python qa_engine.py --query "加班餐补标准" --top_k 3 --category 福利政策
  python qa_engine.py --query "年假天数计算" --output result.json
"""

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 尝试导入 jieba（临时重定向 stdout，屏蔽初始化打印）
import sys
import io
try:
    _saved_stdout = sys.stdout
    sys.stdout = io.StringIO()
    import jieba
    sys.stdout = _saved_stdout
    jieba.setLogLevel(50)
    HAS_JIEBA = True
except ImportError:
    sys.stdout = _saved_stdout if '_saved_stdout' in dir() else sys.__stdout__
    HAS_JIEBA = False


# ============================================================
# 常量
# ============================================================

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
REGISTRY_FILE = DATA_DIR / "docs_registry.json"
CHUNKS_DIR = DATA_DIR / "chunks"

# 问题类型识别关键词
QUESTION_TYPES = {
    "请假类": ["请假", "休假", "假期", "调休", "病假", "事假", "年假", "婚假", "产假",
              "陪产假", "丧假", "探亲假", "公假", "哺乳假", "育儿假", "护理假"],
    "考勤类": ["考勤", "迟到", "早退", "旷工", "打卡", "签到", "签退", "弹性工作",
              "工时", "出勤", "补卡", "外勤", "加班"],
    "报销类": ["报销", "差旅", "交通", "住宿", "招待", "发票", "单据", "审批",
              "费用", "标准", "限额", "贴票", "报账"],
    "福利类": ["福利", "补贴", "补助", "餐补", "交通补贴", "通讯补贴", "房补",
              "公积金", "社保", "五险一金", "体检", "团建", "节日", "礼品",
              "商业保险", "补充医疗", "年金"],
    "薪酬类": ["工资", "薪资", "薪酬", "发薪", "调薪", "涨薪", "年终奖", "绩效奖",
              "奖金", "提成", "个税", "税前", "税后", "13薪", "14薪"],
    "绩效类": ["绩效", "考核", "KPI", "OKR", "评估", "述职", "晋升", "评级",
              "目标", "360", "面谈"],
    "综合类": [],
}

# 停用词
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "被", "把", "让", "对", "从", "但", "而", "且", "与", "或",
    "可以", "需要", "应该", "必须", "可能", "已经", "将", "等", "其",
    "为", "以", "之", "及", "向", "由", "于", "中", "并", "如",
    "规定", "按照", "根据", "相关", "以下", "以上", "包括", "具体",
    "进行", "情况", "单位", "公司", "部门", "员工", "工作",
    "怎么", "如何", "什么", "多少", "哪", "吗", "呢", "吧", "啊",
    "请问", "问一下", "想知道", "了解",
}

# 同义词/近义词映射（增强召回）
SYNONYMS = {
    "年假": ["年休假", "带薪年假", "带薪年休假", "有薪年假"],
    "陪产假": ["陪护假", "护理假", "配偶陪产假", "陪产"],
    "产假": ["生育假", "生育产假", "法定产假"],
    "病假": ["病休", "病事假", "医疗期"],
    "加班": ["延时工作", "超时工作", "加班加点"],
    "餐补": ["伙食补贴", "餐费补贴", "餐饮补贴", "工作餐"],
    "公积金": ["住房公积金", "公积金缴存"],
    "社保": ["社会保险", "五险"],
    "报销": ["报账", "费用报销", "报销流程"],
    "辞职": ["离职", "解除劳动合同", "主动离职"],
    "开除": ["辞退", "解雇", "解除"],
    "调薪": ["涨工资", "涨薪", "薪资调整", "薪酬调整"],
    "年终奖": ["年度奖金", "年终绩效", "十三薪"],
}

# 扩展查询词：将query词映射到同义词
def expand_query_terms(tokens: list[str], query_str: str = "") -> list[str]:
    """扩展查询词的同义词，并支持子串匹配"""
    expanded = list(tokens)

    # 1. 精确 token 匹配
    for token in tokens:
        if token in SYNONYMS:
            expanded.extend(SYNONYMS[token])

    # 2. 子串匹配：原始查询中包含同义词键名即扩展
    if query_str:
        for key in SYNONYMS:
            if key in query_str and key not in expanded:
                expanded.append(key)
                expanded.extend(SYNONYMS[key])

    # 3. 反向映射：token 命中同义词 value，也加入 key
    all_terms = list(expanded)  # 快照，避免遍历时修改
    for token in all_terms:
        for key, values in SYNONYMS.items():
            if token in values and key not in expanded:
                expanded.append(key)

    return list(set(expanded))


# ============================================================
# 分词
# ============================================================

def tokenize(text: str) -> list[str]:
    """中文分词并去停用词"""
    if HAS_JIEBA:
        words = jieba.lcut(text)
    else:
        words = re.split(r'[，。！？；、\s\n（）()《》""\'\'【】：:]+', text)
        words = [w for w in words if len(w) >= 2]
    return [w for w in words if w not in STOP_WORDS and len(w) >= 2]


# ============================================================
# 加载索引
# ============================================================

def load_all_indexes(category_filter: str = "") -> list[dict]:
    """加载所有（或指定分类的）文档索引"""
    registry = _load_json(REGISTRY_FILE)
    if not registry:
        return []

    indexes = []
    for doc_id, doc_entry in registry.get("documents", {}).items():
        if category_filter and doc_entry["category"] != category_filter:
            continue
        index_file = doc_entry.get("index_file", "")
        if index_file and os.path.exists(index_file):
            index = _load_json(index_file)
            if index:
                # 附加文档元数据
                index["doc_id"] = doc_id
                index["doc_name"] = doc_entry["name"]
                index["doc_category"] = doc_entry["category"]
                index["imported_at"] = doc_entry.get("imported_at", "")
                index["file_path"] = doc_entry.get("file_path", "")
                indexes.append(index)
    return indexes


def _load_json(file_path):
    """安全加载 JSON 文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[警告] 无法加载 {file_path}: {e}", file=sys.stderr)
    return None


# ============================================================
# 核心检索
# ============================================================

def search(query: str, top_k: int = 5, category_filter: str = "",
           min_score: float = 0.05) -> list[dict]:
    """
    多策略检索主函数

    返回 Top-K 结果，每个结果包含:
      - chunk_id, text, section, doc_name, doc_category
      - score: 综合相关度分数 (0-1)
      - score_breakdown: 各项得分明细
      - confidence: 置信度 (high/medium/low)
    """
    indexes = load_all_indexes(category_filter)
    if not indexes:
        return []

    # 分词 & 扩展同义词（传入原始查询字符串以支持子串匹配）
    query_tokens = tokenize(query)
    expanded_tokens = expand_query_terms(query_tokens, query)

    if not expanded_tokens:
        return []

    # 识别问题类型
    question_type = identify_question_type(query)

    all_results = []

    for index_data in indexes:
        chunks = index_data.get("chunks", [])
        vectors = index_data.get("vectors", [])
        inverted_index = index_data.get("inverted_index", {})
        df = index_data.get("df", {})
        N = index_data.get("N", len(chunks))

        doc_id = index_data.get("doc_id", "")
        doc_name = index_data.get("doc_name", "")
        doc_category = index_data.get("doc_category", "")
        imported_at = index_data.get("imported_at", "")

        if not chunks or not vectors:
            continue

        # 计算 query 的 TF-IDF 向量
        query_vec = _build_query_vector(expanded_tokens, df, N)

        # 对每个 chunk 打分
        for ci, chunk in enumerate(chunks):
            if ci >= len(vectors):
                continue

            score, breakdown = _score_chunk(
                query_vec, vectors[ci],
                query_tokens, expanded_tokens,
                chunk, inverted_index,
                doc_category, question_type,
                imported_at
            )

            if score >= min_score:
                all_results.append({
                    "chunk_id": chunk.get("chunk_id", ""),
                    "text": chunk.get("text", ""),
                    "section": chunk.get("section", ""),
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "doc_category": doc_category,
                    "score": round(score, 4),
                    "score_breakdown": breakdown,
                    "confidence": _score_to_confidence(score),
                })

    # 排序 & 去重（基于 chunk_id）
    seen_ids = set()
    unique_results = []
    for r in sorted(all_results, key=lambda x: x["score"], reverse=True):
        cid = r["chunk_id"]
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique_results.append(r)

    return unique_results[:top_k]


def _build_query_vector(tokens: list[str], df: dict, N: int) -> dict:
    """构建 query 的 TF-IDF 向量"""
    tf = defaultdict(int)
    for t in tokens:
        tf[t] += 1
    max_tf = max(tf.values()) if tf else 1
    vec = {}
    for term, count in tf.items():
        idf = math.log((N + 1) / (df.get(term, 0) + 1)) + 1
        vec[term] = (count / max_tf) * idf
    return vec


def _score_chunk(query_vec: dict, chunk_vec: dict,
                 query_tokens: list[str], expanded_tokens: list[str],
                 chunk: dict, inverted_index: dict,
                 doc_category: str, question_type: str,
                 imported_at: str) -> tuple[float, dict]:
    """
    综合打分（多策略融合）

    策略权重:
      - TF-IDF 余弦相似度: 60%
      - 关键词精确命中: 20%
      - 章节标题匹配: 10%
      - 时间衰减加权: 5%
      - 问题类型与文档分类匹配: 5%
    """
    breakdown = {}
    chunk_text = chunk.get("text", "").lower()
    chunk_section = chunk.get("section", "").lower()

    # 1. TF-IDF 余弦相似度 (60%)
    cosine_sim = _cosine_similarity(query_vec, chunk_vec)
    tfidf_score = min(cosine_sim, 1.0)
    breakdown["tfidf"] = round(tfidf_score, 4)

    # 2. 关键词精确命中 (20%)
    hit_count = 0
    for token in set(query_tokens):
        if token in chunk_text:
            hit_count += 1
    keyword_score = hit_count / max(len(set(query_tokens)), 1)
    breakdown["keyword"] = round(keyword_score, 4)

    # 3. 章节标题匹配 (10%)
    section_score = 0.0
    for token in set(query_tokens):
        if token in chunk_section:
            section_score += 0.5
    section_score = min(section_score, 1.0)
    breakdown["section"] = round(section_score, 4)

    # 4. 时间衰减加权 (5%) — 最近导入的文档略微加分
    time_score = 0.5  # default
    if imported_at:
        try:
            import_time = datetime.fromisoformat(imported_at)
            days_ago = (datetime.now() - import_time).days
            time_score = 1.0 / (1.0 + days_ago / 365)  # 一年衰减到 0.5
        except (ValueError, TypeError):
            pass
    breakdown["time"] = round(time_score, 4)

    # 5. 问题类型与文档分类匹配 (5%)
    category_map = {
        "请假类": ["员工手册", "考勤制度"],
        "考勤类": ["考勤制度", "员工手册"],
        "报销类": ["报销制度", "员工手册"],
        "福利类": ["福利政策", "员工手册"],
        "薪酬类": ["薪酬制度", "员工手册"],
        "绩效类": ["绩效考核", "员工手册"],
    }
    type_score = 0.5
    if question_type in category_map and doc_category in category_map[question_type]:
        type_score = 1.0
    elif doc_category == "员工手册":
        type_score = 0.7  # 员工手册覆盖面广
    breakdown["type_match"] = round(type_score, 4)

    # 综合得分
    total = (
        tfidf_score * 0.60 +
        keyword_score * 0.20 +
        section_score * 0.10 +
        time_score * 0.05 +
        type_score * 0.05
    )

    return total, breakdown


def _cosine_similarity(vec1: dict, vec2: dict) -> float:
    """计算两个稀疏向量的余弦相似度"""
    if not vec1 or not vec2:
        return 0.0

    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0

    for k, v in vec1.items():
        norm1 += v * v
        if k in vec2:
            dot += v * vec2[k]
    for v in vec2.values():
        norm2 += v * v

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


def _score_to_confidence(score: float) -> str:
    """分数转置信度标签"""
    if score >= 0.4:
        return "high"
    elif score >= 0.15:
        return "medium"
    return "low"


# ============================================================
# 问题类型识别
# ============================================================

def identify_question_type(query: str) -> str:
    """根据查询内容自动识别问题类型"""
    scores = defaultdict(int)
    for qtype, keywords in QUESTION_TYPES.items():
        if qtype == "综合类":
            continue
        for kw in keywords:
            if kw in query:
                scores[qtype] += 1

    if not scores:
        return "综合类"

    return max(scores, key=scores.get)


# ============================================================
# 格式化输出
# ============================================================

def format_results(results: list[dict], query: str) -> str:
    """将检索结果格式化为可读的文本输出"""
    if not results:
        return f"📭 未找到与「{query}」相关的制度内容。\n建议：尝试更换关键词，或联系 HRBP 获取帮助。"

    question_type = identify_question_type(query)
    output = f"🔍 问题类型: {question_type} | 查询: 「{query}」\n"
    output += f"📊 找到 {len(results)} 条相关制度内容:\n"
    output += "=" * 70 + "\n\n"

    for i, r in enumerate(results, 1):
        conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        emoji = conf_emoji.get(r["confidence"], "⚪")

        output += f"【结果 {i}】{emoji} 置信度: {r['confidence']} | 得分: {r['score']}\n"
        output += f"📄 来源: 《{r['doc_name']}》" + (f" | {r['section']}" if r["section"] else "") + "\n"
        output += f"📂 分类: {r['doc_category']}\n"
        output += f"📝 内容:\n{r['text'][:500]}{'...' if len(r['text']) > 500 else ''}\n"
        output += "-" * 50 + "\n\n"

    return output


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="员工手册制度问答检索引擎")
    parser.add_argument("--query", "-q", required=True, help="员工提问的自然语言查询")
    parser.add_argument("--top_k", "-k", type=int, default=5, help="返回 Top-K 个结果 (默认5)")
    parser.add_argument("--category", "-c", default="", help="限定检索的文档分类")
    parser.add_argument("--min_score", "-m", type=float, default=0.05, help="最低相关度阈值 (默认0.05)")
    parser.add_argument("--output", "-o", default="", help="输出结果到 JSON 文件")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json",
                        help="输出格式: json (默认) 或 text")

    args = parser.parse_args()

    # 检查是否有已导入文档
    if not REGISTRY_FILE.exists():
        result = {"error": "no_documents", "message": "尚未导入任何制度文档，请先使用 doc_importer.py 导入文档"}
        print(f"[JSON_RESULT] {json.dumps(result, ensure_ascii=False)}")
        return

    # 执行检索
    results = search(
        query=args.query,
        top_k=args.top_k,
        category_filter=args.category,
        min_score=args.min_score,
    )

    # 构建输出
    question_type = identify_question_type(args.query)
    output_data = {
        "query": args.query,
        "question_type": question_type,
        "top_k": args.top_k,
        "results_count": len(results),
        "results": results,
        "searched_at": datetime.now().isoformat(),
    }

    # 格式化输出
    if args.format == "text":
        print(format_results(results, args.query))
        # text 模式末尾附加 JSON 供 AI 解析
        print(f"\n[JSON_RESULT] {json.dumps(output_data, ensure_ascii=False)}")
    else:
        # json 模式只输出纯 JSON
        print(json.dumps(output_data, ensure_ascii=False))

    # 保存到文件
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n📁 结果已保存到: {args.output}")

    # 简短摘要
    if results:
        top_score = results[0]["score"]
        top_conf = results[0]["confidence"]
        print(f"\n💡 最佳匹配: {results[0]['doc_name']} — {results[0]['section']} (得分: {top_score}, 置信度: {top_conf})")
    else:
        print(f"\n📭 未找到相关内容，建议联系 HRBP")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    main()
