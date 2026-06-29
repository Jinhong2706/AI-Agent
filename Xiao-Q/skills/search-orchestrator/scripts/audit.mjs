#!/usr/bin/env node
/**
 * audit.mjs — Universal Search 搜索后审计 v5.2
 *
 * 输入搜索结果 + 原始 query → 输出审计报告：
 *   - 三层回链检查
 *   - 7 信号自动检测
 *   - 收敛判断
 *   - 信息密度评分
 *   - 锚点相关率
 *
 * 用法:
 *   echo '{...}' | node scripts/audit.mjs
 *   node scripts/audit.mjs --file results.json
 *   node scripts/audit.mjs --query "原始问题" --anchor "词1,词2" --stdin
 */

import { readFileSync } from 'fs';
import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── 解析参数 ──────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { file: '', query: '', anchor: '', stdin: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--file' || args[i] === '-f') opts.file = args[++i] || '';
    else if (args[i] === '--query' || args[i] === '-q') opts.query = args[++i] || '';
    else if (args[i] === '--anchor' || args[i] === '-a') opts.anchor = args[++i] || '';
    else if (args[i] === '--stdin') opts.stdin = true;
  }
  return opts;
}

// ─── 加载输入 ──────────────────────────────────────────────
function loadInput(opts) {
  let raw;
  if (opts.file) {
    raw = readFileSync(opts.file, 'utf-8');
  } else {
    raw = readFileSync(0, 'utf-8');
  }
  const data = JSON.parse(raw);

  // 允许命令行补充 query 和 anchor
  if (opts.query && !data.query) data.query = opts.query;
  if (opts.anchor) data.anchor_words = opts.anchor.split(',').map(s => s.trim());

  return data;
}

// ─── 输入校验 ──────────────────────────────────────────────
function validateInput(data) {
  const errors = [];
  if (!data.query) errors.push('缺少 query');
  if (!data.anchor_words || !Array.isArray(data.anchor_words) || data.anchor_words.length === 0) {
    errors.push('缺少 anchor_words (数组)');
  }
  if (!data.results || !Array.isArray(data.results)) {
    errors.push('缺少 results (数组)');
  }
  if (errors.length > 0) {
    console.error('输入校验失败:', errors.join('; '));
    console.error('预期格式: {"query":"...", "anchor_words":["...","..."], "results":[{"title":"...","content":"..."}], "round":1, "complexity":"L1"}');
    process.exit(1);
  }
}

// ─── 工具函数 ──────────────────────────────────────────────
function normalizeText(text) {
  return (text || '').toLowerCase().trim();
}

function countOccurrences(text, word) {
  const normalized = normalizeText(text);
  const target = normalizeText(word);
  let count = 0;
  let pos = 0;
  while ((pos = normalized.indexOf(target, pos)) !== -1) {
    count++;
    pos += target.length;
  }
  return count;
}

function anyAnchorPresent(text, anchorWords) {
  const t = normalizeText(text);
  return anchorWords.some(a => t.includes(normalizeText(a)));
}

function allAnchorsPresent(text, anchorWords) {
  const t = normalizeText(text);
  return anchorWords.every(a => t.includes(normalizeText(a)));
}

function anchorDensity(text, anchorWords) {
  const t = normalizeText(text);
  let total = 0;
  for (const a of anchorWords) {
    total += countOccurrences(t, a);
  }
  return total;
}

// ─── 三层回链检查 ──────────────────────────────────────────
function backlinkTest(result, anchorWords, query) {
  const title = normalizeText(result.title || '');
  const content = normalizeText(result.content || result.snippet || '');
  const combined = title + ' ' + content;

  // 层1: 锚点在位 — query 中是否原样包含所有锚点词？
  const layer1_present = anchorWords.map(a => ({
    word: a,
    in_content: countOccurrences(combined, a) > 0,
    count: countOccurrences(combined, a),
  }));
  const layer1_pass = layer1_present.some(l => l.in_content);

  // 层2: 去锚测试 — 原问题删掉锚点词后，剩余关键词是否在结果中有独立覆盖？
  // 如果去锚后的关键词在结果中出现 → 结果有独立语义 → 可能主题漂移
  let remainingQuery = query;
  for (const a of anchorWords) {
    remainingQuery = remainingQuery.replace(new RegExp(a, 'gi'), ' ');
  }
  const remainingKeywords = remainingQuery
    .replace(/[^\w\u4e00-\u9fff\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1);
  const independentKeywords = remainingKeywords.filter(kw =>
    countOccurrences(combined, kw) > 0
  );
  // 如果去锚后仍有 ≥2 个独立关键词命中 → 有独立语义（可能漂移）
  const layer2_risk = independentKeywords.length >= 2;

  // 层3: 回链测试 — 这个结果能直接回答原始问题的哪个部分？
  // 锚点词密度 ≥2 且内容长度 ≥50 → 有实质关联
  const density = anchorDensity(combined, anchorWords);
  const hasSubstance = combined.length > 50 && density >= 1;
  const layer3_pass = hasSubstance;

  const layerScores = [layer1_pass, !layer2_risk, layer3_pass];
  const passed = layerScores.filter(Boolean).length >= 2;
  const score = (layer1_pass ? 1 : 0) + (layer2_risk ? 0 : 1) + (layer3_pass ? 1 : 0);

  return {
    passed,
    layer1: { pass: layer1_pass, details: layer1_present },
    layer2: { risk: layer2_risk, independent_keywords: independentKeywords },
    layer3: { pass: layer3_pass, anchor_density: density, has_substance: hasSubstance },
    verdict: passed ? (layer2_risk ? '✅ 相关(降权提示:去锚后仍有独立语义)' : '✅ 相关') : `❌ 不相关(${score}/3)`,
    score,
  };
}

// ─── 信号检测 ──────────────────────────────────────────────
function detectSignals(query, results, anchorWords, round) {
  const ql = normalizeText(query);
  const signals = [];

  // ① 时效信号
  const timeKeywords = ['最新', '新闻', '今天', '突发', '刚刚', '热点', '近日', '本周',
    'latest', 'news', 'today', 'breaking', 'recent', 'this week'];
  if (timeKeywords.some(k => ql.includes(k))) {
    signals.push({ id: 1, name: '时效', active: true, detail: 'query 含时效关键词' });
  }

  // ② 追问信号
  const inquiryKeywords = ['为什么', '原因', '分析', '对比', '比较', '怎么样', '具体',
    '如何', '影响', '细节', 'why', 'reason', 'analysis', 'compare',
    'how', 'impact', 'detail'];
  if (inquiryKeywords.some(k => ql.includes(k))) {
    signals.push({ id: 2, name: '追问', active: true, detail: 'query 含追问/分析关键词' });
  }

  // ③ 空壳实体 — 短内容且不含锚点词才算"空壳"
  const shortResults = results.filter(r => {
    const c = normalizeText(r.content || r.snippet || '');
    if (c.length >= 50) return false;                // ≥50字符 = 不算空壳
    return !anyAnchorPresent(c, anchorWords);         // 含锚点词的短文仍有价值
  });
  if (shortResults.length > 0 && results.length > 0) {
    const ratio = shortResults.length / results.length;
    if (ratio > 0.3) {
      signals.push({
        id: 3, name: '空壳实体', active: true,
        detail: `${shortResults.length}/${results.length} 结果内容短且不含锚点词 (<50字符)`,
      });
    }
  }

  // ④ 单源数据 — 只统计回链通过结果中的关键数字（年份/百分比/金额），≥5个才触发
  const relevantNumberPattern = /\b(\d{4}年?|\d{2,}(?:\.\d+)?%|\d{2,}(?:\.\d+)?(?:万|亿|元|k|m|公里|km))\b/gi;
  const numberSourceMap = new Map();
  for (const r of results) {
    // 只统计通过回链测试的结果（确保数字与原始问题相关）
    const combined = (r.title || '') + ' ' + (r.content || r.snippet || '');
    if (!anyAnchorPresent(combined, anchorWords)) continue;
    const matches = combined.matchAll(relevantNumberPattern);
    for (const m of matches) {
      const num = m[0].toLowerCase();
      if (!numberSourceMap.has(num)) numberSourceMap.set(num, new Set());
      numberSourceMap.get(num).add(r.url || r.source || r.engine || 'unknown');
    }
  }
  const singleSourceNums = [...numberSourceMap.entries()]
    .filter(([, sources]) => sources.size === 1)
    .map(([num]) => num);
  if (singleSourceNums.length >= 5) {
    signals.push({
      id: 4, name: '单源数据', active: true,
      detail: `${singleSourceNums.length} 个关键数值仅单一来源: ${singleSourceNums.slice(0, 5).join(', ')}`,
    });
  }

  // ⑤ 事实冲突 — 暂留接口（需 NLP，人工检查）
  // 不自动标记为 active，返回提示

  // ⑥ 强要求信号
  const forceKeywords = ['全面', '深入', '详细', '研究报告', '透彻', '全方位',
    'comprehensive', 'in-depth', 'detailed', 'thorough', 'full report'];
  if (forceKeywords.some(k => ql.includes(k))) {
    signals.push({ id: 6, name: '强要求', active: true, detail: '用户明确要求深度分析' });
  }

  // ⑦ 信息不足
  const relevantResults = results.filter(r => r.relevance_score !== 0); // 已过滤非相关
  const effectiveCount = relevantResults.length > 0 ? relevantResults.length : results.length;
  if (effectiveCount < 3) {
    signals.push({
      id: 7, name: '信息不足', active: true,
      detail: `独立源仅 ${effectiveCount} 个 (需 ≥3)`,
    });
  }

  return signals;
}

// ─── 收敛判断 ──────────────────────────────────────────────
function checkConvergence(data, backlinkResults, activeSignals) {
  const results = data.results || [];
  const previous = data.previous_rounds || {};
  const complexity = data.complexity || 'L1';

  const passedCount = backlinkResults.filter(r => r.passed).length;
  const totalResults = backlinkResults.length;
  const anchorRelevanceRate = totalResults > 0 ? (passedCount / totalResults * 100) : 0;

  // 独立源计数（只统计通过回链测试的）
  const independentSources = new Set(
    backlinkResults
      .filter(r => r.passed)
      .map(r => r.url || r.source || r.engine)
      .filter(Boolean)
  );

  const checks = {
    core_conclusions_2sources: {
      pass: independentSources.size >= 2,
      detail: `通过回链的独立源: ${independentSources.size} 个 (需 ≥2)`,
    },
    independent_sources_3: {
      pass: independentSources.size >= 3,
      detail: `独立源总数: ${independentSources.size} 个 (需 ≥3)`,
    },
    signals_cleared: {
      // 排除信号④（单源数据是信息提示，不阻塞收敛）
      pass: activeSignals.filter(s => s.active && s.id !== 4).length === 0,
      detail: `激活信号(阻塞收敛): ${activeSignals.filter(s => s.active && s.id !== 4).map(s => s.name).join(', ') || '无'}`,
    },
    anchor_relevance_adequate: {
      pass: anchorRelevanceRate >= 80,
      detail: `锚点相关率: ${anchorRelevanceRate.toFixed(1)}% (需 ≥80%)`,
    },
    no_expansion: {
      pass: (previous.new_relevant_sources || 0) < 2,
      detail: '上一轮无显著新增锚点相关源',
    },
  };

  const allPassed = Object.values(checks).every(c => c.pass);
  const maxDepth = data.max_depth || 5;
  const round = data.round || 1;
  const forceStop = round >= maxDepth;

  return {
    converged: allPassed || forceStop,
    reason: allPassed ? '所有条件满足' : (forceStop ? `已达到最大轮数 ${maxDepth}` : '未收敛'),
    checks,
    force_stop: forceStop,
    independent_sources: independentSources.size,
    anchor_relevance_rate: anchorRelevanceRate,
  };
}

// ─── 信息密度评分 ──────────────────────────────────────────
function scoreInformationDensity(backlinkResults, results) {
  const passed = backlinkResults.filter(r => r.passed);
  const total = backlinkResults.length;

  if (total === 0) return { rating: '空', score: 1, note: '无可用结果' };

  // 计算平均锚点密度
  const avgDensity = passed.reduce((sum, r) => sum + r.layer3.anchor_density, 0) / Math.max(passed.length, 1);

  // 通过率
  const passRate = total > 0 ? passed.length / total : 0;

  // 内容平均长度（作为信息量代理）
  const avgLength = results.reduce((sum, r) => {
    const c = (r.content || r.snippet || '').length;
    return sum + c;
  }, 0) / Math.max(total, 1);

  let rating, score;
  if (passRate >= 0.9 && avgDensity >= 3 && avgLength > 200) {
    rating = '高';
    score = 5;
  } else if (passRate >= 0.7 && avgDensity >= 2 && avgLength > 100) {
    rating = '中高';
    score = 4;
  } else if (passRate >= 0.5 && avgDensity >= 1) {
    rating = '中';
    score = 3;
  } else if (passRate >= 0.3) {
    rating = '中低';
    score = 2;
  } else {
    rating = '低';
    score = 1;
  }

  return {
    rating,
    score,
    pass_rate: (passRate * 100).toFixed(1) + '%',
    avg_anchor_density: avgDensity.toFixed(2),
    avg_content_length: Math.round(avgLength),
    note: rating === '低' ? '建议增加搜索轮次或更换 query 策略' : null,
  };
}

// ─── 主逻辑 ────────────────────────────────────────────────
function main() {
  const opts = parseArgs();
  const data = loadInput(opts);
  validateInput(data);

  const { query, anchor_words: anchorWords, results = [], round = 1, complexity = 'L1' } = data;

  // ── 逐条回链检查 ──
  const backlinkResults = results.map((r, i) => ({
    index: i,
    title: r.title || '(无标题)',
    url: r.url || r.link || r.source || '',
    engine: r.engine || r.source || 'unknown',
    ...backlinkTest(r, anchorWords, query),
  }));

  const passedResults = backlinkResults.filter(r => r.passed);
  const failedResults = backlinkResults.filter(r => !r.passed);

  // ── 信号检测 ──
  const signals = detectSignals(query, results, anchorWords, round);
  const activeSignals = signals.filter(s => s.active);

  // ── 收敛判断 ──
  const convergence = checkConvergence(data, backlinkResults, activeSignals);

  // ── 信息密度 ──
  const density = scoreInformationDensity(backlinkResults, results);

  // ── 低相关标记 ──
  const lowRelevance = failedResults.filter(r => r.score <= 1).map(r => ({
    index: r.index,
    title: r.title,
    reason: r.verdict,
  }));

  // ── 组装输出 ──
  const output = {
    version: '5.2',
    audited_at: new Date().toISOString(),
    summary: {
      total_results: results.length,
      backlink_passed: passedResults.length,
      backlink_failed: failedResults.length,
      anchor_relevance_rate: convergence.anchor_relevance_rate.toFixed(1) + '%',
      active_signals: activeSignals.length,
      converged: convergence.converged,
      convergence_reason: convergence.reason,
      information_density: density,
    },
    backlink_details: {
      passed: passedResults.map(r => ({
        title: r.title.substring(0, 80),
        url: r.url,
        engine: r.engine,
        score: r.score,
        anchor_density: r.layer3.anchor_density,
      })),
      failed: failedResults.map(r => ({
        title: r.title.substring(0, 80),
        url: r.url || '(无)',
        engine: r.engine,
        verdict: r.verdict,
        layer1_pass: r.layer1.pass,
        layer2_risk: r.layer2.risk,
        layer3_pass: r.layer3.pass,
      })),
    },
    signals,
    convergence,
    low_relevance: lowRelevance,
    recommendations: [],
  };

  // ── 建议 ──
  if (!convergence.converged && !convergence.force_stop) {
    output.recommendations.push({
      action: 'deep_round',
      detail: `进入第 ${round + 1} 轮深度搜索`,
      reason: convergence.reason,
      suggested_directions: activeSignals.map(s => s.detail).filter(Boolean),
    });
  }
  if (activeSignals.some(s => s.id === 7)) {
    output.recommendations.push({
      action: 'broaden_search',
      detail: '独立源不足，建议使用更多搜索引擎或扩展 query',
    });
  }
  if (density.score <= 2) {
    output.recommendations.push({
      action: 'refine_query',
      detail: '信息密度低，建议更聚焦的搜索词',
    });
  }

  console.log(JSON.stringify(output, null, 2));
}

main();
