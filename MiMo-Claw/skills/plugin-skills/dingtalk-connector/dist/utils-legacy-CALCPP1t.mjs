//#region src/utils/utils-legacy.ts
/** 钉钉 API 常量 */
const DINGTALK_API = "https://api.dingtalk.com";
const DINGTALK_OAPI = "https://oapi.dingtalk.com";
const apiTokenCache = /* @__PURE__ */ new Map();
const oapiTokenCache = /* @__PURE__ */ new Map();
function cacheKey(config) {
	const clientId = String(config?.clientId ?? "").trim();
	if (!clientId) throw new Error("Invalid DingtalkConfig: clientId is required for token caching. Please ensure your configuration includes a valid clientId.");
	return clientId;
}
/**
* 获取钉钉 Access Token（新版 API）
*/
async function getAccessToken(config) {
	const now = Date.now();
	const key = cacheKey(config);
	const cached = apiTokenCache.get(key);
	if (cached && cached.expiryMs > now + 6e4) return cached.token;
	const { dingtalkHttp } = await import("./http-client-CpnJHB89.mjs");
	const response = await dingtalkHttp.post(`${DINGTALK_API}/v1.0/oauth2/accessToken`, {
		appKey: config.clientId,
		appSecret: config.clientSecret
	});
	const token = response.data.accessToken;
	const expireInSec = Number(response.data.expireIn ?? 0);
	apiTokenCache.set(key, {
		token,
		expiryMs: now + expireInSec * 1e3
	});
	return token;
}
/**
* 获取钉钉 OAPI Access Token（旧版 API，用于媒体上传等）
*/
async function getOapiAccessToken(config) {
	try {
		const now = Date.now();
		const key = cacheKey(config);
		const cached = oapiTokenCache.get(key);
		if (cached && cached.expiryMs > now + 6e4) return cached.token;
		const { dingtalkOapiHttp } = await import("./http-client-CpnJHB89.mjs");
		const resp = await dingtalkOapiHttp.get(`${DINGTALK_OAPI}/gettoken`, { params: {
			appkey: config.clientId,
			appsecret: config.clientSecret
		} });
		if (resp.data?.errcode === 0 && resp.data?.access_token) {
			const token = String(resp.data.access_token);
			const expiresInSec = Number(resp.data.expires_in ?? 7200);
			oapiTokenCache.set(key, {
				token,
				expiryMs: now + expiresInSec * 1e3
			});
			return token;
		}
		return null;
	} catch {
		return null;
	}
}
/** staffId → unionId 缓存（带过期时间的 LRU 缓存） */
const MAX_UNION_ID_CACHE_SIZE = 1e3;
const UNION_ID_CACHE_TTL = 1440 * 60 * 1e3;
const unionIdCache = /* @__PURE__ */ new Map();
/**
* 通过 oapi 旧版接口将 staffId 转换为 unionId
*/
async function getUnionId(staffId, config, log) {
	const cached = unionIdCache.get(staffId);
	if (cached && Date.now() - cached.timestamp < UNION_ID_CACHE_TTL) return cached.unionId;
	try {
		const token = await getOapiAccessToken(config);
		if (!token) {
			log?.error?.("[DingTalk] getUnionId: 无法获取 oapi access_token");
			return null;
		}
		const { dingtalkOapiHttp } = await import("./http-client-CpnJHB89.mjs");
		const resp = await dingtalkOapiHttp.get(`${DINGTALK_OAPI}/user/get`, {
			params: {
				access_token: token,
				userid: staffId
			},
			timeout: 1e4
		});
		const unionId = resp.data?.unionid;
		if (unionId) {
			if (unionIdCache.size >= MAX_UNION_ID_CACHE_SIZE) {
				let oldestKey = null;
				let oldestTime = Date.now();
				for (const [key, entry] of unionIdCache.entries()) if (entry.timestamp < oldestTime) {
					oldestTime = entry.timestamp;
					oldestKey = key;
				}
				if (oldestKey) unionIdCache.delete(oldestKey);
			}
			unionIdCache.set(staffId, {
				unionId,
				timestamp: Date.now()
			});
			log?.info?.(`[DingTalk] getUnionId: ${staffId} → ${unionId}`);
			return unionId;
		}
		log?.error?.(`[DingTalk] getUnionId: 响应中无 unionid 字段: ${JSON.stringify(resp.data)}`);
		return null;
	} catch (err) {
		log?.error?.(`[DingTalk] getUnionId 失败: ${err.message}`);
		return null;
	}
}
/** 消息去重缓存 Map<messageId, timestamp> - 防止同一消息被重复处理 */
const processedMessages = /* @__PURE__ */ new Map();
/** 消息去重缓存过期时间（5分钟） */
const MESSAGE_DEDUP_TTL = 300 * 1e3;
/**
* 清理过期的消息去重缓存
*/
function cleanupProcessedMessages() {
	const now = Date.now();
	for (const [msgId, timestamp] of processedMessages.entries()) if (now - timestamp > MESSAGE_DEDUP_TTL) processedMessages.delete(msgId);
}
/**
* 检查消息是否已处理过（去重）
*/
function isMessageProcessed(messageId) {
	if (!messageId) return false;
	return processedMessages.has(messageId);
}
/**
* 标记消息为已处理
*/
function markMessageProcessed(messageId) {
	if (!messageId) return;
	processedMessages.set(messageId, Date.now());
	if (processedMessages.size >= 100) cleanupProcessedMessages();
}
/**
* 对钉钉 Stream 消息做双层去重检查，并在首次处理时标记。
*
* 背景：钉钉 Stream 模式存在两套消息 ID：
*   - headers.messageId：WebSocket 协议层的投递 ID，每次重发都会生成新值
*   - data.msgId：业务层的用户消息 ID，重发时保持不变
*
* 因此必须同时检查两个 ID，才能可靠地拦截钉钉服务端的重发消息：
*   1. 协议层去重（headers.messageId）：拦截同一次投递的重复回调
*   2. 业务层去重（data.msgId）：拦截 ~60 秒后服务端因未收到业务回复而触发的重发
*
* 重要：key 必须带 accountId 前缀，避免多账号（多机器人）场景下，
* 同一条群消息 @多个机器人时，不同机器人收到相同 msgId 导致误判为重复消息。
*
* @param accountId         - 当前账号 ID（用于命名空间隔离，防止多账号误判）
* @param protocolMessageId - res.headers.messageId（WebSocket 协议层投递 ID）
* @param businessMsgId     - data.msgId（钉钉业务层消息 ID，来自 JSON.parse(res.data).msgId）
* @returns true 表示消息已处理过（应跳过），false 表示首次处理（已标记为已处理）
*/
function checkAndMarkDingtalkMessage(accountId, protocolMessageId, businessMsgId) {
	const scopedProtocolId = protocolMessageId ? `${accountId}:${protocolMessageId}` : void 0;
	const scopedBusinessId = businessMsgId ? `${accountId}:${businessMsgId}` : void 0;
	const isProtocolDuplicate = scopedProtocolId ? isMessageProcessed(scopedProtocolId) : false;
	const isBusinessDuplicate = scopedBusinessId ? isMessageProcessed(scopedBusinessId) : false;
	if (isProtocolDuplicate || isBusinessDuplicate) return true;
	if (scopedProtocolId) markMessageProcessed(scopedProtocolId);
	if (scopedBusinessId) markMessageProcessed(scopedBusinessId);
	return false;
}
/**
* 在用户消息上贴 🤔思考中 表情，表示正在处理
*/
async function addEmotionReply(config, data, log) {
	if (!data.msgId || !data.conversationId) return;
	try {
		const token = await getAccessToken(config);
		const { dingtalkHttp } = await import("./http-client-CpnJHB89.mjs");
		await dingtalkHttp.post(`${DINGTALK_API}/v1.0/robot/emotion/reply`, {
			robotCode: data.robotCode ?? config.clientId,
			openMsgId: data.msgId,
			openConversationId: data.conversationId,
			emotionType: 2,
			emotionName: "🤔思考中",
			textEmotion: {
				emotionId: "2659900",
				emotionName: "🤔思考中",
				text: "🤔思考中",
				backgroundId: "im_bg_1"
			}
		}, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 5e3
		});
		log?.info?.(`[DingTalk][Emotion] 贴表情成功: msgId=${data.msgId}`);
	} catch (err) {
		log?.warn?.(`[DingTalk][Emotion] 贴表情失败（不影响主流程）: ${err.message}`);
	}
}
/**
* 撤回用户消息上的 🤔思考中 表情
*/
async function recallEmotionReply(config, data, log) {
	if (!data.msgId || !data.conversationId) return;
	try {
		const token = await getAccessToken(config);
		const { dingtalkHttp } = await import("./http-client-CpnJHB89.mjs");
		await dingtalkHttp.post(`${DINGTALK_API}/v1.0/robot/emotion/recall`, {
			robotCode: data.robotCode ?? config.clientId,
			openMsgId: data.msgId,
			openConversationId: data.conversationId,
			emotionType: 2,
			emotionName: "🤔思考中",
			textEmotion: {
				emotionId: "2659900",
				emotionName: "🤔思考中",
				text: "🤔思考中",
				backgroundId: "im_bg_1"
			}
		}, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 5e3
		});
		log?.info?.(`[DingTalk][Emotion] 撤回表情成功: msgId=${data.msgId}`);
	} catch (err) {
		log?.warn?.(`[DingTalk][Emotion] 撤回表情失败（不影响主流程）: ${err.message}`);
	}
}
//#endregion
export { cleanupProcessedMessages as a, getUnionId as c, recallEmotionReply as d, checkAndMarkDingtalkMessage as i, isMessageProcessed as l, DINGTALK_OAPI as n, getAccessToken as o, addEmotionReply as r, getOapiAccessToken as s, DINGTALK_API as t, markMessageProcessed as u };
