#!/usr/bin/env node
/**
 * discover.js — Universal Search 能力发现器 v2.1.0
 *
 * 动态扫描环境，自动发现所有可用搜索工具。
 * 预定义矩阵仅作为"已知工具补充描述"，不限制扫描范围。
 * 未在矩阵中的搜索 skill 也会被检测并报告。
 *
 * 用法:
 *   node discover.js                          # 自动检测，输出 JSON
 *   node discover.js --pretty                 # 格式化输出
 *   node discover.js --verify                 # 包含 API Key 连通性验证
 *   node discover.js --search-paths /a:/b     # 额外搜索路径 (冒号分隔)
 *   node discover.js --cache                  # 写入缓存 (后续调用自动读取)
 *   node discover.js --force                  # 忽略缓存，强制重新扫描
 *   node discover.js --cache-ttl 7200000      # 缓存有效期 (ms)，默认 3600000
 *
 * 缓存: /tmp/search-orchestrator-cache.json
 * 默认 TTL: 1 小时。缓存命中时秒级返回，避免重复扫描。
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// ─── 缓存配置 ──────────────────────────────────────────────
const CACHE_FILE = path.join(os.tmpdir(), 'search-orchestrator-cache.json');
const DEFAULT_CACHE_TTL = 3600000; // 1 小时 (毫秒)

function readCache(ttl) {
  try {
    if (!fileExists(CACHE_FILE)) return null;
    const raw = fs.readFileSync(CACHE_FILE, 'utf-8');
    const cache = JSON.parse(raw);
    if (Date.now() - cache.timestamp > ttl) return null; // 过期
    return cache.report;
  } catch { return null; }
}

function writeCache(report) {
  try {
    const cache = { timestamp: Date.now(), report };
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache));
  } catch { /* 缓存写入失败不影响主流程 */ }
}

// ─── 平台兼容工具函数 ──────────────────────────────────────

function envExists(name) {
  return !!process.env[name];
}

/**
 * 跨平台检查二进制/命令是否可用
 */
function binExists(name) {
  try {
    if (process.platform === 'win32') {
      execSync(`where "${name}"`, { stdio: 'pipe' });
    } else {
      execSync(`command -v "${name}"`, { stdio: 'pipe' });
    }
    return true;
  } catch {
    return false;
  }
}

function fileExists(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function dirExists(dirPath) {
  try {
    return fs.statSync(dirPath).isDirectory();
  } catch {
    return false;
  }
}

// ─── 搜索路径发现 ──────────────────────────────────────────

/**
 * 查找 skills 目录的所有候选位置
 * 按优先级排列，找到第一个有效目录即停止（除非 extraPaths 也提供）
 */
function findSkillsDirs(extraPaths = []) {
  const candidates = [];

  // 1. 环境变量指定
  if (process.env.UNIVERSAL_SEARCH_SKILLS_DIR) {
    candidates.push(process.env.UNIVERSAL_SEARCH_SKILLS_DIR);
  }

  // 2. 从当前脚本向上查找 skills/ 目录
  //    标准 OpenClaw 布局: skills/search-orchestrator/scripts/discover.js
  let scanDir = __dirname;
  for (let i = 0; i < 5; i++) {
    scanDir = path.dirname(scanDir);
    const skillsPath = path.join(scanDir, 'skills');
    if (dirExists(skillsPath)) {
      candidates.push(skillsPath);
      break;
    }
  }

  // 3. 用户 home 下的 OpenClaw skills
  const homeSkills = path.join(os.homedir(), '.openclaw', 'skills');
  if (dirExists(homeSkills)) candidates.push(homeSkills);

  // 4. 当前工作目录下的 skills
  const cwdSkills = path.join(process.cwd(), 'skills');
  if (dirExists(cwdSkills)) candidates.push(cwdSkills);

  // 5. 额外搜索路径
  for (const ep of extraPaths) {
    if (dirExists(ep)) candidates.push(ep);
  }

  // 去重
  return [...new Set(candidates)];
}

// ─── Skill 扫描 ────────────────────────────────────────────

/**
 * 从 _meta.json 读取 skill 的声明式依赖信息
 */
function readSkillMeta(skillPath) {
  const metaPath = path.join(skillPath, '_meta.json');
  if (!fileExists(metaPath)) return null;

  try {
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
    // OpenClaw 约定的 requires 格式: { bins: [...], env: [...] }
    const requires = (meta.metadata && meta.metadata.openclaw && meta.metadata.openclaw.requires) || {};
    const dirName = path.basename(skillPath);

    return {
      slug: meta.slug || dirName,
      name: meta.name || meta.display_name || dirName,
      description: meta.description || '',
      dirName: dirName,
      path: skillPath,
      requires: {
        env: requires.env || [],
        bins: requires.bins || [],
        primaryEnv: (meta.metadata && meta.metadata.openclaw && meta.metadata.openclaw.primaryEnv) || null
      },
      homepage: (meta.metadata && meta.metadata.openclaw && meta.metadata.openclaw.homepage) || '',
      emoji: (meta.metadata && meta.metadata.openclaw && meta.metadata.openclaw.emoji) || '',
      // 声明式搜索标记（_meta.json 中 metadata.openclaw.search = true/false）
      search: (meta.metadata && meta.metadata.openclaw && typeof meta.metadata.openclaw.search === 'boolean')
        ? meta.metadata.openclaw.search : undefined,
      _source: '_meta.json'
    };
  } catch {
    return null;
  }
}

/**
 * 简单 YAML frontmatter 解析器（无依赖）
 * 从 SKILL.md 的 --- 块中提取键值对。仅处理顶层标量。
 */
function parseYamlFrontmatter(content) {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!match) return null;
  const fm = {};
  const lines = match[1].split('\n');
  for (const line of lines) {
    const colonIdx = line.indexOf(':');
    if (colonIdx === -1) continue;
    const key = line.substring(0, colonIdx).trim();
    let raw = line.substring(colonIdx + 1).trim();
    // 布尔值
    if (raw === 'true') fm[key] = true;
    else if (raw === 'false') fm[key] = false;
    else if (/^\d+(\.\d+)?$/.test(raw)) fm[key] = Number(raw);
    else fm[key] = raw.replace(/^['"](.*)['"]$/, '$1'); // 去引号
  }
  return fm;
}

/**
 * 从 SKILL.md frontmatter 读取 skill 元信息（_meta.json 缺失时的降级方案）
 */
function readSkillMdMeta(skillPath) {
  const mdPath = path.join(skillPath, 'SKILL.md');
  if (!fileExists(mdPath)) return null;

  try {
    const content = fs.readFileSync(mdPath, 'utf-8');
    const fm = parseYamlFrontmatter(content);
    if (!fm || !fm.name) return null; // 至少要有 name

    const dirName = path.basename(skillPath);
    const slug = fm.slug || dirName;

    return {
      slug,
      name: fm.name || dirName,
      description: fm.description || '',
      dirName,
      path: skillPath,
      requires: { env: [], bins: [], primaryEnv: null },
      homepage: fm.homepage || '',
      emoji: '',
      // 声明式搜索标记：SKILL.md frontmatter 中可写 search: true/false
      search: typeof fm.search === 'boolean' ? fm.search : undefined,
      _source: 'SKILL.md'  // 标记来源，debug 用
    };
  } catch {
    return null;
  }
}

/**
 * 递归扫描目录下所有子目录，收集含有 _meta.json 或 SKILL.md 的 skill
 */
function scanSkillsRecursive(basePath) {
  const skills = [];
  if (!dirExists(basePath)) return skills;

  try {
    // 先检查 basePath 本身是否就是一个 skill 目录
    const selfMeta = readSkillMeta(basePath);
    if (selfMeta) {
      skills.push(selfMeta);
    }

    const entries = fs.readdirSync(basePath, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      // 跳过非 skill 目录 (以 . 或 _ 开头的内部目录，但 _drafts 可能要保留)
      if (entry.name.startsWith('.') && entry.name !== '.') continue;

      const skillPath = path.join(basePath, entry.name);

      // 优先 _meta.json，降级 SKILL.md frontmatter
      let meta = readSkillMeta(skillPath);
      if (!meta) {
        meta = readSkillMdMeta(skillPath);
      } else if (meta.search === undefined) {
        // _meta.json 未声明 search → 合并 SKILL.md 的 search 声明
        const mdMeta = readSkillMdMeta(skillPath);
        if (mdMeta && mdMeta.search !== undefined) meta.search = mdMeta.search;
      }
      if (meta) {
        skills.push(meta);
      }

      // 递归扫描子目录 (如 skills/agent-browser/skills/agent-browser)
      // 限制只深一层避免无限递归
      try {
        const subEntries = fs.readdirSync(skillPath, { withFileTypes: true });
        for (const sub of subEntries) {
          if (!sub.isDirectory()) continue;
          const subPath = path.join(skillPath, sub.name);
          // 跳过常见的非 skill 子目录
          if (['scripts', 'references', 'templates', 'node_modules', '.git'].includes(sub.name)) continue;
          let subMeta = readSkillMeta(subPath);
          if (!subMeta) {
            subMeta = readSkillMdMeta(subPath);
          } else if (subMeta.search === undefined) {
            const subMdMeta = readSkillMdMeta(subPath);
            if (subMdMeta && subMdMeta.search !== undefined) subMeta.search = subMdMeta.search;
          }
          if (subMeta) {
            subMeta.parentDir = entry.name;
            skills.push(subMeta);
          }
        }
      } catch { /* 跳过无权限目录 */ }
    }
  } catch { /* 跳过无权限目录 */ }

  return skills;
}

// ─── 能力推导 ──────────────────────────────────────────────

/**
 * 从 skill 的 slug/name/description 推导搜索能力标签
 * 这是一个启发式推导，矩阵提供精确值
 */
function inferCapabilities(meta) {
  const caps = {
    strengths: [],
    coverage: 'global',
    freshness: 'realtime',
    depth: 'moderate',
    estimated_latency_ms: 2000
  };

  const slug = (meta.slug || '').toLowerCase();
  const name = (meta.name || '').toLowerCase();
  const desc = (meta.description || '').toLowerCase();
  const combined = `${slug} ${name} ${desc}`;

  // 推断 strengths
  if (/baidu|百度|chinese|中文|china/.test(combined)) {
    caps.strengths.push('chinese');
    caps.coverage = 'china';
  }
  if (/tavily|english|ai.?optimized/.test(combined)) caps.strengths.push('english', 'ai_optimized');
  if (/brave|web.?search/.test(combined)) caps.strengths.push('general', 'english');
  if (/amap|map|高德|geograph|location|poi|routing|travel|导航|地图/.test(combined)) {
    caps.strengths.push('geographic');
    caps.coverage = 'china';
  }
  if (/browser|screenshot|automation|dynamic/.test(combined)) {
    caps.strengths.push('dynamic_pages', 'interaction');
    caps.depth = 'deep';
    caps.estimated_latency_ms = 8000;
  }
  if (/minimax|image|visual|understand/.test(combined)) caps.strengths.push('image_understanding');
  if (/news|新闻|timeline/.test(combined)) caps.strengths.push('news');
  if (/deep|深度|research/.test(combined)) caps.depth = 'deep';
  if (/fetch|extract|extractor|全文/.test(combined)) {
    caps.strengths.push('deep_extract', 'verification');
    caps.depth = 'deep';
  }

  // 如果没有匹配到任何 strength，标记为 general
  if (caps.strengths.length === 0) {
    caps.strengths.push('general');
  }

  return caps;
}

// ─── 矩阵查询 ──────────────────────────────────────────────

/**
 * 在已知工具矩阵中查找匹配条目，获取精确能力描述
 */
function findInMatrix(meta, matrix) {
  if (!matrix || !matrix.tools) return null;

  const slug = meta.slug || '';
  const name = meta.name || '';
  const dirName = meta.dirName || '';

  // 多种匹配方式
  for (const [toolId, toolDef] of Object.entries(matrix.tools)) {
    // 直接 slug 匹配
    if (slug === toolId || slug === toolDef.id) return toolDef;
    // 目录名匹配
    if (dirName === toolDef.id) return toolDef;
    // detection.directory 匹配
    if (toolDef.detection && toolDef.detection.directory === dirName) return toolDef;
  }
  return null;
}

// ─── 搜索工具过滤 ──────────────────────────────────────────

/**
 * 根据 strengths 推导工具类型，供 orchestrator 按角色调度
 */
function classifyKind(strengths) {
  const s = new Set(strengths || []);
  // 纯内部抓取工具
  if (s.has('deep_extract') || s.has('verification') || s.has('full_text')) {
    if (!s.has('general') && !s.has('chinese') && !s.has('english') && !s.has('news')) {
      return 'fetcher';
    }
  }
  // 纯浏览器工具
  if ((s.has('dynamic_pages') || s.has('screenshot') || s.has('interaction')) &&
      !s.has('general') && !s.has('chinese') && !s.has('english') && !s.has('news')) {
    return 'browser';
  }
  // 纯地理工具
  if ((s.has('geographic') || s.has('poi') || s.has('routing')) &&
      !s.has('general') && !s.has('chinese') && !s.has('english') && !s.has('news')) {
    return 'geo';
  }
  // 纯图片理解工具
  if (s.has('image_understanding') && s.size === 1) {
    return 'image';
  }
  // 其余一律视为搜索引擎
  return 'search_engine';
}

// ─── 搜索工具过滤（续）──────────────────────────────────────

/**
 * 判断一个扫描到的 skill 是否属于"搜索工具"
 *
 * 判定层级（优先级从高到低）：
 * 1. 在 capability-matrix 中有精确条目 → 是搜索工具
 * 2. _meta.json / SKILL.md 中显式声明 search: true → 是
 * 3. _meta.json / SKILL.md 中显式声明 search: false → 不是
 * 4. 在已知非搜索硬编码名单中（编排器/工具类 Skill 兜底）→ 不是
 * 5. slug/dirname/description 匹配搜索关键词 → 是
 * 6. requires.env 含搜索相关 API Key → 是
 * 7. 以上全不满足 → 不是（默认排除，避免噪音污染）
 */
function isSearchTool(meta, matrixEntry) {
  const slug = (meta.slug || meta.dirName || '').toLowerCase();
  const name = (meta.name || '').toLowerCase();
  const desc = (meta.description || '').toLowerCase();
  const combined = `${slug} ${name} ${desc}`;

  // L1: 在已知矩阵中 → 是搜索工具
  if (matrixEntry) return true;

  // L2-L3: 声明式标记（_meta.json 或 SKILL.md frontmatter 中的 search: true/false）
  if (meta.search === true) return true;
  if (meta.search === false) return false;

  // L4: 硬编码排除名单（编排器/已知非搜索 Skill 兜底。
  //     新 Skill 建议在 _meta.json / SKILL.md 中声明 search: false 以避免进此名单）
  const nonSearchPatterns = [
    'search-orchestrator', 'web-search',
    'adaptive-reasoning', 'calendar-schedule', 'code', 'dream-skill',
    'file-manager', 'memory-manager', 'ontology', 'openclaw-token-optimizer',
    'planning-execution', 'problem-solving-methodology', 'reasoning-personas',
    'self-improving-proactive-agent', 'ssh-tunnel', 'pdf', 'intelligence-ingestion',
    'skill-creator'
  ];
  for (const pattern of nonSearchPatterns) {
    if (slug === pattern || (meta.dirName || '') === pattern) return false;
  }

  // L5: 搜索相关关键词匹配
  const slugParts = slug.split(/[-_]/);
  const searchKeywords = [
    // 通用搜索词
    'search', '搜索', '搜', '查找', 'lookup', 'find', 'query', 'retrieve',
    // 搜索品牌/引擎
    'baidu', '百度', 'tavily', 'perplexity', 'kagi', 'exa', 'searxng',
    'duckduckgo', 'ddg', 'bing', 'serper', 'serpapi', 'searx',
    'metaso', '秘塔', 'minimax', 'you', 'brave',
    // 地图/地理
    'amap', '高德', 'map', '地图', '地理', 'location', 'geo',
    // 浏览器/抓取/截屏
    'browser', '浏览器', 'web', 'fetch', 'extract', 'scrape', 'crawl',
    'screenshot', 'scraper', 'crawler'
  ];
  // 额外检测 slug 前缀模式：mcp-xxx, search-xxx, xxx-search
  const slugLower = slug.toLowerCase();
  const prefixMatch = slugLower.startsWith('mcp-') || slugLower.startsWith('search-');
  const suffixMatch = slugLower.endsWith('-search') || slugLower.endsWith('-mcp');
  const slugMatches = slugParts.some(part => searchKeywords.includes(part.toLowerCase())) || prefixMatch || suffixMatch;
  const descMatches = searchKeywords.some(kw => desc.includes(kw));
  if (slugMatches || descMatches) return true;

  // L6: requires.env 含搜索相关 API Key
  const requires = meta.requires || {};
  if (requires.env && requires.env.length > 0) {
    const searchEnvs = ['BAIDU_API_KEY', 'TAVILY_API_KEY', 'MINIMAX_API_KEY',
                        'AMAP_WEBSERVICE_KEY', 'BRAVE_API_KEY', 'GOOGLE_API_KEY',
                        'BING_API_KEY', 'SERPER_API_KEY', 'SEARCH_API_KEY',
                        'PERPLEXITY_API_KEY', 'EXA_API_KEY', 'KAGI_API_KEY',
                        'JINA_API_KEY', 'FIRECRAWL_API_KEY', 'SEARXNG_URL',
                        'YOUCOM_API_KEY', 'METAPHOR_API_KEY', 'SERAPI_KEY'];
    if (requires.env.some(e => searchEnvs.includes(e))) return true;
  }

  // L7: 默认排除 — 不确定就排除，避免非搜索 Skill 噪音污染搜索系统
  return false;
}

// ─── 可用性检查 ────────────────────────────────────────────

function checkReadiness(meta, matrixEntry) {
  const reasons = [];
  const requires = meta.requires || {};

  // 检查二进制依赖
  if (requires.bins && requires.bins.length > 0) {
    let allBinsOk = true;
    for (const bin of requires.bins) {
      if (!binExists(bin)) {
        reasons.push(`缺少二进制: ${bin}`);
        allBinsOk = false;
      }
    }
    if (allBinsOk) {
      reasons.push(`二进制依赖满足: ${requires.bins.join(', ')}`);
    } else {
      return { status: 'missing_bin', reasons };
    }
  }

  // 检查环境变量
  if (requires.env && requires.env.length > 0) {
    let allEnvOk = true;
    for (const env of requires.env) {
      if (!envExists(env)) {
        reasons.push(`环境变量 ${env} 未配置`);
        allEnvOk = false;
      }
    }
    if (allEnvOk) {
      reasons.push(`环境变量满足: ${requires.env.join(', ')}`);
    } else {
      return { status: 'missing_key', reasons };
    }
  }

  reasons.push('所有依赖满足');
  return { status: 'ready', reasons };
}

/**
 * 构建调用模板（优先从矩阵，其次从 meta 注入点，最后自动探测入口脚本）
 */
function buildCallTemplate(meta, matrixEntry, toolId) {
  if (matrixEntry && matrixEntry.call) return matrixEntry.call;

  // 自动探测 skill 目录下的入口脚本
  const skillDir = meta.path;
  const commonEntries = [
    'scripts/search.mjs',
    'scripts/search.js',
    'scripts/search.py',
    'scripts/run.mjs',
    'scripts/run.js',
    'index.js',
    'index.mjs',
    'main.js',
    'main.mjs'
  ];

  for (const entry of commonEntries) {
    const fullPath = path.join(skillDir, entry);
    if (fileExists(fullPath)) {
      const ext = path.extname(entry);
      let template;
      if (ext === '.mjs' || ext === '.js') {
        template = `cd {skill_dir} && node ${entry} "{query}"`;
      } else if (ext === '.py') {
        template = `cd {skill_dir} && python3 ${entry} "{query}"`;
      } else {
        template = `cd {skill_dir} && ./${entry} "{query}"`;
      }
      return {
        kind: 'shell',
        template,
        params: { query: 'string (required)' },
        auto_detected: true,
        entry_file: entry
      };
    }
  }

  // 完全无法探测 → 回退到 SKILL.md 查阅模式
  return {
    kind: 'skill',
    skill: meta.slug || meta.dirName,
    note: '无法自动探测入口脚本。请读取该 skill 目录下的 SKILL.md 获取调用方式，然后在 skillPath 下查找可执行脚本手动调用。'
  };
}

// ─── 主逻辑 ────────────────────────────────────────────────

function main() {
  const args = {
    pretty: false,
    verify: false,
    paths: [],
    cache: false,
    force: false,
    cacheTtl: DEFAULT_CACHE_TTL
  };

  for (const arg of process.argv.slice(2)) {
    if (arg === '--verify') args.verify = true;
    else if (arg === '--pretty') args.pretty = true;
    else if (arg === '--cache') args.cache = true;
    else if (arg === '--force') args.force = true;
    else if (arg.startsWith('--cache-ttl=')) {
      args.cacheTtl = parseInt(arg.split('=')[1], 10) || DEFAULT_CACHE_TTL;
    }
    else if (arg.startsWith('--search-paths=')) {
      args.paths = arg.split('=')[1].split(':').filter(Boolean);
    }
  }

  // 缓存读取: --force 时跳过，--cache 或无参数时尝试读取
  if (!args.force) {
    const cached = readCache(args.cacheTtl);
    if (cached) {
      cached.cache_hit = true;
      cached.cache_age_ms = Date.now() - new Date(cached.generated_at).getTime();
      if (args.pretty) {
        console.log(JSON.stringify(cached, null, 2));
      } else {
        console.log(JSON.stringify(cached));
      }
      return cached;
    }
  }

  // 1. 加载能力矩阵（作为已知工具增强描述，加载失败不阻塞）
  let matrix = null;
  const matrixPath = path.join(__dirname, '..', 'references', 'capability-matrix.json');
  try {
    matrix = JSON.parse(fs.readFileSync(matrixPath, 'utf-8'));
  } catch {
    matrix = { tools: {} };
  }

  // 2. 查找 skills 目录
  const skillsDirs = findSkillsDirs(args.paths);

  // 3. 扫描所有 skill
  const scannedSkills = [];
  for (const dir of skillsDirs) {
    scannedSkills.push(...scanSkillsRecursive(dir));
  }

  // 去重（按 path）
  const seen = new Set();
  const uniqueSkills = scannedSkills.filter(s => {
    const key = s.path;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  // 4. 处理每个扫描到的 skill（只包含搜索工具）
  const results = [];
  const seenIds = new Set();
  let skippedCount = 0;

  for (const meta of uniqueSkills) {
    const slug = meta.slug || meta.dirName;

    // 跳过自身
    if (slug === 'search-orchestrator') continue;

    const matrixEntry = findInMatrix(meta, matrix);

    // 跳过非搜索工具
    if (!isSearchTool(meta, matrixEntry)) {
      skippedCount++;
      continue;
    }
    const inferred = inferCapabilities(meta);
    const readiness = checkReadiness(meta, matrixEntry);

    // 使用矩阵中的精确值，优先于推断值
    const strengths = (matrixEntry && matrixEntry.strengths) || inferred.strengths;
    const coverage = (matrixEntry && matrixEntry.coverage) || inferred.coverage;
    const depth = (matrixEntry && matrixEntry.depth) || inferred.depth;
    const toolName = (matrixEntry && matrixEntry.name) || meta.name || slug;
    const cost = (matrixEntry && matrixEntry.cost) || 'unknown';
    const estimatedLatency = (matrixEntry && matrixEntry.estimated_latency_ms) || inferred.estimated_latency_ms;

    const toolId = `skill:${slug}`;
    seenIds.add(toolId);

    results.push({
      id: toolId,
      rawId: slug,
      name: toolName,
      type: 'skill',
      status: readiness.status,
      strengths,
      coverage,
      depth,
      cost,
      estimated_latency_ms: estimatedLatency,
      description: meta.description,
      reasons: readiness.reasons,
      skillPath: meta.path,
      call: buildCallTemplate(meta, matrixEntry, toolId)
    });
  }

  // 5. 添加内置系统工具（始终在 OpenClaw 中可用）
  const builtins = [
    {
      id: 'builtin:web_search',
      rawId: 'web_search',
      name: 'Web Search (Brave)',
      type: 'builtin',
      status: 'ready',
      strengths: ['general', 'english', 'news', 'technical'],
      coverage: 'global',
      depth: 'surface',
      cost: 'free',
      estimated_latency_ms: 1500,
      reasons: ['OpenClaw 内置系统工具'],
      call: { kind: 'system_tool', tool_name: 'web_search', params: { query: 'string (required)', count: '1-10', freshness: 'day|week|month' } }
    },
    {
      id: 'builtin:web_fetch',
      rawId: 'web_fetch',
      name: 'URL Content Extractor',
      type: 'builtin',
      status: 'ready',
      strengths: ['deep_extract', 'verification', 'full_text'],
      coverage: 'global',
      depth: 'deep',
      cost: 'free',
      estimated_latency_ms: 2000,
      reasons: ['OpenClaw 内置系统工具'],
      call: { kind: 'system_tool', tool_name: 'web_fetch', params: { url: 'string (required)', extractMode: 'markdown|text' } }
    },
    {
      id: 'builtin:browser',
      rawId: 'browser',
      name: 'Browser Automation',
      type: 'builtin',
      status: 'ready',
      strengths: ['dynamic_pages', 'interaction', 'screenshot'],
      coverage: 'global',
      depth: 'deep',
      cost: 'free',
      estimated_latency_ms: 5000,
      reasons: ['OpenClaw 内置系统工具'],
      call: { kind: 'system_tool', tool_name: 'browser', params: '见 browser tool 文档' }
    }
  ];

  // 内置工具插入到结果前面
  results.unshift(...builtins);

  // 6. 汇总
  const ready = results.filter(r => r.status === 'ready');
  const degraded = results.filter(r => ['missing_key', 'missing_bin'].includes(r.status));
  const missing = results.filter(r => ['missing_skill', 'missing_file'].includes(r.status));

  const report = {
    generated_at: new Date().toISOString(),
    version: matrix ? matrix.version : 'unknown',
    summary: {
      total_scanned: uniqueSkills.length,
      non_search_skipped: skippedCount,
      search_tools_found: results.length,
      ready: ready.length,
      degraded: degraded.length,
      missing: missing.length,
      skills_dirs_scanned: skillsDirs.length
    },
    tools: results,
    ready: ready.map(r => ({ id: r.id, rawId: r.rawId, name: r.name, strengths: r.strengths, kind: classifyKind(r.strengths) })),
    degraded: degraded.map(r => ({ id: r.id, rawId: r.rawId, status: r.status, reasons: r.reasons })),
    recommendations: []
  };

  // 7. 生成建议
  for (const d of degraded) {
    if (d.status === 'missing_key') {
      const meta = uniqueSkills.find(s => (s.slug || s.dirName) === d.rawId);
      const envs = meta ? (meta.requires.env || []).join(', ') : 'required API key';
      report.recommendations.push({
        tool: d.id,
        action: 'configure_env',
        message: `配置 ${envs} 即可启用 ${d.name || d.rawId}`,
        env: meta ? meta.requires.env : []
      });
    }
    if (d.status === 'missing_bin') {
      report.recommendations.push({
        tool: d.id,
        action: 'install_dependency',
        message: `安装所需二进制依赖即可启用 ${d.name || d.rawId}`
      });
    }
  }

  // 工具少于 2 个时建议安装更多
  if (ready.length < 2) {
    report.recommendations.push({
      tool: 'any',
      action: 'install_skill',
      message: '当前可用的搜索工具不足2个，搜索质量为单源模式。建议安装至少一个搜索 skill（如 baidu-search、tavily-search 或 minimax-token-plan-tool）以确保双源交叉验证。'
    });
  }

  // 输出
  if (args.pretty) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(JSON.stringify(report));
  }

  // 缓存写入
  if (args.cache) {
    writeCache(report);
  }

  return report;
}

main();
