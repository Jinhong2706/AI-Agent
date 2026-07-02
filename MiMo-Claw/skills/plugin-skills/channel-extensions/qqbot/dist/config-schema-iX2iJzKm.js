import { a as normalizeStringifiedEntries, c as getPlatformAdapter, d as registerPlatformAdapterFactory, l as hasPlatformAdapter, n as normalizeLowercaseStringOrEmpty, o as readStringField, r as normalizeOptionalLowercaseString, t as asOptionalObjectRecord, u as registerPlatformAdapter } from "./string-normalize-R_0cKO7Q.js";
import { buildSecretInputSchema, coerceSecretRef, hasConfiguredSecretInput, normalizeResolvedSecretInputString, normalizeSecretInputString } from "openclaw/plugin-sdk/secret-input";
import { resolvePreferredOpenClawTmpDir } from "openclaw/plugin-sdk/temp-path";
import fs from "node:fs";
import { resolveDefaultSecretProviderAlias } from "openclaw/plugin-sdk/provider-auth";
import { applyAccountNameToChannelSection, deleteAccountFromConfigSection, setAccountEnabledInConfigSection } from "openclaw/plugin-sdk/core";
import { DEFAULT_ACCOUNT_ID, createStandardChannelSetupStatus, setSetupChannelEnabled } from "openclaw/plugin-sdk/setup";
import { formatDocsLink } from "openclaw/plugin-sdk/setup-tools";
import { AllowFromListSchema, buildChannelConfigSchema } from "openclaw/plugin-sdk/channel-config-schema";
import { z } from "zod";
//#region extensions/qqbot/src/bridge/logger.ts
let loggerInstance = null;
/** Register the framework logger. Called once in startGateway(). */
function setBridgeLogger(logger) {
	loggerInstance = logger;
}
/** Get the bridge logger. Falls back to console if not yet registered. */
function getBridgeLogger() {
	return loggerInstance ?? {
		info: (msg) => console.log(msg),
		error: (msg) => console.error(msg),
		debug: (msg) => console.log(msg)
	};
}
//#endregion
//#region extensions/qqbot/src/bridge/bootstrap.ts
/**
* Bootstrap the PlatformAdapter for the built-in version.
*
* ## Design
*
* The adapter is registered via two complementary mechanisms:
*
* 1. **Factory registration** (`registerPlatformAdapterFactory`) — a lightweight
*    callback stored in `adapter/index.ts` that is invoked lazily by
*    `getPlatformAdapter()` on first access. This guarantees the adapter is
*    available regardless of module evaluation order or bundler chunk splitting.
*
* 2. **Eager side-effect** (`ensurePlatformAdapter()`) — called at module
*    evaluation time when `channel.ts` imports this file. Provides the adapter
*    immediately for code that runs synchronously during startup.
*
* Heavy async-only dependencies (`media-runtime`, `config-runtime`,
* `approval-gateway-runtime`) are lazy-imported inside each async method body
* so that this module evaluates with minimal overhead.
*
* Synchronous dependencies (`secret-input`, `temp-path`) are imported
* statically at the top level so they work reliably in both production and
* vitest (which resolves bare specifiers via `resolve.alias`, not Node CJS).
*/
function createBuiltinAdapter() {
	return {
		async validateRemoteUrl(_url, _options) {},
		async resolveSecret(value) {
			if (typeof value === "string") return value || void 0;
		},
		async downloadFile(url, destDir, filename) {
			const { readRemoteMediaBuffer } = await import("openclaw/plugin-sdk/media-runtime");
			const result = await readRemoteMediaBuffer({
				url,
				filePathHint: filename
			});
			const fs = await import("node:fs");
			const path = await import("node:path");
			if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, { recursive: true });
			const destPath = path.join(destDir, filename ?? "download");
			fs.writeFileSync(destPath, result.buffer);
			return destPath;
		},
		async fetchMedia(options) {
			const { readRemoteMediaBuffer } = await import("openclaw/plugin-sdk/media-runtime");
			const result = await readRemoteMediaBuffer({
				url: options.url,
				filePathHint: options.filePathHint,
				maxBytes: options.maxBytes,
				maxRedirects: options.maxRedirects,
				ssrfPolicy: options.ssrfPolicy,
				requestInit: options.requestInit
			});
			return {
				buffer: result.buffer,
				fileName: result.fileName
			};
		},
		getTempDir() {
			return resolvePreferredOpenClawTmpDir();
		},
		hasConfiguredSecret(value) {
			return hasConfiguredSecretInput(value);
		},
		normalizeSecretInputString(value) {
			return normalizeSecretInputString(value) ?? void 0;
		},
		resolveSecretInputString(params) {
			return normalizeResolvedSecretInputString(params) ?? void 0;
		},
		async resolveApproval(approvalId, decision) {
			try {
				const { getRuntimeConfig } = await import("openclaw/plugin-sdk/runtime-config-snapshot");
				const { resolveApprovalOverGateway } = await import("openclaw/plugin-sdk/approval-gateway-runtime");
				await resolveApprovalOverGateway({
					cfg: getRuntimeConfig(),
					approvalId,
					decision,
					clientDisplayName: "QQBot Approval Handler"
				});
				return true;
			} catch (err) {
				getBridgeLogger().error(`[qqbot] resolveApproval failed: ${String(err)}`);
				return false;
			}
		}
	};
}
/**
* Ensure the built-in PlatformAdapter is registered.
*
* Safe to call multiple times — only registers on the first invocation.
* Exported for backward compatibility with code that calls it explicitly.
*/
function ensurePlatformAdapter() {
	if (!hasPlatformAdapter()) registerPlatformAdapter(createBuiltinAdapter());
}
registerPlatformAdapterFactory(createBuiltinAdapter);
ensurePlatformAdapter();
//#endregion
//#region extensions/qqbot/src/engine/config/resolve.ts
/**
* QQBot config resolution (pure logic layer).
* QQBot 配置解析（纯逻辑层）。
*
* Resolves account IDs, default account selection, and base account
* info from raw config objects. Secret/credential resolution is
* intentionally left to the outer layer (src/bridge/config.ts) so that
* this module stays framework-agnostic and self-contained.
*/
/**
* Default account ID, used for the unnamed top-level account.
* 默认账号 ID，用于顶层配置中未命名的账号。
*/
const DEFAULT_ACCOUNT_ID$2 = "default";
function normalizeAppId(raw) {
	if (typeof raw === "string") return raw.trim();
	if (typeof raw === "number") return String(raw);
	return "";
}
function normalizeAccountConfig(account) {
	if (!account) return {};
	const audioPolicy = asOptionalObjectRecord(account.audioFormatPolicy);
	return {
		...account,
		...audioPolicy ? { audioFormatPolicy: { ...audioPolicy } } : {}
	};
}
function readQQBotSection(cfg) {
	return asOptionalObjectRecord(asOptionalObjectRecord(cfg.channels)?.qqbot);
}
/**
* List all configured QQBot account IDs.
* 列出所有已配置的 QQBot 账号 ID。
*/
function listAccountIds(cfg) {
	const ids = /* @__PURE__ */ new Set();
	const qqbot = readQQBotSection(cfg);
	if (qqbot?.appId || process.env.QQBOT_APP_ID) ids.add(DEFAULT_ACCOUNT_ID$2);
	if (qqbot?.accounts) {
		for (const accountId of Object.keys(qqbot.accounts)) if (qqbot.accounts[accountId]?.appId) ids.add(accountId);
	}
	return Array.from(ids);
}
/**
* Resolve the default QQBot account ID.
* 解析默认 QQBot 账号 ID（优先级：defaultAccount > 顶层 appId > 第一个命名账号）。
*/
function resolveDefaultAccountId(cfg) {
	const qqbot = readQQBotSection(cfg);
	const configuredDefaultAccountId = normalizeOptionalLowercaseString(qqbot?.defaultAccount);
	if (configuredDefaultAccountId && (configuredDefaultAccountId === "default" || Boolean(qqbot?.accounts?.[configuredDefaultAccountId]?.appId))) return configuredDefaultAccountId;
	if (qqbot?.appId || process.env.QQBOT_APP_ID) return DEFAULT_ACCOUNT_ID$2;
	if (qqbot?.accounts) {
		const ids = Object.keys(qqbot.accounts);
		if (ids.length > 0) return ids[0];
	}
	return DEFAULT_ACCOUNT_ID$2;
}
/**
* Resolve base account info (without credentials).
* 解析账号基础信息（不含凭证）。
*
* Resolves everything except Secret/credential fields. The outer
* config.ts layer calls this and adds Secret handling on top.
*/
function resolveAccountBase(cfg, accountId) {
	const resolvedAccountId = accountId ?? resolveDefaultAccountId(cfg);
	const qqbot = readQQBotSection(cfg);
	let accountConfig = {};
	let appId = "";
	if (resolvedAccountId === "default") {
		accountConfig = normalizeAccountConfig(asOptionalObjectRecord(qqbot));
		appId = normalizeAppId(qqbot?.appId);
	} else {
		const account = qqbot?.accounts?.[resolvedAccountId];
		accountConfig = normalizeAccountConfig(asOptionalObjectRecord(account));
		appId = normalizeAppId(asOptionalObjectRecord(account)?.appId);
	}
	if (!appId && process.env.QQBOT_APP_ID && resolvedAccountId === "default") appId = normalizeAppId(process.env.QQBOT_APP_ID);
	return {
		accountId: resolvedAccountId,
		name: readStringField(accountConfig, "name"),
		enabled: accountConfig.enabled !== false,
		appId,
		systemPrompt: readStringField(accountConfig, "systemPrompt"),
		markdownSupport: accountConfig.markdownSupport !== false,
		config: accountConfig
	};
}
/** Apply account config updates into a raw config object. */
function applyAccountConfig(cfg, accountId, input) {
	const next = { ...cfg };
	const channels = asOptionalObjectRecord(cfg.channels) ?? {};
	const existingQQBot = asOptionalObjectRecord(channels.qqbot) ?? {};
	if (accountId === "default") {
		const allowFrom = existingQQBot.allowFrom ?? ["*"];
		next.channels = {
			...channels,
			qqbot: {
				...existingQQBot,
				enabled: true,
				allowFrom,
				...input.appId ? { appId: input.appId } : {},
				...input.clientSecret ? {
					clientSecret: input.clientSecret,
					clientSecretFile: void 0
				} : input.clientSecretFile ? {
					clientSecretFile: input.clientSecretFile,
					clientSecret: void 0
				} : {},
				...input.name ? { name: input.name } : {}
			}
		};
	} else {
		const accounts = existingQQBot.accounts ?? {};
		const existingAccount = accounts[accountId] ?? {};
		const allowFrom = existingAccount.allowFrom ?? ["*"];
		next.channels = {
			...channels,
			qqbot: {
				...existingQQBot,
				enabled: true,
				accounts: {
					...accounts,
					[accountId]: {
						...existingAccount,
						enabled: true,
						allowFrom,
						...input.appId ? { appId: input.appId } : {},
						...input.clientSecret ? {
							clientSecret: input.clientSecret,
							clientSecretFile: void 0
						} : input.clientSecretFile ? {
							clientSecretFile: input.clientSecretFile,
							clientSecret: void 0
						} : {},
						...input.name ? { name: input.name } : {}
					}
				}
			}
		};
	}
	return next;
}
/** Check whether a QQBot account has been fully configured. */
function isAccountConfigured(account) {
	return Boolean(account?.appId && (Boolean(account?.clientSecret) || getPlatformAdapter().hasConfiguredSecret(account?.config?.clientSecret) || Boolean(account?.config?.clientSecretFile?.trim())));
}
/** Build a summary description of an account. */
function describeAccount(account) {
	return {
		accountId: account?.accountId ?? "default",
		name: account?.name,
		enabled: account?.enabled ?? false,
		configured: isAccountConfigured(account),
		tokenSource: account?.secretSource
	};
}
/** Normalize allowFrom entries into uppercase strings without the qqbot: prefix. */
function formatAllowFrom(allowFrom) {
	return normalizeStringifiedEntries(allowFrom ?? []).map((entry) => entry.replace(/^qqbot:/i, "")).map((entry) => entry.toUpperCase());
}
//#endregion
//#region extensions/qqbot/src/bridge/config.ts
const DEFAULT_ACCOUNT_ID$1 = DEFAULT_ACCOUNT_ID$2;
function assertNotLegacySecretRefMarker(value, path) {
	const normalized = normalizeSecretInputString(value);
	if (!normalized || !/^secretref(?:-env)?:/i.test(normalized)) return;
	throw new Error(`${path}: legacy SecretRef marker strings are not valid QQ Bot clientSecret values; use a structured SecretRef object instead.`);
}
function resolveEnvSecretRefValue(params) {
	const ref = coerceSecretRef(params.value, params.cfg.secrets?.defaults);
	if (!ref || ref.source !== "env") return;
	const providerConfig = params.cfg.secrets?.providers?.[ref.provider];
	if (providerConfig) {
		if (providerConfig.source !== "env") throw new Error(`Secret provider "${ref.provider}" has source "${providerConfig.source}" but ref requests "env".`);
		if (providerConfig.allowlist && !providerConfig.allowlist.includes(ref.id)) throw new Error(`Environment variable "${ref.id}" is not allowlisted in secrets.providers.${ref.provider}.allowlist.`);
	} else if (ref.provider !== resolveDefaultSecretProviderAlias(params.cfg, "env")) throw new Error(`Secret provider "${ref.provider}" is not configured (ref: env:${ref.provider}:${ref.id}).`);
	return normalizeSecretInputString((params.env ?? process.env)[ref.id]);
}
function resolveQQBotClientSecretInput(params) {
	assertNotLegacySecretRefMarker(params.value, params.path);
	const envSecret = resolveEnvSecretRefValue({
		cfg: params.cfg,
		value: params.value
	});
	if (envSecret) return envSecret;
	return getPlatformAdapter().resolveSecretInputString({
		value: params.value,
		path: params.path
	});
}
/** List all configured QQBot account IDs. */
function listQQBotAccountIds(cfg) {
	return listAccountIds(cfg);
}
/** Resolve the default QQBot account ID. */
function resolveDefaultQQBotAccountId(cfg) {
	return resolveDefaultAccountId(cfg);
}
/** Resolve QQBot account config for runtime or setup flows. */
function resolveQQBotAccount(cfg, accountId, opts) {
	const base = resolveAccountBase(cfg, accountId);
	const qqbot = cfg.channels?.qqbot;
	/**
	* Legacy top-level account uses `channels.qqbot` as the base, but per-account
	* fields (allowFrom, streaming, …) often live under `accounts.default`.
	* Merge that slice so runtime sees `config.streaming` etc.
	*/
	const accountConfig = base.accountId === DEFAULT_ACCOUNT_ID$1 ? {
		...qqbot,
		...qqbot?.accounts?.[DEFAULT_ACCOUNT_ID$1]
	} : qqbot?.accounts?.[base.accountId] ?? {};
	let clientSecret = "";
	let secretSource = "none";
	const clientSecretPath = base.accountId === DEFAULT_ACCOUNT_ID$1 ? "channels.qqbot.clientSecret" : `channels.qqbot.accounts.${base.accountId}.clientSecret`;
	const adapter = getPlatformAdapter();
	if (adapter.hasConfiguredSecret(accountConfig.clientSecret)) {
		clientSecret = opts?.allowUnresolvedSecretRef ? adapter.normalizeSecretInputString(accountConfig.clientSecret) ?? "" : resolveQQBotClientSecretInput({
			cfg,
			value: accountConfig.clientSecret,
			path: clientSecretPath
		}) ?? "";
		secretSource = "config";
	} else if (accountConfig.clientSecretFile) try {
		clientSecret = fs.readFileSync(accountConfig.clientSecretFile, "utf8").trim();
		secretSource = "file";
	} catch {
		secretSource = "none";
	}
	else if (process.env.QQBOT_CLIENT_SECRET && base.accountId === DEFAULT_ACCOUNT_ID$1) {
		clientSecret = process.env.QQBOT_CLIENT_SECRET;
		secretSource = "env";
	}
	return {
		accountId: base.accountId,
		name: accountConfig.name,
		enabled: base.enabled,
		appId: base.appId,
		clientSecret,
		secretSource,
		systemPrompt: base.systemPrompt,
		markdownSupport: base.markdownSupport,
		config: accountConfig
	};
}
/** Apply account config updates back into the OpenClaw config object. */
function applyQQBotAccountConfig(cfg, accountId, input) {
	return applyAccountConfig(cfg, accountId, input);
}
//#endregion
//#region extensions/qqbot/src/engine/config/setup-logic.ts
/**
* QQBot setup business logic (pure layer).
* QQBot setup 相关纯业务逻辑。
*
* Token parsing, input validation, and setup config application.
* All functions are framework-agnostic and operate on plain objects.
*/
/** Parse an inline "appId:clientSecret" token string. */
function parseInlineToken(token) {
	const colonIdx = token.indexOf(":");
	if (colonIdx <= 0 || colonIdx === token.length - 1) return null;
	const appId = token.slice(0, colonIdx).trim();
	const clientSecret = token.slice(colonIdx + 1).trim();
	if (!appId || !clientSecret) return null;
	return {
		appId,
		clientSecret
	};
}
/** Validate setup input for a QQBot account. Returns an error string or null. */
function validateSetupInput(accountId, input) {
	if (!input.token && !input.tokenFile && !input.useEnv) return "QQBot requires --token (format: appId:clientSecret) or --use-env";
	if (input.useEnv && accountId !== "default") return "QQBot --use-env only supports the default account";
	if (input.token && !parseInlineToken(input.token)) return "QQBot --token must be in appId:clientSecret format";
	return null;
}
/** Apply setup input to account config. Returns updated config. */
function applySetupAccountConfig(cfg, accountId, input) {
	if (input.useEnv && accountId !== "default") return cfg;
	let appId = "";
	let clientSecret = "";
	if (input.token) {
		const parsed = parseInlineToken(input.token);
		if (!parsed) return cfg;
		appId = parsed.appId;
		clientSecret = parsed.clientSecret;
	}
	if (!appId && !input.tokenFile && !input.useEnv) return cfg;
	return applyAccountConfig(cfg, accountId, {
		appId,
		clientSecret,
		clientSecretFile: input.tokenFile,
		name: input.name
	});
}
//#endregion
//#region extensions/qqbot/src/bridge/config-shared.ts
const qqbotMeta = {
	id: "qqbot",
	label: "QQ Bot",
	selectionLabel: "QQ Bot (Bot API)",
	docsPath: "/channels/qqbot",
	blurb: "Connect to QQ via official QQ Bot API",
	order: 50
};
function validateQQBotSetupInput(params) {
	return validateSetupInput(params.accountId, params.input);
}
function applyQQBotSetupAccountConfig(params) {
	return applySetupAccountConfig(params.cfg, params.accountId, params.input);
}
function isQQBotConfigured(account) {
	return isAccountConfigured(account);
}
function describeQQBotAccount(account) {
	return describeAccount(account);
}
function formatQQBotAllowFrom(params) {
	return formatAllowFrom(params.allowFrom);
}
const qqbotConfigAdapter = {
	listAccountIds: (cfg) => listQQBotAccountIds(cfg),
	resolveAccount: (cfg, accountId) => resolveQQBotAccount(cfg, accountId, { allowUnresolvedSecretRef: true }),
	defaultAccountId: (cfg) => resolveDefaultQQBotAccountId(cfg),
	setAccountEnabled: ({ cfg, accountId, enabled }) => setAccountEnabledInConfigSection({
		cfg,
		sectionKey: "qqbot",
		accountId,
		enabled,
		allowTopLevel: true
	}),
	deleteAccount: ({ cfg, accountId }) => deleteAccountFromConfigSection({
		cfg,
		sectionKey: "qqbot",
		accountId,
		clearBaseFields: [
			"appId",
			"clientSecret",
			"clientSecretFile",
			"name"
		]
	}),
	isConfigured: isQQBotConfigured,
	describeAccount: describeQQBotAccount,
	resolveAllowFrom: ({ cfg, accountId }) => resolveQQBotAccount(cfg, accountId, { allowUnresolvedSecretRef: true }).config?.allowFrom,
	formatAllowFrom: ({ allowFrom }) => formatQQBotAllowFrom({ allowFrom })
};
const qqbotSetupAdapterShared = {
	resolveAccountId: ({ cfg, accountId }) => normalizeLowercaseStringOrEmpty(accountId) || resolveDefaultQQBotAccountId(cfg),
	applyAccountName: ({ cfg, accountId, name }) => applyAccountNameToChannelSection({
		cfg,
		channelKey: "qqbot",
		accountId,
		name
	}),
	validateInput: ({ accountId, input }) => validateQQBotSetupInput({
		accountId,
		input
	}),
	applyAccountConfig: ({ cfg, accountId, input }) => applyQQBotSetupAccountConfig({
		cfg,
		accountId,
		input
	})
};
//#endregion
//#region extensions/qqbot/src/bridge/setup/finalize.ts
function isQQBotAccountConfigured(cfg, accountId) {
	const account = resolveQQBotAccount(cfg, accountId, { allowUnresolvedSecretRef: true });
	return Boolean(account.appId && account.clientSecret);
}
async function linkViaQrCode(params) {
	try {
		const { qrConnect } = await import("@tencent-connect/qqbot-connector");
		const accounts = await qrConnect({ source: "openclaw" });
		if (accounts.length === 0) {
			await params.prompter.note("未获取到任何 QQ Bot 账号信息。", "QQ Bot");
			return params.cfg;
		}
		let next = params.cfg;
		for (let i = 0; i < accounts.length; i++) {
			const { appId, appSecret } = accounts[i];
			const targetAccountId = i === 0 ? params.accountId : appId;
			next = applyQQBotAccountConfig(next, targetAccountId, {
				appId,
				clientSecret: appSecret
			});
		}
		if (accounts.length === 1) params.runtime.log(`✔ QQ Bot 绑定成功！(AppID: ${accounts[0].appId})`);
		else {
			const idList = accounts.map((a) => a.appId).join(", ");
			params.runtime.log(`✔ ${accounts.length} 个 QQ Bot 绑定成功！(AppID: ${idList})`);
		}
		return next;
	} catch (error) {
		params.runtime.error(`QQ Bot 绑定失败: ${String(error)}`);
		await params.prompter.note(["绑定失败，您可以稍后手动配置。", `文档: ${formatDocsLink("/channels/qqbot", "qqbot")}`].join("\n"), "QQ Bot");
		return params.cfg;
	}
}
async function linkViaManualInput(params) {
	const appId = await params.prompter.text({
		message: "请输入 QQ Bot AppID",
		validate: (value) => value.trim() ? void 0 : "AppID 不能为空"
	});
	const appSecret = await params.prompter.text({
		message: "请输入 QQ Bot AppSecret",
		validate: (value) => value.trim() ? void 0 : "AppSecret 不能为空"
	});
	const next = applyQQBotAccountConfig(params.cfg, params.accountId, {
		appId: appId.trim(),
		clientSecret: appSecret.trim()
	});
	await params.prompter.note("✔ QQ Bot 配置完成！", "QQ Bot");
	return next;
}
async function finalizeQQBotSetup(params) {
	const accountId = params.accountId.trim() || DEFAULT_ACCOUNT_ID;
	let next = params.cfg;
	const configured = isQQBotAccountConfigured(next, accountId);
	const mode = await params.prompter.select({
		message: configured ? "QQ 已绑定，选择操作" : "选择 QQ 绑定方式",
		options: [
			{
				value: "qr",
				label: "扫码绑定（推荐）",
				hint: "使用 QQ 扫描二维码自动完成绑定"
			},
			{
				value: "manual",
				label: "手动输入 QQ Bot AppID 和 AppSecret",
				hint: "需到 QQ 开放平台 q.qq.com 查看"
			},
			{
				value: "skip",
				label: configured ? "保持当前配置" : "稍后配置"
			}
		]
	});
	if (mode === "qr") next = await linkViaQrCode({
		cfg: next,
		accountId,
		prompter: params.prompter,
		runtime: params.runtime
	});
	else if (mode === "manual") next = await linkViaManualInput({
		cfg: next,
		accountId,
		prompter: params.prompter
	});
	else if (!configured) await params.prompter.note(["您可以稍后运行以下命令重新选择 QQ Bot 进行配置：", "  openclaw channels add"].join("\n"), "QQ Bot");
	return { cfg: next };
}
//#endregion
//#region extensions/qqbot/src/bridge/setup/surface.ts
const channel = "qqbot";
const qqbotSetupWizard = {
	channel,
	status: createStandardChannelSetupStatus({
		channelLabel: "QQ Bot",
		configuredLabel: "configured",
		unconfiguredLabel: "needs AppID + AppSercet",
		configuredHint: "configured",
		unconfiguredHint: "needs AppID + AppSercet",
		configuredScore: 1,
		unconfiguredScore: 6,
		resolveConfigured: ({ cfg, accountId }) => (accountId ? [accountId] : listQQBotAccountIds(cfg)).some((resolvedAccountId) => {
			return isAccountConfigured(resolveQQBotAccount(cfg, resolvedAccountId, { allowUnresolvedSecretRef: true }));
		})
	}),
	credentials: [],
	finalize: async ({ cfg, accountId, forceAllowFrom, prompter, runtime }) => await finalizeQQBotSetup({
		cfg,
		accountId,
		forceAllowFrom,
		prompter,
		runtime
	}),
	disable: (cfg) => setSetupChannelEnabled(cfg, channel, false)
};
//#endregion
//#region extensions/qqbot/src/config-schema.ts
const AudioFormatPolicySchema = z.object({
	sttDirectFormats: z.array(z.string()).optional(),
	uploadDirectFormats: z.array(z.string()).optional(),
	transcodeEnabled: z.boolean().optional()
}).optional();
const QQBotSttSchema = z.object({
	enabled: z.boolean().optional(),
	provider: z.string().optional(),
	baseUrl: z.string().optional(),
	apiKey: z.string().optional(),
	model: z.string().optional()
}).strict().optional();
/** When `true`, same as `mode: "partial"` and `c2cStreamApi: true` for C2C. Object form kept for legacy configs. */
const QQBotStreamingSchema = z.union([z.boolean(), z.object({
	/** "partial" (default) enables block streaming; "off" disables it. */
	mode: z.enum(["off", "partial"]).default("partial"),
	/** @deprecated Prefer `streaming: true`. */
	c2cStreamApi: z.boolean().optional()
}).passthrough()]).optional();
const QQBotExecApprovalsSchema = z.object({
	enabled: z.union([z.boolean(), z.literal("auto")]).optional(),
	approvers: z.array(z.string()).optional(),
	agentFilter: z.array(z.string()).optional(),
	sessionFilter: z.array(z.string()).optional(),
	target: z.enum([
		"dm",
		"channel",
		"both"
	]).optional()
}).strict().optional();
const QQBotDmPolicySchema = z.enum([
	"open",
	"allowlist",
	"disabled"
]).optional();
const QQBotGroupPolicySchema = z.enum([
	"open",
	"allowlist",
	"disabled"
]).optional();
const QQBotAccountSchema = z.object({
	enabled: z.boolean().optional(),
	name: z.string().optional(),
	appId: z.string().optional(),
	clientSecret: buildSecretInputSchema().optional(),
	clientSecretFile: z.string().optional(),
	allowFrom: AllowFromListSchema,
	groupAllowFrom: AllowFromListSchema,
	dmPolicy: QQBotDmPolicySchema,
	groupPolicy: QQBotGroupPolicySchema,
	systemPrompt: z.string().optional(),
	markdownSupport: z.boolean().optional(),
	voiceDirectUploadFormats: z.array(z.string()).optional(),
	audioFormatPolicy: AudioFormatPolicySchema,
	urlDirectUpload: z.boolean().optional(),
	upgradeUrl: z.string().optional(),
	upgradeMode: z.enum(["doc", "hot-reload"]).optional(),
	streaming: QQBotStreamingSchema,
	execApprovals: QQBotExecApprovalsSchema
}).passthrough();
const qqbotChannelConfigSchema = buildChannelConfigSchema(QQBotAccountSchema.extend({
	stt: QQBotSttSchema,
	accounts: z.object({}).catchall(QQBotAccountSchema.passthrough()).optional(),
	defaultAccount: z.string().optional()
}).passthrough());
//#endregion
export { qqbotSetupAdapterShared as a, listQQBotAccountIds as c, DEFAULT_ACCOUNT_ID$2 as d, resolveAccountBase as f, setBridgeLogger as h, qqbotMeta as i, resolveDefaultQQBotAccountId as l, getBridgeLogger as m, qqbotSetupWizard as n, DEFAULT_ACCOUNT_ID$1 as o, ensurePlatformAdapter as p, qqbotConfigAdapter as r, applyQQBotAccountConfig as s, qqbotChannelConfigSchema as t, resolveQQBotAccount as u };
