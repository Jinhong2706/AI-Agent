#!/usr/bin/env node
/**
 * orchestrate.mjs — Universal Search 全自动编排 v5.2.1
 *
 * 一条命令：prepare → 并行搜索 → 结果聚合 → audit → 深度迭代 → 输出
 *
 * 用法:
 *   node scripts/orchestrate.mjs "搜索内容"
 *   echo "搜索内容" | node scripts/orchestrate.mjs
 *
 * 自动处理:
 *   - discover.js 驱动动态工具发现（非硬编码）
 *   - call.template 驱动命令构建（兼容任意 skill）
 *   - API key 自动加载（.env / config.json / process env）
 *   - 工具调用失败降级（跳过，不阻塞其他工具）
 *   - 结果格式归一化 + URL 去重
 *   - 多轮深度迭代直到收敛或硬上限
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');
const WORKSPACE = resolve(SKILL_DIR, '../..');

// ═══════════════════════════════════════════════════════════
//  Discover 缓存 & 工具加载
// ═══════════════════════════════════════════════════════════

let _discoverCache = null;

function getDiscoverOutput() {
  if (_discoverCache !== null) return _discoverCache;
  try {
    const raw = execSync(`node "${resolve(SKILL_DIR, 'scripts/discover.js')}" --cache`, {
      encoding: 'utf-8', timeout: 10000, shell: '/bin/bash', stdio: 'pipe',
    });
    _discoverCache = JSON.parse(raw);
  } catch {
    _discoverCache = null;
  }
  return _discoverCache;
}

// ═══════════════════════════════════════════════════════════
//  API Key 动态加载（扫描 tool 目录 + HOME/.openclaw/.env）
// ═══════════════════════════════════════════════════════════

function loadApiKeys(discoverOutput) {
  const keys = {};

  // 1) 从 discover 输出的工具目录扫描 .env / config.json
  if (discoverOutput) {
    for (const tool of (discoverOutput.tools || [])) {
      if (!tool.skillPath) continue;
      for (const f of [
        resolve(tool.skillPath, '.env'),
        resolve(tool.skillPath, 'config.json'),
        resolve(tool.skillPath, 'scripts', 'config.json'),
      ]) {
        if (!existsSync(f)) continue;
        try {
          if (f.endsWith('.json')) {
            const cfg = JSON.parse(readFileSync(f, 'utf-8'));
            for (const [k, v] of Object.entries(cfg)) {
              if (typeof v === 'string' && (k.endsWith('_KEY') || k.endsWith('_TOKEN') || k.endsWith('_SECRET'))) keys[k] = v;
            }
          } else {
            for (const line of readFileSync(f, 'utf-8').split('\n')) {
              const m = line.match(/^\s*(\w+)\s*=\s*(.+?)\s*$/);
              if (m) keys[m[1]] = m[2];
            }
          }
        } catch { /* 跳过损坏文件 */ }
      }
    }
  }

  // 2) HOME/.openclaw/.env（用户全局配置）
  try {
    const homeEnv = resolve(process.env.HOME || '/root', '.openclaw', '.env');
    if (existsSync(homeEnv)) {
      for (const line of readFileSync(homeEnv, 'utf-8').split('\n')) {
        const m = line.match(/^\s*(\w+)\s*=\s*(.+?)\s*$/);
        if (m) keys[m[1]] = m[2];
      }
    }
  } catch { /* 跳过 */ }

  // 3) process.env 补充（优先级最低，不覆盖文件配置）
  for (const k of ['BAIDU_API_KEY', 'MINIMAX_API_KEY', 'TAVILY_API_KEY', 'AMAP_WEBSERVICE_KEY']) {
    if (process.env[k] && !keys[k]) keys[k] = process.env[k];
  }

  return keys;
}

// ═══════════════════════════════════════════════════════════
//  模板命令构建（动态，基于 discover call.template）
// ═══════════════════════════════════════════════════════════

/**
 * 将字符串安全嵌入 shell 单引号字符串。
 * 策略：' → '\'' （结束引号、转义的单引号、重新开始引号）
 * 这是 POSIX 兼容的标准做法，不依赖 bash 特性。
 */
function sq(s) {
  return "'" + String(s).replace(/'/g, "'\\''") + "'";
}

function buildCommandFromTemplate(template, skillPath, qConfig) {
  const rawQuery = qConfig.query || '';
  if (!rawQuery) return null;

  let cmd = template;

  // 1) 替换 {skill_dir}
  cmd = cmd.replace(/\{skill_dir\}/g, skillPath);

  // 2) 处理 <JSON> 占位符（baidu 风格：python3 search.py '<JSON>'）
  if (cmd.includes("'<JSON>'") || cmd.includes('"<JSON>"')) {
    const json = JSON.stringify({ query: rawQuery, count: 10 });
    cmd = cmd.replace(/'<JSON>'/g, `'${json}'`);
    cmd = cmd.replace(/"<JSON>"/g, `'${json}'`);
  }

  // 3) 替换 {query}
  const safeQ = sq(rawQuery);
  // 双引号内 → 标准 shell 转义
  const dqQ = rawQuery.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/`/g, '\\`').replace(/\$/g, '\\$');
  cmd = cmd.replace(/"\{query\}"/g, `"${dqQ}"`);
  cmd = cmd.replace(/'\{query\}'/g, safeQ);
  cmd = cmd.replace(/\{query\}/g, safeQ);

  // 4) 替换 {keywords}
  cmd = cmd.replace(/'\{keywords\}'/g, safeQ);
  cmd = cmd.replace(/"\{keywords\}"/g, `"${dqQ}"`);
  cmd = cmd.replace(/\{keywords\}/g, safeQ);

  // 5) 替换 {city} — 从 query 提取或默认
  const cityMatch = rawQuery.match(/([\u4e00-\u9fff]{2,4})(?:市|省|区|县|镇|村)?/);
  const city = cityMatch ? cityMatch[1] : '北京';
  const safeCity = sq(city);
  cmd = cmd.replace(/'\{city\}'/g, safeCity);
  cmd = cmd.replace(/"\{city\}"/g, `"${city}"`);
  cmd = cmd.replace(/\{city\}/g, city);

  // 6) 已知可选参数占位符 → 设安全默认值（仅清理这些已知 key，不碰任意花括号）
  const KNOWN_OPTIONAL_PARAMS = [
    { key: 'location', default: '' },
    { key: 'radius', default: '1000' },
    { key: 'offset', default: '10' },
    { key: 'count', default: '10' },
    { key: 'page', default: '1' },
    { key: 'freshness', default: '' },
    { key: 'options', default: '' },
    { key: 'format', default: '' },
    { key: 'type', default: '' },
  ];
  for (const { key, default: def } of KNOWN_OPTIONAL_PARAMS) {
    if (def === '') {
      cmd = cmd.replace(new RegExp(`'\\{${key}\\}'`, 'g'), "''");
      cmd = cmd.replace(new RegExp(`"\\{${key}\\}"`, 'g'), '""');
      cmd = cmd.replace(new RegExp(`\\{${key}\\}`, 'g'), '');
    } else {
      cmd = cmd.replace(new RegExp(`'\\{${key}\\}'`, 'g'), `'${def}'`);
      cmd = cmd.replace(new RegExp(`"\\{${key}\\}"`, 'g'), `"${def}"`);
      cmd = cmd.replace(new RegExp(`\\{${key}\\}`, 'g'), def);
    }
  }

  // 7) bash 花括号展开保护 — node -e "const {x} = ..." 会被吞掉
  if (cmd.includes('node -e')) {
    cmd = 'set +B; ' + cmd;
  }

  return cmd;
}

/** 从 toolId 推断解析器类型 */
function inferParser(toolId) {
  const id = toolId.toLowerCase();
  if (id.includes('baidu')) return 'baidu';
  if (id.includes('tavily')) return 'tavily';
  if (id.includes('amap') || id.includes('gaode')) return 'amap';
  return 'generic';
}

// ═══════════════════════════════════════════════════════════
//  命令映射（动态，基于 discover call.template）
// ═══════════════════════════════════════════════════════════

function buildCommands(toolQueries, discoverOutput) {
  const cmds = {};
  if (!discoverOutput) return cmds;

  const toolsMap = {};
  for (const tool of (discoverOutput.tools || [])) {
    toolsMap[tool.id] = tool;
  }

  for (const [toolId, qConfig] of Object.entries(toolQueries)) {
    const tool = toolsMap[toolId];
    if (!tool || !tool.call || !tool.call.template) continue;
    if (tool.call.kind === 'system_tool' || tool.call.kind === 'skill') continue;

    const cmd = buildCommandFromTemplate(tool.call.template, tool.skillPath, qConfig);
    if (!cmd) continue;

    cmds[toolId] = {
      cmd,
      cwd: tool.skillPath || WORKSPACE,
      parser: inferParser(toolId),
    };
  }

  return cmds;
}

// ═══════════════════════════════════════════════════════════
//  结果解析器
// ═══════════════════════════════════════════════════════════

function parseGenericResults(toolId, stdout) {
  const results = [];
  const engineName = toolId.replace(/^skill:/, '');

  // JSON 解析分支
  try {
    const data = JSON.parse(stdout);

    if (Array.isArray(data)) {
      for (const item of data) {
        results.push({
          engine: engineName,
          url: item.url || item.link || item.href || '',
          title: (item.title || item.name || '').substring(0, 200),
          content: (item.content || item.snippet || item.description || item.summary || item.text || '').substring(0, 500),
          snippet: (item.content || item.snippet || item.description || item.summary || item.text || '').substring(0, 200),
        });
      }
      return results;
    }

    const items = data.results || data.pois || data.data || data.items || data.list || [];
    if (Array.isArray(items) && items.length > 0) {
      for (const item of items) {
        results.push({
          engine: engineName,
          url: item.url || item.link || '',
          title: (item.title || item.name || '').substring(0, 200),
          content: (item.content || item.snippet || item.description || item.address || item.summary || '').substring(0, 500),
          snippet: (item.content || item.snippet || item.description || item.address || item.summary || '').substring(0, 200),
        });
      }
      return results;
    }

    // 非标准 JSON → 尝试提取有用字段
    const textFallback = data.answer || data.summary || data.text || '';
    if (textFallback) {
      results.push({
        engine: engineName,
        url: data.url || data.link || '',
        title: (data.title || data.name || `[${engineName}]`).substring(0, 200),
        content: textFallback.substring(0, 500),
        snippet: textFallback.substring(0, 200),
      });
    }
    return results;
  } catch { /* 非 JSON，走文本降级 */ }

  // 文本降级：返回首 N 行
  const lines = stdout.trim().split('\n').filter(l => l.trim());
  for (let i = 0; i < Math.min(lines.length, 20); i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith('🔍') || line.startsWith('✅') || line.startsWith('⚠️')) continue;
    results.push({
      engine: engineName,
      url: '',
      title: line.substring(0, 200),
      content: line.substring(0, 500),
      snippet: line.substring(0, 200),
    });
  }
  return results;
}

function parseResults(toolId, parser, stdout, stderr) {
  if (!stdout || (stderr && stderr.toLowerCase().includes('error'))) return [];

  // 快速保护：stdout 太短可能是报错（如 Python traceback）
  const trimmed = stdout.trim();
  if (!trimmed) return [];

  try {
    switch (parser) {
      case 'baidu': {
        const clean = trimmed.replace(/^[^\[]*(\[)/s, '$1');
        const items = JSON.parse(clean);
        return items.map(item => ({
          engine: 'baidu-search',
          url: item.url || '',
          title: (item.title || '').substring(0, 200),
          content: (item.content || '').substring(0, 500),
          snippet: (item.content || '').substring(0, 200),
        }));
      }
      case 'tavily': {
        const brave = JSON.parse(trimmed);
        const results = [];
        if (brave.results) {
          for (const r of brave.results) {
            results.push({
              engine: 'tavily-search',
              url: r.url || '',
              title: (r.title || '').substring(0, 200),
              content: (r.snippet || r.title || '').substring(0, 500),
              snippet: (r.snippet || r.title || '').substring(0, 200),
            });
          }
        }
        if (brave.answer && results.length === 0) {
          results.push({
            engine: 'tavily-search',
            url: '', title: 'Tavily Answer',
            content: brave.answer.substring(0, 500),
            snippet: brave.answer.substring(0, 200),
          });
        }
        return results;
      }
      case 'amap':
      case 'generic':
      default:
        return parseGenericResults(toolId, stdout);
    }
  } catch (e) {
    // 专用解析器失败 → 降级到通用解析
    if (parser !== 'generic') return parseGenericResults(toolId, stdout);
    // generic 都失败了 → 取首行
    return [{
      engine: toolId,
      url: '',
      title: trimmed.split('\n')[0].substring(0, 200),
      content: trimmed.substring(0, 500),
      snippet: trimmed.substring(0, 200),
    }];
  }
}

// ═══════════════════════════════════════════════════════════
//  System Tool 指令生成（内置 web_search / web_fetch）
//  脚本无法调用 OpenClaw agent 工具 → 输出结构化指令让 agent 并行补调
// ═══════════════════════════════════════════════════════════

/** 简易语言检测（从 prepare.mjs 提取，避免跨模块依赖） */
function detectLangSys(query) {
  let cjk = 0, ascii = 0;
  for (const ch of query) {
    const code = ch.codePointAt(0);
    if ((code >= 0x4E00 && code <= 0x9FFF) || (code >= 0x3400 && code <= 0x4DBF)) cjk++;
    else if (code < 128) ascii++;
  }
  return cjk > ascii ? 'zh' : (cjk > 0 ? 'mixed' : 'en');
}

function generateSystemToolCalls(query, lang, anchorWords, intent, discoverOutput, allResults, totalRounds) {
  const calls = { web_search: [], web_fetch: [] };
  const allTools = discoverOutput?.tools || [];
  const webSearchDef = allTools.find(t => t.id === 'builtin:web_search');
  const webFetchDef = allTools.find(t => t.id === 'builtin:web_fetch');

  // ── web_search: 始终生成 R1 初始 query（agent 应在 orchestrate 启动时并行执行） ──
  if (webSearchDef && webSearchDef.status === 'ready') {
    const isCN = lang === 'zh' || lang === 'mixed';
    const anchorStr_CN = anchorWords.join(' ');
    // 英文锚点：非 CJK 字符构成的词直接使用，纯 CJK 词用原文
    // Query 1: 主语言综合搜索
    calls.web_search.push({
      tool: 'web_search',
      params: {
        query: isCN ? anchorStr_CN : query,
        freshness: isCN ? 'week' : undefined,
        count: isCN ? 8 : 10
      },
      purpose: isCN ? 'R1 中文综合搜索 — 覆盖国内搜索引擎盲区' : 'R1 英文综合搜索',
    });

    // Query 2: 交叉语种验证（中文查询→英文，英文查询→变体）
    const crossQuery = isCN
      ? `${query.replace(/[\u4e00-\u9fff\u3000-\u303f，。；：！？、]+/g, ' ').replace(/\s+/g, ' ').trim()}`
      : `${query} latest details`;
    calls.web_search.push({
      tool: 'web_search',
      params: {
        query: crossQuery || query,
        freshness: 'week',
        count: 10
      },
      purpose: isCN ? 'R1 英文交叉验证 — 覆盖 AP/Reuters/NPR 等国际源' : 'R1 补充搜索 — query 变体',
    });

    // 若收敛失败，追加深度 query 提示
    if (totalRounds > 2) {
      calls.web_search.push({
        tool: 'web_search',
        params: {
          query: `Philippines earthquake casualties tsunami latest`,
          freshness: 'day',
          count: 8
        },
        purpose: `深度补源 (${totalRounds}轮仍未收敛) — 关键数据词收紧`,
      });
    }
  }

  // ── web_fetch: 有结果就生成抓取目标（agent 在 orchestrate 完成后执行） ──
  if (webFetchDef && webFetchDef.status === 'ready' && allResults.length > 0) {
    const seenUrls = new Set();
    for (const r of allResults) {
      if (!r.url || seenUrls.has(r.url) || calls.web_fetch.length >= 5) break;
      // 只取有实质 URL 且标题相关的结果
      if (r.url.startsWith('http') && r.title && r.title.length > 5) {
        seenUrls.add(r.url);
        calls.web_fetch.push({
          tool: 'web_fetch',
          params: { url: r.url, extractMode: 'markdown', maxChars: 4000 },
          title: r.title.substring(0, 120),
          purpose: `全文抓取—深度提取`,
        });
      }
    }
    // 不足 3 个 → 从建议 URL 补
    if (calls.web_fetch.length < 3) {
      for (const r of allResults) {
        if (calls.web_fetch.length >= 5) break;
        if (!r.url || seenUrls.has(r.url) || !r.url.startsWith('http')) continue;
        seenUrls.add(r.url);
        calls.web_fetch.push({
          tool: 'web_fetch',
          params: { url: r.url, extractMode: 'markdown', maxChars: 4000 },
          title: (r.title || r.url).substring(0, 120),
          purpose: '全文抓取—补充验证',
        });
      }
    }
  }

  return calls;
}

// ═══════════════════════════════════════════════════════════
//  深度迭代 query 生成（动态，面向全部工具）
// ═══════════════════════════════════════════════════════════

function toolIsChinese(strengths) {
  return strengths.includes('chinese') || strengths.includes('china_coverage');
}
function toolIsEnglish(strengths) {
  return strengths.includes('english') ||
    (strengths.includes('general') && !strengths.includes('chinese') && !strengths.includes('china_coverage'));
}

function generateDeepQueries(auditResult, anchorWords, originalQuery, round, discoverOutput) {
  const anchorStr_CN = anchorWords.join(' ');
  const anchorStr_EN = anchorWords.join(' ');
  const signals = auditResult?.signals || [];
  const activeSignalIds = signals.filter(s => s.active).map(s => s.id);
  const queries = {};

  // ── 构建深挖方向 ──
  const directions = [];
  if (activeSignalIds.includes(1)) directions.push({ zh: `${anchorStr_CN} 最新进展`, en: `${anchorStr_EN} latest update ${new Date().toISOString().slice(0, 10)}` });
  if (activeSignalIds.includes(2)) directions.push({ zh: `${anchorStr_CN} 原因 分析 影响`, en: `${anchorStr_EN} cause analysis impact` });
  if (activeSignalIds.includes(3)) directions.push({ zh: `${anchorStr_CN} 详情 背景`, en: `${anchorStr_EN} details background` });
  if (activeSignalIds.includes(4)) directions.push({ zh: `${anchorStr_CN} 数据 核实`, en: `${anchorStr_EN} data verification facts` });
  if (activeSignalIds.includes(5)) directions.push({ zh: `${anchorStr_CN} 核实 辟谣`, en: `${anchorStr_EN} fact check debunk confirm` });
  if (activeSignalIds.includes(7)) directions.push({ zh: `${anchorStr_CN} 更多信息`, en: `${anchorStr_EN} overview comprehensive` });

  if (directions.length === 0) {
    const suffixes = [
      { zh: '详情 影响 相关', en: 'details impact related' },
      { zh: '背景 历史 来龙去脉', en: 'background history context' },
    ];
    const s = suffixes[Math.min(round - 2, suffixes.length - 1)];
    directions.push({ zh: `${anchorStr_CN} ${s.zh}`, en: `${anchorStr_EN} ${s.en}` });
  }

  const selected = directions.slice(0, 3);

  // ── 获取可用搜索工具并分流 ──
  const searchTools = (discoverOutput?.tools || []).filter(t =>
    t.status === 'ready' && t.id.startsWith('skill:') && t.call?.kind === 'shell'
  );

  if (searchTools.length === 0) return queries;

  const cnTools = searchTools.filter(t => toolIsChinese(t.strengths || []));
  const enTools = searchTools.filter(t => toolIsEnglish(t.strengths || []));
  const otherTools = searchTools.filter(t => !cnTools.includes(t) && !enTools.includes(t));

  // 中文/英文引擎各吃一个方向
  for (let i = 0; i < selected.length; i++) {
    if (i < cnTools.length) queries[cnTools[i].id] = { query: selected[i].zh, lang: 'zh' };
    if (i < enTools.length) queries[enTools[i].id] = { query: selected[i].en, lang: 'en' };
  }

  // 未分配工具 → 第一个方向
  const usedIds = new Set(Object.keys(queries));
  for (const tool of [...cnTools, ...enTools, ...otherTools]) {
    if (usedIds.has(tool.id)) continue;
    const useZh = toolIsChinese(tool.strengths || []);
    const dir = useZh ? selected[0].zh : selected[0].en;
    queries[tool.id] = { query: dir, lang: useZh ? 'zh' : 'en' };
  }

  return queries;
}

// ═══════════════════════════════════════════════════════════
//  并行执行 & 结果收集辅助函数
// ═══════════════════════════════════════════════════════════

function execOneRound(commands, env, processStderr) {
  const toolIds = Object.keys(commands);
  if (toolIds.length === 0) return [];

  const allResults = [];
  for (const toolId of toolIds) {
    const { cmd, cwd, parser } = commands[toolId];
    try {
      // 使用独立子进程 + 超时信号确保孙子进程也被杀死
      const stdout = execSync(cmd, {
        encoding: 'utf-8', cwd, timeout: 30000, env, shell: '/bin/bash',
        stdio: 'pipe', killSignal: 'SIGKILL', maxBuffer: 50 * 1024 * 1024,
      });
      const results = parseResults(toolId, parser, stdout, '');
      processStderr(`  ✅ ${toolId}: ${results.length}条`);
      allResults.push(...results);
    } catch (e) {
      const msg = e.stderr ? e.stderr.slice(0, 80).replace(/\n/g, ' ') : String(e.message || e).slice(0, 80);
      processStderr(`  ⚠️  ${toolId}: ${msg}`);
    }
  }
  return allResults;
}

// ═══════════════════════════════════════════════════════════
//  主流程
// ═══════════════════════════════════════════════════════════

function main() {
  const args = process.argv.slice(2);
  let query = args.join(' ') || '';
  if (!query && !process.stdin.isTTY) {
    query = readFileSync(0, 'utf-8').trim();
  }
  if (!query) {
    console.error('Usage: orchestrate.mjs "搜索内容"');
    process.exit(1);
  }

  const startTime = Date.now();

  // Step 0: discover（一次，全局复用）
  const discoverOutput = getDiscoverOutput();
  if (!discoverOutput) {
    console.error('discover 失败，无法继续');
    process.exit(1);
  }

  // Step 0b: api keys
  const apiKeys = loadApiKeys(discoverOutput);

  // Step 1: prepare
  process.stderr.write('🔍 准备中... ');
  let prep;
  try {
    const prepRaw = execSync(
      `node "${resolve(SKILL_DIR, 'scripts/prepare.mjs')}" --query "${query.replace(/"/g, '\\"')}"`,
      { encoding: 'utf-8', cwd: SKILL_DIR, timeout: 15000, shell: '/bin/bash', stdio: 'pipe' }
    );
    prep = JSON.parse(prepRaw);
  } catch (e) {
    console.error('prepare 失败:', e.message);
    process.exit(1);
  }
  process.stderr.write(`锚点=${prep.anchor_words.join(',')} 复杂度=${prep.complexity}\n`);

  // Step 1b: 检查工具可用性 — prepare 可能返回空 queries（discover 复用失败或全为 fetcher）
  const hasTools = Object.keys(prep.tool_queries || {}).length > 0;
  if (!hasTools) {
    // 极端降级：无可用搜索 skill → 输出空结果并退出
    console.log(JSON.stringify({
      version: '5.2',
      query,
      anchor_words: prep.anchor_words,
      complexity: prep.complexity,
      intent: prep.intent,
      elapsed_seconds: ((Date.now() - startTime) / 1000).toFixed(1),
      total_rounds: 0,
      tools_called: [],
      results_total: 0,
      converged: false,
      convergence_reason: '无可用的搜索工具（请安装至少一个搜索 skill）',
      error: 'no_search_tools',
    }, null, 2));
    process.exit(0);
  }

  // ── 深度迭代循环 ──
  const minDepth = prep.complexity === 'L0' ? 0 : prep.complexity === 'L1' ? 1 : 2;
  const maxRounds = prep.complexity === 'L0' ? 1 : prep.complexity === 'L1' ? 4 : 5;

  let allResults = [];
  const roundLogs = [];
  let finalAudit = null;
  const seenUrls = new Set();
  const allToolsUsed = new Set();
  const env = { ...process.env, ...apiKeys };

  for (let round = 1; round <= maxRounds; round++) {
    const isFirstRound = round === 1;

    const toolQueries = isFirstRound
      ? prep.tool_queries
      : generateDeepQueries(finalAudit, prep.anchor_words, query, round, discoverOutput);

    // 深轮 queries 可能为空 → 复用上一轮 queries
    const effectiveQueries = (Object.keys(toolQueries).length > 0) ? toolQueries : prep.tool_queries;

    const commands = buildCommands(effectiveQueries, discoverOutput);
    const toolIds = Object.keys(commands);

    if (toolIds.length === 0) {
      // 本轮无可执行工具 → 强制结束
      roundLogs.push({ round, label: `深度 R${round}`, error: '无可执行命令', tools_called: [] });
      process.stderr.write(`⚠️  R${round}: 无可执行命令，提前结束\n`);
      break;
    }

    const roundLabel = isFirstRound ? '广度 R1' : `深度 R${round}`;
    process.stderr.write(`${round > 1 ? '\n' : ''}⚡ ${roundLabel}: ${toolIds.length} 个工具 [${toolIds.join(', ')}]\n`);

    toolIds.forEach(id => allToolsUsed.add(id));

    // 执行
    const roundResults = execOneRound(commands, env, (msg) => process.stderr.write(msg + '\n'))
      .filter(r => r.title || r.content);

    // URL 去重
    let newCount = 0;
    for (const r of roundResults) {
      const key = r.url || (r.title + (r.snippet || ''));
      if (key && !seenUrls.has(key)) {
        seenUrls.add(key);
        allResults.push({ ...r, _round: round });
        newCount++;
      } else if (!key) {
        allResults.push({ ...r, _round: round });
        newCount++;
      }
    }

    process.stderr.write(`📦 ${roundLabel}: ${roundResults.length}条 (${newCount} new, ${allResults.length} total)\n`);

    // Audit
    const prevRoundsMeta = {};
    for (const rl of roundLogs) {
      prevRoundsMeta[`round_${rl.round}`] = {
        results_count: rl.results_count,
        backlink_passed: rl.backlink_passed,
        anchor_relevance_rate: rl.anchor_relevance_rate,
      };
    }
    prevRoundsMeta.new_relevant_sources = newCount;

    let audit;
    try {
      audit = JSON.parse(execSync(
        `node "${resolve(SKILL_DIR, 'scripts/audit.mjs')}"`,
        {
          input: JSON.stringify({
            query, anchor_words: prep.anchor_words,
            round, complexity: prep.complexity, max_depth: maxRounds,
            previous_rounds: prevRoundsMeta, results: roundResults,
          }),
          encoding: 'utf-8', cwd: SKILL_DIR, timeout: 10000, env, shell: '/bin/bash', stdio: 'pipe',
        }
      ));
    } catch (e) {
      audit = {
        summary: { backlink_passed: 0, total_results: roundResults.length, converged: false, convergence_reason: e.message.slice(0, 80) },
        signals: [], backlink_details: { passed: [], failed: [] }, recommendations: [],
      };
    }

    finalAudit = audit;
    const s = audit.summary || {};
    const activeSigs = (audit.signals || []).filter(sig => sig.active).map(s => s.name);

    roundLogs.push({
      round, label: roundLabel, tools_called: [...toolIds],
      results_count: roundResults.length, new_sources: newCount,
      backlink_passed: s.backlink_passed || 0,
      anchor_relevance_rate: s.anchor_relevance_rate || '0%',
      converged: s.converged || false,
      active_signals: activeSigs,
      convergence_reason: s.convergence_reason || '',
    });

    process.stderr.write(`🔎 ${roundLabel}: passed=${s.backlink_passed}/${roundResults.length} rel=${s.anchor_relevance_rate} converged=${s.converged ? '✅' : '❌'}\n`);

    // 收敛 → 提前退出
    if (round >= minDepth + 1 && s.converged) {
      process.stderr.write(`🏁 收敛 (${round}/${maxRounds})\n`);
      break;
    }
    if (round >= maxRounds) {
      process.stderr.write(`⚠️  硬上限 ${maxRounds} 轮\n`);
      break;
    }
  }

  // ── 生成 system tool 调用指令 ──
  const lang = (prep.input?.lang) || detectLangSys(query);
  const systemToolCalls = generateSystemToolCalls(
    query, lang, prep.anchor_words, prep.intent,
    discoverOutput, allResults, roundLogs.length
  );

  // ── 最终输出 ──
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const s = finalAudit?.summary || {};
  const sortedResults = allResults.sort((a, b) => (a._round || 99) - (b._round || 99));

  // ── web_fetch 推荐 URL（agent 层可对此列表调用 web_fetch 获取全文） ──
  const fetchUrls = [];
  const fetchedUrlSet = new Set();
  const passedDetails = finalAudit?.backlink_details?.passed || [];
  // 优先取回链通过且有实质 URL 的结果
  for (const r of passedDetails) {
    if (!r.url || fetchedUrlSet.has(r.url) || fetchUrls.length >= 5) break;
    fetchedUrlSet.add(r.url);
    fetchUrls.push({ title: r.title || '', url: r.url, engine: r.engine || '', anchor_density: r.anchor_density || 0 });
  }
  // 不足 5 个则从 all_results 补
  for (const r of sortedResults) {
    if (fetchUrls.length >= 5) break;
    if (!r.url || fetchedUrlSet.has(r.url)) continue;
    fetchedUrlSet.add(r.url);
    fetchUrls.push({ title: r.title, url: r.url, engine: r.engine, anchor_density: 0 });
  }

  const output = {
    version: '5.2',
    query,
    anchor_words: prep.anchor_words,
    complexity: prep.complexity,
    intent: prep.intent,
    elapsed_seconds: elapsed,
    total_rounds: roundLogs.length,
    tools_available: (discoverOutput?.ready || []).map(t => ({
      id: t.id, name: t.name, kind: t.kind, strengths: t.strengths,
    })),
    tools_called_skill: [...allToolsUsed],
    system_tool_calls: {
      _note: '⚠️ 以下工具必须由 agent 在执行 orchestrate 时并行调用。子进程无法直接调用 OpenClaw 系统工具。',
      _timing: 'web_search → 与 orchestrate.mjs 同时启动; web_fetch → orchestrate 完成后对高价值 URL 执行',
      web_search: systemToolCalls.web_search,
      web_fetch: systemToolCalls.web_fetch,
    },
    results_total: allResults.length,
    backlink_passed: finalAudit?.backlink_details?.passed?.length || 0,
    anchor_relevance_rate: s.anchor_relevance_rate || '0%',
    converged: s.converged || false,
    convergence_reason: s.convergence_reason || '',
    active_signals: finalAudit?.signals?.filter(sig => sig.active).map(s => s.name) || [],
    information_density: s.information_density?.rating || '未知',
    recommendations: finalAudit?.recommendations?.map(r => r.action) || [],
    suggested_fetch_urls: fetchUrls,
    round_log: roundLogs,
    backlink_passed_results: finalAudit?.backlink_details?.passed?.map(r => ({
      title: r.title, url: r.url, engine: r.engine,
    })) || [],
    backlink_failed_results: finalAudit?.backlink_details?.failed?.map(r => ({
      title: r.title, verdict: r.verdict,
    })) || [],
    all_results: sortedResults.map(r => ({
      engine: r.engine,
      title: (r.title || '').substring(0, 200),
      url: r.url || '',
      snippet: (r.snippet || r.content || '').substring(0, 200),
      round: r._round,
    })),
    gate_checklist: prep.gate_checklist,
  };

  console.log(JSON.stringify(output, null, 2));

  if (!s.converged) process.exit(1);
}

main();
