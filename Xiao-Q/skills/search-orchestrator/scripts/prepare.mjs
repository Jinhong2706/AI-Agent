#!/usr/bin/env node
/**
 * prepare.mjs — Universal Search 搜索前准备 v5.2.1
 *
 * 输入原始 query → 输出结构化搜索参数：
 *   - 锚点词提取
 *   - 复杂度分级 (L0/L1/L2)
 *   - 意图路由
 *   - 每个工具的分流 query（动态，面向所有 discovered 工具）
 *   - GATE checklist
 *
 * 用法:
 *   echo "中日军事冲突风险分析" | node scripts/prepare.mjs
 *   node scripts/prepare.mjs --query "比亚迪 2026 新车 发布"
 */

import { readFileSync } from 'fs';
import { execSync } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

// ── 模块级 discover 缓存（prepare 全生命周期只跑一次） ──────
let _discoverCache = null;
function getDiscoverOutput() {
  if (_discoverCache !== null) return _discoverCache;
  try {
    const raw = execSync(`node "${resolve(SKILL_DIR, 'scripts/discover.js')}" --cache`, {
      encoding: 'utf-8', timeout: 10000, shell: '/bin/bash',
      stdio: 'pipe'
    });
    _discoverCache = JSON.parse(raw);
  } catch {
    _discoverCache = null;
  }
  return _discoverCache;
}

// ─── 解析参数 ──────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { query: '', lang: 'auto' };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--query' || args[i] === '-q') opts.query = args[++i] || '';
    else if (args[i] === '--lang') opts.lang = args[++i] || 'auto';
    else if (!args[i].startsWith('-')) opts.query = args[i];
  }
  if (!opts.query && !process.stdin.isTTY) {
    opts.query = readFileSync(0, 'utf-8').trim();
  }
  return opts;
}

// ─── 语言检测 ──────────────────────────────────────────────
function detectLang(query) {
  let cjk = 0, ascii = 0;
  for (const ch of query) {
    const code = ch.codePointAt(0);
    if (code >= 0x4E00 && code <= 0x9FFF) cjk++;
    else if (code >= 0x3400 && code <= 0x4DBF) cjk++;
    else if (code >= 0xF900 && code <= 0xFAFF) cjk++;
    else if (code < 128) ascii++;
  }
  if (cjk > ascii) return 'zh';
  if (cjk > 0 && ascii > cjk) return 'mixed';
  return 'en';
}

// ─── 中文分隔词 ────────────────────────────────────────────
const CN_DELIMITERS = [
  '什么', '怎么', '如何', '为什么', '哪些', '哪个', '多少',
  '怎样', '什么样', '谁', '哪儿', '哪里', '是否', '有没有',
  '的', '了', '是', '在', '和', '与', '或', '及', '以及',
  '而且', '但', '而', '因此', '所以', '因为', '如果', '虽然',
  '吗', '呢', '吧', '啊', '嘛', '哦', '嗯', '呀', '啦', '哇',
  '这', '那', '哪', '可以', '能够', '应该', '需要', '必须',
  '希望', '想要', '一个', '一种', '一些', '这个', '那个',
  '每个', '所有', '已经', '正在', '将要', '曾经', '一直',
  '总是', '非常', '比较', '稍微', '特别', '尤其',
  '请问', '帮我', '帮忙', '一下', '一点', '谢谢', '麻烦',
  '发布', '推出', '上市', '发售', '正式', '宣布', '公布',
  '介绍', '展示', '亮相', '首秀',
  '全部', '所有', '各种', '都有', '还有', '包括',
  '进行', '使用', '需要', '应该', '可以',
  '最近', '最新', '近期', '近日', '刚刚', '今天',
  '哪些', '哪种',
  '是否', '有没有', '是不是', '会不会', '能不能',
];
const CN_DELIMITER_SET = new Set(CN_DELIMITERS);
const CN_BOUNDARY_RE = /([年月日时市省区县镇村号版款型代版本类系])/g;

function cnSegment(text) {
  const mixedParts = [];
  const cleaned = text.replace(/[A-Za-z][A-Za-z0-9._\-+]*/g, (match) => {
    mixedParts.push(match);
    return ' ';
  });

  let result = cleaned.replace(/[，,。；;：:！!？?\s\t\n\r]+/g, '|');

  const sorted = [...CN_DELIMITERS].sort((a, b) => b.length - a.length);
  for (const d of sorted) {
    result = result.split(new RegExp(d.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))).join('|');
  }

  const segments = result.split('|')
    .map(s => s.trim())
    .filter(s => s.length >= 1 && !/^[|]+$/.test(s));

  const refinedSegments = [];
  for (const seg of segments) {
    const subSegs = seg.split(/(?<=\d)(?=[\u4e00-\u9fff])|(?<=[\u4e00-\u9fff])(?=\d)|(?<=[a-zA-Z])(?=[\u4e00-\u9fff])|(?<=[\u4e00-\u9fff])(?=[a-zA-Z])/);
    refinedSegments.push(...subSegs.filter(s => s.length >= 1));
  }

  const words = [];
  for (const seg of refinedSegments) {
    if (seg.length <= 5) {
      words.push(seg);
    } else {
      const parts = seg.split(CN_BOUNDARY_RE).filter(Boolean);
      if (parts.length > 1) {
        for (let i = 0; i < parts.length; i++) {
          const p = parts[i];
          if (/^[年月日时市省区县镇村号版款型代版本类系]$/.test(p) && i > 0) continue;
          let chunk = p;
          if (i + 1 < parts.length && /^[年月日时市省区县镇村号版款型代版本类系]$/.test(parts[i + 1])) {
            chunk += parts[i + 1];
            i++;
          }
          if (chunk.length >= 2 && !CN_DELIMITER_SET.has(chunk)) words.push(chunk);
        }
      } else {
        if (seg.length <= 20) words.push(seg);
      }
    }
  }

  words.push(...mixedParts);
  return [...new Set(words.filter(w => w.length >= 1))];
}

// ─── 锚点词提取 ────────────────────────────────────────────
const CN_QUESTION_WORDS = new Set([
  '什么', '怎么', '如何', '为什么', '哪些', '哪个', '多少',
  '怎样', '什么样', '谁', '哪儿', '哪里', '是否', '有没有',
]);

const EN_QUESTION_WORDS = new Set([
  'what', 'how', 'why', 'which', 'who', 'when', 'where',
  'whom', 'whose', 'whether', 'does', 'did', 'do', 'is',
  'are', 'was', 'were', 'can', 'could', 'will', 'would',
  'should', 'shall', 'may', 'might', 'tell', 'find',
  'search', 'look', 'check', 'please',
]);

const EN_STOP_WORDS = new Set([
  'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of',
  'with', 'from', 'by', 'as', 'into', 'than', 'about', 'over',
  'this', 'that', 'these', 'those', 'it', 'its', 'and', 'or',
  'but', 'not', 'no', 'yes', 'so', 'if', 'then', 'also',
]);

function extractAnchorWords(query, lang) {
  if (lang === 'zh' || lang === 'mixed') return extractAnchorWordsCN(query);
  return extractAnchorWordsEN(query);
}

function extractAnchorWordsCN(query) {
  const properNouns = [];
  const properPatterns = [
    /[A-Za-z][A-Za-z0-9.\-+]{1,}/g,
    /[A-Za-z]+[\u4e00-\u9fff]+/g,
    /[\u4e00-\u9fff]+[A-Za-z0-9]+/g,
    /\b\d{4}年/g,
  ];
  for (const p of properPatterns) {
    const m = query.match(p);
    if (m) properNouns.push(...m);
  }

  const segments = cnSegment(query);
  const scored = segments.map(w => {
    let score = w.length * 1.5;
    for (const pn of properNouns) {
      if (w.includes(pn) || pn.includes(w)) score += 5;
    }
    if (/[a-zA-Z]/.test(w)) score += 4;
    if (/\d/.test(w)) score += 3;
    if (/[市省区县镇村公司集团科技汽车银行大学医院]$/.test(w)) score += 3;
    if (/^\d{1,3}$/.test(w)) score -= 5;
    if (/^[a-zA-Z]{1,2}$/.test(w)) score -= 5;
    return { word: w, score: Math.max(0, score) };
  });

  scored.sort((a, b) => b.score - a.score);
  const anchors = [];
  const seen = new Set();
  for (const { word } of scored) {
    if (word.length < 1 || seen.has(word)) continue;
    if (anchors.some(a => a.includes(word))) continue;
    const supersedes = anchors.findIndex(a => word.includes(a));
    if (supersedes >= 0) anchors.splice(supersedes, 1);
    seen.add(word);
    anchors.push(word);
    if (anchors.length >= 4) break;
  }

  if (anchors.length < 2) {
    for (const { word } of scored) {
      if (!seen.has(word) && word.length >= 1) {
        seen.add(word);
        anchors.push(word);
        if (anchors.length >= 2) break;
      }
    }
  }

  return anchors.length >= 2 ? anchors : [query.replace(/\s+/g, '')];
}

function extractAnchorWordsEN(query) {
  const properNouns = [];
  const capitalized = query.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g);
  if (capitalized) properNouns.push(...capitalized);

  const tokens = query.toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 0);

  const meaningful = tokens.filter(w =>
    !EN_QUESTION_WORDS.has(w) && !EN_STOP_WORDS.has(w)
  );

  const scored = meaningful.map(w => {
    let score = w.length;
    for (const pn of properNouns) {
      if (pn.toLowerCase().includes(w) || w.includes(pn.toLowerCase())) score += 5;
    }
    if (/^[A-Z]/.test(w)) score += 3;
    return { word: w, score };
  });

  scored.sort((a, b) => b.score - a.score);
  const anchors = [];
  const seen = new Set();
  for (const { word } of scored) {
    if (!seen.has(word) && word.length >= 1) {
      seen.add(word);
      anchors.push(word);
      if (anchors.length >= 4) break;
    }
  }

  return anchors.length >= 2 ? anchors : [query.replace(/\s+/g, ' ').trim()];
}

// ─── 复杂度分级 ────────────────────────────────────────────
const L2_SIGNALS_CN = ['全面', '深入', '详细', '研究报告', '透彻', '完整论文',
  '全方位', '全貌', '综述', '白皮书', '调研', '尽调'];
const L2_SIGNALS_EN = ['comprehensive', 'in-depth', 'detailed', 'research report',
  'thorough', 'full paper', 'overview', 'survey', 'white paper', 'analysis'];
const L0_SIGNALS_CN = ['是什么', '定义', '版本号', '最新版本', '多高', '多大',
  '多少钱', '几点', '几号', '日期', '价格'];
const L0_SIGNALS_EN = ['what is', 'define', 'definition', 'latest version',
  'version number', 'how much', 'what time', 'date', 'price of'];

function classifyComplexity(query, lang) {
  const ql = query.toLowerCase();
  const l2Signals = lang === 'zh' ? L2_SIGNALS_CN
    : lang === 'en' ? L2_SIGNALS_EN
    : [...L2_SIGNALS_CN, ...L2_SIGNALS_EN];
  for (const s of l2Signals) {
    if (ql.includes(s.toLowerCase())) return 'L2';
  }
  const l2Extra = lang === 'zh'
    ? ['分析', '对比', '比较', '原因', '影响', '评估', '展望', '预测']
    : ['analysis', 'compare', 'comparison', 'reason', 'impact', 'evaluate', 'forecast'];
  for (const s of l2Extra) {
    if (ql.includes(s.toLowerCase())) return 'L2';
  }

  const l0Signals = lang === 'zh' ? L0_SIGNALS_CN
    : lang === 'en' ? L0_SIGNALS_EN
    : [...L0_SIGNALS_CN, ...L0_SIGNALS_EN];
  for (const s of l0Signals) {
    if (ql.includes(s.toLowerCase())) return 'L0';
  }

  return 'L1';
}

// ─── 意图路由 ──────────────────────────────────────────────
const INTENT_MAP = [
  { pattern: /地图|导航|路线|距离|周边|附近|位置|坐标|在哪|地址|geograph|map|route|direction|nearby|location|where is/i, intent: 'geographic' },
  { pattern: /新闻|最新|今天|昨日|本周|近日|刚刚|突发|热点|news|latest|today|breaking|recent/i, intent: 'chinese_news' },
  { pattern: /技术|代码|api|编程|性能|bug|算法|架构|technical|code|programming|algorithm|architecture/i, intent: 'technical' },
  { pattern: /核实|验证|真假|真的吗|谣言|fact.?check|verify|true|false|debunk/i, intent: 'fact_check' },
  { pattern: /对比|比较|区别|差异|vs|compare|comparison|difference|versus/i, intent: 'comparative' },
  { pattern: /全面|深入|详细|研究|报告|分析|报告|deep|research|thorough/i, intent: 'deep_research' },
];

function routeIntent(query, lang) {
  for (const { pattern, intent } of INTENT_MAP) {
    if (pattern.test(query)) return intent;
  }
  if (lang === 'zh' || lang === 'mixed') return 'chinese_general';
  return 'english_general';
}

// ─── 工具分类辅助函数 ──────────────────────────────────────
function toolIsGeo(strengths) {
  return strengths.includes('geographic') || strengths.includes('poi') || strengths.includes('routing');
}
function toolIsChinese(strengths) {
  return strengths.includes('chinese') || strengths.includes('china_coverage');
}
function toolIsEnglish(strengths) {
  // 有 english 标签，或有 general 但没 chinese（避免误分类）
  return strengths.includes('english') ||
    (strengths.includes('general') && !strengths.includes('chinese') && !strengths.includes('china_coverage'));
}
function toolIsPureFetcher(strengths) {
  return (strengths.includes('deep_extract') || strengths.includes('verification')) &&
    !strengths.includes('chinese') && !strengths.includes('english') &&
    !strengths.includes('general') && !strengths.includes('geographic');
}

// ─── 工具 query 分流（动态，面向全部 discovered 工具） ──────
function generateToolQueries(anchorWords, query, lang, intent) {
  const anchorStr_CN = anchorWords.join(' ');
  const anchorStr_EN = anchorWords.map(w =>
    /[\u4e00-\u9fff]/.test(w) ? w : w.toLowerCase()
  ).join(' ');
  const isDeep = intent === 'deep_research' || intent === 'comparative';

  const queries = {};

  const discoverOutput = getDiscoverOutput();
  if (!discoverOutput) {
    // discover 失败 → 空 queries，由调用方兜底
    return queries;
  }

  const readyTools = (discoverOutput.tools || []).filter(t =>
    t.status === 'ready' &&
    t.id.startsWith('skill:') &&
    t.call?.kind === 'shell'
  );

  for (const tool of readyTools) {
    const strengths = tool.strengths || [];

    // 跳过纯抓取/浏览器工具（Round 1 不适用）
    if (toolIsPureFetcher(strengths)) continue;

    let toolQuery, toolLang;

    if (toolIsGeo(strengths)) {
      toolQuery = anchorStr_CN;
      toolLang = 'zh';
    } else if (toolIsChinese(strengths)) {
      toolQuery = anchorStr_CN === query ? query : `${anchorStr_CN} ${query}`;
      toolLang = 'zh';
    } else if (toolIsEnglish(strengths)) {
      const suffix = isDeep ? ' research analysis' : '';
      toolQuery = `${anchorStr_EN}${suffix}`;
      toolLang = 'en';
    } else {
      // 未识别的工具：用原始 query + 检测到的语言
      toolQuery = query;
      toolLang = lang;
    }

    queries[tool.id] = {
      query: toolQuery,
      lang: toolLang,
      strengths: strengths,
      tool_name: tool.name,
    };
  }

  return queries;
}

// ─── GATE Checklist ────────────────────────────────────────
function generateGateChecklist(anchorWords, queries) {
  return {
    'GATE-0_discover': { status: 'pending', note: '先跑 discover.js --cache' },
    'GATE-1_tool_count': {
      status: 'pending',
      note: `从 discover 输出提取 ready 数量。当前可用工具: ${Object.keys(queries).length}`,
    },
    'GATE-2_all_called': { status: 'pending', note: '每个 ready 工具强执行，不得跳过' },
    'GATE-3_parallel': { status: 'pending', note: '全部并行，不准串行' },
    'GATE-QUERY_diverse': {
      status: 'pending',
      note: '各工具用不同 query（按能力自动分流）',
      tool_queries: queries,
    },
    'GATE-RELEVANCE_anchored': {
      status: 'pending',
      anchor_words: anchorWords,
      note: '每轮所有 query 必须包含锚点词（或其合理译版）',
    },
    'GATE-4_skip_ratio': { status: 'pending', note: '回复前自检: tool_skip_ratio 必须为 0' },
  };
}

// ─── 主逻辑 ────────────────────────────────────────────────
function main() {
  const opts = parseArgs();
  if (!opts.query) {
    console.error('Usage: prepare.mjs --query "搜索内容" 或 echo "..." | node prepare.mjs');
    process.exit(1);
  }

  const query = opts.query.trim();
  const lang = opts.lang === 'auto' ? detectLang(query) : opts.lang;
  const anchorWords = extractAnchorWords(query, lang);
  const complexity = classifyComplexity(query, lang);
  const intent = routeIntent(query, lang);
  const toolQueries = generateToolQueries(anchorWords, query, lang, intent);

  // ── builtin 工具（agent 层调用，不参与 shell 执行） ──
  const discoverOutput = getDiscoverOutput();
  const builtinTools = (discoverOutput?.tools || [])
    .filter(t => t.status === 'ready' && t.id.startsWith('builtin:'))
    .map(t => ({
      id: t.id, name: t.name, strengths: t.strengths || [], kind: t.call?.kind || 'system_tool',
    }));

  const gateChecklist = generateGateChecklist(anchorWords, toolQueries);

  const output = {
    version: '5.2',
    generated_at: new Date().toISOString(),
    input: { query, lang },
    anchor_words: anchorWords,
    complexity,
    intent,
    min_depth: complexity === 'L0' ? 0 : complexity === 'L1' ? 1 : 2,
    max_depth: complexity === 'L0' ? 0 : complexity === 'L1' ? 4 : 5,
    tool_queries: toolQueries,
    builtin_tools: builtinTools,
    gate_checklist: gateChecklist,
  };

  console.log(JSON.stringify(output, null, 2));
}

main();
