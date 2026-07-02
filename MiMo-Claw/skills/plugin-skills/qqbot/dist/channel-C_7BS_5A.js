import { c as getPlatformAdapter, t as asOptionalObjectRecord } from "./string-normalize-R_0cKO7Q.js";
import { a as qqbotSetupAdapterShared, c as listQQBotAccountIds, i as qqbotMeta, m as getBridgeLogger, n as qqbotSetupWizard, o as DEFAULT_ACCOUNT_ID$1, p as ensurePlatformAdapter, r as qqbotConfigAdapter, s as applyQQBotAccountConfig, t as qqbotChannelConfigSchema, u as resolveQQBotAccount } from "./config-schema-iX2iJzKm.js";
import { T as debugWarn, t as getQQBotRuntime, w as debugLog, z as formatErrorMessage } from "./runtime-TzkQ0YbR.js";
import { getExecApprovalReplyMetadata } from "openclaw/plugin-sdk/approval-runtime";
import { createMessageReceiptFromOutboundResults, defineChannelMessageAdapter } from "openclaw/plugin-sdk/channel-outbound";
import { createChannelApprovalCapability } from "openclaw/plugin-sdk/approval-delivery-runtime";
import { createLazyChannelApprovalNativeRuntimeAdapter } from "openclaw/plugin-sdk/approval-handler-adapter-runtime";
import { resolveApprovalRequestChannelAccountId, resolveApprovalRequestSessionConversation } from "openclaw/plugin-sdk/approval-native-runtime";
import { normalizeLowercaseStringOrEmpty, normalizeOptionalString } from "openclaw/plugin-sdk/string-coerce-runtime";
import { markImplicitSameChatApprovalAuthorization, resolveApprovalApprovers } from "openclaw/plugin-sdk/approval-auth-runtime";
import { createChannelExecApprovalProfile, isChannelExecApprovalClientEnabledFromConfig, matchesApprovalRequestFilters } from "openclaw/plugin-sdk/approval-client-runtime";
import { normalizeAccountId } from "openclaw/plugin-sdk/routing";
import * as fs$1 from "node:fs";
import fs from "node:fs";
import * as os$1 from "node:os";
import { replaceFileAtomicSync } from "openclaw/plugin-sdk/security-runtime";
import * as path$1 from "node:path";
import path from "node:path";
import { loadJsonFile } from "openclaw/plugin-sdk/json-store";
//#region extensions/qqbot/src/engine/approval/index.ts
function buildExecApprovalText(request) {
	const expiresIn = Math.max(0, Math.round((request.expiresAtMs - Date.now()) / 1e3));
	const lines = ["🔐 命令执行审批", ""];
	const cmd = request.request.commandPreview ?? request.request.command ?? "";
	if (cmd) lines.push(`\`\`\`\n${cmd.slice(0, 300)}\n\`\`\``);
	if (request.request.cwd) lines.push(`\u{1f4c1} \u76ee\u5f55: ${request.request.cwd}`);
	if (request.request.agentId) lines.push(`\u{1f916} Agent: ${request.request.agentId}`);
	lines.push("", `\u23f1\ufe0f \u8d85\u65f6: ${expiresIn} \u79d2`);
	return lines.join("\n");
}
function appendCommandActionLines(lines, actions) {
	const commandActions = actions.filter((action) => (action.kind === "command" || action.decision == null) && typeof action.command === "string" && action.command.trim().length > 0);
	if (commandActions.length === 0) return;
	lines.push("", "🗨️ 命令:");
	for (const action of commandActions) lines.push(`- ${action.label}: ${action.command.trim()}`);
}
function buildPluginApprovalText(request, actions = []) {
	const timeoutSec = Math.round((request.request.timeoutMs ?? 12e4) / 1e3);
	const lines = [`${request.request.severity === "critical" ? "🔴" : request.request.severity === "info" ? "🔵" : "🟡"} \u5ba1\u6279\u8bf7\u6c42`, ""];
	lines.push(`\u{1f4cb} ${request.request.title}`);
	if (request.request.description) lines.push(`\u{1f4dd} ${request.request.description}`);
	if (request.request.toolName) lines.push(`\u{1f527} \u5de5\u5177: ${request.request.toolName}`);
	if (request.request.pluginId) lines.push(`\u{1f50c} \u63d2\u4ef6: ${request.request.pluginId}`);
	if (request.request.agentId) lines.push(`\u{1f916} Agent: ${request.request.agentId}`);
	appendCommandActionLines(lines, actions);
	lines.push("", `\u23f1\ufe0f \u8d85\u65f6: ${timeoutSec} \u79d2`);
	return lines.join("\n");
}
/**
* Build the three-button inline keyboard for approval messages.
*
* type=1 (Callback): click triggers INTERACTION_CREATE, button_data = data field.
* group_id "approval": clicking one button grays out the others (mutual exclusion).
* click_limit=1: each user can only click once.
* permission.type=2: all users can interact.
*/
function buildApprovalKeyboard(approvalId, allowedDecisions = [
	"allow-once",
	"allow-always",
	"deny"
]) {
	const makeBtn = (id, label, visitedLabel, data, style) => ({
		id,
		render_data: {
			label,
			visited_label: visitedLabel,
			style
		},
		action: {
			type: 1,
			data,
			permission: { type: 2 },
			click_limit: 1
		},
		group_id: "approval"
	});
	const buttons = [];
	if (allowedDecisions.includes("allow-once")) buttons.push(makeBtn("allow", "✅ 允许一次", "已允许", `approve:${approvalId}:allow-once`, 1));
	if (allowedDecisions.includes("allow-always")) buttons.push(makeBtn("always", "⭐ 始终允许", "已始终允许", `approve:${approvalId}:allow-always`, 1));
	if (allowedDecisions.includes("deny")) buttons.push(makeBtn("deny", "❌ 拒绝", "已拒绝", `approve:${approvalId}:deny`, 0));
	return { content: { rows: [{ buttons }] } };
}
/**
* Extract the delivery target from a sessionKey or turnSourceTo string.
*
* Expected formats:
*   agent:main:qqbot:direct:OPENID  -> { type: "c2c", id: "OPENID" }
*   agent:main:qqbot:c2c:OPENID     -> { type: "c2c", id: "OPENID" }
*   agent:main:qqbot:group:GROUPID  -> { type: "group", id: "GROUPID" }
*
* Returns null if neither field matches the expected pattern.
*/
function resolveApprovalTarget(sessionKey, turnSourceTo) {
	const sk = sessionKey ?? turnSourceTo;
	if (!sk) return null;
	const m = sk.match(/qqbot:(c2c|direct|group):([A-F0-9]+)/i);
	if (!m) return null;
	return {
		type: m[1].toLowerCase() === "group" ? "group" : "c2c",
		id: m[2]
	};
}
/**
* Parse the button_data string from an INTERACTION_CREATE event.
*
* Expected format: `approve:<approvalId>:<decision>`
* where approvalId may be prefixed with "exec:" or "plugin:".
*
* Returns null if the data does not match the approval button format.
*/
function parseApprovalButtonData(buttonData) {
	const m = buttonData.match(/^approve:((?:(?:exec|plugin):)?[0-9a-f-]+):(allow-once|allow-always|deny)$/i);
	if (!m) return null;
	return {
		approvalId: m[1],
		decision: m[2]
	};
}
//#endregion
//#region extensions/qqbot/src/exec-approvals.ts
function normalizeApproverId(value) {
	return normalizeOptionalString(String(value)) || void 0;
}
function resolveQQBotExecApprovalConfig(params) {
	const account = resolveQQBotAccount(params.cfg, params.accountId);
	const config = account.config.execApprovals;
	if (!config) return;
	return {
		...config,
		enabled: account.enabled && account.secretSource !== "none" ? config.enabled : false
	};
}
function getQQBotExecApprovalApprovers(params) {
	const accountConfig = resolveQQBotAccount(params.cfg, params.accountId).config;
	return resolveApprovalApprovers({
		explicit: resolveQQBotExecApprovalConfig(params)?.approvers,
		allowFrom: accountConfig.allowFrom,
		normalizeApprover: normalizeApproverId
	});
}
function countQQBotExecApprovalEligibleAccounts(params) {
	return listQQBotAccountIds(params.cfg).filter((accountId) => {
		const account = resolveQQBotAccount(params.cfg, accountId);
		if (!account.enabled || account.secretSource === "none") return false;
		const config = resolveQQBotExecApprovalConfig({
			cfg: params.cfg,
			accountId
		});
		return isChannelExecApprovalClientEnabledFromConfig({
			enabled: config?.enabled,
			approverCount: getQQBotExecApprovalApprovers({
				cfg: params.cfg,
				accountId
			}).length
		}) && matchesApprovalRequestFilters({
			request: params.request.request,
			agentFilter: config?.agentFilter,
			sessionFilter: config?.sessionFilter,
			fallbackAgentIdFromSessionKey: true
		});
	}).length;
}
function matchesQQBotRequestAccount(params) {
	const turnSourceChannel = normalizeLowercaseStringOrEmpty(params.request.request.turnSourceChannel);
	const boundAccountId = resolveApprovalRequestChannelAccountId({
		cfg: params.cfg,
		request: params.request,
		channel: "qqbot"
	});
	if (turnSourceChannel && turnSourceChannel !== "qqbot" && !boundAccountId) return countQQBotExecApprovalEligibleAccounts({
		cfg: params.cfg,
		request: params.request
	}) <= 1;
	return !boundAccountId || !params.accountId || normalizeAccountId(boundAccountId) === normalizeAccountId(params.accountId);
}
/**
* Count QQBot accounts that could actually deliver a native approval
* message — i.e. accounts that are enabled and have resolvable secrets.
* Disabled or unconfigured accounts never spawn a handler, so they
* must not contribute to the single-account shortcut in the fallback
* ownership check below.
*/
function countQQBotFallbackEligibleAccounts(cfg) {
	return listQQBotAccountIds(cfg).filter((accountId) => {
		const account = resolveQQBotAccount(cfg, accountId);
		return account.enabled && account.secretSource !== "none";
	}).length;
}
/**
* Fallback account-ownership check — applied when `execApprovals` is NOT
* configured for any QQBot account. In this mode every enabled account
* handler would otherwise race to deliver the same approval to its own
* openid namespace, so we must enforce per-account isolation.
*
* Rules:
*   - If the request carries a bound account (via `turnSourceAccountId`
*     or session binding), only the handler whose `accountId` matches it
*     delivers the approval. This is strict: a handler with an unknown
*     `accountId` (null/undefined) must not claim a bound request.
*   - If no account is bound, only deliver when there is a single
*     *eligible* QQBot account (enabled + secret resolved). Disabled or
*     unconfigured accounts never deliver anyway, so they shouldn't
*     block the remaining single account from handling the approval.
*     Multiple eligible accounts cannot safely race because openids are
*     account-scoped — cross-account delivery hits the QQ Bot API with
*     a mismatched token and fails.
*/
function matchesQQBotFallbackRequestAccount(params) {
	const boundAccountId = resolveApprovalRequestChannelAccountId({
		cfg: params.cfg,
		request: params.request,
		channel: "qqbot"
	});
	if (boundAccountId) {
		if (!params.accountId) return false;
		return normalizeAccountId(boundAccountId) === normalizeAccountId(params.accountId);
	}
	return countQQBotFallbackEligibleAccounts(params.cfg) <= 1;
}
/**
* Unified per-account ownership check used by both the profile and
* fallback approval paths. Dispatches to the profile rules when the
* current account has `execApprovals` configured, otherwise uses the
* fallback rules.
*
* This is the single source of truth for "does this QQBot handler own
* this approval request?" and is consumed by both the capability
* gate (shouldHandle) and the lazy native runtime adapter.
*/
function matchesQQBotApprovalAccount(params) {
	const normalized = {
		cfg: params.cfg,
		accountId: params.accountId,
		request: params.request
	};
	if (resolveQQBotExecApprovalConfig(normalized) !== void 0) return matchesQQBotRequestAccount(normalized);
	return matchesQQBotFallbackRequestAccount(normalized);
}
const qqbotExecApprovalProfile = createChannelExecApprovalProfile({
	resolveConfig: resolveQQBotExecApprovalConfig,
	resolveApprovers: getQQBotExecApprovalApprovers,
	matchesRequestAccount: matchesQQBotRequestAccount,
	fallbackAgentIdFromSessionKey: true,
	requireClientEnabledForLocalPromptSuppression: false
});
const isQQBotExecApprovalClientEnabled = qqbotExecApprovalProfile.isClientEnabled;
const isQQBotExecApprovalApprover = qqbotExecApprovalProfile.isApprover;
const isQQBotExecApprovalAuthorizedSender = qqbotExecApprovalProfile.isAuthorizedSender;
const shouldHandleQQBotExecApprovalRequest = qqbotExecApprovalProfile.shouldHandleRequest;
function authorizeQQBotApprovalAction(params) {
	if (resolveQQBotExecApprovalConfig(params) === void 0) return markImplicitSameChatApprovalAuthorization({ authorized: true });
	return (params.approvalKind === "plugin" ? isQQBotExecApprovalApprover(params) : isQQBotExecApprovalAuthorizedSender(params)) ? { authorized: true } : {
		authorized: false,
		reason: "You are not authorized to approve this request."
	};
}
//#endregion
//#region extensions/qqbot/src/bridge/approval/capability.ts
/**
* QQ Bot Approval Capability — entry point.
*
* QQBot uses a simpler approval model than Telegram/Slack: when no
* approver list is configured, the bot sends the approval message to the
* originating conversation and any participant can approve from there.
*
* When `execApprovals` IS configured, it gates which requests are
* handled natively and who is authorized.  When it is NOT configured,
* QQBot falls back to "always handle, anyone can approve".
*/
/**
* When `execApprovals` is configured, delegate to the profile-based
* check.  Otherwise fall back to target-resolvability plus the shared
* per-account ownership rule in `matchesQQBotApprovalAccount` so that
* each QQBot account handler only delivers approvals that originated
* from its own account (openids are account-scoped — cross-account
* delivery fails with 500 on the QQ Bot API).
*/
function shouldHandleRequest(params) {
	if (hasExecApprovalConfig(params)) return shouldHandleQQBotExecApprovalRequest(params);
	if (!canResolveTarget(params.request)) return false;
	return matchesQQBotApprovalAccount({
		cfg: params.cfg,
		accountId: params.accountId,
		request: params.request
	});
}
function hasExecApprovalConfig(params) {
	return resolveQQBotExecApprovalConfig(params) !== void 0;
}
function isNativeDeliveryEnabled(params) {
	if (hasExecApprovalConfig(params)) return isQQBotExecApprovalClientEnabled(params);
	const account = resolveQQBotAccount(params.cfg, params.accountId);
	return account.enabled && account.secretSource !== "none";
}
function canResolveTarget(request) {
	if (resolveApprovalTarget(request.request.sessionKey ?? null, request.request.turnSourceTo ?? null)) return true;
	return resolveApprovalRequestSessionConversation({
		request,
		channel: "qqbot",
		bundledFallback: true
	})?.id != null;
}
function createQQBotApprovalCapability() {
	return createChannelApprovalCapability({
		authorizeActorAction: ({ cfg, accountId, senderId, approvalKind }) => authorizeQQBotApprovalAction({
			cfg,
			accountId,
			senderId,
			approvalKind
		}),
		getActionAvailabilityState: ({ cfg, accountId }) => {
			return isNativeDeliveryEnabled({
				cfg,
				accountId
			}) ? { kind: "enabled" } : { kind: "disabled" };
		},
		getExecInitiatingSurfaceState: ({ cfg, accountId }) => {
			return isNativeDeliveryEnabled({
				cfg,
				accountId
			}) ? { kind: "enabled" } : { kind: "disabled" };
		},
		describeExecApprovalSetup: ({ accountId }) => {
			return `QQBot native exec approvals are enabled by default. To restrict who can approve, configure \`${accountId && accountId !== "default" ? `channels.qqbot.accounts.${accountId}` : "channels.qqbot"}.execApprovals.approvers\` with QQ user OpenIDs.`;
		},
		delivery: {
			hasConfiguredDmRoute: () => true,
			shouldSuppressForwardingFallback: (input) => {
				const channel = normalizeOptionalString(input.target?.channel);
				if (channel !== "qqbot") return false;
				const accountId = normalizeOptionalString(input.target?.accountId) ?? normalizeOptionalString(input.request?.request?.turnSourceAccountId);
				const result = isNativeDeliveryEnabled({
					cfg: input.cfg,
					accountId
				});
				getBridgeLogger().debug?.(`[qqbot:approval] shouldSuppressForwardingFallback channel=${channel} accountId=${accountId} → ${result}`);
				return result;
			}
		},
		native: {
			describeDeliveryCapabilities: ({ cfg, accountId }) => ({
				enabled: isNativeDeliveryEnabled({
					cfg,
					accountId
				}),
				preferredSurface: "origin",
				supportsOriginSurface: true,
				supportsApproverDmSurface: false,
				notifyOriginWhenDmOnly: false
			}),
			resolveOriginTarget: ({ request }) => {
				const target = resolveApprovalTarget(request.request.sessionKey ?? null, request.request.turnSourceTo ?? null);
				if (target) return { to: `${target.type}:${target.id}` };
				const sessionConversation = resolveApprovalRequestSessionConversation({
					request,
					channel: "qqbot",
					bundledFallback: true
				});
				if (sessionConversation?.id) return { to: `${sessionConversation.kind === "group" ? "group" : "c2c"}:${sessionConversation.id}` };
				return null;
			}
		},
		nativeRuntime: createLazyChannelApprovalNativeRuntimeAdapter({
			eventKinds: ["exec", "plugin"],
			isConfigured: ({ cfg, accountId }) => {
				const result = isNativeDeliveryEnabled({
					cfg,
					accountId
				});
				getBridgeLogger().debug?.(`[qqbot:approval] nativeRuntime.isConfigured accountId=${accountId} → ${result}`);
				return result;
			},
			shouldHandle: ({ cfg, accountId, request }) => {
				const result = shouldHandleRequest({
					cfg,
					accountId,
					request
				});
				getBridgeLogger().debug?.(`[qqbot:approval] nativeRuntime.shouldHandle accountId=${accountId} → ${result}`);
				return result;
			},
			load: async () => {
				ensurePlatformAdapter();
				return (await import("./handler-runtime-CSVOet7I.js")).qqbotApprovalNativeRuntime;
			}
		})
	});
}
const qqbotApprovalCapability = createQQBotApprovalCapability();
let cachedCapability;
function getQQBotApprovalCapability() {
	cachedCapability ??= qqbotApprovalCapability;
	return cachedCapability;
}
//#endregion
//#region extensions/qqbot/src/bridge/narrowing.ts
/**
* Map resolved plugin account to the engine gateway account shape (single assertion on nested config).
*/
function toGatewayAccount(account) {
	return {
		accountId: account.accountId,
		appId: account.appId,
		clientSecret: account.clientSecret,
		markdownSupport: account.markdownSupport,
		systemPrompt: account.systemPrompt,
		config: account.config
	};
}
/**
* Persist OpenClaw config through the injected plugin runtime (typed entry point).
*/
async function writeOpenClawConfigThroughRuntime(runtime, cfg) {
	await runtime.config.replaceConfigFile({
		nextConfig: cfg,
		afterWrite: { mode: "auto" }
	});
}
//#endregion
//#region extensions/qqbot/src/engine/utils/platform.ts
/**
* Cross-platform path and detection helpers for core/ modules.
*
* Provides home/data/media directory helpers, platform detection,
* silk-wasm availability checks — all without importing `openclaw/plugin-sdk`.
* The temp-directory fallback is delegated to the PlatformAdapter.
*/
/**
* Resolve the current user's OS home directory safely across platforms.
*
* Priority:
* 1. `os.homedir()`
* 2. `$HOME` or `%USERPROFILE%`
* 3. PlatformAdapter.getTempDir() as a last resort
*
* This is the *operating-system* home and intentionally ignores
* `OPENCLAW_HOME`. Persistent QQ Bot data (sessions, known users, refs) is
* keyed on this value to keep upgrades from hiding existing state when an
* operator later sets `OPENCLAW_HOME`.
*/
function getHomeDir() {
	try {
		const home = os$1.homedir();
		if (home && fs$1.existsSync(home)) return home;
	} catch {}
	const envHome = process.env.HOME || process.env.USERPROFILE;
	if (envHome && fs$1.existsSync(envHome)) return envHome;
	return getPlatformAdapter().getTempDir();
}
/**
* Resolve the effective OpenClaw home directory.
*
* Mirrors the contract from core (`src/infra/home-dir.ts::resolveEffectiveHomeDir`)
* so QQ Bot media roots live under the same tree the rest of OpenClaw treats as
* `~`. The extension cannot import the core helper directly (it is a separate
* package with `openclaw` as a peer dependency), so this re-implements the
* minimal contract:
*
* 1. `OPENCLAW_HOME` when set (with `~` / `~/...` expanded against the OS home).
* 2. Otherwise fall back to {@link getHomeDir} so existing single-home
*    deployments are unaffected.
*
* Empty / `"undefined"` / `"null"` strings are treated as unset to match how
* core normalizes the variable.
*/
function resolveOpenClawHome() {
	const raw = process.env.OPENCLAW_HOME?.trim();
	if (!raw || raw === "undefined" || raw === "null") return getHomeDir();
	if (raw === "~" || raw.startsWith("~/") || raw.startsWith("~\\")) {
		const osHome = getHomeDir();
		if (raw === "~") return osHome;
		return path$1.join(osHome, raw.slice(2));
	}
	return raw;
}
/**
* Return a path under `~/.openclaw/qqbot` without creating it.
*
* Anchored on the OS home (not `OPENCLAW_HOME`) so persisted QQ Bot data
* (sessions, known users, ref index, credential backups) does not silently
* disappear when an operator adds `OPENCLAW_HOME` after the fact.
*/
function getQQBotDataPath(...subPaths) {
	return path$1.join(getHomeDir(), ".openclaw", "qqbot", ...subPaths);
}
/** Return a path under `~/.openclaw/qqbot`, creating it on demand. */
function getQQBotDataDir(...subPaths) {
	const dir = getQQBotDataPath(...subPaths);
	if (!fs$1.existsSync(dir)) fs$1.mkdirSync(dir, { recursive: true });
	return dir;
}
/**
* Return a path under `<openclaw-home>/.openclaw/media/qqbot` without creating it.
*
* Unlike `getQQBotDataPath`, this lives under OpenClaw's core media allowlist
* so downloaded images and audio can be accessed by framework media tooling.
* The base honors `OPENCLAW_HOME` (when set) so files written by agents into
* the OpenClaw-managed media tree are reachable by this plugin even when
* `HOME` and `OPENCLAW_HOME` differ (Docker, multi-user hosts). Fixes #83562.
*/
function getQQBotMediaPath(...subPaths) {
	return path$1.join(resolveOpenClawHome(), ".openclaw", "media", "qqbot", ...subPaths);
}
/** Return a path under `<openclaw-home>/.openclaw/media/qqbot`, creating it on demand. */
function getQQBotMediaDir(...subPaths) {
	const dir = getQQBotMediaPath(...subPaths);
	if (!fs$1.existsSync(dir)) fs$1.mkdirSync(dir, { recursive: true });
	return dir;
}
/**
* Return `<openclaw-home>/.openclaw/media`, OpenClaw's shared media root.
*
* This mirrors the directory that core's `buildMediaLocalRoots` exposes as an
* allowlisted location (see `openclaw/src/media/local-roots.ts`). Using it as a
* QQ Bot payload root lets the plugin trust framework-produced files that live
* in sibling subdirectories such as `outbound/` (written by
* `saveMediaBuffer(..., "outbound", ...)`) or `inbound/`, while still keeping
* the check anchored to a single, well-known directory. Like
* {@link getQQBotMediaPath}, the base honors `OPENCLAW_HOME`.
*/
function getOpenClawMediaDir() {
	return path$1.join(resolveOpenClawHome(), ".openclaw", "media");
}
function isWindows() {
	return process.platform === "win32";
}
/** Return the preferred temporary directory. */
function getTempDir() {
	return getPlatformAdapter().getTempDir();
}
let silkWasmAvailable = null;
/** Check whether silk-wasm can run in the current environment. */
async function checkSilkWasmAvailable() {
	if (silkWasmAvailable !== null) return silkWasmAvailable;
	try {
		const { isSilk } = await import("silk-wasm");
		isSilk(new Uint8Array(0));
		silkWasmAvailable = true;
		debugLog("[platform] silk-wasm: available");
	} catch (err) {
		silkWasmAvailable = false;
		debugWarn(`[platform] silk-wasm: NOT available (${formatErrorMessage(err)})`);
	}
	return silkWasmAvailable;
}
/** Expand `~` to the current user's home directory. */
function expandTilde(p) {
	if (!p) return p;
	if (p === "~") return getHomeDir();
	if (p.startsWith("~/") || p.startsWith("~\\")) return path$1.join(getHomeDir(), p.slice(2));
	return p;
}
/** Normalize a user-provided path by trimming, stripping `file://`, and expanding `~`. */
function normalizePath(p) {
	let result = p.trim();
	if (result.startsWith("file://")) {
		result = result.slice(7);
		try {
			result = decodeURIComponent(result);
		} catch {}
	}
	return expandTilde(result);
}
/** Return true when the string looks like a local filesystem path rather than a URL. */
function isLocalPath(p) {
	if (!p) return false;
	if (p.startsWith("file://")) return true;
	if (p === "~" || p.startsWith("~/") || p.startsWith("~\\")) return true;
	if (p.startsWith("/")) return true;
	if (/^[a-zA-Z]:[\\/]/.test(p)) return true;
	if (p.startsWith("\\\\")) return true;
	if (p.startsWith("./") || p.startsWith("../")) return true;
	if (p.startsWith(".\\") || p.startsWith("..\\")) return true;
	return false;
}
function isPathWithinRoot(candidate, root) {
	const relative = path$1.relative(root, candidate);
	return relative === "" || !relative.startsWith("..") && !path$1.isAbsolute(relative);
}
/** Remap legacy or hallucinated QQ Bot local media paths to real files when possible. */
function resolveQQBotLocalMediaPath(p) {
	const normalized = normalizePath(p);
	if (!isLocalPath(normalized) || fs$1.existsSync(normalized)) return normalized;
	const osHomeDir = getHomeDir();
	const openclawHomeDir = resolveOpenClawHome();
	const mediaRoot = getQQBotMediaPath();
	const dataRoot = getQQBotDataPath();
	const candidateRoots = [
		...Array.from(new Set([path$1.join(osHomeDir, ".openclaw", "workspace", "qqbot"), path$1.join(openclawHomeDir, ".openclaw", "workspace", "qqbot")])).map((from) => ({
			from,
			to: mediaRoot
		})),
		{
			from: dataRoot,
			to: mediaRoot
		},
		{
			from: mediaRoot,
			to: dataRoot
		}
	];
	for (const { from, to } of candidateRoots) {
		if (!isPathWithinRoot(normalized, from)) continue;
		const relative = path$1.relative(from, normalized);
		const candidate = path$1.join(to, relative);
		if (fs$1.existsSync(candidate)) {
			debugWarn(`[platform] Remapped missing QQBot media path ${normalized} -> ${candidate}`);
			return candidate;
		}
	}
	return normalized;
}
/**
* Resolve a structured-payload local file path and enforce that it stays within
* QQ Bot-owned storage roots.
*/
function resolveQQBotPayloadLocalFilePath(p) {
	const candidate = resolveQQBotLocalMediaPath(p);
	if (!candidate.trim()) return null;
	const resolvedCandidate = path$1.resolve(candidate);
	if (!fs$1.existsSync(resolvedCandidate)) return null;
	const canonicalCandidate = fs$1.realpathSync(resolvedCandidate);
	const allowedRoots = [getOpenClawMediaDir(), getQQBotMediaPath()];
	for (const root of allowedRoots) {
		const resolvedRoot = path$1.resolve(root);
		if (isPathWithinRoot(canonicalCandidate, fs$1.existsSync(resolvedRoot) ? fs$1.realpathSync(resolvedRoot) : resolvedRoot)) return canonicalCandidate;
	}
	return null;
}
//#endregion
//#region extensions/qqbot/src/engine/utils/data-paths.ts
/**
* Centralised filename helpers for persisted QQBot state.
*
* Every persistence module routes file paths through these helpers so the
* naming convention stays in sync and legacy migrations are handled
* consistently.
*
* Key design decisions:
* - Credential backup is keyed only by `accountId` because recovery runs
*   exactly when the appId is missing from config.
*/
/**
* Normalise an identifier so it is safe to embed in a filename.
* Keeps alphanumerics, dot, underscore, dash; everything else becomes `_`.
*/
function safeName(id) {
	return id.replace(/[^a-zA-Z0-9._-]/g, "_");
}
/**
* Per-accountId credential backup file. Not keyed by appId because the
* whole point of this file is to recover credentials when appId is
* missing from the live config.
*/
function getCredentialBackupFile(accountId) {
	return path.join(getQQBotDataPath("data"), `credential-backup-${safeName(accountId)}.json`);
}
/** Legacy single-file credential backup (pre-multi-account-isolation). */
function getLegacyCredentialBackupFile() {
	return path.join(getQQBotDataPath("data"), "credential-backup.json");
}
//#endregion
//#region extensions/qqbot/src/engine/config/credential-backup.ts
/**
* Credential backup & recovery.
* 凭证暂存与恢复。
*
* Solves the "hot-upgrade interrupted, appId/secret vanished from
* openclaw.json" failure mode.
*
* Mechanics:
*   - After each successful gateway start we snapshot the currently
*     resolved `appId` / `clientSecret` to a per-account backup file.
*   - During plugin startup, if the live config has an empty appId or
*     secret, the gateway consults the backup and restores the values
*     via the config mutation API.
*   - Backups live under `~/.openclaw/qqbot/data/` so they survive
*     plugin directory replacement.
*
* Safety notes:
*   - Only restore when credentials are **actually empty** — never
*     overwrite a user's intentional config change.
*   - Atomic write (temp file + rename) to avoid torn files.
*   - Per-account file: `credential-backup-<accountId>.json`. We do
*     **not** also key by appId because recovery happens precisely
*     when appId is unknown.
*   - Legacy single `credential-backup.json` is migrated automatically
*     when the stored accountId matches the caller.
*/
/** Persist a credential snapshot (called once gateway reaches READY). */
function saveCredentialBackup(accountId, appId, clientSecret) {
	if (!appId || !clientSecret) return;
	try {
		const backupPath = getCredentialBackupFile(accountId);
		const data = {
			accountId,
			appId,
			clientSecret,
			savedAt: (/* @__PURE__ */ new Date()).toISOString()
		};
		replaceFileAtomicSync({
			filePath: backupPath,
			content: `${JSON.stringify(data, null, 2)}\n`,
			tempPrefix: ".qqbot-credential-backup"
		});
	} catch {}
}
/**
* Load a credential snapshot for `accountId`.
*
* Consults the new per-account file first; falls back to the legacy
* global backup file and migrates it when the embedded `accountId`
* matches the request. Returns `null` when no usable backup exists.
*/
function loadCredentialBackup(accountId) {
	try {
		if (accountId) {
			const data = loadJsonFile(getCredentialBackupFile(accountId));
			if (data?.appId && data.clientSecret) return data;
		}
		const legacy = getLegacyCredentialBackupFile();
		const data = loadJsonFile(legacy);
		if (data) {
			if (!data?.appId || !data?.clientSecret) return null;
			if (accountId && data.accountId !== accountId) return null;
			if (data.accountId) try {
				replaceFileAtomicSync({
					filePath: getCredentialBackupFile(data.accountId),
					content: `${JSON.stringify(data, null, 2)}\n`,
					tempPrefix: ".qqbot-credential-backup"
				});
				fs.unlinkSync(legacy);
			} catch {}
			return data;
		}
	} catch {}
	return null;
}
//#endregion
//#region extensions/qqbot/src/engine/config/credentials.ts
/**
* QQBot credential management (pure logic layer).
* QQBot 凭证管理（纯逻辑层）。
*
* Credential clearing and field-level cleanup for logout and setup
* flows. All functions operate on plain objects (Record<string, unknown>)
* and stay framework-agnostic.
*/
/**
* Remove clientSecret / clientSecretFile from a QQBot account config.
*
* Returns a shallow-cloned config with credentials removed, plus flags
* indicating whether anything actually changed.
*/
function clearAccountCredentials(cfg, accountId) {
	const nextCfg = { ...cfg };
	const channels = asOptionalObjectRecord(cfg.channels);
	const nextQQBot = channels?.qqbot ? { ...asOptionalObjectRecord(channels.qqbot) } : void 0;
	let cleared = false;
	let changed = false;
	if (nextQQBot) {
		const qqbot = nextQQBot;
		if (accountId === "default") {
			if (qqbot.clientSecret) {
				delete qqbot.clientSecret;
				cleared = true;
				changed = true;
			}
			if (qqbot.clientSecretFile) {
				delete qqbot.clientSecretFile;
				cleared = true;
				changed = true;
			}
		}
		const accounts = qqbot.accounts;
		if (accounts && accountId in accounts) {
			const entry = accounts[accountId];
			if (entry && "clientSecret" in entry) {
				delete entry.clientSecret;
				cleared = true;
				changed = true;
			}
			if (entry && "clientSecretFile" in entry) {
				delete entry.clientSecretFile;
				cleared = true;
				changed = true;
			}
			if (entry && Object.keys(entry).length === 0) {
				delete accounts[accountId];
				changed = true;
			}
		}
	}
	if (changed && nextQQBot) nextCfg.channels = {
		...channels,
		qqbot: nextQQBot
	};
	return {
		nextCfg,
		cleared,
		changed
	};
}
//#endregion
//#region extensions/qqbot/src/engine/messaging/target-parser.ts
/**
* Parse a qqbot target string into a structured delivery target.
*
* Supported formats:
* - `qqbot:c2c:openid` → C2C direct message
* - `qqbot:group:groupid` → Group message
* - `qqbot:channel:channelid` → Channel message
* - `c2c:openid` → C2C (without qqbot: prefix)
* - `group:groupid` → Group (without qqbot: prefix)
* - `channel:channelid` → Channel (without qqbot: prefix)
* - `openid` → C2C (bare openid, default)
*
* @param to - Raw target string.
* @returns Parsed target with type and id.
* @throws {Error} When the target format is invalid.
*/
function parseTarget(to) {
	let id = to.replace(/^qqbot:/i, "");
	if (id.startsWith("c2c:")) {
		const userId = id.slice(4);
		if (!userId) throw new Error(`Invalid c2c target format: ${to} - missing user ID`);
		return {
			type: "c2c",
			id: userId
		};
	}
	if (id.startsWith("group:")) {
		const groupId = id.slice(6);
		if (!groupId) throw new Error(`Invalid group target format: ${to} - missing group ID`);
		return {
			type: "group",
			id: groupId
		};
	}
	if (id.startsWith("channel:")) {
		const channelId = id.slice(8);
		if (!channelId) throw new Error(`Invalid channel target format: ${to} - missing channel ID`);
		return {
			type: "channel",
			id: channelId
		};
	}
	if (!id) throw new Error(`Invalid target format: ${to} - empty ID after removing qqbot: prefix`);
	return {
		type: "c2c",
		id
	};
}
/**
* Normalize a QQ Bot target string into the canonical `qqbot:...` form.
*
* Returns `undefined` when the target does not look like a QQ Bot address.
*/
function normalizeTarget(target) {
	const id = target.replace(/^qqbot:/i, "");
	if (id.startsWith("c2c:") || id.startsWith("group:") || id.startsWith("channel:")) return `qqbot:${id}`;
	if (/^[0-9a-fA-F]{32}$/.test(id)) return `qqbot:c2c:${id}`;
	if (/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(id)) return `qqbot:c2c:${id}`;
}
/**
* Return true when the string looks like a QQ Bot target ID.
*/
function looksLikeQQBotTarget(id) {
	if (/^qqbot:(c2c|group|channel):/i.test(id)) return true;
	if (/^(c2c|group|channel):/i.test(id)) return true;
	if (/^[0-9a-fA-F]{32}$/.test(id)) return true;
	return /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(id);
}
//#endregion
//#region extensions/qqbot/src/channel.ts
let gatewayModulePromise;
function loadGatewayModule() {
	gatewayModulePromise ??= import("./gateway-BdWwKDtj.js");
	return gatewayModulePromise;
}
function createQQBotSendReceipt(params) {
	const messageId = params.messageId?.trim();
	return createMessageReceiptFromOutboundResults({
		results: messageId ? [{
			channel: "qqbot",
			messageId,
			conversationId: params.target
		}] : [],
		threadId: params.target,
		kind: params.kind
	});
}
async function sendQQBotText(params) {
	await loadGatewayModule();
	const account = resolveQQBotAccount(params.cfg, params.accountId);
	const { sendText } = await import("./outbound-DHc9KJCp.js").then((n) => n.t);
	const result = await sendText({
		to: params.to,
		text: params.text,
		accountId: params.accountId,
		replyToId: params.replyToId,
		account: toGatewayAccount(account)
	});
	return {
		channel: "qqbot",
		messageId: result.messageId ?? "",
		receipt: createQQBotSendReceipt({
			messageId: result.messageId,
			target: params.to,
			kind: "text"
		}),
		meta: result.error ? { error: result.error } : void 0
	};
}
async function sendQQBotMedia(params) {
	await loadGatewayModule();
	const account = resolveQQBotAccount(params.cfg, params.accountId);
	const { sendMedia } = await import("./outbound-DHc9KJCp.js").then((n) => n.t);
	const result = await sendMedia({
		to: params.to,
		text: params.text ?? "",
		mediaUrl: params.mediaUrl ?? "",
		accountId: params.accountId,
		replyToId: params.replyToId,
		account: toGatewayAccount(account)
	});
	return {
		channel: "qqbot",
		messageId: result.messageId ?? "",
		receipt: createQQBotSendReceipt({
			messageId: result.messageId,
			target: params.to,
			kind: "media"
		}),
		meta: result.error ? { error: result.error } : void 0
	};
}
function toQQBotMessageSendResult(result) {
	return {
		messageId: result.messageId,
		receipt: result.receipt
	};
}
const qqbotMessageAdapter = defineChannelMessageAdapter({
	id: "qqbot",
	durableFinal: { capabilities: {
		text: true,
		media: true,
		replyTo: true
	} },
	send: {
		text: async (ctx) => toQQBotMessageSendResult(await sendQQBotText({
			cfg: ctx.cfg,
			to: ctx.to,
			text: ctx.text,
			accountId: ctx.accountId,
			replyToId: ctx.replyToId
		})),
		media: async (ctx) => toQQBotMessageSendResult(await sendQQBotMedia({
			cfg: ctx.cfg,
			to: ctx.to,
			text: ctx.text,
			mediaUrl: ctx.mediaUrl,
			accountId: ctx.accountId,
			replyToId: ctx.replyToId
		}))
	}
});
const EXEC_APPROVAL_COMMAND_RE = /\/approve(?:@[^\s]+)?\s+[A-Za-z0-9][A-Za-z0-9._:-]*\s+(?:allow-once|allow-always|always|deny)\b/i;
function persistAccountCredentialSnapshot(account) {
	if (account.appId && account.clientSecret) saveCredentialBackup(account.accountId, account.appId, account.clientSecret);
}
function shouldSuppressLocalQQBotApprovalPrompt(params) {
	if (params.hint?.kind !== "approval-pending" || params.hint.approvalKind !== "exec") return false;
	const account = resolveQQBotAccount(params.cfg, params.accountId);
	if (!account.enabled || account.secretSource === "none") return false;
	if (getExecApprovalReplyMetadata(params.payload)) return true;
	const text = typeof params.payload.text === "string" ? params.payload.text : "";
	return EXEC_APPROVAL_COMMAND_RE.test(text);
}
const qqbotPlugin = {
	id: "qqbot",
	setupWizard: qqbotSetupWizard,
	meta: { ...qqbotMeta },
	capabilities: {
		chatTypes: ["direct", "group"],
		media: true,
		reactions: false,
		threads: false,
		blockStreaming: true
	},
	reload: { configPrefixes: ["channels.qqbot"] },
	configSchema: qqbotChannelConfigSchema,
	config: {
		...qqbotConfigAdapter,
		/**
		* Treat an account as configured when either the live config has
		* credentials OR a recoverable credential backup exists. This mirrors
		* the standalone plugin and lets the gateway survive a hot upgrade
		* that wiped openclaw.json mid-flight.
		*/
		isConfigured: (account) => {
			if (qqbotConfigAdapter.isConfigured(account)) return true;
			if (!account) return false;
			const backup = loadCredentialBackup(account.accountId);
			return Boolean(backup?.appId && backup?.clientSecret);
		}
	},
	setup: { ...qqbotSetupAdapterShared },
	approvalCapability: getQQBotApprovalCapability(),
	message: qqbotMessageAdapter,
	messaging: {
		targetPrefixes: ["qqbot"],
		/** Normalize common QQ Bot target formats into the canonical qqbot:... form. */
		normalizeTarget,
		targetResolver: {
			/** Return true when the id looks like a QQ Bot target. */
			looksLikeId: looksLikeQQBotTarget,
			hint: "QQ Bot target format: qqbot:c2c:openid (direct) or qqbot:group:groupid (group)"
		}
	},
	outbound: {
		deliveryMode: "direct",
		chunker: (text, limit) => getQQBotRuntime().channel.text.chunkMarkdownText(text, limit),
		chunkerMode: "markdown",
		textChunkLimit: 5e3,
		shouldSuppressLocalPayloadPrompt: ({ cfg, accountId, payload, hint }) => shouldSuppressLocalQQBotApprovalPrompt({
			cfg,
			accountId,
			payload,
			hint
		}),
		sendText: async ({ to, text, accountId, replyToId, cfg }) => await sendQQBotText({
			cfg,
			to,
			text,
			accountId,
			replyToId
		}),
		sendMedia: async ({ to, text, mediaUrl, accountId, replyToId, cfg }) => await sendQQBotMedia({
			cfg,
			to,
			text,
			mediaUrl,
			accountId,
			replyToId
		})
	},
	gateway: {
		startAccount: async (ctx) => {
			let { account, cfg } = ctx;
			const { abortSignal, log } = ctx;
			if (!account.appId || !account.clientSecret) {
				const backup = loadCredentialBackup(account.accountId);
				if (backup?.appId && backup?.clientSecret) try {
					const nextCfg = applyQQBotAccountConfig(cfg, account.accountId, {
						appId: backup.appId,
						clientSecret: backup.clientSecret
					});
					await writeOpenClawConfigThroughRuntime(getQQBotRuntime(), nextCfg);
					cfg = nextCfg;
					account = resolveQQBotAccount(nextCfg, account.accountId);
					log?.info(`[qqbot:${account.accountId}] Restored credentials from backup (appId=${account.appId})`);
				} catch (err) {
					log?.error(`[qqbot:${account.accountId}] Failed to restore credentials from backup: ${err instanceof Error ? err.message : String(err)}`);
				}
			}
			const { startGateway } = await loadGatewayModule();
			log?.info(`[qqbot:${account.accountId}] Starting gateway — appId=${account.appId}, enabled=${account.enabled}, name=${account.name ?? "unnamed"}`);
			await startGateway({
				account,
				abortSignal,
				cfg,
				log,
				channelRuntime: ctx.channelRuntime,
				onReady: () => {
					log?.info(`[qqbot:${account.accountId}] Gateway ready`);
					ctx.setStatus({
						...ctx.getStatus(),
						running: true,
						connected: true,
						lastConnectedAt: Date.now()
					});
					persistAccountCredentialSnapshot(account);
				},
				onResumed: () => {
					log?.info(`[qqbot:${account.accountId}] Gateway resumed`);
					ctx.setStatus({
						...ctx.getStatus(),
						running: true,
						connected: true,
						lastConnectedAt: Date.now()
					});
					persistAccountCredentialSnapshot(account);
				},
				onError: (error) => {
					log?.error(`[qqbot:${account.accountId}] Gateway error: ${error.message}`);
					ctx.setStatus({
						...ctx.getStatus(),
						lastError: error.message
					});
				}
			});
		},
		logoutAccount: async ({ accountId, cfg }) => {
			const { nextCfg, cleared, changed } = clearAccountCredentials(cfg, accountId);
			if (changed) await writeOpenClawConfigThroughRuntime(getQQBotRuntime(), nextCfg);
			const loggedOut = resolveQQBotAccount(changed ? nextCfg : cfg, accountId).secretSource === "none";
			return {
				ok: true,
				cleared,
				envToken: Boolean(process.env.QQBOT_CLIENT_SECRET),
				loggedOut
			};
		}
	},
	status: {
		defaultRuntime: {
			accountId: DEFAULT_ACCOUNT_ID$1,
			running: false,
			connected: false,
			lastConnectedAt: null,
			lastError: null,
			lastInboundAt: null,
			lastOutboundAt: null
		},
		buildChannelSummary: ({ snapshot }) => ({
			configured: snapshot.configured ?? false,
			tokenSource: snapshot.tokenSource ?? "none",
			running: snapshot.running ?? false,
			connected: snapshot.connected ?? false,
			lastConnectedAt: snapshot.lastConnectedAt ?? null,
			lastError: snapshot.lastError ?? null
		}),
		buildAccountSnapshot: ({ account, runtime }) => ({
			accountId: account?.accountId ?? DEFAULT_ACCOUNT_ID$1,
			name: account?.name,
			enabled: account?.enabled ?? false,
			configured: Boolean(account?.appId && account?.clientSecret),
			tokenSource: account?.secretSource,
			running: runtime?.running ?? false,
			connected: runtime?.connected ?? false,
			lastConnectedAt: runtime?.lastConnectedAt ?? null,
			lastError: runtime?.lastError ?? null,
			lastInboundAt: runtime?.lastInboundAt ?? null,
			lastOutboundAt: runtime?.lastOutboundAt ?? null
		})
	}
};
//#endregion
export { parseApprovalButtonData as C, buildPluginApprovalText as S, matchesQQBotApprovalAccount as _, getQQBotDataDir as a, buildApprovalKeyboard as b, getQQBotMediaPath as c, isWindows as d, normalizePath as f, isQQBotExecApprovalClientEnabled as g, authorizeQQBotApprovalAction as h, getHomeDir as i, getTempDir as l, toGatewayAccount as m, parseTarget as n, getQQBotDataPath as o, resolveQQBotPayloadLocalFilePath as p, checkSilkWasmAvailable as r, getQQBotMediaDir as s, qqbotPlugin as t, isLocalPath as u, resolveQQBotExecApprovalConfig as v, resolveApprovalTarget as w, buildExecApprovalText as x, shouldHandleQQBotExecApprovalRequest as y };
