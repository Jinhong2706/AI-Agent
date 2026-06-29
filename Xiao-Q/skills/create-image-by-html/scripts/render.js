#!/usr/bin/env node
/**
 * html-to-image 渲染脚本（Node.js 版本）
 * 将 HTML 文件通过 Playwright 浏览器截图输出为 PNG
 *
 * 用法:
 *   node render.js <html文件路径> [--output <输出PNG路径>] [--wait <ms>] [--scale <2>]
 */

const { chromium } = require('/tmp/node_modules/playwright');
const path = require('path');
const fs = require('fs');

// Chrome 路径
const CHROME_PATH = '/Users/huanghaifeng/Library/Caches/ms-playwright/chromium-1208/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';

async function render(htmlPath, { output, wait = 300, scale = 2 } = {}) {
  htmlPath = path.resolve(htmlPath);
  if (!fs.existsSync(htmlPath)) {
    throw new Error(`HTML 文件不存在: ${htmlPath}`);
  }

  if (!output) {
    output = path.join(path.dirname(htmlPath), path.basename(htmlPath, '.html') + '.png');
  }
  output = path.resolve(output);

  const browser = await chromium.launch({ executablePath: CHROME_PATH });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: scale });

  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(wait);

  const box = await page.evaluate(() => {
    const el = document.querySelector('.container');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  });

  if (!box) {
    await page.screenshot({ path: output, fullPage: true });
    console.log(`⚠️ 未找到 .container，截取整页: ${output}`);
  } else {
    await page.screenshot({
      path: output,
      clip: { x: box.x - 16, y: box.y - 16, width: box.w + 32, height: box.h + 32 }
    });
    console.log(`✅ ${output} (${Math.round(box.w)}x${Math.round(box.h)})`);
  }

  await browser.close();
  return output;
}

// CLI 入口
const args = process.argv.slice(2);
if (args.length === 0) {
  console.log('用法: node render.js <html文件> [--output <png路径>] [--wait <ms>] [--scale <n>]');
  process.exit(1);
}

const htmlPath = args[0];
const opts = {};
for (let i = 1; i < args.length; i++) {
  if (args[i] === '--output' || args[i] === '-o') opts.output = args[++i];
  else if (args[i] === '--wait' || args[i] === '-w') opts.wait = parseInt(args[++i]);
  else if (args[i] === '--scale' || args[i] === '-s') opts.scale = parseInt(args[++i]);
}

render(htmlPath, opts)
  .then(f => console.log(`输出: ${f}`))
  .catch(e => { console.error(`❌ ${e.message}`); process.exit(1); });
