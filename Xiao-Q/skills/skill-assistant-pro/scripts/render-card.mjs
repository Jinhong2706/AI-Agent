#!/usr/bin/env node
/**
 * skill-assistant — 成果卡片渲染脚本
 *
 * 用法：
 *   node scripts/render-card.mjs <data.json> [output.png]
 *
 * data.json 字段（缺失字段会用模板默认占位符）：
 *   {
 *     "mode": "single" | "iter" | "hybrid",     // 卡片模式
 *     "skill_name": "target-skill",
 *     "skill_id": ".cursor/skills/target-skill",
 *     "card_title": "Skill 进化报告",
 *     "card_mode": "Iteration",                  // 顶部 mode tag 文本
 *     "date": "2026.04.28",
 *     "score_before": 72,                        // iter / hybrid 模式必填
 *     "score_after": 87,
 *     "grade": "B+ 良好",
 *     "static_score": 87,                        // hybrid 模式必填
 *     "static_grade": "B 良好",
 *     "static_note": "结构规整，反模式覆盖完整",
 *     "dynamic_score": 79,                       // hybrid 模式必填
 *     "dynamic_grade": "B 略优于 baseline",
 *     "dynamic_note": "2 条 happy path 通过，1 条副作用",
 *     "dims": [                                  // 最多 8 项
 *       { "name": "指令", "from": 5, "to": 9, "weight": "hot" },
 *       { "name": "约束", "from": 5, "to": 8, "weight": "hot" },
 *       ...
 *     ],
 *     "summary": [                               // 最多 4 条
 *       "补充了 NEVER 列表 + WHY，约束维度从 5 升到 8",
 *       ...
 *     ],
 *     "footer_url": "iwiki.woa.com/p/4019623347",
 *     "footer_by": "Powered by skill-assistant"
 *   }
 *
 * 特性：
 * - 2x deviceScaleFactor 高清输出
 * - 只截 .card 元素，无多余背景
 * - 自动 open 图片（macOS）
 * - Playwright 缺失时给出明确提示
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_PATH = resolve(__dirname, '../templates/result-card.html');

async function loadPlaywright() {
  const { createRequire } = await import('module');
  const req = createRequire(import.meta.url);
  const candidates = [
    'playwright',
    'playwright-core',
    '/usr/local/lib/node_modules/playwright',
    '/opt/homebrew/lib/node_modules/playwright',
  ];
  for (const name of candidates) {
    try {
      return req(name);
    } catch (_) { /* try next */ }
  }
  console.error('❌ 未找到 playwright。请先安装：');
  console.error('   npm install -g playwright   # 全局安装（推荐）');
  console.error('   或 npx playwright install chromium  # 仅安装浏览器内核');
  process.exit(1);
}

function applyData(html, data) {
  let result = html;

  // 1. body data-mode
  if (data.mode) {
    result = result.replace(/<body data-mode="iter">/, `<body data-mode="${data.mode}">`);
  }

  // 2. Ring 进度条 dashoffset（circumference = 2π×75 ≈ 471.24）
  const CIRC = 471.24;
  const score = Number(data.score_after ?? 0);
  const ringOffset = Math.max(0, Math.min(CIRC, CIRC * (1 - score / 100)));
  result = result.replace(
    /(class="ring-fill"[^>]*stroke-dashoffset:)\s*[\d.]+/,
    `$1 ${ringOffset.toFixed(2)}`,
  );

  // 3. 平铺字段替换
  const delta = data.score_delta ?? (
    data.score_after != null && data.score_before != null
      ? `${data.score_after - data.score_before >= 0 ? '+' : ''}${data.score_after - data.score_before}`
      : undefined
  );
  const flatFields = {
    'card-title':     data.card_title,
    'card-mode':      data.card_mode,
    'date':           data.date,
    'skill-name':     data.skill_name,
    'skill-id':       data.skill_id,
    'score-before':   data.score_before,
    'score-after':    data.score_after,
    'score-after-inline': data.score_after,
    'score-delta':    delta,
    'grade':          data.grade,
    'static-score':   data.static_score,
    'static-grade':   data.static_grade,
    'static-note':    data.static_note,
    'dynamic-score':  data.dynamic_score,
    'dynamic-grade':  data.dynamic_grade,
    'dynamic-note':   data.dynamic_note,
    'summary-header': data.summary_header,
    'dims-header':    data.dims_header,
    'footer-url':     data.footer_url,
    'footer-by':      data.footer_by,
  };
  for (const [field, value] of Object.entries(flatFields)) {
    if (value === undefined || value === null) continue;
    const re = new RegExp(`(data-field="${field}"[^>]*>)[^<]*(<)`, 'g');
    result = result.replace(re, `$1${escapeHtml(String(value))}$2`);
  }

  // 4. 维度（最多 8 项）+ weight 类注入 + 多余格隐藏
  const dims = Array.isArray(data.dims) ? data.dims.slice(0, 8) : [];
  dims.forEach((dim, idx) => {
    const i = idx + 1;
    const d = dim.to - dim.from;
    const deltaStr = dim.delta ?? `${d > 0 ? '+' : ''}${d}`;
    const deltaClass = d >= 3 ? 'pos-big' : d >= 1 ? 'pos-mid' : d === 1 ? 'pos-sml' : d < 0 ? 'neg' : 'flat';

    // 文本替换
    const sub = {
      [`dim${i}-name`]:  dim.name,
      [`dim${i}-from`]:  dim.from,
      [`dim${i}-to`]:    dim.to,
      [`dim${i}-delta`]: deltaStr,
    };
    for (const [field, value] of Object.entries(sub)) {
      if (value === undefined || value === null) continue;
      const re = new RegExp(`(data-field="${field}"[^>]*>)[^<]*(<)`, 'g');
      result = result.replace(re, `$1${escapeHtml(String(value))}$2`);
    }

    // weight 类（hot / warm / 默认）
    const weightClass = dim.weight === 'hot' ? 'hot' : dim.weight === 'warm' ? 'warm' : '';
    result = result.replace(
      new RegExp(`(<div class="dim-cell)[^"]*(" data-dim="${i}")`),
      `$1${weightClass ? ' ' + weightClass : ''}$2`,
    );

    // delta badge 颜色类
    result = result.replace(
      new RegExp(`(data-field="dim${i}-delta"[^>]*class=")dim-delta [^"]*"`),
      `$1dim-delta ${deltaClass}"`,
    );
  });

  // 多余的 dim 格打上 data-hidden
  for (let i = dims.length + 1; i <= 8; i++) {
    result = result.replace(
      new RegExp(`(<div class="dim-cell[^"]*" data-dim="${i}")`),
      `$1 data-hidden="1"`,
    );
  }

  // 5. 摘要（最多 4 条）+ 多余条隐藏
  const summaries = Array.isArray(data.summary) ? data.summary.slice(0, 4) : [];
  summaries.forEach((line, idx) => {
    const re = new RegExp(`(data-field="summary-${idx + 1}"[^>]*>)[^<]*(<)`, 'g');
    result = result.replace(re, `$1${escapeHtml(line)}$2`);
    // 确保该行可见（移除 display:none）
    result = result.replace(
      new RegExp(`(data-field="summary-${idx + 1}"[^>]*) style="display:none"`),
      '$1',
    );
  });
  // 隐藏未填充的摘要条
  for (let i = summaries.length + 1; i <= 4; i++) {
    result = result.replace(
      new RegExp(`(data-field="summary-${i}"[^>]*)>`),
      `$1 style="display:none">`,
    );
  }

  return result;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('用法: node scripts/render-card.mjs <data.json> [output.png]');
    process.exit(2);
  }

  const dataPath = resolve(args[0]);
  const outputPath = resolve(args[1] || dataPath.replace(/\.json$/, '.png'));

  if (!existsSync(dataPath)) {
    console.error(`❌ 数据文件不存在: ${dataPath}`);
    process.exit(1);
  }
  if (!existsSync(TEMPLATE_PATH)) {
    console.error(`❌ 模板文件不存在: ${TEMPLATE_PATH}`);
    process.exit(1);
  }

  const data = JSON.parse(readFileSync(dataPath, 'utf-8'));
  const tplHtml = readFileSync(TEMPLATE_PATH, 'utf-8');
  const filledHtml = applyData(tplHtml, data);

  // 用临时文件渲染（保持模板原文不被改写）
  const tmpHtml = outputPath.replace(/\.png$/, '.tmp.html');
  await import('fs').then(fs => fs.writeFileSync(tmpHtml, filledHtml));

  const pw = await loadPlaywright();
  const browser = await pw.chromium.launch();

  try {
    const context = await browser.newContext({
      viewport: { width: 940, height: 1600 },
      deviceScaleFactor: 2,
    });
    const page = await context.newPage();
    await page.goto(`file://${tmpHtml}`, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(800);

    const card = await page.locator('.card');
    await card.screenshot({ path: outputPath, type: 'png' });

    const box = await card.boundingBox();
    console.log(`✅ 卡片已生成: ${outputPath}`);
    console.log(`   尺寸: ${Math.round(box.width)}x${Math.round(box.height)}px (CSS) / 2x 输出 ${Math.round(box.width * 2)}x${Math.round(box.height * 2)}px`);
  } finally {
    await browser.close();
  }

  // 清理临时 html
  try { await import('fs').then(fs => fs.unlinkSync(tmpHtml)); } catch (_) { /* ignore */ }

  // 自动打开（PNG 直接用系统默认图片查看器即可）
  if (process.platform === 'darwin') {
    try { execSync(`open "${outputPath}"`); } catch { /* ignore */ }
  } else if (process.platform === 'linux') {
    try { execSync(`xdg-open "${outputPath}"`); } catch { /* ignore */ }
  } else if (process.platform === 'win32') {
    try { execSync(`start "" "${outputPath}"`); } catch { /* ignore */ }
  }
}

main().catch(err => {
  console.error('❌ 渲染失败:', err.message);
  process.exit(1);
});
