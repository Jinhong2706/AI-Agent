import { n as dingtalkOapiHttp, t as dingtalkHttp } from "./http-client-DFWZgO1n.mjs";
//#region src/utils/token.ts
const DINGTALK_API = "https://api.dingtalk.com";
const DINGTALK_OAPI = "https://oapi.dingtalk.com";
/**
* 按 clientId 分桶缓存，避免多账号串 token。
*/
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
//#endregion
//#region src/utils/empty-reply.ts
/**
* 空回复（final 文本为空）兜底文案集中处。
*
* 背景
* ----
* 群聊场景下用户 @ 机器人后看到空回复兜底文案，常见根因不是 connector，
* 而是上游 OpenClaw 的 reply delivery mode（`source-reply-delivery-mode.ts`）：群聊
* 默认走 `message_tool_only`，会跳过 `onPartialReply` 与 `accumulatedText`，
* 导致本插件累积的文本始终为空，最后落到 connector 的空回复兜底。
*
* 修复路径在 OpenClaw 的 `openclaw.json`：
*   {
*     "messages": {
*       "groupChat": { "visibleReplies": "automatic" }
*     }
*   }
*
* 本模块的优化目标：让兜底文案在两种场景下都自然不"像报错"——
*   - 群聊：返回一段可操作的运维指引（指向 `messages.groupChat.visibleReplies`）。
*   - 单聊：返回一段口语化的简短确认语（单聊空 final 通常是模型自身没产出文本，
*     如纯思考、只走 tool_call、对 ACK 类输入选择沉默等），并隐含邀请用户继续提问，
*     避免历史上的「✅ 任务执行完成（无文本输出）」让用户误以为是报错。
*/
const DIRECT_FALLBACK_TEXT = "好的 👌 有其他问题随时找我";
const GROUP_FALLBACK_TEXT = [
	"ℹ️ 暂未收到模型回复内容。",
	"若群聊频繁出现该提示，请联系机器人管理员检查 OpenClaw 配置：",
	"`messages.groupChat.visibleReplies` 需设为 `\"automatic\"`",
	"（详见 README / TROUBLESHOOTING.md）。"
].join("\n");
const GROUP_FALLBACK_LOG_HINT = "群聊 final 文本为空：常见根因是 OpenClaw `messages.groupChat.visibleReplies` 未设为 \"automatic\"（上游 source-reply-delivery-mode.ts 默认 message_tool_only， 会跳过 partial/accumulated 文本）。请在 openclaw.json 中追加：{ \"messages\": { \"groupChat\": { \"visibleReplies\": \"automatic\" } } }，然后 `openclaw gateway restart`。详见 docs/TROUBLESHOOTING.md。";
/**
* 选取空回复的兜底文案。
*
* - 群聊：附带修复指引（指向 OpenClaw `messages.groupChat.visibleReplies` 配置）。
* - 单聊：维持原文案，避免对模型本身就输出空的常规场景产生噪音。
*/
function pickEmptyReplyFallbackText(isGroup) {
	return isGroup ? GROUP_FALLBACK_TEXT : DIRECT_FALLBACK_TEXT;
}
/**
* 群聊空回复时给运维的 warn 级别日志指引（含 openclaw.json 修复片段）。
* 单聊不需要这条 hint，因为单聊空回复多半与配置无关。
*/
function emptyGroupReplyLogHint() {
	return GROUP_FALLBACK_LOG_HINT;
}
/**
* 群聊是否未显式将 OpenClaw `messages.groupChat.visibleReplies` 设为 `"automatic"`。
*
* `undefined` / 缺失 / `messages: {}` 均视为未开启（与上游默认 `message_tool_only` 行为一致），
* 需要 connector 在「本轮无任何用户可见回复」时用 idle 兜底提示配置。
*/
function groupChatLacksVisibleRepliesAutomatic(cfg) {
	return cfg?.messages?.groupChat?.visibleReplies !== "automatic";
}
//#endregion
export { DINGTALK_OAPI as a, DINGTALK_API as i, groupChatLacksVisibleRepliesAutomatic as n, getAccessToken as o, pickEmptyReplyFallbackText as r, getOapiAccessToken as s, emptyGroupReplyLogHint as t };
