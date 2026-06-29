# -*- coding: utf-8 -*-
"""
记忆管家 V3.0 - TF-IDF 语义搜索模块
P2-3: 纯 Python 实现，零外部依赖，作为关键词匹配的增强层
"""

import re
import math
from collections import Counter


# 中英文分词正则：中文按单字+常用2字词, 英文按单词
_WORD_RE = re.compile(r'[\u4e00-\u9fff]{1,2}|[a-zA-Z0-9]+', re.UNICODE)

# 基础停用词表
_STOPWORDS = frozenset({
    # 中文
    '的', '了', '是', '在', '和', '与', '或', '等', '于', '对',
    '这', '那', '有', '我', '你', '他', '她', '它', '们', '不', '也', '就',
    '一个', '我们', '他们', '这个', '什么', '如何', '怎么', '没有',
    '可以', '需要', '如果', '因为', '所以', '但是', '而且', '已经',
    '或者', '以及', '对于', '关于', '通过', '使用', '进行', '所有',
    '实现', '完成', '开始', '结束', '之后', '之前', '时候', '目前',
    '情况', '问题', '方法', '内容', '文件', '功能', '支持', '提供',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'can', 'shall',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'and', 'or', 'but', 'not', 'no', 'so', 'if', 'as', 'it',
    'this', 'that', 'these', 'those', 'its', 'they', 'them',
})


def _tokenize(text):
    """中英文混合分词，返回词列表"""
    if not text:
        return []
    tokens = []
    for m in _WORD_RE.finditer(text.lower()):
        token = m.group()
        if token not in _STOPWORDS and len(token) > 1:
            tokens.append(token)
    return tokens


def _compute_tf(tokens):
    """计算词频 TF(t, d) = count(t, d) / total_terms(d)"""
    if not tokens:
        return {}
    counter = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counter.items()}


def _compute_idf(documents):
    """计算逆文档频率 IDF(t) = log(N / df(t))

    Args:
        documents: list[list[str]] — 每个文档的分词结果

    Returns:
        dict[str, float]: 词 → IDF 值
    """
    N = len(documents)
    if N == 0:
        return {}

    df = Counter()
    for doc_tokens in documents:
        unique_terms = set(doc_tokens)
        for term in unique_terms:
            df[term] += 1

    return {term: math.log((N + 1) / (count + 1)) + 1.0 for term, count in df.items()}


def build_tfidf_index(documents, doc_ids=None):
    """构建 TF-IDF 索引。

    Args:
        documents: list[str] — 文档文本列表
        doc_ids: list[str] — 可选的文档 ID 列表（默认用索引）

    Returns:
        dict: {
            "idf": {term: idf},
            "doc_vectors": [{term: tfidf}],
            "doc_ids": [str]
        }
    """
    if doc_ids is None:
        doc_ids = [str(i) for i in range(len(documents))]

    tokenized = [_tokenize(doc) for doc in documents]
    idf = _compute_idf(tokenized)

    doc_vectors = []
    for tokens in tokenized:
        tf = _compute_tf(tokens)
        vector = {term: tf.get(term, 0) * idf.get(term, 0) for term in tf}
        doc_vectors.append(vector)

    return {
        "idf": idf,
        "doc_vectors": doc_vectors,
        "doc_ids": doc_ids
    }


def search_tfidf(index, query, top_k=10, min_score=0.01):
    """在 TF-IDF 索引中搜索。

    Args:
        index: build_tfidf_index 的返回值
        query: str — 查询文本
        top_k: int — 返回结果数
        min_score: float — 最低相似度阈值

    Returns:
        list[dict]: [{doc_id, score}] 按分数降序
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    query_tf = _compute_tf(query_tokens)
    idf = index["idf"]
    doc_vectors = index["doc_vectors"]
    doc_ids = index["doc_ids"]

    # 构建查询向量
    query_vector = {
        term: query_tf.get(term, 0) * idf.get(term, 0)
        for term in set(list(query_tf.keys()))
    }

    # 计算余弦相似度
    results = []
    query_norm = math.sqrt(sum(v ** 2 for v in query_vector.values()))
    if query_norm == 0:
        return []

    for i, doc_vec in enumerate(doc_vectors):
        doc_norm = math.sqrt(sum(v ** 2 for v in doc_vec.values()))
        if doc_norm == 0:
            continue

        # 点积
        dot = sum(query_vector.get(term, 0) * doc_vec.get(term, 0) for term in query_vector)
        similarity = dot / (query_norm * doc_norm)

        if similarity >= min_score:
            results.append({
                "doc_id": doc_ids[i],
                "score": round(similarity, 4)
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
