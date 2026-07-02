//#region src/sdk/helpers.ts
/**
* 默认账号 ID
*/
const DEFAULT_ACCOUNT_ID = "__default__";
/**
* 规范化账号 ID
*
* 注意：账号 ID 保留原始大小写，仅做 trim 处理。
* 不做 toLowerCase，因为配置文件中的 accounts key 是大小写敏感的，
* 如 "zhizaoDashuIP" 与 "zhizaodashuip" 是不同的账号。
* 特殊值 "default"（不区分大小写）和空字符串映射到 DEFAULT_ACCOUNT_ID。
*/
function normalizeAccountId(accountId) {
	const trimmed = accountId.trim();
	if (trimmed.toLowerCase() === "default" || trimmed === "") return DEFAULT_ACCOUNT_ID;
	return trimmed;
}
/**
* 判断是否为 SecretInput 引用
*/
function isSecretInputRef(value) {
	if (!value || typeof value !== "object") return false;
	const ref = value;
	return typeof ref.source === "string" && [
		"env",
		"file",
		"exec"
	].includes(ref.source) && typeof ref.provider === "string" && ref.provider.length > 0 && typeof ref.id === "string" && ref.id.length > 0;
}
/**
* 规范化 SecretInput 字符串
* 用于显示和日志，会隐藏敏感信息
*/
function normalizeSecretInputString(value) {
	if (typeof value === "string") return value.trim() || void 0;
	if (isSecretInputRef(value)) {
		const ref = value;
		return `<${ref.source}:${ref.provider}:${ref.id}>`;
	}
}
/**
* 检查 SecretInput 是否已配置
*/
function hasConfiguredSecretInput(value) {
	if (typeof value === "string") return value.trim().length > 0;
	if (isSecretInputRef(value)) {
		const ref = value;
		if (ref.source === "env") return typeof process.env[ref.id] === "string" && process.env[ref.id].trim().length > 0;
		return true;
	}
	return false;
}
/**
* 规范化已解析的 SecretInput 字符串
* 用于配置验证和错误提示
*/
function normalizeResolvedSecretInputString(params) {
	const { value, path } = params;
	if (typeof value === "string") {
		const trimmed = value.trim();
		if (trimmed) return trimmed;
		throw new Error(`${path} must be a non-empty string`);
	}
	if (isSecretInputRef(value)) {
		const ref = value;
		if (![
			"env",
			"file",
			"exec"
		].includes(ref.source)) throw new Error(`${path}.source must be one of: env, file, exec`);
		if (typeof ref.provider !== "string" || !ref.provider.trim()) throw new Error(`${path}.provider must be a non-empty string`);
		if (typeof ref.id !== "string" || !ref.id.trim()) throw new Error(`${path}.id must be a non-empty string`);
		if (ref.source === "env") {
			const envValue = process.env[ref.id];
			if (!envValue || !envValue.trim()) throw new Error(`${path}: environment variable ${ref.id} is not set`);
			return envValue.trim();
		}
		return `<${ref.source}:${ref.provider}:${ref.id}>`;
	}
	throw new Error(`${path} must be a string or SecretInput object`);
}
/**
* 解析默认群组策略
*/
function resolveDefaultGroupPolicy(cfg) {
	return (cfg.channels?.["dingtalk-connector"])?.groupPolicy ?? "open";
}
/**
* 解析允许列表提供者运行时群组策略
*/
function resolveAllowlistProviderRuntimeGroupPolicy(params) {
	const { providerConfigPresent, groupPolicy, defaultGroupPolicy } = params;
	if (groupPolicy) return { groupPolicy };
	if (providerConfigPresent) return { groupPolicy: defaultGroupPolicy };
	return { groupPolicy: "disabled" };
}
/**
* 创建默认通道运行时状态
*/
function createDefaultChannelRuntimeState(accountId, extras) {
	return {
		running: false,
		lastStartAt: null,
		lastStopAt: null,
		lastError: null,
		port: null,
		accountId,
		...extras
	};
}
/**
* 添加通配符到 allowFrom
*/
function addWildcardAllowFrom(existing) {
	if (!existing || existing.length === 0) return ["*"];
	if (existing.includes("*")) return existing;
	return [...existing, "*"];
}
/**
* 格式化文档链接
*/
function formatDocsLink(path, label) {
	return `https://docs.openclaw.ai${path}`;
}
//#endregion
//#region src/config/accounts.ts
/**
* List all configured account IDs from the accounts field.
*/
function listConfiguredAccountIds(cfg) {
	const accounts = (cfg.channels?.["dingtalk-connector"])?.accounts;
	if (!accounts || typeof accounts !== "object") return [];
	return Object.keys(accounts).filter(Boolean);
}
/**
* List all DingTalk account IDs.
* If no accounts are configured, returns [DEFAULT_ACCOUNT_ID] for backward compatibility.
*/
function listDingtalkAccountIds(cfg) {
	const ids = listConfiguredAccountIds(cfg);
	if (ids.length === 0) return [DEFAULT_ACCOUNT_ID];
	return [...ids].toSorted((a, b) => a.localeCompare(b));
}
/**
* Resolve the default account selection and its source.
*/
function resolveDefaultDingtalkAccountSelection(cfg) {
	const preferredRaw = (cfg.channels?.["dingtalk-connector"])?.defaultAccount?.trim();
	const preferred = preferredRaw ? normalizeAccountId(preferredRaw) : void 0;
	if (preferred) return {
		accountId: preferred,
		source: "explicit-default"
	};
	const ids = listDingtalkAccountIds(cfg);
	if (ids.includes("__default__")) return {
		accountId: DEFAULT_ACCOUNT_ID,
		source: "mapped-default"
	};
	return {
		accountId: ids[0] ?? "__default__",
		source: "fallback"
	};
}
/**
* Resolve the default account ID.
*/
function resolveDefaultDingtalkAccountId(cfg) {
	return resolveDefaultDingtalkAccountSelection(cfg).accountId;
}
/**
* Get the raw account-specific config.
*/
function resolveAccountConfig(cfg, accountId) {
	const accounts = (cfg.channels?.["dingtalk-connector"])?.accounts;
	if (!accounts || typeof accounts !== "object") return;
	return accounts[accountId];
}
/**
* Merge top-level config with account-specific config.
* Account-specific fields override top-level fields.
*/
function mergeDingtalkAccountConfig(cfg, accountId) {
	const { accounts: _ignored, defaultAccount: _ignoredDefaultAccount, ...base } = cfg.channels?.["dingtalk-connector"] ?? {};
	const account = resolveAccountConfig(cfg, accountId) ?? {};
	return {
		...base,
		...account
	};
}
function resolveDingtalkCredentials(cfg, options) {
	const normalizeString = (value) => {
		if (typeof value === "number") return String(value);
		if (typeof value !== "string") return;
		const trimmed = value.trim();
		return trimmed ? trimmed : void 0;
	};
	const resolveSecretLike = (value, path) => {
		if (value === void 0 || value === null) return;
		const asString = normalizeString(value);
		if (asString) return asString;
		if (options?.allowUnresolvedSecretRef && typeof value === "object" && value !== null) {
			const rec = value;
			const source = normalizeString(rec.source)?.toLowerCase();
			const id = normalizeString(rec.id);
			if (source === "env" && id) {
				const envValue = normalizeString(process.env[id]);
				if (envValue) return envValue;
			}
		}
		if (options?.allowUnresolvedSecretRef) return normalizeSecretInputString(value);
		return normalizeResolvedSecretInputString({
			value,
			path
		});
	};
	const clientId = resolveSecretLike(cfg?.clientId, "channels.dingtalk-connector.clientId");
	const clientSecret = resolveSecretLike(cfg?.clientSecret, "channels.dingtalk-connector.clientSecret");
	if (!clientId || !clientSecret) return null;
	return {
		clientId,
		clientSecret
	};
}
/**
* Resolve a complete DingTalk account with merged config.
*/
function resolveDingtalkAccount(params) {
	const hasExplicitAccountId = typeof params.accountId === "string" && params.accountId.trim() !== "";
	const defaultSelection = hasExplicitAccountId ? null : resolveDefaultDingtalkAccountSelection(params.cfg);
	const accountId = hasExplicitAccountId ? normalizeAccountId(params.accountId ?? "") : defaultSelection?.accountId ?? "__default__";
	const selectionSource = hasExplicitAccountId ? "explicit" : defaultSelection?.source ?? "fallback";
	const baseEnabled = (params.cfg.channels?.["dingtalk-connector"])?.enabled !== false;
	const merged = mergeDingtalkAccountConfig(params.cfg, accountId);
	const accountEnabled = merged.enabled !== false;
	const enabled = baseEnabled && accountEnabled;
	const creds = resolveDingtalkCredentials(merged);
	const accountName = merged.name;
	return {
		accountId,
		selectionSource,
		enabled,
		configured: Boolean(creds),
		name: typeof accountName === "string" ? accountName.trim() || void 0 : void 0,
		clientId: creds?.clientId,
		clientSecret: creds?.clientSecret,
		config: merged
	};
}
/**
* List all enabled and configured accounts.
* Deduplicates by clientId to avoid creating multiple connections with the same credentials.
*/
function listEnabledDingtalkAccounts(cfg) {
	const accounts = listDingtalkAccountIds(cfg).map((accountId) => resolveDingtalkAccount({
		cfg,
		accountId
	})).filter((account) => account.enabled && account.configured);
	const seen = /* @__PURE__ */ new Set();
	return accounts.filter((account) => {
		if (!account.clientId) return true;
		if (seen.has(account.clientId)) return false;
		seen.add(account.clientId);
		return true;
	});
}
//#endregion
export { resolveDingtalkAccount as a, addWildcardAllowFrom as c, hasConfiguredSecretInput as d, normalizeAccountId as f, resolveDefaultDingtalkAccountSelection as i, createDefaultChannelRuntimeState as l, resolveDefaultGroupPolicy as m, listEnabledDingtalkAccounts as n, resolveDingtalkCredentials as o, resolveAllowlistProviderRuntimeGroupPolicy as p, resolveDefaultDingtalkAccountId as r, DEFAULT_ACCOUNT_ID as s, listDingtalkAccountIds as t, formatDocsLink as u };
