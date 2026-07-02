//#region src/utils/constants.ts
/**
* 常量定义模块
*/
/** 新会话触发命令 */
const NEW_SESSION_COMMANDS = [
	"/new",
	"/reset",
	"/clear",
	"新会话",
	"重新开始",
	"清空对话"
];
/**
* 媒体类消息类型集合。
*
* 这些消息类型需要通过钉钉原生消息 API 发送，不支持 AI Card 形式，
* 在 sendProactiveInternal 中会强制跳过 AI Card 路径。
*/
const MEDIA_MSG_TYPES = new Set([
	"image",
	"voice",
	"file",
	"video"
]);
/**
* 队列繁忙时的即时 ACK 回复短语。
*
* 当消息入队时检测到上一条消息仍在处理中，立即从此列表中随机选取一条回复，
* 告知用户消息已收到并排队，避免用户以为 Bot 没有响应。
* 参考 delivery.rs 中 DINGTALK_ACK_PHRASES_BUSY_ZH_CN 的设计。
*/
const QUEUE_BUSY_ACK_PHRASES = [
	"上一条还没结束，这条我已经记下，稍后按顺序继续处理。",
	"当前还在忙，你的新消息已经排队，上一条完成后我马上继续。",
	"我这边还在处理上一条，这条已加入队列，完成后继续处理。"
];
//#endregion
//#region src/utils/session.ts
/**
* 会话管理模块
* 构建 OpenClaw 标准会话上下文
*/
/**
* 构建 OpenClaw 标准会话上下文
* 遵循 OpenClaw session.dmScope 机制，让 Gateway 根据配置自动处理会话隔离
* 
* @param sharedMemoryAcrossConversations - 是否在不同会话间共享记忆（默认 false）
*   - true: 所有会话共享记忆，使用 accountId 作为记忆标识
*   - false: 不同会话独立记忆，使用完整的 sessionContext 作为记忆标识
*/
function buildSessionContext(params) {
	const { accountId, senderId, senderName, conversationType, conversationId, groupSubject, separateSessionByConversation, groupSessionScope, sharedMemoryAcrossConversations } = params;
	const isDirect = conversationType === "1";
	const peerId = isDirect ? senderId : conversationId || senderId;
	if (sharedMemoryAcrossConversations === true) return {
		channel: "dingtalk-connector",
		accountId,
		chatType: isDirect ? "direct" : "group",
		peerId,
		sessionPeerId: accountId,
		conversationId: isDirect ? void 0 : conversationId,
		senderName,
		groupSubject: isDirect ? void 0 : groupSubject
	};
	if (separateSessionByConversation === false) return {
		channel: "dingtalk-connector",
		accountId,
		chatType: isDirect ? "direct" : "group",
		peerId,
		sessionPeerId: senderId,
		conversationId: isDirect ? void 0 : conversationId,
		senderName,
		groupSubject: isDirect ? void 0 : groupSubject
	};
	if (isDirect) return {
		channel: "dingtalk-connector",
		accountId,
		chatType: "direct",
		peerId,
		sessionPeerId: senderId,
		senderName
	};
	if (groupSessionScope === "group_sender") return {
		channel: "dingtalk-connector",
		accountId,
		chatType: "group",
		peerId,
		sessionPeerId: `${conversationId}:${senderId}`,
		conversationId,
		senderName,
		groupSubject
	};
	return {
		channel: "dingtalk-connector",
		accountId,
		chatType: "group",
		peerId,
		sessionPeerId: conversationId || senderId,
		conversationId,
		senderName,
		groupSubject
	};
}
/**
* 检查消息是否是新会话命令
*/
function normalizeSlashCommand(text) {
	const lower = text.trim().toLowerCase();
	if (NEW_SESSION_COMMANDS.some((cmd) => lower === cmd.toLowerCase())) return "/new";
	return text;
}
//#endregion
export { QUEUE_BUSY_ACK_PHRASES as a, NEW_SESSION_COMMANDS as i, normalizeSlashCommand as n, MEDIA_MSG_TYPES as r, buildSessionContext as t };
