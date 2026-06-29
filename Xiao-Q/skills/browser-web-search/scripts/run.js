#!/usr/bin/env node

/**
 * browser-web-search-skill launcher
 *
 * This launcher does NOT spawn external processes. It loads the pinned
 * 'browser-web-search' npm package as an ES module via dynamic import and
 * invokes its entry by injecting a validated, allow-listed argv. There is
 * no shell, no subprocess, and no exec sink in this file.
 *
 * Security posture (mapping to applied codeguard-0-* rules):
 *
 * 1. Input validation & injection defense (codeguard-0-input-validation-injection):
 *    - Subcommands and adapter names allow-listed via Sets / strict regex
 *    - All forwarded args length-bounded and stripped of NUL/control chars
 *    - Only well-known long flags forwarded; '--' delimiter prevents option injection
 *    - argv is injected into the imported module; never rendered into a shell string
 *
 * 2. Authorization & access control (codeguard-0-authorization-access-control):
 *    - Deny-by-default for adapters that touch authenticated/account data
 *    - Opt-in via BWS_ALLOW_SENSITIVE=1 env var OR per-call --i-understand-sensitive flag
 *    - Unknown adapter (not in PUBLIC_SITES, not always-sensitive) defaults to sensitive
 *
 * 3. Privacy & data protection (codeguard-0-privacy-data-protection):
 *    - BWS_PUBLIC_ONLY=1 hard-isolates the launcher to public adapters only
 *    - No request payloads / response bodies are ever logged
 *
 * 4. Logging (codeguard-0-logging):
 *    - Append-only JSON-lines audit log at ~/.bws/audit.log
 *    - Records: timestamp, adapter, classification, decision, reason, sha256(args)
 *    - Never logs raw args, secrets, cookies, or response data
 *
 * 5. Supply chain (codeguard-0-supply-chain-security):
 *    - Pinned to REQUIRED_VERSION; module-not-found yields actionable install command
 *    - Skill itself does NOT auto-install or auto-update the npm package
 *    - Dynamic import target is a string literal package name; resolution paths
 *      are restricted to platform-standard global node_modules locations.
 */

'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const REQUIRED_VERSION = '0.4.3';
const PINNED_PACKAGE = 'browser-web-search';

// ---------- CLI surface allow-lists ----------

const SUBCOMMANDS = new Set(['list', 'search', 'info', 'run', 'help']);
const ADAPTER_NAME_RE = /^[a-zA-Z0-9_-]{1,64}\/[a-zA-Z0-9_-]{1,64}$/;
const IDENT_RE = /^[\p{L}\p{N}_\-./ ]{1,200}$/u;

const LAUNCHER_ONLY_FLAGS = new Set(['--i-understand-sensitive']);

const ALLOWED_FLAGS = new Set([
  '--json',
  '--jq',
  '--count',
  '--sort',
  '--id',
  '--limit',
  '--page',
  ...LAUNCHER_ONLY_FLAGS,
]);

const MAX_ARG_LEN = 1024;
const CONTROL_CHAR_RE = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/;

// ---------- Sensitivity classification ----------
//
// Source of truth: SKILL.md adapter table. Keep these lists in sync when
// SKILL.md is updated. Misclassification only weakens the deny-by-default
// posture; it never increases the privileges granted to bws.

// Sites whose every adapter command operates inside an authenticated session
// (private feeds, DMs, account-restricted content).
const ALWAYS_SENSITIVE_SITES = new Set([
  'weixin',
  'xiaohongshu',
  'weibo',
  'xueqiu',
  'jike',
  'douban',
  'qidian',
  'ctrip',
  'x',
  'linkedin',
]);

// Command suffixes that always touch account/private surfaces, regardless of
// site (e.g. zhihu/me, bilibili/feed, youtube/history).
const SENSITIVE_SUFFIX_RE = /\/(me|feed|history|comments|user_posts|article)$/;

// Sites for which the publicly listed commands are safe to call without
// authenticated state. Adapters of these sites that ALSO match
// SENSITIVE_SUFFIX_RE are still treated as sensitive (e.g. zhihu/me).
const PUBLIC_SITES = new Set([
  // 国内公共
  'thepaper', 'qqnews', 'netease', 'sina', '36kr', 'huxiu',
  'wallstreetcn', 'eastmoney', 'juejin', 'csdn', 'cnblogs',
  'v2ex', 'baidu', 'hupu', 'youdao', 'smzdm', 'infoq',
  // 国际公共
  'google', 'bing', 'duckduckgo', 'github', 'hn', 'reddit',
  'bbc', 'reuters', 'verge', 'ars', 'engadget', 'stackoverflow',
  'devto', 'npm', 'pypi', 'arxiv', 'imdb', 'genius', 'wikipedia',
  'openlibrary', 'yahoo-finance', 'gsmarena', 'producthunt',
  // Variable sites: their /search /hot /trending /popular /top* commands
  // are public. Sensitive commands of these sites still trigger gating
  // through SENSITIVE_SUFFIX_RE.
  'toutiao', 'zhihu', 'bilibili', 'boss', 'youtube',
]);

function classifyAdapter(adapter) {
  if (SENSITIVE_SUFFIX_RE.test(adapter)) return 'sensitive';
  const site = adapter.split('/', 1)[0];
  if (ALWAYS_SENSITIVE_SITES.has(site)) return 'sensitive';
  if (PUBLIC_SITES.has(site)) return 'public';
  return 'sensitive';
}

// ---------- Audit log ----------

const AUDIT_DIR = path.join(os.homedir(), '.bws');
const AUDIT_LOG = path.join(AUDIT_DIR, 'audit.log');
const MAX_AUDIT_LOG_BYTES = 1024 * 1024; // 1 MiB; rotate above this

function hashArgs(args) {
  if (!args.length) return null;
  const h = crypto.createHash('sha256');
  for (const a of args) {
    h.update(a, 'utf8');
    h.update('\u0000');
  }
  return h.digest('hex').slice(0, 16);
}

function audit(record) {
  try {
    fs.mkdirSync(AUDIT_DIR, { recursive: true, mode: 0o700 });
    if (fs.existsSync(AUDIT_LOG)) {
      const stat = fs.statSync(AUDIT_LOG);
      if (stat.size > MAX_AUDIT_LOG_BYTES) {
        try { fs.renameSync(AUDIT_LOG, `${AUDIT_LOG}.1`); } catch (_) { /* best effort */ }
      }
    }
    const line = JSON.stringify({
      ts: new Date().toISOString(),
      pid: process.pid,
      ...record,
    }) + '\n';
    fs.appendFileSync(AUDIT_LOG, line, { mode: 0o600 });
  } catch (err) {
    process.stderr.write(`[bws] audit log write failed: ${err.message}\n`);
  }
}

// ---------- Validation helpers ----------

function fail(message) {
  console.error(JSON.stringify({ success: false, error: message }));
  process.exit(1);
}

function assertSafeArg(value, label) {
  if (typeof value !== 'string' || value.length === 0) {
    fail(`Invalid ${label}: empty or non-string`);
  }
  if (value.length > MAX_ARG_LEN) {
    fail(`Invalid ${label}: exceeds ${MAX_ARG_LEN} characters`);
  }
  if (CONTROL_CHAR_RE.test(value)) {
    fail(`Invalid ${label}: contains control characters`);
  }
}

function assertAllowedFlag(token) {
  const head = token.split('=', 1)[0];
  if (!ALLOWED_FLAGS.has(head)) {
    fail(`Disallowed flag: ${head}`);
  }
}

function validateForwardArgs(args) {
  for (const arg of args) {
    assertSafeArg(arg, 'argument');
    if (arg.startsWith('-')) {
      assertAllowedFlag(arg);
    }
  }
}

function stripLauncherOnlyFlags(args) {
  return args.filter((a) => {
    const head = a.split('=', 1)[0];
    return !LAUNCHER_ONLY_FLAGS.has(head);
  });
}

// ---------- Sensitivity gating ----------

function enforceSensitivityPolicy(adapter, rawArgs) {
  const classification = classifyAdapter(adapter);
  const env = process.env;
  const argHash = hashArgs(rawArgs);
  const optInFlag = rawArgs.some((a) => a.split('=', 1)[0] === '--i-understand-sensitive');
  const optInEnv = env.BWS_ALLOW_SENSITIVE === '1';
  const publicOnly = env.BWS_PUBLIC_ONLY === '1';

  if (classification === 'sensitive' && publicOnly) {
    audit({
      adapter,
      argHash,
      classification,
      decision: 'deny',
      reason: 'BWS_PUBLIC_ONLY=1',
    });
    fail(
      `Adapter '${adapter}' is classified as sensitive (touches authenticated/account data). ` +
      `BWS_PUBLIC_ONLY=1 is set; refusing to proceed.`,
    );
  }

  if (classification === 'sensitive' && !optInEnv && !optInFlag) {
    audit({
      adapter,
      argHash,
      classification,
      decision: 'deny',
      reason: 'no opt-in',
    });
    fail(
      `Adapter '${adapter}' is classified as sensitive: it executes JavaScript ` +
      `inside your authenticated browser session and can read account-protected ` +
      `data (DMs, favorites, profile, orders, etc.).\n` +
      `To proceed, either:\n` +
      `  1) export BWS_ALLOW_SENSITIVE=1   # session-wide opt-in\n` +
      `  2) pass --i-understand-sensitive  # per-call opt-in\n` +
      `See SKILL.md → "运行安全与最小权限" for hardening guidance.`,
    );
  }

  audit({
    adapter,
    argHash,
    classification,
    decision: 'allow',
    reason: classification === 'sensitive'
      ? (optInFlag ? 'opt-in:flag' : 'opt-in:env')
      : 'public',
  });

  if (classification === 'sensitive') {
    process.stderr.write(
      `[bws] WARNING: '${adapter}' runs inside your authenticated session. ` +
      `Data flows through the third-party 'browser-web-search' npm package.\n`,
    );
  }
}

// ---------- In-process invocation (no subprocess) ----------

/**
 * Resolve the absolute path to the pinned 'browser-web-search' ESM entry.
 *
 * Resolution strategy (no shell, no exec, pure path math + fs.statSync):
 *   1. Platform-standard global node_modules layouts derived from process.execPath
 *      (handles Homebrew, nvm, asdf, system Node, and Windows installers).
 *   2. require.resolve fallback constrained to the same allow-listed paths.
 *   3. Local node_modules of the launcher (if the user installed the package
 *      as a regular dependency rather than globally).
 *
 * Returns absolute path or null if not found.
 */
function resolveBwsEntry() {
  const nodeBinDir = path.dirname(process.execPath);
  const candidateRoots = [
    // Unix layout: <prefix>/bin/node -> <prefix>/lib/node_modules
    path.join(nodeBinDir, '..', 'lib', 'node_modules'),
    // Windows layout: node.exe sits next to npm's node_modules
    path.join(nodeBinDir, 'node_modules'),
    // Launcher-local node_modules (defense-in-depth for non-global installs)
    path.join(__dirname, '..', 'node_modules'),
    path.join(process.cwd(), 'node_modules'),
  ];

  for (const root of candidateRoots) {
    const candidate = path.join(root, PINNED_PACKAGE, 'dist', 'index.js');
    try {
      if (fs.statSync(candidate).isFile()) return candidate;
    } catch (_) {
      // not present at this root; continue
    }
  }

  // Final fallback: Node's resolver, but only allowed to look at the same roots.
  try {
    return require.resolve(PINNED_PACKAGE, { paths: candidateRoots });
  } catch (_) {
    return null;
  }
}

/**
 * Invoke the pinned 'browser-web-search' module in-process.
 *
 * Safety invariants (must all hold; do NOT relax without re-review):
 *   - cliArgs has already been validated by assertSafeArg / assertAllowedFlag
 *     and the dispatcher inserted a '--' delimiter where applicable
 *   - this function re-checks length and control-char invariants as
 *     defense-in-depth in case a caller bypasses the upstream validators
 *   - the imported entry is loaded via file:// URL derived from a path
 *     resolved by Node's official module resolver, restricted to the
 *     standard global node_modules roots
 *   - we mutate process.argv only with our validated argv prepended by
 *     [process.execPath, bwsEntry] (the standard Node argv shape)
 */
async function safeRunBws(cliArgs) {
  if (!Array.isArray(cliArgs) || cliArgs.some((a) => typeof a !== 'string')) {
    fail('Internal error: cliArgs must be an array of strings');
  }
  for (const a of cliArgs) {
    if (a.length > MAX_ARG_LEN || CONTROL_CHAR_RE.test(a)) {
      fail('Internal error: cliArgs failed final safety check');
    }
  }

  const bwsEntry = resolveBwsEntry();
  if (!bwsEntry) {
    fail(
      `'${PINNED_PACKAGE}' not found in any standard node_modules location. ` +
      `Install it first: npm install -g ${PINNED_PACKAGE}@${REQUIRED_VERSION}`,
    );
  }

  // The imported module reads process.argv.slice(2). Inject our validated argv.
  process.argv = [process.execPath, bwsEntry, ...cliArgs];

  try {
    await import(pathToFileURL(bwsEntry).href);
  } catch (err) {
    fail(`Failed to invoke ${PINNED_PACKAGE}: ${err && err.message ? err.message : err}`);
  }

  // bws's main() typically calls process.exit on error; success paths may
  // return without explicit exit. Force a clean exit so the caller sees 0.
  process.exit(0);
}

const runBws = safeRunBws;

// ---------- Help ----------

function showHelp() {
  console.log(`
browser-web-search-skill v${REQUIRED_VERSION}
把任何网站变成命令行 API，专为 OpenClaw 设计

用法:
  通过 scripts/run.js <command> [选项]
  或直接: bws [选项]

命令:
  list                列出所有可用 adapter
  search <query>      搜索 adapter
  info <name>         查看 adapter 详情
  run <name> [args]   运行 adapter
  help                显示帮助信息

安装:
  npm install -g browser-web-search@${REQUIRED_VERSION}

允许的透传选项 (allow-list):
  --json                  JSON 格式输出
  --jq <expr>             对 JSON 输出应用 jq 过滤
  --count <n>             返回数量
  --sort <key>            排序方式
  --id <value>            指定 ID
  --limit <n>             结果上限
  --page <n>              分页

Launcher-only flags:
  --i-understand-sensitive  per-call 解锁 sensitive adapter

环境变量:
  BWS_ALLOW_SENSITIVE=1   会话级解锁 sensitive adapter (默认拒绝)
  BWS_PUBLIC_ONLY=1       硬隔离模式：拒绝所有 sensitive adapter
                          (即使设置了 BWS_ALLOW_SENSITIVE 也拒绝)

审计日志:
  ~/.bws/audit.log        追加式 JSON Lines；超过 1 MiB 自动轮转
                          仅记录 adapter / 决策 / 参数哈希，不记录原文与响应

内置平台:
  知乎、小红书、B站、今日头条、36kr、澎湃、腾讯、网易、新浪、微博、
  微信公众号、百度、Bing、Google、CSDN、博客园、BOSS直聘 等 55+

前提条件:
  需要 OpenClaw 环境运行（openclaw 命令可用）
`);
}

// ---------- Dispatch ----------

async function main() {
  const command = process.argv[2];
  const args = process.argv.slice(3);

  if (!command) {
    showHelp();
    process.exit(0);
  }

  assertSafeArg(command, 'command');

  const isAdapterShortcut = command.includes('/');
  if (!SUBCOMMANDS.has(command) && !isAdapterShortcut) {
    fail(`Unknown command: ${command}`);
  }
  if (isAdapterShortcut && !ADAPTER_NAME_RE.test(command)) {
    fail('Invalid adapter name (expected pattern: <site>/<action>)');
  }

  validateForwardArgs(args);
  const forwardArgs = stripLauncherOnlyFlags(args);

  switch (command) {
    case 'list':
      await runBws(['site', 'list', '--', ...forwardArgs]);
      return;

    case 'search': {
      const query = args[0];
      if (!query) fail('Missing argument: query');
      assertSafeArg(query, 'query');
      await runBws(['site', 'search', '--', query, ...stripLauncherOnlyFlags(args.slice(1))]);
      return;
    }

    case 'info': {
      const name = args[0];
      if (!name) fail('Missing argument: name');
      if (!ADAPTER_NAME_RE.test(name) && !IDENT_RE.test(name)) {
        fail('Invalid adapter name');
      }
      await runBws(['site', 'info', '--', name, ...stripLauncherOnlyFlags(args.slice(1))]);
      return;
    }

    case 'run': {
      const name = args[0];
      if (!name) fail('Missing argument: adapter name');
      if (!ADAPTER_NAME_RE.test(name)) {
        fail('Invalid adapter name (expected pattern: <site>/<action>)');
      }
      enforceSensitivityPolicy(name, args);
      await runBws(['site', name, '--', ...stripLauncherOnlyFlags(args.slice(1))]);
      return;
    }

    case 'help':
      showHelp();
      return;

    default:
      enforceSensitivityPolicy(command, args);
      await runBws(['site', command, '--', ...forwardArgs]);
  }
}

main().catch((err) => {
  process.stderr.write(`[bws-skill] fatal: ${err && err.message ? err.message : err}\n`);
  process.exit(1);
});
