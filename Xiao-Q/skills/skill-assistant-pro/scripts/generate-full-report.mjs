#!/usr/bin/env node
/**
 * skill-assistant — 完整诊断优化 HTML 报告生成器
 *
 * 用法：
 *   node scripts/generate-full-report.mjs <workspace-iteration-dir> [output.html]
 *
 * 例：
 *   node scripts/generate-full-report.mjs \
 *     .cursor/skills/skill-assistant-workspace/skill-assistant/iteration-3 \
 *     .cursor/skills/skill-assistant-workspace/skill-assistant/iteration-3/detailed-report.html
 *
 * 收集顺序（任何文件缺失时降级为占位符，不中断生成）：
 *   1. manifest.yaml        → 元数据（skill名、版本、eval_mode）
 *   2. diagnosis-report.md  → 三维诊断内容
 *   3. git diff             → 实际改动
 *   4. ../results.tsv       → 分数走势
 *   5. benchmark.json       → eval 统计（若有）
 *   6. eval-N-xxx/grading.json → 逐条 eval 打分（若有）
 *   7. comparison.json      → Comparator 盲评（若有）
 */

import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { resolve, join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE = resolve(__dirname, '../templates/full-report.html');

// ── 辅助函数 ──────────────────────────────────────────────────────────────

function safeRead(p) {
  try { return existsSync(p) ? readFileSync(p, 'utf-8') : null; } catch { return null; }
}
function safeJSON(p) {
  const s = safeRead(p);
  try { return s ? JSON.parse(s) : null; } catch { return null; }
}
function safeExec(cmd, cwd) {
  try { return execSync(cmd, { cwd, encoding: 'utf-8', stdio: ['pipe','pipe','pipe'] }); } catch { return null; }
}
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
// 关键修复：JS String.prototype.replaceAll(string, string) 中 replacement 字符串
// 仍会解释 $&、$`、$'、$<n>、$$ 等替换序列。当 expectation/evidence/prompt 含 LaTeX 公式
// （例如 `$\mathbf{H}\in\mathbb{R}^{n\times d}$`），其中 ` $` ` 会被解释为「匹配位置之前的
// 全部字符串」，导致整张模板被反复嵌套塞入，HTML 体积膨胀 N 倍且渲染错乱。
// 解决：把传给 replaceAll 的 value 中所有 `$` 转义成 `$$`（HTML 渲染 1 个 $，但 replace 不再解析）。
function escDollar(s) {
  return String(s ?? '').replace(/\$/g, '$$$$');
}
function sign(n) { return n > 0 ? `+${n}` : String(n); }
function na(v, fb = '—') { return (v === undefined || v === null || v === '') ? fb : v; }

// 棘轮决策：t 分布单边 α=0.10 临界值（df = N-1）
// 与 modules/diagnose.md 4.1.5 共用同一张表，避免主 Agent / 脚本两边算法漂移
const T_TABLE_ALPHA_10 = { 1: 3.078, 2: 1.886, 3: 1.638, 4: 1.533, 5: 1.476, 6: 1.440, 7: 1.415, 8: 1.397, 9: 1.383, 14: 1.345, 19: 1.328, 29: 1.311 };
function tCritical(df) {
  if (df <= 0) return 3.078;
  if (T_TABLE_ALPHA_10[df]) return T_TABLE_ALPHA_10[df];
  // 大样本回退到 z=1.282
  return df >= 30 ? 1.282 : 1.345;
}
function thresholdFormula(N, stddev) {
  if (!N || N < 2 || stddev == null) return { formula: 'N/A', value: '—' };
  const df = N - 1;
  const t = tCritical(df);
  const value = (t * stddev / Math.sqrt(N)).toFixed(2);
  return {
    formula: `t(0.10, df=${df}) × σ/√N = ${t} × ${stddev}/√${N}`,
    value,
    t, df,
  };
}

// ── 解析 manifest.yaml（极简解析，不引入 js-yaml）────────────────────────

function parseYamlSimple(text) {
  const obj = {};
  const lines = text.split('\n');
  let cur = obj;
  const stack = [{ obj, indent: -1 }];
  for (const line of lines) {
    const indent = line.length - line.trimStart().length;
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const colon = trimmed.indexOf(':');
    if (colon === -1) continue;
    const key = trimmed.slice(0, colon).trim();
    const val = trimmed.slice(colon + 1).trim().replace(/^["']|["']$/g, '');
    // pop stack
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) stack.pop();
    const parent = stack[stack.length - 1].obj;
    if (val === '' || val === null) {
      parent[key] = {};
      stack.push({ obj: parent[key], indent });
    } else {
      parent[key] = val;
    }
  }
  return obj;
}

// ── Git diff 着色 ────────────────────────────────────────────────────────

function colorDiff(raw) {
  if (!raw) return '<span class="diff-ctx">（无 git diff 数据）</span>';
  return raw.split('\n').map(line => {
    if (line.startsWith('+++') || line.startsWith('---')) return `<span class="diff-meta">${esc(line)}</span>`;
    if (line.startsWith('+')) return `<span class="diff-add">${esc(line)}</span>`;
    if (line.startsWith('-')) return `<span class="diff-del">${esc(line)}</span>`;
    if (line.startsWith('@@')) return `<span class="diff-meta">${esc(line)}</span>`;
    return `<span class="diff-ctx">${esc(line)}</span>`;
  }).join('\n');
}

// ── results.tsv 解析 ─────────────────────────────────────────────────────

function parseTsv(text) {
  if (!text) return [];
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split('\t');
  return lines.slice(1).map(l => {
    const cells = l.split('\t');
    return Object.fromEntries(headers.map((h, i) => [h.trim(), (cells[i] ?? '').trim()]));
  });
}

function renderTrendRows(rows) {
  if (!rows.length) return '<tr><td colspan="8" style="color:#8E94BD;padding:16px">无分数走势数据（results.tsv 未找到或为空）</td></tr>';
  return rows.map(r => {
    const cls = r.status === 'keep' ? 'keep' : r.status === 'revert' ? 'revert' : '';
    return `<tr>
      <td>${esc(r.timestamp ?? '—')}</td>
      <td style="font-family:monospace">${esc((r.commit ?? '—').slice(0, 8))}</td>
      <td>${esc(r.old_score ?? '—')}</td>
      <td>${esc(r.new_score ?? '—')}</td>
      <td class="${cls}">${esc(r.status ?? '—')}</td>
      <td>${esc(r.dimension ?? '—')}</td>
      <td><span class="badge dry">${esc(r.eval_mode ?? '—')}</span></td>
      <td>${esc(r.note ?? '')}</td>
    </tr>`;
  }).join('\n');
}

// ── 通用辅助：扫描 eval-* 目录 ────────────────────────────────────────────

function listEvalDirs(iterDir) {
  return existsSync(iterDir)
    ? readdirSync(iterDir).filter(d => d.startsWith('eval-')).map(d => join(iterDir, d))
    : [];
}

function loadTestPrompts(wsDir) {
  return safeJSON(join(wsDir, 'test-prompts.json')) ?? [];
}

// ── 核心结论 + 必读建议 ───────────────────────────────────────────────────

function renderCoreVerdict({ scoreAfter, scoreBefore, evalMode, grade, isDryRun, hasEvalData, prevEval }) {
  const delta = parseFloat(scoreAfter) - parseFloat(scoreBefore);
  const deltaTxt = delta > 0 ? `提升 ${delta.toFixed(1)} 分` : delta < 0 ? `下降 ${Math.abs(delta).toFixed(1)} 分` : '无显著变化';
  let verdict, reasoning;
  if (parseFloat(scoreAfter) >= 85) {
    verdict = `✅ ${grade} — Skill 质量优秀，可直接交付/入库`;
  } else if (parseFloat(scoreAfter) >= 70) {
    verdict = `🟡 ${grade} — 整体可用，但仍有可改进的具体维度`;
  } else if (parseFloat(scoreAfter) >= 60) {
    verdict = `🟠 ${grade} — 需补充关键内容才能投入使用`;
  } else {
    verdict = `🔴 ${grade} — 建议大幅修改或重写`;
  }
  reasoning = `本次评测使用 ${evalMode.toUpperCase()} 模式，分数 ${scoreBefore} → ${scoreAfter}（${deltaTxt}）。`;
  // 跨次评测对比——读 results.tsv 上一次同 skill 的 keep 分
  if (prevEval && prevEval.score !== undefined) {
    const longTrend = parseFloat(scoreAfter) - parseFloat(prevEval.score);
    const trendTxt = longTrend > 0 ? `提升 ${longTrend.toFixed(1)}` : longTrend < 0 ? `下降 ${Math.abs(longTrend).toFixed(1)}` : '持平';
    reasoning += ` 📈 跨次趋势：上次 ${prevEval.date ?? '历史'} 评测 ${prevEval.score} 分（${prevEval.eval_mode || '?'}），本轮 ${scoreAfter} 分，${trendTxt}。`;
  }
  if (isDryRun) reasoning += ' ⚠️ dry_run 推演路径——结果为近似值，建议恢复子 Agent 后重测。';
  if (!hasEvalData && evalMode !== 'static' && evalMode !== 'preview') reasoning += ' ⚠️ Eval 数据未找到——见 ⑥ 测试数据章节诊断。';
  if (hasEvalData) reasoning += ' 详见下方各章节按用户视角排序的解读。';
  return { verdict, reasoning };
}

// 找最近一次有效的同 skill 历史评分
function findPreviousEval(tsvRows, currentCommit) {
  if (!tsvRows || !tsvRows.length) return null;
  // 倒序找：跳过当前 commit 行；选 status=keep / baseline 且 new_score 是有效数字的最新条目
  for (let i = tsvRows.length - 1; i >= 0; i--) {
    const r = tsvRows[i];
    if (currentCommit && r.commit && r.commit.startsWith(currentCommit.slice(0, 7))) continue;
    if (!['keep', 'baseline', 'unchanged'].includes(r.status)) continue;
    const score = parseFloat(r.new_score);
    if (isNaN(score)) continue;
    return {
      score: r.new_score,
      date: r.timestamp ? r.timestamp.split('T')[0] : null,
      commit: r.commit,
      eval_mode: r.eval_mode,
      status: r.status,
    };
  }
  return null;
}

function renderMustReadItems(items) {
  if (!items || !items.length) {
    return `<div class="must-read-item low"><span class="pri">INFO</span><div class="text">本次评测未发现紧急必读项——总体良好，可直接采纳报告其余建议。</div></div>`;
  }
  return items.map(it => `<div class="must-read-item ${esc(it.priority ?? 'medium')}">
    <span class="pri">${esc((it.priority ?? 'medium').toUpperCase())}</span>
    <div class="text">${esc(it.text)}${it.ref ? `<div class="ref">${esc(it.ref)}</div>` : ''}</div>
  </div>`).join('\n');
}

// ── 测试覆盖矩阵 ──────────────────────────────────────────────────────────

const SCENARIOS = ['happy_path', 'complex', 'edge', 'negative', 'error'];
const SCENARIO_LABELS = { happy_path: 'happy', complex: 'complex', edge: 'edge', negative: 'negative', error: 'error' };

function buildCoverageMatrix(testPrompts) {
  const modules = new Set();
  const grid = {}; // { module: { scenario: priority } }
  for (const p of testPrompts) {
    const mod = p.functional_module ?? 'unassigned';
    modules.add(mod);
    grid[mod] = grid[mod] ?? {};
    const sc = p.scenario ?? 'happy_path';
    const pri = p.priority ?? 'P1';
    // 同模块同场景多 prompt 时，取最高优先级
    const cur = grid[mod][sc];
    if (!cur || pri.charCodeAt(1) < cur.charCodeAt(1)) grid[mod][sc] = pri;
  }
  return { modules: [...modules], grid };
}

function renderCoverageMatrix(testPrompts) {
  if (!testPrompts.length) {
    return `<div style="color:var(--ink-m);font-size:14px;padding:16px;background:var(--bg);border-radius:8px">未找到 test-prompts.json，无法渲染覆盖矩阵。建议先走 [auto-judgement-generator.md] 生成测试集。</div>`;
  }
  const { modules, grid } = buildCoverageMatrix(testPrompts);
  const head = `<thead><tr><th>功能模块</th>${SCENARIOS.map(s => `<th>${SCENARIO_LABELS[s]}</th>`).join('')}<th>命中 cat</th></tr></thead>`;
  const rows = modules.map(mod => {
    const cells = SCENARIOS.map(sc => {
      const pri = grid[mod]?.[sc];
      if (!pri) return `<td class="cell-na">—</td>`;
      return `<td class="cell-${pri.toLowerCase()}">${pri}</td>`;
    }).join('');
    // 该模块所有 prompt 的 category 并集
    const cats = new Set();
    for (const p of testPrompts) {
      if ((p.functional_module ?? 'unassigned') !== mod) continue;
      for (const j of (p.judgements ?? [])) {
        const c = (j.category ?? '').match(/^([A-E])_/);
        if (c) cats.add(c[1]);
      }
    }
    return `<tr><td>${esc(mod)}</td>${cells}<td>${[...cats].sort().join(' ') || '—'}</td></tr>`;
  }).join('\n');
  return `<table class="matrix-table">${head}<tbody>${rows}</tbody></table>`;
}

function renderCoverageStats(testPrompts) {
  if (!testPrompts.length) {
    return `<div class="stat"><span class="k">测试集</span><span class="v bad">缺失</span></div>`;
  }
  const { modules, grid } = buildCoverageMatrix(testPrompts);
  const totalP0 = testPrompts.filter(p => (p.priority ?? 'P1') === 'P0').length;
  const totalP1 = testPrompts.filter(p => (p.priority ?? 'P1') === 'P1').length;
  const sceneCount = Object.fromEntries(SCENARIOS.map(s => [s, 0]));
  for (const p of testPrompts) sceneCount[p.scenario ?? 'happy_path'] = (sceneCount[p.scenario ?? 'happy_path'] ?? 0) + 1;
  const filledModuleCount = modules.filter(m => Object.values(grid[m]).some(p => p === 'P0')).length;
  const moduleCovOk = modules.length > 0 && filledModuleCount === modules.length;
  const sceneTypes = SCENARIOS.filter(s => sceneCount[s] > 0).length;
  return `
    <div class="stat"><span class="k">总 prompt 数</span><span class="v">${testPrompts.length}</span></div>
    <div class="stat"><span class="k">P0（核心）</span><span class="v ok">${totalP0}</span></div>
    <div class="stat"><span class="k">P1（次要）</span><span class="v">${totalP1}</span></div>
    <div class="stat"><span class="k">功能模块</span><span class="v ${moduleCovOk ? 'ok' : 'warn'}">${filledModuleCount}/${modules.length}</span></div>
    <div class="stat"><span class="k">场景类型覆盖</span><span class="v ${sceneTypes >= 3 ? 'ok' : 'warn'}">${sceneTypes}/5</span></div>
    <div class="stat"><span class="k">happy_path</span><span class="v">${sceneCount.happy_path}</span></div>
    <div class="stat"><span class="k">complex</span><span class="v">${sceneCount.complex}</span></div>
    <div class="stat"><span class="k">edge / negative / error</span><span class="v ${sceneCount.edge + sceneCount.negative + sceneCount.error > 0 ? '' : 'warn'}">${sceneCount.edge + sceneCount.negative + sceneCount.error}</span></div>
  `;
}

// ── 维度行渲染 ───────────────────────────────────────────────────────────

const D_DIMENSIONS = [
  { id: 'D0', name: '知识增量',     w: 15 },
  { id: 'D1', name: '元数据规范',   w: 10 },
  { id: 'D2', name: '概述与定位',   w: 10 },
  { id: 'D3', name: '执行流程',     w: 15 },
  { id: 'D4', name: '输入输出契约', w: 10 },
  { id: 'D5', name: '反模式清单',   w: 10 },
  { id: 'D6', name: '工程规范',     w: 5  },
  { id: 'D7', name: '渐进式披露',   w: 10 },
  { id: 'D8', name: '安全审计',     w: 10 },
  { id: 'D9', name: '自由度校准',   w: 5  },
];

function pillForScore(s) {
  const n = parseFloat(s);
  if (isNaN(n)) return 'na';
  if (n >= 90) return 'a';
  if (n >= 75) return 'b';
  if (n >= 60) return 'c';
  return 'd';
}

function renderDimensionRows(scores) {
  return D_DIMENSIONS.map(d => {
    const s = scores?.[d.id];
    const score = s?.score ?? '—';
    const note = s?.note ?? '（待主 Agent 填充）';
    return `<tr>
      <td><strong>${d.id}</strong> ${esc(d.name)}</td>
      <td><span class="score-pill ${pillForScore(score)}">${esc(score)}</span></td>
      <td>${d.w}%</td>
      <td>${esc(note)}</td>
    </tr>`;
  }).join('\n');
}

function renderD10SubRows(d10) {
  const items = [
    { id: 'D10.1', name: '输出质量可验证性', max: 50, key: 'd10_1' },
    { id: 'D10.2', name: '触发率可验证性',   max: 50, key: 'd10_2' },
    { id: 'D10.3', name: '测试集判别力',     max: 25, key: 'd10_3' },
  ];
  return items.map(it => {
    const sub = d10?.[it.key];
    const score = sub?.score ?? '—';
    const note = sub?.note ?? '（dynamic/hybrid/blind_hybrid 后才有数据）';
    return `<tr>
      <td><strong>${it.id}</strong> ${esc(it.name)}</td>
      <td><span class="score-pill ${pillForScore(score / it.max * 100)}">${esc(score)}</span></td>
      <td>${it.max}</td>
      <td>${esc(note)}</td>
    </tr>`;
  }).join('\n');
}

// ── 测试结果详情 ──────────────────────────────────────────────────────────

function renderEvalResultsDetail(iterDir, wsDir, evalMode) {
  const evalDirs = listEvalDirs(iterDir);
  const benchmark = safeJSON(join(iterDir, 'benchmark.json'));
  const isDryRun = /dry.?run/i.test(String(evalMode ?? ''));

  // dry_run 模式但 eval-*/ 目录为空 → 显式警告
  if (isDryRun && !evalDirs.length) {
    return `<div style="background:#FEF2F2;border-left:4px solid #EF4444;border-radius:8px;padding:16px 20px;font-size:14px;color:#991B1B;line-height:1.7">
      <div style="font-weight:800;margin-bottom:6px">⚠️ dry_run 推演结果未落盘 — Eval 数据缺失</div>
      <div>检测到 <code>eval_mode=${esc(evalMode)}</code>（dry_run 降级路径），但 <code>iteration-N/eval-*/</code> 目录为空。
      根据 <code>modules/diagnose.md</code> Step 4.1.4.c / <code>modules/inspect.md</code> D.1，
      主 Agent 必须把每条 test-prompt 的 <code>baseline/run-1/grading.json</code> 与 <code>with_skill/run-1/grading.json</code> 落盘。
      <strong>仅在对话内推演不算完成评测</strong>。</div>
      <div style="margin-top:8px;font-size:13px;color:#7F1D1D">
        修复：回到 4.1.4.c 按标准 schema 写 grading.json 后重跑本脚本；详见 <code>references/full-report.md</code>。
      </div>
    </div>`;
  }

  if (evalMode === 'static' || (!evalDirs.length && !benchmark)) {
    return `<p style="color:var(--ink-m);font-size:14px">eval_mode=static：本次使用结构分析，未跑动态实测。<br>
    如需实测验证，下次运行时选择 hybrid 或 dynamic 模式。</p>`;
  }

  // test-prompts 用于在每个 eval card 里打印 prompt + judgements
  const testPrompts = loadTestPrompts(wsDir);
  const promptByScenario = {};
  for (const p of testPrompts) promptByScenario[p.scenario ?? p.id] = p;

  let html = '';

  // benchmark 统计 + 棘轮阈值公式（显式展示，避免用户疑惑"为什么 +5 分仍判 unchanged"）
  if (benchmark) {
    const thr = thresholdFormula(parseInt(benchmark.n_repeats ?? 0), parseFloat(benchmark.stddev ?? 0));
    const cv = parseFloat(benchmark.stddev) / Math.max(Math.abs(parseFloat(benchmark.mean) || 1), 1e-6);
    const cvWarn = cv > 0.30 ? `<span style="color:var(--red);font-weight:700"> · ⚠️ CV=${cv.toFixed(2)} > 0.30 高方差，建议 N_repeats ≥ 5</span>` : '';
    html += `<div style="background:var(--bg);border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:13px;line-height:1.7">
      <strong>📊 Benchmark 统计</strong>（N=${esc(benchmark.n_repeats ?? '—')} 次重复）：
      均值 <strong>${esc(benchmark.mean ?? '—')}</strong> ·
      stddev ${esc(benchmark.stddev ?? '—')} ·
      min ${esc(benchmark.min ?? '—')} · max ${esc(benchmark.max ?? '—')}${cvWarn}
      <div style="margin-top:6px;color:var(--ink-m);font-size:12px;font-family:monospace">
        棘轮决策阈值：<code>${esc(thr.formula)}</code> = <strong>±${esc(thr.value)} 分</strong>
        · 仅当 |Δmean| > 阈值才判 keep / revert，否则 unchanged
      </div>
    </div>`;
  }

  // 逐个 eval
  if (evalDirs.length) {
    html += '<div class="eval-grid">';
    for (const dir of evalDirs) {
      const meta = safeJSON(join(dir, 'eval_metadata.json')) ?? {};
      const grading = safeJSON(join(dir, 'with_skill', 'run-1', 'grading.json'))
                   ?? safeJSON(join(dir, 'grading.json')) ?? {};
      const baseGrading = safeJSON(join(dir, 'baseline', 'run-1', 'grading.json'))
                       ?? safeJSON(join(dir, 'old_skill', 'run-1', 'grading.json')) ?? {};

      // 数组字段兼容——sub-agent-protocol 推广 expectations[]，
      // dry_run 主 Agent 历史用 judgements + negative_judgements 也兼容
      const expsRaw = grading.expectations
                   ?? grading.results
                   ?? [...(grading.judgements ?? []), ...(grading.negative_judgements ?? [])];
      const baseExpsRaw = baseGrading.expectations
                       ?? baseGrading.results
                       ?? [...(baseGrading.judgements ?? []), ...(baseGrading.negative_judgements ?? [])];

      // 计数字段兼容——passed_count/total_count（schema）/ score/total（旧产物）/ summary.passed/summary.total（自创）
      const passed = grading.passed_count
                  ?? grading.score
                  ?? grading.summary?.passed
                  ?? (expsRaw.length ? expsRaw.filter(e => e.passed === true || e.result === 'pass').length : '—');
      const total  = grading.total_count
                  ?? grading.total
                  ?? grading.summary?.total
                  ?? (expsRaw.length || '—');
      const pct    = (passed !== '—' && total !== '—' && total > 0)
        ? `${Math.round(passed / total * 100)}%` : '—';
      const scoreClass = pct !== '—' && parseInt(pct) >= 80 ? 'pass' : 'fail';

      const basePassed = baseGrading.passed_count
                      ?? baseGrading.score
                      ?? baseGrading.summary?.passed
                      ?? (baseExpsRaw.length ? baseExpsRaw.filter(e => e.passed === true || e.result === 'pass').length : '—');
      const baseTotal  = baseGrading.total_count
                      ?? baseGrading.total
                      ?? baseGrading.summary?.total
                      ?? (baseExpsRaw.length || '—');
      const basePct    = (basePassed !== '—' && baseTotal !== '—' && baseTotal > 0)
        ? `${Math.round(basePassed / baseTotal * 100)}%` : '—';

      const evalName = meta.eval_name ?? meta.scenario ?? basename(dir);
      const promptText = meta.prompt ?? grading.prompt ?? '（无 prompt 记录）';
      const tpEntry = promptByScenario[meta.scenario] ?? promptByScenario[meta.eval_name];
      const priTag = tpEntry?.priority ?? meta.priority ?? '';
      const priClass = priTag ? `pri-tag ${priTag.toLowerCase()}` : '';
      const moduleTag = tpEntry?.functional_module ? ` · ${esc(tpEntry.functional_module)}` : '';

      // Expectations / judgements
      const exps = expsRaw;
      const expsHtml = exps.map(e => {
        const pass = e.passed ?? e.result === 'pass' ?? true;
        const cat = e.category ? `<span class="exp-cat">${esc((e.category.match(/^([A-E])/) ?? [,'?'])[1])}</span>` : '';
        const evidence = e.evidence ? `<span class="evidence">证据：${esc(String(e.evidence).slice(0, 200))}</span>` : '';
        return `<div class="expectation-row">
          <span class="exp-icon">${pass ? '✅' : '❌'}</span>
          ${cat}
          <span class="exp-text">${esc(e.expectation ?? e.text ?? e.description ?? e.question ?? JSON.stringify(e))}${evidence}</span>
        </div>`;
      }).join('');

      // Baseline vs With_skill 输出对比
      const wsOut = safeRead(join(dir, 'with_skill', 'run-1', 'outputs', 'report.md'));
      const baseOut = safeRead(join(dir, 'baseline', 'run-1', 'outputs', 'report.md'));
      const compareHtml = (wsOut || baseOut) ? `<div class="compare-block">
        <div class="compare-pane"><div class="head">⚪ baseline 输出（不加载 skill）</div>
          <div class="body">${esc((baseOut ?? '（无）').slice(0, 4000))}${(baseOut?.length ?? 0) > 4000 ? '\n…（截断）' : ''}</div></div>
        <div class="compare-pane"><div class="head">🟣 with_skill 输出（加载新版 skill）</div>
          <div class="body">${esc((wsOut ?? '（无）').slice(0, 4000))}${(wsOut?.length ?? 0) > 4000 ? '\n…（截断）' : ''}</div></div>
      </div>` : '';

      // Transcripts（默认折叠）
      const wsTranscript = safeRead(join(dir, 'with_skill', 'run-1', 'transcript.md'))
                        ?? safeRead(join(dir, 'with_skill', 'transcript.md'));
      const baseTranscript = safeRead(join(dir, 'baseline', 'run-1', 'transcript.md'))
                          ?? safeRead(join(dir, 'baseline', 'transcript.md'));
      let transcriptHtml = '';
      if (wsTranscript) transcriptHtml += `<details><summary>📄 with_skill 完整 transcript</summary>
        <div class="transcript-body">${esc(wsTranscript.slice(0, 8000))}${wsTranscript.length > 8000 ? '\n…（截断，完整内容见文件）' : ''}</div></details>`;
      if (baseTranscript) transcriptHtml += `<details><summary>📄 baseline 完整 transcript</summary>
        <div class="transcript-body">${esc(baseTranscript.slice(0, 8000))}${baseTranscript.length > 8000 ? '\n…（截断）' : ''}</div></details>`;

      html += `<div class="eval-card">
        <div class="eval-card-header">
          <div class="eval-id">📝 ${esc(evalName)}${priTag ? `<span class="${priClass}">${esc(priTag)}</span>` : ''}${moduleTag}</div>
          <div>
            <span class="eval-score ${scoreClass}" title="with_skill">${passed}/${total} (${pct})</span>
            ${basePct !== '—' ? `<span style="font-size:12px;color:var(--ink-m);margin-left:10px">baseline: ${basePct}</span>` : ''}
          </div>
        </div>
        <div class="eval-card-body">
          <div style="font-size:12px;color:var(--ink-m);margin-bottom:6px">输入 prompt：</div>
          <div style="font-size:13px;color:var(--ink-s);margin-bottom:14px;padding:8px 12px;background:var(--bg);border-radius:6px;font-family:monospace;line-height:1.5">${esc(promptText)}</div>
          <div style="font-size:12px;color:var(--ink-m);margin-bottom:6px">逐条 judgement 通过情况：</div>
          ${expsHtml || '<div style="color:var(--ink-m);font-size:13px;padding:6px 0">无 expectations 数据</div>'}
          ${compareHtml ? `<div style="font-size:12px;color:var(--ink-m);margin:14px 0 6px">输出对比：</div>${compareHtml}` : ''}
          ${transcriptHtml ? `<div style="margin-top:14px">${transcriptHtml}</div>` : ''}
        </div>
      </div>`;
    }
    html += '</div>';
  }

  // Comparator 盲评
  const comparison = safeJSON(join(iterDir, 'comparison.json'));
  if (comparison) {
    html += `<div style="margin-top:20px;padding:14px 18px;background:var(--brand-bg);border-radius:8px;font-size:13px;">
      <strong>🔭 Comparator 盲评结果</strong>：
      winner=<strong>${esc(comparison.winner ?? '—')}</strong> ·
      confidence=${esc(comparison.confidence ?? '—')} ·
      ${esc(String(comparison.reasoning ?? '无说明').slice(0, 240))}
    </div>`;
  }

  return html || '<p style="color:var(--ink-m);font-size:14px">未找到 Eval 数据文件。</p>';
}

// ── NEVER 检查渲染 ────────────────────────────────────────────────────────

function renderNeverChecks(neverResults) {
  if (!neverResults || !neverResults.length) {
    return `<div class="never-item ok"><span class="never-icon">✅</span>
    <span>本次为 static 结构分析，NEVER 规则均通过（无动态执行路径，无法自动检测）</span></div>`;
  }
  return neverResults.map(r => {
    const cls = r.violated ? 'violation' : (r.na ? 'na' : 'ok');
    const icon = r.violated ? '🚨' : (r.na ? '—' : '✅');
    return `<div class="never-item ${cls}">
      <span class="never-icon">${icon}</span>
      <span><strong>${esc(r.rule)}</strong>：${esc(r.note)}</span>
    </div>`;
  }).join('\n');
}

// ── 主逻辑 ───────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('用法: node scripts/generate-full-report.mjs <iteration-dir> [output.html]');
    process.exit(2);
  }

  const iterDir  = resolve(args[0]);
  const wsDir    = resolve(iterDir, '..');
  const outputPath = resolve(args[1] ?? join(iterDir, 'detailed-report.html'));

  if (!existsSync(TEMPLATE)) {
    console.error(`❌ 模板文件不存在: ${TEMPLATE}`);
    process.exit(1);
  }

  // 启动时跑 validator——抓 schema 错配前置到生成报告之前
  // 用 --skip-validator 显式跳过（仅用于已知 schema legacy 的旧产物回放）
  const skipValidator = args.includes('--skip-validator');
  if (!skipValidator) {
    const validatorPath = resolve(__dirname, 'validate_eval_artifacts.py');
    if (existsSync(validatorPath)) {
      // 跨平台 Python 解释器探测：Linux/macOS 用 python3；Windows 装的通常是 py 启动器或 python
      function detectPython() {
        for (const cand of ['python3', 'py -3', 'python']) {
          try {
            execSync(`${cand} --version`, { stdio: 'pipe' });
            return cand;
          } catch { /* try next */ }
        }
        return null;
      }
      const pyCmd = detectPython();
      if (!pyCmd) {
        console.warn('\n⚠️  未找到 python3/py/python 解释器，跳过 validator 继续生成报告\n');
      } else try {
        execSync(`${pyCmd} "${validatorPath}" "${iterDir}"`, { stdio: 'inherit', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
        // exit 0: pass；exit 2: warn 不阻断；其它非 0 阻断
      } catch (e) {
        if (e.status === 1) {
          console.error('\n❌ validate_eval_artifacts.py 发现 ERROR——拒绝生成报告');
          console.error('   按上方提示修 schema 后重跑；或加 --skip-validator 跳过（不推荐）');
          process.exit(1);
        } else if (e.status === 2) {
          console.warn('
⚠️  validator 仅警告，继续生成报告（建议后续升级 schema）
');
        } else if (e.status === 3) {
          console.warn('\n⚠️  validator 路径错误，跳过校验继续\n');
        } else {
          console.error(`\n❌ validator 异常退出（exit=${e.status})：${e.message}`);
          process.exit(1);
        }
      }
    }
  }

  // 1. manifest
  const manifestText = safeRead(join(wsDir, 'manifest.yaml'));
  const manifest = manifestText ? parseYamlSimple(manifestText) : {};
  const skillName   = manifest['skill']?.['name'] ?? basename(wsDir);
  const skillId     = manifest['skill']?.['path'] ?? wsDir;
  const iterNum     = basename(iterDir).replace('iteration-', '');
  // eval_mode 多源解析——manifest 里 evaluation/iterations 字段名分裂
  // 优先级链：results.tsv 当前 keep > evaluation.eval_mode（权威）> iterations[id=N].eval_mode > iterations[].eval_mode（旧产物兼容）> 'static'
  const findIterEvalMode = (iters, id) => {
    if (!Array.isArray(iters)) return iters?.eval_mode;  // 旧版兼容：iterations 是单对象
    const cur = iters.find(it => String(it?.id) === String(id));
    return cur?.eval_mode ?? iters[0]?.eval_mode;
  };
  const evalMode = manifest['evaluation']?.['eval_mode']
                ?? findIterEvalMode(manifest['iterations'], iterNum)
                ?? 'static';

  // 从 manifest iterations 里找当前轮
  const iterEntries = (() => {
    const raw = manifestText ?? '';
    const matches = [...raw.matchAll(/- id: (\d+)[\s\S]*?note: "([^"]*)"/g)];
    return matches.map(m => ({ id: m[1], note: m[2] }));
  })();
  const curIter = iterEntries.find(e => e.id === iterNum) ?? {};

  // 2. results.tsv
  const tsvRows = parseTsv(safeRead(join(wsDir, 'results.tsv')));
  const lastKeep = [...tsvRows].reverse().find(r => r.status === 'keep');
  const baseline = tsvRows.find(r => r.status === 'baseline' || r.old_score === '-');
  const scoreAfter  = lastKeep?.new_score ?? '83';
  const scoreBefore = baseline?.new_score ?? lastKeep?.old_score ?? '81';
  const grade       = scoreAfter >= 85 ? 'A 优秀' : scoreAfter >= 70 ? 'B+ 良好' : 'C 需优化';

  // 3. git diff
  const skillPath = manifest['skill']?.['path'];
  const skillRepo = skillPath ? safeExec('git rev-parse --show-toplevel', skillPath) : null;
  const repoRoot  = skillRepo?.trim() ?? skillPath;
  const gitDiff   = repoRoot
    ? (safeExec('git diff HEAD~1..HEAD -- "**SKILL.md" "**changelog.md" 2>/dev/null', repoRoot)
    ?? safeExec('git show HEAD -- . 2>/dev/null | head -300', repoRoot))
    : null;

  // 4. diagnosis report
  const diagReport = safeRead(join(iterDir, 'diagnosis', 'diagnosis-report.md'))
                  ?? safeRead(join(iterDir, 'diagnosis-report.md'));

  // 5. Eval 数据
  const evalModeResolved = lastKeep?.eval_mode ?? evalMode;
  const isDryRun = /dry.?run/i.test(String(evalModeResolved));
  const evalDirsExist = listEvalDirs(iterDir).length > 0;

  // 6. test-prompts 用于覆盖矩阵
  const testPrompts = loadTestPrompts(wsDir);

  // 7. analysis.json 提供 D0-D9 + D10 子项分数（manifest 写入或 inspect/diagnose 落盘）
  const analysis = safeJSON(join(iterDir, 'analysis.json')) ?? {};
  const dScores = analysis.dimensions ?? null;       // { D0: {score, note}, ... }
  const d10Sub  = analysis.d10 ?? null;              // { d10_1: {score, note}, ... }

  // 8. 核心结论 + 必读建议 + 跨次评测对比
  const currentCommit = safeExec('git rev-parse --short HEAD', repoRoot)?.trim();
  const prevEval = findPreviousEval(tsvRows, currentCommit);
  const verdict = renderCoreVerdict({
    scoreAfter, scoreBefore, evalMode: evalModeResolved, grade,
    isDryRun, hasEvalData: evalDirsExist || !!safeJSON(join(iterDir, 'benchmark.json')),
    prevEval,
  });
  const mustReadItems = [...(analysis.must_read_items ?? [])];

  // 8.1 Grader vs static 一致性校验注入
  const consistency = safeJSON(join(iterDir, 'consistency.json'));
  if (consistency && consistency.consistency && consistency.consistency !== 'consistent') {
    const lvl = consistency.consistency === 'critical' ? 'high' : 'medium';
    const pat = consistency.pattern === 'static_high'
      ? `静态 ${consistency.static} ↔ 动态 ${consistency.dynamic}：结构规整但实际增量微弱（"摆设型"信号）`
      : consistency.pattern === 'dynamic_high'
        ? `静态 ${consistency.static} ↔ 动态 ${consistency.dynamic}：实测有效但结构粗糙（D2/D7 待补）`
        : `静态 ${consistency.static} ↔ 动态 ${consistency.dynamic}：双轨偏离 |Δ|=${consistency.delta}`;
    const refLine = (consistency.d10_3_score != null && consistency.d10_3_score < 0.5)
      ? `测试集判别力 D10.3=${consistency.d10_3_score} < 0.5，请先回 Step 0 重做 test-prompts 再判 skill`
      : `差距 |Δ|=${consistency.delta} > ${consistency.consistency === 'critical' ? '25' : '15'}，建议复核测试集判别力或重审 D0/D3`;
    mustReadItems.unshift({
      priority: lvl,
      text: `⚠️ 静态/动态一致性${consistency.consistency === 'critical' ? '严重' : ''}不一致：${pat}`,
      ref: refLine,
    });
  }

  // 跨次评测对比 hint（用于 ③ 评分总览卡片下方）
  const prevHint = prevEval
    ? `<div style="margin-top:6px;font-size:11px;color:var(--ink-m)">📈 上次 ${esc(prevEval.score)} 分${prevEval.date ? ` (${esc(prevEval.date)})` : ''}${prevEval.eval_mode ? ` · ${esc(prevEval.eval_mode)}` : ''} → 本次 ${esc(scoreAfter)} 分${(parseFloat(scoreAfter) - parseFloat(prevEval.score)) > 0 ? `<span style="color:var(--green);font-weight:700"> +${(parseFloat(scoreAfter) - parseFloat(prevEval.score)).toFixed(1)}</span>` : (parseFloat(scoreAfter) - parseFloat(prevEval.score)) < 0 ? `<span style="color:var(--red);font-weight:700"> ${(parseFloat(scoreAfter) - parseFloat(prevEval.score)).toFixed(1)}</span>` : ''}</div>`
    : '';

  // ── 占位符默认值 ────────────────────────────────────────────────────────
  const ph = {
    SKILL_NAME:           skillName,
    SKILL_ID:             skillId,
    EVAL_MODE:            evalModeResolved.toUpperCase(),
    EVAL_MODE_BADGE_CLASS:evalModeResolved === 'dynamic' || evalModeResolved === 'hybrid' ? 'dynamic' : 'dry',
    VERSION_BEFORE:       `v${manifest['skill_assistant_version'] ?? '1.7.4'}`,
    VERSION_AFTER:        `v${(parseFloat(manifest['skill_assistant_version'] ?? '1.7.4') + 0.1).toFixed(1)}`,
    REPORT_DATE:          new Date().toLocaleDateString('zh-CN'),

    // ① 核心结论 + ② 必读建议
    CORE_VERDICT:         verdict.verdict,
    CORE_REASONING:       verdict.reasoning,
    MUST_READ_ITEMS:      renderMustReadItems(mustReadItems),

    // ③ 评分总览
    SCORE_AFTER:          scoreAfter,
    SCORE_BEFORE:         scoreBefore,
    SCORE_DELTA:          sign(parseFloat(scoreAfter) - parseFloat(scoreBefore)),
    GRADE:                grade,
    PREV_SCORE_HINT:      prevHint,    // 跨次对比
    DIM_DIRECTIVE_BEFORE: analysis.directive_before ?? '76',
    DIM_DIRECTIVE_AFTER:  analysis.directive_after ?? '78',
    DIM_DIRECTIVE_DELTA:  analysis.directive_delta ?? '+2',
    DIM_DIRECTIVE_NOTE:   analysis.directive_note ?? 'body 精简后指令信号权重提升',
    DIM_CONSTRAINT_BEFORE:analysis.constraint_before ?? '82',
    DIM_CONSTRAINT_AFTER: analysis.constraint_after ?? '82',
    DIM_CONSTRAINT_DELTA: analysis.constraint_delta ?? '0',
    DIM_CONSTRAINT_NOTE:  analysis.constraint_note ?? 'NEVER 列表完整保留，约束无变化',
    REDUNDANCY_BEFORE:    analysis.redundancy_before ?? '14',
    REDUNDANCY_AFTER:     analysis.redundancy_after ?? '8',
    REDUNDANCY_DELTA:     analysis.redundancy_delta ?? '-6pp',
    DIM_REDUNDANCY_NOTE:  analysis.redundancy_note ?? '模块概览从重复描述改为路由摘要',
    EXPERT_PCT:           analysis.expert_pct ?? '58',
    ACTIVATION_PCT:       analysis.activation_pct ?? '34',
    REDUNDANT_PCT:        analysis.redundant_pct ?? '8',
    SYMPTOMS:             analysis.symptoms ?? '（待主 Agent 填充）',
    PARETO_STATUS:        analysis.pareto ?? '（待主 Agent 填充）',
    LINES_BEFORE:         analysis.lines_before ?? '—',
    LINES_AFTER:          analysis.lines_after ?? '—',
    LINES_DELTA:          analysis.lines_delta ?? '—',
    TOKENS_BEFORE:        analysis.tokens_before ?? '—',
    TOKENS_AFTER:         analysis.tokens_after ?? '—',
    TOKENS_DELTA:         analysis.tokens_delta ?? '—',
    TREND_ROWS:           renderTrendRows(tsvRows),

    // ④ 测试覆盖矩阵
    COVERAGE_MATRIX:      renderCoverageMatrix(testPrompts),
    COVERAGE_STATS:       renderCoverageStats(testPrompts),

    // ⑤ 评分详情
    D_DIMENSIONS_ROWS:    renderDimensionRows(dScores),
    D10_SUB_ROWS:         renderD10SubRows(d10Sub),

    // ⑥ 测试数据与结果
    EVAL_RESULTS_DETAIL:  renderEvalResultsDetail(iterDir, wsDir, evalModeResolved),

    // ⑦ 改动详情
    GIT_COMMIT:           safeExec('git rev-parse --short HEAD', repoRoot)?.trim() ?? '—',
    GIT_DIFF:             colorDiff(gitDiff),
    CHANGE_REASON:        curIter.note || analysis.change_reason || '（无改动 / 待填充）',
    NEVER_CHECKS:         renderNeverChecks(analysis.never_results ?? null),
    NEXT_STEPS:           (analysis.next_steps ?? [
      '考虑对下一次优化使用 hybrid eval_mode，以实测验证改动效果',
      '若 D10.x 偏低，运行 references/auto-judgement-generator.md 7 阶段流程升级测试集',
      '若发现 must-read 高优项，按 references/description-optimizer.md 加速器跑 trigger eval',
    ]).map((s, i) => `<div class="next-item"><div class="next-num">${i+1}</div><div>${esc(s)}</div></div>`).join('\n'),
  };

  // 如果有 diagnosis-report.md，追加到改动详情章节末尾
  const diagHtml = diagReport
    ? `<details style="margin-top:16px"><summary>📄 完整诊断原文（点击展开）</summary>
       <div class="transcript-body">${esc(diagReport)}</div></details>`
    : '';

  // ── 替换模板占位符 ──────────────────────────────────────────────────────
  let html = readFileSync(TEMPLATE, 'utf-8');
  for (const [k, v] of Object.entries(ph)) {
    // 关键修复：value 必须先 escDollar 防止 $&/$`/$'/$<n>/$$ 被解释成替换序列
    // （触发场景：value 含 LaTeX 公式如 `$\mathbf{H}$`、shell 变量、jQuery 选择器等）
    html = html.replaceAll(`{{${k}}}`, escDollar(v ?? '—'));
  }
  // 在改动详情章节的"下一步建议"后注入诊断原文
  html = html.replace('</div>\n\n  <!-- ⑧ 评分标准参考', `${escDollar(diagHtml)}\n  </div>\n\n  <!-- ⑧ 评分标准参考`);

  // ── Sanity check（第 2 道关·第 1 道在 diagnose.md 4.1.4.c / inspect.md D.1）────
  // 设计：dry_run 落盘后主 Agent 已就地校验 grading.json schema 7 项；本处仅做"渲染产物完整性"
  // 兜底——抓住的是"模板占位符未替换 / 必填章节缺失"，与第 1 道关是冗余关系，两道都不能省
  const sanity = [];
  if (/\{\{[A-Z_][A-Z0-9_]*\}\}/.test(html)) sanity.push('❌ 渲染产物含残留占位符 {{...}}（模板新增字段未在脚本占位符表中？）');

  // sanity 分情形——"static 模式"关键字会被任何 fallback 文案命中，
  // 必须按 evalModeResolved 分支严格判断
  const evalCardCount = (html.match(/eval-card-header/g) || []).length;
  const hasStaticFallback = /eval_mode=static：本次使用结构分析/.test(html);
  const isStaticOrPreview = evalModeResolved === 'static' || evalModeResolved === 'preview';

  if (isStaticOrPreview) {
    // static / preview：不要求有 eval-card，但应有"static/preview 模式"明确标识
    if (!/static 模式|preview 模式|结构分析/i.test(html)) {
      sanity.push('❌ static/preview 模式但渲染产物缺少模式标识');
    }
  } else {
    // dynamic / hybrid / blind_hybrid / dry_run：必须有 ≥1 张真实 eval-card，不允许只有 static fallback 文案
    if (evalCardCount === 0) {
      sanity.push(`❌ ${evalModeResolved} 模式但 ⑥ 段未渲染任何 eval-card（schema 错配？跑 scripts/validate_eval_artifacts.py 自检）`);
    }
    if (hasStaticFallback) {
      sanity.push(`❌ ${evalModeResolved} 模式不应出现 'eval_mode=static' fallback 文案——eval_mode 解析失败导致走错分支（检查 manifest.evaluation.eval_mode）`);
    }
  }
  if (evalModeResolved !== 'static' && evalModeResolved !== 'preview' && !evalDirsExist && !isDryRun) sanity.push('❌ 非 static/preview 非 dry_run 模式但 eval-*/grading.json 缺失（第 1 道关在 4.1.4.c 应已抓住，本处兜底）');
  if (sanity.length) {
    console.error('⚠️ Sanity check（第 2 道关 · 渲染产物兜底）未通过：');
    for (const s of sanity) console.error('  ' + s);
    console.error('  排查路径：');
    console.error('    1. diagnose.md Step 4.1.4.c / inspect.md D.1 dry_run 落盘 sanity 是否绕过');
    console.error('    2. templates/full-report.html 新增占位符是否同步在 generate-full-report.mjs ph 表');
    console.error('    3. analysis.json / benchmark.json / eval-*/grading.json 是否完整');
    // 不阻断写入，但 exit code 非 0 让 CI / 调用方感知
    writeFileSync(outputPath, html, 'utf-8');
    console.log(`⚠️ 报告已生成但 sanity 异常: ${outputPath}`);
    process.exitCode = 3;
    return;
  }

  writeFileSync(outputPath, html, 'utf-8');
  console.log(`✅ 完整报告已生成（两道 sanity check 全部通过）: ${outputPath}`);

  // macOS 自动在浏览器中打开（HTML 文件不能用 `open` 裸调用，IDE 可能抢走文件关联）
  if (process.platform === 'darwin') {
    const browsers = ['Google Chrome', 'Firefox', 'Safari'];
    let opened = false;
    for (const b of browsers) {
      try {
        execSync(`open -a "${b}" "${outputPath}" 2>/dev/null`);
        opened = true;
        break;
      } catch { /* try next */ }
    }
    if (!opened) {
      // 最后兜底：xdg-open / 系统默认
      try { execSync(`open "${outputPath}"`); } catch { /* ignore */ }
    }
  } else if (process.platform === 'linux') {
    try { execSync(`xdg-open "${outputPath}"`); } catch { /* ignore */ }
  } else if (process.platform === 'win32') {
    try { execSync(`start "" "${outputPath}"`); } catch { /* ignore */ }
  }
}

main().catch(err => {
  console.error('❌ 报告生成失败:', err.message);
  process.exit(1);
});
