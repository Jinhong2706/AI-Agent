import { u as uploadMediaToDingTalk } from "./media-BViJQGgb.mjs";
import { n as createLoggerFromConfig } from "./logger-BDWwViGT.mjs";
import { t as dingtalkHttp } from "./http-client-DFWZgO1n.mjs";
import { i as DINGTALK_API, o as getAccessToken, s as getOapiAccessToken } from "./utils-DgNm1Ek_.mjs";
import { r as MEDIA_MSG_TYPES } from "./session-DJ4jYqPv.mjs";
//#region src/services/messaging/card.ts
const AI_CARD_TEMPLATE_ID = "02fcf2f4-5e02-4a85-b672-46d1f715543e.schema";
/**
* 钉钉卡片 API 的最大 QPS（官方限制约 40 次/秒）。
* 保守取 20，为 createAICardForTarget / finishAICard 等非流式调用留余量。
*/
const CARD_API_MAX_QPS = 20;
/** QPS 限流退避时长（ms），遇到 403 QpsLimit 后暂停发送 */
const QPS_BACKOFF_DURATION_MS = 2e3;
/**
* 全局令牌桶限流器，所有 streamAICard 调用共享。
*
* 解决的问题：每个 reply-dispatcher 实例有独立的 500ms 节流间隔，
* 但多个会话并发时总 QPS 会叠加超过钉钉 API 限制（40 次/秒），
* 导致频繁触发 403 QpsLimit 错误。
*
* 工作原理：
* - 令牌桶以 CARD_API_MAX_QPS 的速率补充令牌
* - 每次 API 调用前消耗一个令牌，无令牌时等待
* - 遇到 QpsLimit 错误时触发退避，暂停所有调用
*/
const cardRateLimiter = {
	tokens: CARD_API_MAX_QPS,
	lastRefillTime: Date.now(),
	backoffUntil: 0,
	_queueTail: Promise.resolve(),
	refill() {
		const now = Date.now();
		const elapsedSeconds = (now - this.lastRefillTime) / 1e3;
		if (elapsedSeconds > 0) {
			this.tokens = Math.min(CARD_API_MAX_QPS, this.tokens + elapsedSeconds * CARD_API_MAX_QPS);
			this.lastRefillTime = now;
		}
	},
	async waitForToken() {
		const prev = this._queueTail;
		let release;
		this._queueTail = new Promise((resolve) => {
			release = resolve;
		});
		try {
			await prev;
		} catch {}
		try {
			let totalWaitMs = 0;
			const now = Date.now();
			if (now < this.backoffUntil) {
				const backoffWaitMs = this.backoffUntil - now;
				await sleep(backoffWaitMs);
				totalWaitMs += backoffWaitMs;
			}
			this.refill();
			if (this.tokens < 1) {
				const waitMs = Math.ceil((1 - this.tokens) / CARD_API_MAX_QPS * 1e3);
				await sleep(waitMs);
				totalWaitMs += waitMs;
				this.refill();
			}
			this.tokens -= 1;
			return totalWaitMs;
		} finally {
			release();
		}
	},
	triggerBackoff() {
		const backoffEnd = Date.now() + QPS_BACKOFF_DURATION_MS;
		this.backoffUntil = backoffEnd;
		this.tokens = 0;
		this.lastRefillTime = backoffEnd;
	}
};
/** 简单的 sleep 工具函数 */
function sleep(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}
/**
* 判断错误是否为钉钉 QPS 限流错误。
*
* 导出给上层调用（如 reply-dispatcher），用于在错误处理时区分
* 「瞬时可恢复错误」与「真正的发送失败」，避免把 QPS 限流这种
* 内部已自动退避重试、后续会自动恢复的错误展示为用户可见的
* 「消息发送失败」提示。
*/
function isQpsLimitError(err) {
	const errorCode = err?.response?.data?.code;
	return err?.response?.status === 403 && typeof errorCode === "string" && errorCode.includes("QpsLimit");
}
/** AI Card 状态 */
const AICardStatus = {
	PROCESSING: "1",
	INPUTING: "2",
	FINISHED: "3",
	EXECUTING: "4",
	FAILED: "5"
};
/**
* 统一换行符为 \n，避免 CRLF 干扰 Markdown 解析
*/
function normalizeLineEndings(text) {
	return text.replace(/\r\n?/g, "\n");
}
/**
* 确保 Markdown 表格前有空行，否则钉钉无法正确渲染表格
*/
function ensureTableBlankLines(text) {
	const lines = normalizeLineEndings(text).split("\n");
	const result = [];
	const tableDividerRegex = /^\s*\|?\s*:?-+:?\s*(\|?\s*:?-+:?\s*)+\|?\s*$/;
	const tableRowRegex = /^\s*\|?.*\|.*\|?\s*$/;
	const isDivider = (line) => line && typeof line === "string" && line.includes("|") && tableDividerRegex.test(line);
	for (let i = 0; i < lines.length; i++) {
		const currentLine = lines[i];
		const nextLine = lines[i + 1] ?? "";
		if (tableRowRegex.test(currentLine) && isDivider(nextLine) && i > 0 && lines[i - 1].trim() !== "" && !tableRowRegex.test(lines[i - 1])) result.push("");
		result.push(currentLine);
	}
	return result.join("\n");
}
/**
* 将单个 \n 转换为 <br>，保留 \n\n 段落分隔。
*
* 钉钉 AI Card 渲染器的换行约定：
* - 普通文本：用 `<br>` 做换行，`\n` 不创建视觉换行
* - 代码块（```）：用 `\n` 做换行，`<br>` 会原样显示为文本
* - 列表（- / 1.）、表格（|）、标题（#）：用 `\n` 做语法行分隔
* - 引用块（>）：用 `<br>` + lazy continuation，续行不需要 `>`
* - 段落间距：`\n\n`
*
* 本函数按上述约定转换：
* - 代码块内：完全保留原始 `\n`
* - 连续引用行：合并为一行，`<br>` 连接，去掉续行 `>` 前缀
* - 其余：Markdown 块语法行前保留 `\n`，单 `\n` → `<br>`
*/
function fixNewlines(text) {
	const normalized = normalizeLineEndings(text);
	const markdownBlockStartPattern = /^(\s{0,3}(?:[-*+]|\d+[.)])[ ])|(\s{0,3}\|)|(\s{0,3}#{1,6}\s)|(\s{0,3}(?:[-*_])\s*(?:[-*_])\s*(?:[-*_]))/;
	const fencePattern = /^\s{0,3}```/;
	const quotePattern = /^\s{0,3}>\s?/;
	const mergedLines = [];
	let pendingQuoteLines = [];
	let inCodeBlock = false;
	const flushPendingQuoteLines = () => {
		if (pendingQuoteLines.length > 0) {
			mergedLines.push(pendingQuoteLines.join("<br>"));
			pendingQuoteLines = [];
		}
	};
	for (const line of normalized.split("\n")) {
		const isFence = fencePattern.test(line);
		if (inCodeBlock) {
			flushPendingQuoteLines();
			mergedLines.push(line);
			if (isFence) inCodeBlock = false;
			continue;
		}
		if (isFence) {
			flushPendingQuoteLines();
			mergedLines.push(line);
			inCodeBlock = true;
			continue;
		}
		if (quotePattern.test(line)) if (pendingQuoteLines.length === 0) pendingQuoteLines.push(line);
		else pendingQuoteLines.push(line.replace(quotePattern, ""));
		else {
			flushPendingQuoteLines();
			mergedLines.push(line);
		}
	}
	flushPendingQuoteLines();
	const lines = mergedLines;
	inCodeBlock = false;
	const parts = [];
	for (let i = 0; i < lines.length; i++) {
		const currentLine = lines[i];
		const nextInCodeBlock = fencePattern.test(currentLine) ? !inCodeBlock : inCodeBlock;
		if (i < lines.length - 1) {
			const nextLine = lines[i + 1];
			const keepNewline = nextInCodeBlock || currentLine === "" || nextLine === "" || fencePattern.test(nextLine) || markdownBlockStartPattern.test(nextLine);
			parts.push(currentLine + (keepNewline ? "\n" : "<br>"));
		} else parts.push(currentLine);
		inCodeBlock = nextInCodeBlock;
	}
	return parts.join("");
}
/**
* 标准化 AI Card 消息内容：先修复表格空行，再处理换行符。
* 用于 streamAICard 和 finishAICard 的所有路径，确保行为一致。
*/
function normalizeForCard(content) {
	return fixNewlines(ensureTableBlankLines(content));
}
/**
* 构建卡片投放请求体
*/
function buildDeliverBody(cardInstanceId, target, robotCode) {
	const base = {
		outTrackId: cardInstanceId,
		userIdType: 1
	};
	if (target.type === "group") return {
		...base,
		openSpaceId: `dtv1.card//IM_GROUP.${target.openConversationId}`,
		imGroupOpenDeliverModel: { robotCode }
	};
	return {
		...base,
		openSpaceId: `dtv1.card//IM_ROBOT.${target.userId}`,
		imRobotOpenDeliverModel: {
			spaceType: "IM_ROBOT",
			robotCode,
			extension: { dynamicSummary: "true" }
		}
	};
}
/**
* 通用 AI Card 创建函数
*/
async function createAICardForTarget(config, target, log) {
	const targetDesc = target.type === "group" ? `群聊 ${target.openConversationId}` : `用户 ${target.userId}`;
	try {
		const token = await getAccessToken(config);
		const cardInstanceId = `card_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
		log?.info?.(`[DingTalk][AICard] 开始创建卡片：${targetDesc}, outTrackId=${cardInstanceId}`);
		const createBody = {
			cardTemplateId: AI_CARD_TEMPLATE_ID,
			outTrackId: cardInstanceId,
			cardData: { cardParamMap: { config: JSON.stringify({ autoLayout: true }) } },
			callbackType: "STREAM",
			imGroupOpenSpaceModel: { supportForward: true },
			imRobotOpenSpaceModel: { supportForward: true }
		};
		await dingtalkHttp.post(`${DINGTALK_API}/v1.0/card/instances`, createBody, { headers: {
			"x-acs-dingtalk-access-token": token,
			"Content-Type": "application/json"
		} });
		const deliverBody = buildDeliverBody(cardInstanceId, target, String(config.clientId ?? ""));
		await dingtalkHttp.post(`${DINGTALK_API}/v1.0/card/instances/deliver`, deliverBody, { headers: {
			"x-acs-dingtalk-access-token": token,
			"Content-Type": "application/json"
		} });
		return {
			cardInstanceId,
			accessToken: token,
			tokenExpireTime: Date.now() + 7200 * 1e3,
			inputingStarted: false
		};
	} catch (err) {
		log?.error?.(`[DingTalk][AICard] 创建卡片失败 (${targetDesc}): ${err.message}`);
		if (err.response) log?.error?.(`[DingTalk][AICard] 错误响应：status=${err.response.status}`);
		return null;
	}
}
/**
* 确保 Token 有效（自动刷新过期的 Token）
*/
async function ensureValidToken(card, config) {
	if (Date.now() > card.tokenExpireTime - 300 * 1e3) {
		card.accessToken = await getAccessToken(config);
		card.tokenExpireTime = Date.now() + 7200 * 1e3;
	}
	return card.accessToken;
}
/**
* 流式更新 AI Card 内容
*
* 内置全局令牌桶限流：所有会话共享同一速率限制，
* 遇到 QpsLimit 错误时自动退避 2 秒后重试一次。
*/
async function streamAICard(card, content, finished = false, config, log) {
	if (!card) {
		log?.warn?.(`[DingTalk][AICard] streamAICard 收到 null card，跳过更新`);
		return;
	}
	if (config) await ensureValidToken(card, config);
	if (!card.inputingStarted) {
		const inputingWaitMs = await cardRateLimiter.waitForToken();
		if (inputingWaitMs > 0) log?.debug?.(`[DingTalk][AICard] INPUTING 等待限流令牌 ${inputingWaitMs}ms`);
		const statusBody = {
			outTrackId: card.cardInstanceId,
			cardData: { cardParamMap: {
				flowStatus: AICardStatus.INPUTING,
				msgContent: normalizeForCard(content),
				staticMsgContent: "",
				sys_full_json_obj: JSON.stringify({ order: ["msgContent"] }),
				config: JSON.stringify({ autoLayout: true })
			} }
		};
		const putInputing = () => dingtalkHttp.put(`${DINGTALK_API}/v1.0/card/instances`, statusBody, { headers: {
			"x-acs-dingtalk-access-token": card.accessToken,
			"Content-Type": "application/json"
		} });
		try {
			const statusResp = await putInputing();
			log?.info?.(`[DingTalk][AICard] INPUTING 响应：status=${statusResp.status}`);
		} catch (err) {
			if (isQpsLimitError(err)) {
				cardRateLimiter.triggerBackoff();
				log?.warn?.(`[DingTalk][AICard] INPUTING 触发 QPS 限流，退避 ${QPS_BACKOFF_DURATION_MS}ms 后重试`);
				await cardRateLimiter.waitForToken();
				try {
					const retryResp = await putInputing();
					log?.info?.(`[DingTalk][AICard] INPUTING 重试成功：status=${retryResp.status}`);
				} catch (retryErr) {
					log?.error?.(`[DingTalk][AICard] INPUTING 重试失败：${retryErr.message}`);
					throw retryErr;
				}
			} else {
				log?.error?.(`[DingTalk][AICard] INPUTING 切换失败：${err.message}`);
				throw err;
			}
		}
		card.inputingStarted = true;
	}
	const fixedContent = normalizeForCard(content);
	const streamContent = finished ? fixedContent : fixedContent.replace(/\n+$/, "");
	const body = {
		outTrackId: card.cardInstanceId,
		guid: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
		key: "msgContent",
		content: streamContent,
		isFull: true,
		isFinalize: finished,
		isError: false
	};
	const streamWaitMs = await cardRateLimiter.waitForToken();
	if (streamWaitMs > 0) log?.debug?.(`[DingTalk][AICard] streaming 等待限流令牌 ${streamWaitMs}ms`);
	log?.info?.(`[DingTalk][AICard] PUT /v1.0/card/streaming contentLen=${content.length} isFinalize=${finished}`);
	try {
		const streamResp = await dingtalkHttp.put(`${DINGTALK_API}/v1.0/card/streaming`, body, { headers: {
			"x-acs-dingtalk-access-token": card.accessToken,
			"Content-Type": "application/json"
		} });
		log?.info?.(`[DingTalk][AICard] streaming 响应：status=${streamResp.status}`);
	} catch (err) {
		if (isQpsLimitError(err)) {
			cardRateLimiter.triggerBackoff();
			log?.warn?.(`[DingTalk][AICard] streaming 触发 QPS 限流，退避 ${QPS_BACKOFF_DURATION_MS}ms 后重试`);
			await cardRateLimiter.waitForToken();
			try {
				body.guid = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
				await dingtalkHttp.put(`${DINGTALK_API}/v1.0/card/streaming`, body, { headers: {
					"x-acs-dingtalk-access-token": card.accessToken,
					"Content-Type": "application/json"
				} });
				log?.info?.(`[DingTalk][AICard] streaming 重试成功`);
				return;
			} catch (retryErr) {
				log?.error?.(`[DingTalk][AICard] streaming 重试失败：${retryErr.message}`);
				throw retryErr;
			}
		}
		throw err;
	}
}
/**
* 完成 AI Card
*/
async function finishAICard(card, content, config, log) {
	if (config) await ensureValidToken(card, config);
	const fixedContent = normalizeForCard(content);
	log?.info?.(`[DingTalk][AICard] 开始 finish，最终内容长度=${fixedContent.length}`);
	await streamAICard(card, fixedContent, true, config, log);
	const body = {
		outTrackId: card.cardInstanceId,
		cardData: { cardParamMap: {
			flowStatus: AICardStatus.FINISHED,
			msgContent: fixedContent,
			staticMsgContent: "",
			sys_full_json_obj: JSON.stringify({ order: ["msgContent"] }),
			config: JSON.stringify({ autoLayout: true })
		} },
		cardUpdateOptions: { updateCardDataByKey: true }
	};
	const putFinished = () => dingtalkHttp.put(`${DINGTALK_API}/v1.0/card/instances`, body, { headers: {
		"x-acs-dingtalk-access-token": card.accessToken,
		"Content-Type": "application/json"
	} });
	try {
		await cardRateLimiter.waitForToken();
		const finishResp = await putFinished();
		log?.info?.(`[DingTalk][AICard] FINISHED 响应：status=${finishResp.status}`);
	} catch (err) {
		if (isQpsLimitError(err)) {
			cardRateLimiter.triggerBackoff();
			log?.warn?.(`[DingTalk][AICard] FINISHED 触发 QPS 限流，退避 ${QPS_BACKOFF_DURATION_MS}ms 后重试`);
			try {
				await cardRateLimiter.waitForToken();
				const retryResp = await putFinished();
				log?.info?.(`[DingTalk][AICard] FINISHED 重试成功：status=${retryResp.status}`);
				return;
			} catch (retryErr) {
				log?.error?.(`[DingTalk][AICard] FINISHED 重试失败：${retryErr.message}`);
			}
		} else log?.error?.(`[DingTalk][AICard] FINISHED 更新失败：${err.message}`);
	}
}
//#endregion
//#region src/services/messaging/mentions.ts
/**
* 从全局 cfg 里构建「bot 别名 → chatbotUserId」的解析表。
*
* 会同时扫描：
* - `channels.dingtalk-connector.accounts.*`：accountId + name + chatbotUserId
* - `bindings[]`：根据 `match.accountId` 反查 agentId
*/
function buildBotMentionTable(cfg, options = {}) {
	const accountsMap = (cfg?.channels?.["dingtalk-connector"])?.accounts || {};
	const byAccountId = /* @__PURE__ */ new Map();
	for (const [accountId, acct] of Object.entries(accountsMap)) {
		if (!acct) continue;
		byAccountId.set(accountId, {
			accountId,
			chatbotUserId: acct.chatbotUserId?.trim?.() || void 0,
			name: acct.name?.trim?.() || void 0,
			agentIds: [],
			aliases: []
		});
	}
	const bindings = cfg?.bindings;
	if (Array.isArray(bindings)) for (const b of bindings) {
		const match = b?.match;
		if (!match) continue;
		if (match.channel && match.channel !== "dingtalk-connector") continue;
		const accountId = match.accountId;
		const agentId = b.agentId;
		if (typeof accountId !== "string" || typeof agentId !== "string") continue;
		const entry = byAccountId.get(accountId);
		if (!entry) continue;
		if (!entry.agentIds.includes(agentId)) entry.agentIds.push(agentId);
	}
	const extraMap = /* @__PURE__ */ new Map();
	if (options.extraAliases) {
		for (const [alias, accountId] of Object.entries(options.extraAliases)) if (alias && accountId) extraMap.set(alias.toLowerCase(), accountId);
	}
	for (const entry of byAccountId.values()) {
		const aliasSet = /* @__PURE__ */ new Set();
		aliasSet.add(entry.accountId);
		if (entry.name) aliasSet.add(entry.name);
		for (const aid of entry.agentIds) aliasSet.add(aid);
		for (const [alias, accountId] of extraMap.entries()) if (accountId === entry.accountId) aliasSet.add(alias);
		entry.aliases = Array.from(aliasSet);
	}
	return Array.from(byAccountId.values());
}
/** chatbotUserId 加密 ID 的正则（用于检测文本里已经写成加密形式的 @） */
const CHATBOT_ID_PATTERN = /\$:LWCP_v1:\$[A-Za-z0-9+/=]+/g;
/**
* 把一批 accountId 解析成对应的 chatbotUserId 数组。
* 找不到 chatbotUserId 的账号会被跳过，并通过 `missing` 报告，方便上层 log 警告。
*/
function resolveAtAccountIdsToChatbotUserIds(cfg, atAccountIds) {
	if (!atAccountIds || atAccountIds.length === 0) return {
		resolved: [],
		missing: []
	};
	const table = buildBotMentionTable(cfg);
	const byAccountId = new Map(table.map((e) => [e.accountId, e]));
	const resolved = [];
	const missing = [];
	for (const id of atAccountIds) {
		if (!id) continue;
		const entry = byAccountId.get(id);
		if (entry?.chatbotUserId) resolved.push(entry.chatbotUserId);
		else missing.push(id);
	}
	return {
		resolved,
		missing
	};
}
/**
* 对文本中的 @ 别名做自动替换：
* 1. `@<alias>` → `@<chatbotUserId>`（alias 命中某个 bot 时）
* 2. 已经是 `@$:LWCP_v1:$xxx` 形式的 @ 原样保留
*
* 返回：
* - `text`：替换后的文本
* - `injectedChatbotUserIds`：本次替换中涉及到的 chatbotUserId 列表（调用方可合并到 atDingtalkIds）
*/
function substituteBotMentions(text, cfg, options = {}) {
	if (!text || typeof text !== "string") return {
		text: text ?? "",
		injectedChatbotUserIds: []
	};
	const table = buildBotMentionTable(cfg, options);
	const aliasToChatbotUserId = /* @__PURE__ */ new Map();
	for (const entry of table) {
		if (!entry.chatbotUserId) continue;
		for (const alias of entry.aliases) {
			const key = alias.toLowerCase();
			if (!aliasToChatbotUserId.has(key)) aliasToChatbotUserId.set(key, entry.chatbotUserId);
		}
	}
	if (aliasToChatbotUserId.size === 0) return {
		text,
		injectedChatbotUserIds: []
	};
	const aliases = Array.from(aliasToChatbotUserId.keys()).sort((a, b) => b.length - a.length);
	const injected = /* @__PURE__ */ new Set();
	let out = text;
	for (const alias of aliases) {
		const chatbotUserId = aliasToChatbotUserId.get(alias);
		const escaped = alias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
		const pattern = new RegExp(`@(${escaped})(?![A-Za-z0-9_\\u4e00-\\u9fff\\-])`, "gi");
		out = out.replace(pattern, (match, _matched, offset) => {
			if (out.slice(Math.max(0, offset - 1), offset) === "$") return match;
			injected.add(chatbotUserId);
			return `@${chatbotUserId}`;
		});
	}
	if (options.detectBareAliases) for (const alias of aliases) {
		const chatbotUserId = aliasToChatbotUserId.get(alias);
		const escaped = alias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
		if (new RegExp(`(?<![@A-Za-z0-9_\\u4e00-\\u9fff\\-])(${escaped})(?![A-Za-z0-9_\\u4e00-\\u9fff\\-])`, "gi").test(out)) injected.add(chatbotUserId);
	}
	const rawIds = out.match(CHATBOT_ID_PATTERN) || [];
	for (const id of rawIds) injected.add(id);
	return {
		text: out,
		injectedChatbotUserIds: Array.from(injected)
	};
}
/**
* 高层入口：同时处理显式 `atAccountIds` 与文本里的自然语言 @。
*
* 用于 `dingtalk-connector.send*` 系列 Gateway 方法，在调 `sendProactive` 前把最终
* 的 `content / atDingtalkIds` 准备好。
*/
function prepareMultiBotMentions(params) {
	const { cfg, content, atAccountIds, atDingtalkIds = [], extraAliases } = params;
	const explicit = resolveAtAccountIdsToChatbotUserIds(cfg, atAccountIds);
	const substituted = substituteBotMentions(content, cfg, { extraAliases });
	const merged = /* @__PURE__ */ new Set();
	for (const id of atDingtalkIds) if (id) merged.add(id);
	for (const id of explicit.resolved) merged.add(id);
	for (const id of substituted.injectedChatbotUserIds) merged.add(id);
	let finalContent = substituted.text;
	for (const id of explicit.resolved) if (!finalContent.includes(`@${id}`)) finalContent = `${finalContent} @${id}`;
	return {
		content: finalContent,
		atDingtalkIds: Array.from(merged),
		missingAccountIds: explicit.missing
	};
}
//#endregion
//#region src/services/messaging.ts
/**
* 发送 Markdown 消息
* 支持 @用户（atUserId）和 @机器人（atDingtalkIds）
*/
async function sendMarkdownMessage(config, sessionWebhook, title, markdown, options = {}) {
	const token = await getAccessToken(config);
	let text = markdown;
	let mergedAtDingtalkIds = Array.isArray(options.atDingtalkIds) ? [...options.atDingtalkIds] : [];
	if (options.cfg) {
		const substituted = substituteBotMentions(text, options.cfg, { detectBareAliases: Boolean(options.detectBareAliases) });
		text = substituted.text;
		for (const id of substituted.injectedChatbotUserIds) if (!mergedAtDingtalkIds.includes(id)) mergedAtDingtalkIds.push(id);
	}
	if (options.atUserId) text = `${text} @${options.atUserId}`;
	if (mergedAtDingtalkIds.length) {
		for (const id of mergedAtDingtalkIds) if (!text.includes(`@${id}`)) text = `${text} @${id}`;
	}
	const body = {
		msgtype: "markdown",
		markdown: {
			title: title || "Message",
			text
		}
	};
	const atUserIds = options.atUserId ? [options.atUserId] : [];
	const atDingtalkIds = mergedAtDingtalkIds;
	if (atUserIds.length > 0 || atDingtalkIds.length > 0) body.at = {
		...atUserIds.length > 0 ? { atUserIds } : {},
		...atDingtalkIds.length > 0 ? { atDingtalkIds } : {},
		isAtAll: false
	};
	return (await dingtalkHttp.post(sessionWebhook, body, { headers: {
		"x-acs-dingtalk-access-token": token,
		"Content-Type": "application/json"
	} })).data;
}
/**
* 发送文本消息
* 支持 @用户（atUserId）和 @机器人（atDingtalkIds）
*/
async function sendTextMessage(config, sessionWebhook, text, options = {}) {
	const token = await getAccessToken(config);
	let content = text;
	let mergedAtDingtalkIds = Array.isArray(options.atDingtalkIds) ? [...options.atDingtalkIds] : [];
	if (options.cfg) {
		const substituted = substituteBotMentions(content, options.cfg, { detectBareAliases: Boolean(options.detectBareAliases) });
		content = substituted.text;
		for (const id of substituted.injectedChatbotUserIds) if (!mergedAtDingtalkIds.includes(id)) mergedAtDingtalkIds.push(id);
	}
	if (mergedAtDingtalkIds.length) {
		for (const id of mergedAtDingtalkIds) if (!content.includes(`@${id}`)) content = `${content} @${id}`;
	}
	const body = {
		msgtype: "text",
		text: { content }
	};
	const atUserIds = options.atUserId ? [options.atUserId] : [];
	const atDingtalkIds = mergedAtDingtalkIds;
	if (atUserIds.length > 0 || atDingtalkIds.length > 0) body.at = {
		...atUserIds.length > 0 ? { atUserIds } : {},
		...atDingtalkIds.length > 0 ? { atDingtalkIds } : {},
		isAtAll: false
	};
	return (await dingtalkHttp.post(sessionWebhook, body, { headers: {
		"x-acs-dingtalk-access-token": token,
		"Content-Type": "application/json"
	} })).data;
}
/**
* 智能选择 text / markdown
*/
async function sendMessage(config, sessionWebhook, text, options = {}) {
	const mergedOptions = { ...options };
	let workingText = text;
	if (options.cfg && typeof workingText === "string" && workingText.length > 0) {
		const substituted = substituteBotMentions(workingText, options.cfg, { detectBareAliases: Boolean(options.detectBareAliases) });
		workingText = substituted.text;
		if (substituted.injectedChatbotUserIds.length > 0) {
			const existing = Array.isArray(mergedOptions.atDingtalkIds) ? mergedOptions.atDingtalkIds : [];
			mergedOptions.atDingtalkIds = Array.from(new Set([...existing, ...substituted.injectedChatbotUserIds]));
		}
	}
	if (typeof workingText === "string" && workingText.length > 0) {
		const found = Array.from(new Set(workingText.match(/\$:LWCP_v1:\$[A-Za-z0-9+/=]+/g) || []));
		if (found.length > 0) {
			const existing = Array.isArray(mergedOptions.atDingtalkIds) ? mergedOptions.atDingtalkIds : [];
			mergedOptions.atDingtalkIds = Array.from(new Set([...existing, ...found]));
		}
	}
	const hasMarkdown = /^[#*>-]|[*_`#\[\]]/.test(workingText) || workingText && typeof workingText === "string" && workingText.includes("\n");
	const useMarkdown = mergedOptions.useMarkdown !== false && (mergedOptions.useMarkdown || hasMarkdown);
	const downstreamOptions = { ...mergedOptions };
	delete downstreamOptions.cfg;
	if (useMarkdown) return sendMarkdownMessage(config, sessionWebhook, downstreamOptions.title || workingText.split("\n")[0].replace(/^[#*\s\->]+/, "").slice(0, 20) || "Message", workingText, downstreamOptions);
	return sendTextMessage(config, sessionWebhook, workingText, downstreamOptions);
}
/**
* 构建普通消息的 msgKey 和 msgParam
*
* 第四个参数可携带 at 信息：
* - atDingtalkIds：对方加密 dingtalkId / chatbotUserId（多机器人协作时使用）
* - atUserIds：普通成员 staffId
* 这些 ID 会以 `@${id}` 文本附加到 content 末尾（钉钉客户端会尝试将其渲染成 @ 标签）。
*/
function buildMsgPayload(msgType, content, title, atOptions) {
	const appendAtMentions = (raw) => {
		if (!atOptions) return raw;
		let out = raw ?? "";
		const ids = [...atOptions.atDingtalkIds || [], ...atOptions.atUserIds || []];
		for (const id of ids) if (id && !out.includes(`@${id}`)) out = `${out} @${id}`;
		if (atOptions.atAll && !out.includes("@all")) out = `${out} @all`;
		return out;
	};
	switch (msgType) {
		case "markdown": {
			const text = appendAtMentions(content);
			return {
				msgKey: "sampleMarkdown",
				msgParam: {
					title: title || content.split("\n")[0].replace(/^[#*\s\->]+/, "").slice(0, 20) || "Message",
					text
				}
			};
		}
		case "link": try {
			return {
				msgKey: "sampleLink",
				msgParam: typeof content === "string" ? JSON.parse(content) : content
			};
		} catch {
			return { error: "Invalid link message format, expected JSON" };
		}
		case "actionCard": try {
			return {
				msgKey: "sampleActionCard",
				msgParam: typeof content === "string" ? JSON.parse(content) : content
			};
		} catch {
			return { error: "Invalid actionCard message format, expected JSON" };
		}
		case "image": return {
			msgKey: "sampleImageMsg",
			msgParam: { photoURL: content }
		};
		default: return {
			msgKey: "sampleText",
			msgParam: { content: appendAtMentions(content) }
		};
	}
}
/**
* 发送文本消息（用于 outbound 接口）
*/
async function sendTextToDingTalk(params) {
	const { config, target, text, replyToId } = params;
	const log = createLoggerFromConfig(config, "sendTextToDingTalk");
	if (!target || typeof target !== "string") {
		log.error("target 参数无效:", target);
		return {
			ok: false,
			error: "Invalid target parameter",
			usedAICard: false
		};
	}
	let targetParam;
	if (target.startsWith("group:")) targetParam = {
		type: "group",
		openConversationId: target.slice(6)
	};
	else if (target.startsWith("user:")) targetParam = {
		type: "user",
		userId: target.slice(5)
	};
	else if (target.startsWith("cid")) targetParam = {
		type: "group",
		openConversationId: target
	};
	else targetParam = {
		type: "user",
		userId: target
	};
	return sendProactive(config, targetParam, text, {
		msgType: "text",
		replyToId
	});
}
/**
* 发送媒体消息（用于 outbound 接口）
*/
async function sendMediaToDingTalk(params) {
	const log = createLoggerFromConfig(params.config, "sendMediaToDingTalk");
	log.info("开始处理，params:", JSON.stringify({
		target: params.target,
		text: params.text,
		mediaUrl: params.mediaUrl,
		replyToId: params.replyToId,
		hasConfig: !!params.config
	}));
	const { config, target, text, mediaUrl, replyToId, mediaLocalRoots } = params;
	if (!target || typeof target !== "string") {
		log.error("target 参数无效:", target);
		return {
			ok: false,
			error: "Invalid target parameter",
			usedAICard: false
		};
	}
	let targetParam;
	if (target.startsWith("group:")) targetParam = {
		type: "group",
		openConversationId: target.slice(6)
	};
	else if (target.startsWith("user:")) targetParam = {
		type: "user",
		userId: target.slice(5)
	};
	else if (target.startsWith("cid")) targetParam = {
		type: "group",
		openConversationId: target
	};
	else targetParam = {
		type: "user",
		userId: target
	};
	log.info("参数解析完成，mediaUrl:", mediaUrl, "type:", typeof mediaUrl);
	if (!mediaUrl) {
		log.info("mediaUrl 为空，返回错误提示");
		return sendProactive(config, targetParam, text ?? "⚠️ 缺少媒体文件 URL", {
			msgType: "text",
			replyToId
		});
	}
	if (text && text.trim().length > 0) {
		log.info("先发送文本消息:", text);
		await sendProactive(config, targetParam, text, {
			msgType: "text",
			replyToId
		});
	}
	try {
		log.info("开始获取 oapiToken");
		const oapiToken = await getOapiAccessToken(config);
		log.info("oapiToken 获取成功");
		log.info("开始解析文件扩展名，mediaUrl:", mediaUrl);
		const ext = mediaUrl.toLowerCase().split(".").pop() || "";
		log.info("文件扩展名:", ext);
		let mediaType = "file";
		if ([
			"jpg",
			"jpeg",
			"png",
			"gif",
			"bmp",
			"webp"
		].includes(ext)) mediaType = "image";
		else if ([
			"mp4",
			"avi",
			"mov",
			"mkv",
			"flv",
			"wmv",
			"webm"
		].includes(ext)) mediaType = "video";
		else if ([
			"mp3",
			"wav",
			"aac",
			"ogg",
			"m4a",
			"flac",
			"wma",
			"amr"
		].includes(ext)) mediaType = "voice";
		log.info("媒体类型判断完成:", mediaType);
		let maxSize;
		switch (mediaType) {
			case "image":
				maxSize = 10 * 1024 * 1024;
				break;
			case "voice":
				maxSize = 2 * 1024 * 1024;
				break;
			case "video":
			case "file":
				maxSize = 20 * 1024 * 1024;
				break;
			default: maxSize = 20 * 1024 * 1024;
		}
		log.info("准备调用 uploadMediaToDingTalk，参数:", {
			mediaUrl,
			mediaType,
			maxSizeMB: (maxSize / (1024 * 1024)).toFixed(0)
		});
		if (!oapiToken) {
			log.error("oapiToken 为空，无法上传媒体文件");
			return sendProactive(config, targetParam, "⚠️ 媒体文件处理失败：缺少 oapiToken", {
				msgType: "text",
				replyToId
			});
		}
		let resolvedMediaUrl = mediaUrl;
		const { toLocalPath } = await import("./media-CIO05hZn.mjs");
		const _fs = await import("fs");
		const _path = await import("path");
		const directPath = toLocalPath(mediaUrl);
		if (!_fs.existsSync(directPath) && mediaLocalRoots?.length && !_path.isAbsolute(directPath)) for (const root of mediaLocalRoots) {
			const candidate = _path.resolve(root, directPath);
			if (_fs.existsSync(candidate)) {
				log.info(`相对路径解析成功：${mediaUrl} → ${candidate}（基于 mediaLocalRoots）`);
				resolvedMediaUrl = candidate;
				break;
			}
		}
		const uploadResult = await uploadMediaToDingTalk(resolvedMediaUrl, mediaType, oapiToken, maxSize, log);
		log.info("uploadMediaToDingTalk 返回结果:", uploadResult);
		if (!uploadResult) {
			log.error("上传失败，返回错误提示");
			return sendProactive(config, targetParam, "⚠️ 媒体文件上传失败", {
				msgType: "text",
				replyToId
			});
		}
		log.info("提取 media_id:", uploadResult.mediaId);
		const fileName = mediaUrl.split("/").pop() || "file";
		if (mediaType === "image") {
			const result = await sendProactive(config, targetParam, uploadResult.mediaId, {
				msgType: "image",
				replyToId
			});
			return {
				...result,
				processQueryKey: result.processQueryKey || "image-message-sent"
			};
		}
		if (mediaType === "video") {
			const videoMarker = `[DINGTALK_VIDEO]{"path":"${mediaUrl}"}[/DINGTALK_VIDEO]`;
			const { processVideoMarkers } = await import("./media-CIO05hZn.mjs");
			await processVideoMarkers(videoMarker, "", config, oapiToken, console, true, targetParam);
			if (text?.trim()) {
				const result = await sendProactive(config, targetParam, text, {
					msgType: "text",
					replyToId
				});
				return {
					...result,
					processQueryKey: result.processQueryKey || "video-text-sent"
				};
			}
			return {
				ok: true,
				usedAICard: false,
				processQueryKey: "video-message-sent"
			};
		}
		(await import("fs")).statSync(mediaUrl);
		const fileInfo = {
			path: mediaUrl,
			fileName,
			fileType: ext || "file"
		};
		const { sendFileProactive } = await import("./media-CIO05hZn.mjs");
		await sendFileProactive(config, targetParam, fileInfo, uploadResult.mediaId, log);
		return {
			ok: true,
			usedAICard: false,
			processQueryKey: "file-message-sent"
		};
	} catch (err) {
		log.error("发送媒体消息失败:", err.message);
		return sendProactive(config, targetParam, `⚠️ 媒体文件处理失败: ${err.message}`, {
			msgType: "text",
			replyToId
		});
	}
}
/**
* 智能发送消息
*/
async function sendProactive(config, target, content, options = {}) {
	const log = createLoggerFromConfig(config, "sendProactive");
	log.info("开始处理，参数:", JSON.stringify({
		target,
		contentLength: content?.length,
		hasOptions: !!options
	}));
	if (!options.msgType) {
		if (/^[#*>-]|[*_`#\[\]]/.test(content) || content && typeof content === "string" && content.includes("\n")) options.msgType = "markdown";
	}
	if (target.userId || target.userIds) {
		const userId = (target.userIds || [target.userId])[0];
		log.info("发送给用户，userId:", userId);
		return sendProactiveInternal(config, {
			type: "user",
			userId
		}, content, options);
	}
	if (target.openConversationId) {
		log.info("发送给群聊，openConversationId:", target.openConversationId);
		return sendProactiveInternal(config, {
			type: "group",
			openConversationId: target.openConversationId
		}, content, options);
	}
	log.error("target 参数缺少必要字段:", target);
	return {
		ok: false,
		error: "Must specify userId, userIds, or openConversationId",
		usedAICard: false
	};
}
/**
* 内部发送实现
*/
async function sendProactiveInternal(config, target, content, options) {
	const log = createLoggerFromConfig(config, "sendProactiveInternal");
	log.info("开始处理，参数:", JSON.stringify({
		target,
		contentLength: content?.length,
		msgType: options.msgType,
		useAICard: options.useAICard,
		targetType: target?.type,
		hasTarget: !!target
	}));
	if (!target || typeof target !== "object") {
		log.error("target 参数无效:", target);
		return {
			ok: false,
			error: "Invalid target parameter",
			usedAICard: false
		};
	}
	const { msgType = "text", useAICard = true, fallbackToNormal = true, log: externalLog } = options;
	const isMediaMessage = MEDIA_MSG_TYPES.has(msgType);
	if (useAICard && !isMediaMessage) try {
		const card = await createAICardForTarget(config, target, externalLog);
		if (card) {
			await finishAICard(card, content, config, externalLog);
			return {
				ok: true,
				cardInstanceId: card.cardInstanceId,
				usedAICard: true
			};
		}
		if (!fallbackToNormal) return {
			ok: false,
			error: "Failed to create AI Card",
			usedAICard: false
		};
	} catch (err) {
		externalLog?.error?.(`AI Card 发送失败: ${err.message}`);
		if (!fallbackToNormal) return {
			ok: false,
			error: err.message,
			usedAICard: false
		};
	}
	try {
		log.info("准备发送普通消息，target.type:", target.type);
		const token = await getAccessToken(config);
		const isUser = target.type === "user";
		log.info("isUser:", isUser, "target:", JSON.stringify(target));
		const targetId = isUser ? target.userId : target.openConversationId;
		log.info("targetId:", targetId);
		const webhookUrl = isUser ? `${DINGTALK_API}/v1.0/robot/oToMessages/batchSend` : `${DINGTALK_API}/v1.0/robot/groupMessages/send`;
		const payload = buildMsgPayload(msgType, content, options.title, {
			atDingtalkIds: options.atDingtalkIds,
			atUserIds: options.atUserIds,
			atAll: options.atAll
		});
		if ("error" in payload) {
			log.error("构建消息失败:", payload.error);
			return {
				ok: false,
				error: payload.error,
				usedAICard: false
			};
		}
		const body = {
			robotCode: String(config.clientId),
			msgKey: payload.msgKey,
			msgParam: JSON.stringify(payload.msgParam)
		};
		if (isUser) body.userIds = [targetId];
		else body.openConversationId = targetId;
		externalLog?.info?.(`发送${isUser ? "单聊" : "群聊"}消息：${isUser ? "userIds=" : "openConversationId="}${targetId}`);
		const resp = await dingtalkHttp.post(webhookUrl, body, { headers: {
			"x-acs-dingtalk-access-token": token,
			"Content-Type": "application/json"
		} });
		try {
			const dataPreview = JSON.stringify(resp.data ?? {});
			const truncated = dataPreview.length > 2e3 ? `${dataPreview.slice(0, 2e3)}...(truncated)` : dataPreview;
			const msg = `发送${isUser ? "单聊" : "群聊"}消息响应：status=${resp.status}, processQueryKey=${resp.data?.processQueryKey ?? ""}, data=${truncated}`;
			log.info(msg);
			externalLog?.info?.(msg);
		} catch {
			const msg = `发送${isUser ? "单聊" : "群聊"}消息响应：status=${resp.status}, processQueryKey=${resp.data?.processQueryKey ?? ""}`;
			log.info(msg);
			externalLog?.info?.(msg);
		}
		return {
			ok: true,
			processQueryKey: resp.data?.processQueryKey,
			usedAICard: false
		};
	} catch (err) {
		const status = err?.response?.status;
		const respData = err?.response?.data;
		let respPreview = "";
		try {
			const raw = JSON.stringify(respData ?? {});
			respPreview = raw.length > 2e3 ? `${raw.slice(0, 2e3)}...(truncated)` : raw;
		} catch {
			respPreview = String(respData ?? "");
		}
		const baseMsg = err?.message ? String(err.message) : String(err);
		const extra = typeof status === "number" ? ` status=${status}${respPreview ? `, data=${respPreview}` : ""}` : respPreview ? ` data=${respPreview}` : "";
		const msg = `发送${target.type === "user" ? "单聊" : "群聊"}消息失败：${baseMsg}${extra}`;
		log.error(msg);
		externalLog?.error?.(msg);
		return {
			ok: false,
			error: baseMsg,
			usedAICard: false
		};
	}
}
//#endregion
export { sendTextMessage as a, prepareMultiBotMentions as c, isQpsLimitError as d, streamAICard as f, sendProactive as i, createAICardForTarget as l, sendMediaToDingTalk as n, sendTextToDingTalk as o, sendMessage as r, buildBotMentionTable as s, sendMarkdownMessage as t, finishAICard as u };
