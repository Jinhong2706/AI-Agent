#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_reader.py
从 JSON 章节数据生成 HTML 阅读器（含 Edge TTS 朗读功能）
用法: python build_reader.py <json_path> <output_html_path> [--title "书名"]
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os

TTS_SERVER_PORT = 8766


def build_html(chapters, book_title="小说阅读器"):
    """生成完整 HTML 阅读器"""
    chapters_json = json.dumps(chapters, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{book_title}</title>
<style>
  :root {{
    --bg: #1a1a2e;
    --sidebar-bg: #16213e;
    --accent: #0f3460;
    --highlight: #e94560;
    --text: #c8c8d0;
    --title-color: #e8e8f0;
    --sidebar-width: 280px;
    --font-size: 18px;
    --line-height: 2;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Georgia', 'STSong', '宋体', serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }}

  #sidebar {{
    width: var(--sidebar-width);
    background: var(--sidebar-bg);
    display: flex;
    flex-direction: column;
    border-right: 1px solid #2a2a4a;
    flex-shrink: 0;
  }}
  #sidebar-header {{
    padding: 20px 16px 12px;
    border-bottom: 1px solid #2a2a4a;
  }}
  #sidebar-header h2 {{
    font-size: 15px;
    color: var(--highlight);
    margin-bottom: 4px;
    word-break: break-all;
  }}
  #sidebar-header p {{
    font-size: 12px;
    color: #888;
  }}
  #search-box {{
    padding: 10px 16px;
    border-bottom: 1px solid #2a2a4a;
  }}
  #search-box input {{
    width: 100%;
    padding: 7px 10px;
    background: #0d0d1f;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    color: var(--text);
    font-size: 13px;
    outline: none;
  }}
  #search-box input:focus {{ border-color: var(--highlight); }}
  #chapter-list {{
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
    scrollbar-width: thin;
    scrollbar-color: #2a2a4a transparent;
  }}
  #chapter-list::-webkit-scrollbar {{ width: 4px; }}
  #chapter-list::-webkit-scrollbar-thumb {{ background: #2a2a4a; border-radius: 2px; }}
  .ch-item {{
    padding: 8px 16px;
    font-size: 13px;
    cursor: pointer;
    color: #aaa;
    transition: all 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.5;
  }}
  .ch-item:hover {{ background: #0f3460; color: #eee; }}
  .ch-item.active {{ background: var(--highlight); color: #fff; font-weight: bold; }}

  #main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  #toolbar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--sidebar-bg);
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
    flex-wrap: wrap;
  }}
  .btn {{
    background: var(--accent);
    color: #ccc;
    border: none;
    padding: 5px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.2s;
    white-space: nowrap;
  }}
  .btn:hover {{ background: var(--highlight); color: #fff; }}
  .btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
  #chapter-counter {{
    font-size: 12px;
    color: #888;
    flex: 1;
    text-align: center;
    white-space: nowrap;
  }}

  /* TTS bar */
  #tts-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    background: #0d1a30;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
    flex-wrap: wrap;
  }}
  #tts-voice-select {{
    background: #0d1a30;
    color: #ccc;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 12px;
    max-width: 160px;
    outline: none;
    cursor: pointer;
  }}
  #tts-voice-select option {{ background: #16213e; }}
  #tts-bar .btn {{ background: var(--accent); }}
  #tts-speed {{
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #888;
  }}
  #tts-speed input {{ width: 64px; accent-color: #e94560; cursor: pointer; }}
  #tts-status {{
    font-size: 11px;
    color: #666;
    flex: 1;
    text-align: right;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 220px;
  }}

  #content-area {{
    flex: 1;
    overflow-y: auto;
    padding: 40px 60px;
    max-width: 860px;
    margin: 0 auto;
    width: 100%;
    scrollbar-width: thin;
    scrollbar-color: #2a2a4a transparent;
  }}
  #content-area::-webkit-scrollbar {{ width: 6px; }}
  #content-area::-webkit-scrollbar-thumb {{ background: #2a2a4a; border-radius: 3px; }}
  #chapter-title {{
    font-size: 22px;
    color: var(--title-color);
    text-align: center;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid #2a2a4a;
    letter-spacing: 2px;
  }}
  #chapter-body p {{
    font-size: var(--font-size);
    line-height: var(--line-height);
    margin-bottom: 12px;
    text-indent: 2em;
    color: var(--text);
  }}
  #chapter-body p:first-child {{ text-indent: 0; }}
  #progress-bar {{
    height: 3px;
    background: var(--highlight);
    position: fixed;
    top: 0; left: 0;
    transition: width 0.3s;
    z-index: 999;
  }}

  /* Light theme */
  body.light-theme {{
    --bg: #faf8f3;
    --sidebar-bg: #f0ede4;
    --accent: #d4c5a9;
    --highlight: #c0392b;
    --text: #3a3020;
    --title-color: #1a1008;
  }}
  body.light-theme .ch-item {{ color: #555; }}
  body.light-theme .ch-item:hover {{ background: #d4c5a9; color: #222; }}
  body.light-theme .ch-item.active {{ background: #c0392b; color: #fff; }}
  body.light-theme #tts-voice-select {{ background: #f0ede4; color: #333; border-color: #c8c0a8; }}
  body.light-theme #tts-voice-select option {{ background: #f0ede4; }}
  body.light-theme #tts-bar {{ background: #e8e4d8; border-color: #c8c0a8; }}
  body.light-theme #tts-bar .btn {{ background: #d4c5a9; color: #555; }}
  body.light-theme #tts-bar .btn:hover {{ background: #c0392b; color: #fff; }}
  body.light-theme #tts-speed {{ color: #666; }}
  body.light-theme #tts-status {{ color: #888; }}

  @media (max-width: 768px) {{
    #sidebar {{ display: none; }}
    #sidebar.open {{
      display: flex;
      position: fixed;
      left: 0; top: 0; bottom: 0;
      z-index: 100;
    }}
    #content-area {{ padding: 20px; }}
  }}
</style>
</head>
<body>
<div id="progress-bar"></div>

<div id="sidebar">
  <div id="sidebar-header">
    <h2>{book_title}</h2>
    <p>共 {len(chapters)} 章</p>
  </div>
  <div id="search-box">
    <input type="text" id="search-input" placeholder="搜索章节..." oninput="filterChapters(this.value)">
  </div>
  <div id="chapter-list"></div>
</div>

<div id="main">
  <div id="toolbar">
    <button class="btn" onclick="toggleSidebar()">&#9776; 目录</button>
    <button class="btn" id="prev-btn" onclick="navigate(-1)">&#9664; 上一章</button>
    <span id="chapter-counter">第 1 章 / 共 {len(chapters)} 章</span>
    <button class="btn" id="next-btn" onclick="navigate(1)">下一章 &#9654;</button>
    <div id="font-controls" style="display:flex;align-items:center;gap:4px;">
      <span style="font-size:12px;color:#888;">字号</span>
      <button class="btn" onclick="changeFontSize(-1)" style="padding:5px 8px;">A-</button>
      <button class="btn" onclick="changeFontSize(1)" style="padding:5px 8px;">A+</button>
    </div>
    <button class="btn" onclick="toggleTheme()">&#9788;/&#9790;</button>
  </div>

  <div id="tts-bar">
    <select id="tts-voice-select">
      <option value="">加载语音中...</option>
    </select>
    <button class="btn" id="tts-play-btn" onclick="ttsPlay()">&#9654; 朗读</button>
    <button class="btn" id="tts-pause-btn" onclick="ttsPause()" style="display:none">&#9646;&#9646; 暂停</button>
    <button class="btn" id="tts-stop-btn" onclick="ttsStop()" style="display:none">&#9632; 停止</button>
    <div id="tts-speed">
      <span>语速</span>
      <input type="range" id="tts-rate" min="0.5" max="2" step="0.1" value="1" oninput="ttsSetRate(this.value)">
      <span id="tts-rate-label">1.0x</span>
    </div>
    <span id="tts-status">就绪</span>
  </div>

  <div id="content-area">
    <h2 id="chapter-title"></h2>
    <div id="chapter-body"></div>
    <div style="display:flex;gap:12px;justify-content:center;padding:32px 0;">
      <button class="btn" id="bottom-prev" onclick="navigate(-1)">&#9664; 上一章</button>
      <button class="btn" id="bottom-next" onclick="navigate(1)">下一章 &#9654;</button>
    </div>
  </div>
</div>

<script>
// ===== Chapter Data =====
const CHAPTERS = {chapters_json};
const TOTAL = CHAPTERS.length;
let currentIdx = 0;
let fontSize = 18;

// ---- Nav & UI ----
function buildList(filter) {{
  const list = document.getElementById('chapter-list');
  list.innerHTML = '';
  CHAPTERS.forEach((ch, i) => {{
    if (filter && !ch.title.includes(filter)) return;
    const div = document.createElement('div');
    div.className = 'ch-item' + (i === currentIdx ? ' active' : '');
    div.textContent = ch.title;
    div.onclick = () => loadChapter(i, true);
    list.appendChild(div);
  }});
}}

function loadChapter(idx, scrollTop) {{
  currentIdx = idx;
  const ch = CHAPTERS[idx];
  // Build HTML: title line + paragraphs
  let html = '';
  for (let i = 1; i < ch.content.length; i++) {{
    html += '<p>' + ch.content[i].replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</p>';
  }}
  document.getElementById('chapter-body').innerHTML = html;
  document.getElementById('chapter-title').textContent = ch.title;
  document.getElementById('chapter-counter').textContent = '第 ' + (idx+1) + ' 章 / 共 ' + TOTAL + ' 章';
  document.getElementById('prev-btn').disabled = idx === 0;
  document.getElementById('next-btn').disabled = idx === TOTAL - 1;
  document.getElementById('bottom-prev').disabled = idx === 0;
  document.getElementById('bottom-next').disabled = idx === TOTAL - 1;
  localStorage.setItem('utopia_progress', idx);
  if (scrollTop) document.getElementById('content-area').scrollTop = 0;
  document.querySelectorAll('.ch-item').forEach(el => {{
    el.classList.toggle('active', parseInt(el.dataset.idx || el.getAttribute('data-idx')) === idx);
  }});
  updateProgress();
}}

function navigate(dir) {{
  const n = currentIdx + dir;
  if (n >= 0 && n < TOTAL) loadChapter(n, true);
}}

function filterChapters(val) {{ buildList(val.trim()); }}
function changeFontSize(delta) {{
  fontSize = Math.max(14, Math.min(26, fontSize + delta));
  document.documentElement.style.setProperty('--font-size', fontSize + 'px');
}}

function toggleTheme() {{ document.body.classList.toggle('light-theme'); }}
function toggleSidebar() {{ document.getElementById('sidebar').classList.toggle('open'); }}

function updateProgress() {{
  const area = document.getElementById('content-area');
  const pct = area.scrollTop / (area.scrollHeight - area.clientHeight) * 100 || 0;
  document.getElementById('progress-bar').style.width = pct + '%';
}}
document.getElementById('content-area').addEventListener('scroll', updateProgress);

// ---- TTS Edge Neural Voice ----
const TTS_SERVER = 'http://127.0.0.1:{TTS_SERVER_PORT}';
let ttsVoiceList = [];
let ttsDefaultVoice = 'zh-CN-XiaoxiaoNeural';
let ttsCurVoice = ttsDefaultVoice;
let ttsAudio = null;
let ttsParagraphs = [];
let ttsCurIdx = 0;
let ttsPlaying = false;
let ttsPaused = false;
let ttsRate = 1.0;

async function ttsLoadVoices() {{
  try {{
    const res = await fetch(TTS_SERVER + '/voices');
    const data = await res.json();
    ttsVoiceList = data.voices || [];
    ttsDefaultVoice = data.default || 'zh-CN-XiaoxiaoNeural';
    ttsCurVoice = localStorage.getItem('tts_voice') || ttsDefaultVoice;
    const sel = document.getElementById('tts-voice-select');
    sel.innerHTML = '';
    const groups = {{}};
    ttsVoiceList.forEach(v => {{
      const g = v.lang.split('-')[0];
      if (!groups[g]) groups[g] = [];
      groups[g].push(v);
    }});
    const langNames = {{ 'zh': '中文', 'zh-CN': '普通话', 'zh-HK': '粤语', 'zh-TW': '台湾话' }};
    Object.entries(groups).forEach(([lang, voices]) => {{
      const og = document.createElement('optgroup');
      og.label = langNames[lang] || lang;
      voices.forEach(v => {{
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.name + ' (' + v.gender + ')';
        og.appendChild(opt);
      }});
      sel.appendChild(og);
    }});
    sel.value = ttsCurVoice;
    sel.onchange = () => {{
      ttsCurVoice = sel.value;
      localStorage.setItem('tts_voice', ttsCurVoice);
    }};
  }} catch (e) {{
    document.getElementById('tts-voice-select').innerHTML = '<option value="">服务器未启动</option>';
    document.getElementById('tts-status').textContent = '请先启动 TTS 服务器';
  }}
}}

function ttsBuildParagraphs() {{
  const paras = document.querySelectorAll('#chapter-body p');
  ttsParagraphs = Array.from(paras)
    .map(p => p.textContent.trim())
    .filter(t => t.length > 0);
}}

async function ttsPlay() {{
  if (ttsPlaying && !ttsPaused) return;
  if (ttsPaused && ttsAudio) {{
    ttsAudio.play();
    ttsPaused = false;
    setTtsBtns('play');
    document.getElementById('tts-status').textContent = '朗读中...';
    return;
  }}
  ttsBuildParagraphs();
  if (!ttsParagraphs.length) {{
    document.getElementById('tts-status').textContent = '无内容';
    return;
  }}
  ttsCurIdx = 0;
  ttsPlaying = true;
  ttsPaused = false;
  setTtsBtns('play');
  await ttsPlayNext();
}}

async function ttsPlayNext() {{
  if (!ttsPlaying || ttsCurIdx >= ttsParagraphs.length) {{ ttsFinish(); return; }}
  const text = ttsParagraphs[ttsCurIdx];
  document.getElementById('tts-status').textContent = '合成 ' + (ttsCurIdx+1) + '/' + ttsParagraphs.length + '...';
  try {{
    const url = TTS_SERVER + '/tts?text=' + encodeURIComponent(text) + '&voice=' + encodeURIComponent(ttsCurVoice) + '&rate=' + encodeURIComponent(ttsRate.toString());
    if (ttsAudio) {{ ttsAudio.pause(); ttsAudio = null; }}
    ttsAudio = new Audio(url);
    ttsAudio.preload = 'auto';
    ttsAudio.oncanplaythrough = () => {{
      if (!ttsPlaying) return;
      const prev = text.slice(0, 14);
      document.getElementById('tts-status').textContent = '朗读: ' + prev + (text.length > 14 ? '...' : '') + ' [' + (ttsCurIdx+1) + '/' + ttsParagraphs.length + ']';
      ttsAudio.play().catch(() => {{}});
    }};
    ttsAudio.onended = () => {{
      if (!ttsPlaying) return;
      ttsCurIdx++;
      ttsPlayNext();
    }};
    ttsAudio.onerror = () => {{
      if (!ttsPlaying) return;
      ttsCurIdx++;
      ttsPlayNext();
    }};
  }} catch (e) {{
    document.getElementById('tts-status').textContent = '错误: ' + e.message;
    ttsFinish();
  }}
}}

function ttsPause() {{
  if (!ttsPlaying || !ttsAudio) return;
  if (!ttsPaused) {{
    ttsAudio.pause();
    ttsPaused = true;
    document.getElementById('tts-pause-btn').textContent = '\\u25b6 继续';
    document.getElementById('tts-status').textContent = '已暂停 [' + (ttsCurIdx+1) + '/' + ttsParagraphs.length + ']';
  }} else {{
    ttsAudio.play();
    ttsPaused = false;
    document.getElementById('tts-pause-btn').textContent = '\\u2588\\u2588 暂停';
    document.getElementById('tts-status').textContent = '朗读中...';
  }}
}}

function ttsStop() {{
  ttsPlaying = false;
  ttsPaused = false;
  if (ttsAudio) {{ ttsAudio.pause(); ttsAudio = null; }}
  ttsParagraphs = [];
  ttsCurIdx = 0;
  setTtsBtns('stop');
  document.getElementById('tts-status').textContent = '已停止';
}}

function ttsFinish() {{
  ttsPlaying = false;
  ttsPaused = false;
  if (ttsAudio) {{ ttsAudio.pause(); ttsAudio = null; }}
  setTtsBtns('stop');
  document.getElementById('tts-status').textContent = '完成 \\u2713 共' + ttsParagraphs.length + '段';
  ttsParagraphs = [];
  ttsCurIdx = 0;
}}

function setTtsBtns(s) {{
  const play = document.getElementById('tts-play-btn');
  const pause = document.getElementById('tts-pause-btn');
  const stop = document.getElementById('tts-stop-btn');
  if (s === 'play') {{
    play.style.display = 'none';
    pause.style.display = '';
    pause.textContent = '\\u2588\\u2588 暂停';
    stop.style.display = '';
  }} else {{
    play.style.display = '';
    pause.style.display = 'none';
    stop.style.display = 'none';
  }}
}}

function ttsSetRate(v) {{
  ttsRate = parseFloat(v);
  document.getElementById('tts-rate-label').textContent = ttsRate.toFixed(1) + 'x';
  localStorage.setItem('tts_rate', ttsRate);
}}

function ttsStopOnChapterChange() {{ ttsStop(); }}

// Hook chapter change
const _origLoad = loadChapter;
loadChapter = function(idx, st) {{ ttsStopOnChapterChange(); _origLoad(idx, st); }};

// Init
buildList('');
const saved = parseInt(localStorage.getItem('utopia_progress') || '0');
loadChapter(isNaN(saved) ? 0 : saved, true);
ttsLoadVoices();

// Restore TTS rate
const savedRate = localStorage.getItem('tts_rate');
if (savedRate) {{
  ttsRate = parseFloat(savedRate);
  document.getElementById('tts-rate').value = ttsRate;
  document.getElementById('tts-rate-label').textContent = ttsRate.toFixed(1) + 'x';
}}

// Keyboard nav
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === 'ArrowLeft' || e.key === 'PageUp') navigate(-1);
  if (e.key === 'ArrowRight' || e.key === 'PageDown') navigate(1);
}});
</script>
</body>
</html>'''
    return html


def main():
    if len(sys.argv) < 3:
        print("用法: python build_reader.py <json_path> <output_html_path> [--title '书名']")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2]
    book_title = "小说阅读器"

    for i, arg in enumerate(sys.argv):
        if arg == '--title' and i + 1 < len(sys.argv):
            book_title = sys.argv[i + 1]

    if not os.path.exists(json_path):
        print(f"错误: JSON 文件不存在 {json_path}")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    print(f"加载 {len(chapters)} 章，开始生成 HTML...")

    html = build_html(chapters, book_title)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size = os.path.getsize(output_path)
    print(f"生成完成: {output_path} ({size // 1024} KB)")


if __name__ == '__main__':
    main()
