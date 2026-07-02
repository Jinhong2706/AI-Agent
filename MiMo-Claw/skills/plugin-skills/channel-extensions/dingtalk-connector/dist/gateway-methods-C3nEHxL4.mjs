import { a as resolveDingtalkAccount, t as listDingtalkAccountIds } from "./accounts-CF4oK_HZ.mjs";
import { t as dingtalkHttp } from "./http-client-DFWZgO1n.mjs";
import { i as DINGTALK_API, o as getAccessToken } from "./utils-DgNm1Ek_.mjs";
import { c as prepareMultiBotMentions, i as sendProactive, s as buildBotMentionTable, u as finishAICard } from "./messaging-C2zJ8O-o.mjs";
import { c as getUnionId, d as recallEmotionReply } from "./utils-legacy-CALCPP1t.mjs";
//#region src/docs.ts
var DingtalkDocsClient = class {
	config;
	log;
	constructor(config, log) {
		this.config = config;
		this.log = log;
	}
	/** 获取带鉴权的请求头 */
	async getHeaders() {
		return {
			"x-acs-dingtalk-access-token": await getAccessToken(this.config),
			"Content-Type": "application/json"
		};
	}
	/**
	* 获取文档元信息
	*/
	async getDocInfo(spaceId, docId) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 获取文档信息: spaceId=${spaceId}, docId=${docId}`);
			const data = (await dingtalkHttp.get(`${DINGTALK_API}/v1.0/doc/spaces/${spaceId}/docs/${docId}`, {
				headers,
				timeout: 1e4
			})).data;
			this.log?.info?.(`[DingTalk][Docs] 文档信息获取成功: title=${data?.title}`);
			return {
				docId: data.docId || docId,
				title: data.title || "",
				docType: data.docType || "unknown",
				creatorId: data.creatorId,
				updatedAt: data.updatedAt
			};
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 获取文档信息失败: ${err.message}`);
			return null;
		}
	}
	/**
	* 读取文档内容（通过 v2.0/wiki 节点 API）
	*/
	async readDoc(nodeId, operatorId) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 读取知识库节点: nodeId=${nodeId}, operatorId=${operatorId}`);
			if (!operatorId) {
				this.log?.error?.("[DingTalk][Docs] readDoc 需要 operatorId（unionId）");
				return null;
			}
			const resp = await dingtalkHttp.get(`${DINGTALK_API}/v2.0/wiki/nodes/${nodeId}/content`, {
				headers,
				params: { operatorId },
				timeout: 3e4
			});
			const node = resp.data?.node || resp.data;
			const name = node.name || "未知文档";
			const category = node.category || "unknown";
			const url = node.url || "";
			const workspaceId = node.workspaceId || "";
			const content = [
				`文档名: ${name}`,
				`类型: ${category}`,
				`URL: ${url}`,
				`工作区: ${workspaceId}`
			].join("\n");
			this.log?.info?.(`[DingTalk][Docs] 节点信息获取成功: name=${name}, category=${category}`);
			return content;
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 读取节点失败: ${err.message}`);
			if (err.response) this.log?.error?.(`[DingTalk][Docs] 错误详情: status=${err.response.status} data=${JSON.stringify(err.response.data)}`);
			return null;
		}
	}
	/**
	* 从 block 树中递归提取纯文本内容
	*/
	extractTextFromBlocks(blocks) {
		const result = [];
		for (const block of blocks) {
			if (block.text) result.push(block.text);
			if (block.children && block.children.length > 0) result.push(...this.extractTextFromBlocks(block.children));
		}
		return result;
	}
	/**
	* 向文档追加内容
	*/
	async appendToDoc(docId, content, index = -1) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 向文档追加内容: docId=${docId}, contentLen=${content.length}`);
			const body = {
				blockType: "PARAGRAPH",
				body: { text: content },
				index
			};
			await dingtalkHttp.post(`${DINGTALK_API}/v1.0/doc/documents/${docId}/blocks/root/children`, body, {
				headers,
				timeout: 1e4
			});
			this.log?.info?.(`[DingTalk][Docs] 内容追加成功`);
			return true;
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 追加内容失败: ${err.message}`);
			if (err.response) this.log?.error?.(`[DingTalk][Docs] 错误详情: status=${err.response.status} data=${JSON.stringify(err.response.data)}`);
			return false;
		}
	}
	/**
	* 创建新文档
	*/
	async createDoc(spaceId, title, content) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 创建文档: spaceId=${spaceId}, title=${title}`);
			const body = {
				spaceId,
				parentDentryId: "",
				name: title,
				docType: "alidoc"
			};
			const data = (await dingtalkHttp.post(`${DINGTALK_API}/v1.0/doc/spaces/${spaceId}/docs`, body, {
				headers,
				timeout: 1e4
			})).data;
			this.log?.info?.(`[DingTalk][Docs] 文档创建成功: docId=${data?.docId}`);
			const docInfo = {
				docId: data.docId || data.dentryUuid || "",
				title,
				docType: data.docType || "alidoc"
			};
			if (content && docInfo.docId) await this.appendToDoc(docInfo.docId, content);
			return docInfo;
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 创建文档失败: ${err.message}`);
			if (err.response) this.log?.error?.(`[DingTalk][Docs] 错误详情: status=${err.response.status} data=${JSON.stringify(err.response.data)}`);
			return null;
		}
	}
	/**
	* 搜索文档
	*/
	async searchDocs(keyword, spaceId) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 搜索文档: keyword=${keyword}, spaceId=${spaceId || "全部"}`);
			const body = {
				keyword,
				maxResults: 20
			};
			if (spaceId) body.spaceId = spaceId;
			const docs = ((await dingtalkHttp.post(`https://api.dingtalk.com/v1.0/doc/docs/search`, body, {
				headers,
				timeout: 1e4
			})).data?.items || []).map((item) => ({
				docId: item.docId || item.dentryUuid || "",
				title: item.name || item.title || "",
				docType: item.docType || "unknown",
				creatorId: item.creatorId,
				updatedAt: item.updatedAt
			}));
			this.log?.info?.(`[DingTalk][Docs] 搜索到 ${docs.length} 个文档`);
			return docs;
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 搜索文档失败: ${err.message}`);
			return [];
		}
	}
	/**
	* 列出空间下的文档
	*/
	async listDocs(spaceId, parentId) {
		try {
			const headers = await this.getHeaders();
			this.log?.info?.(`[DingTalk][Docs] 列出文档: spaceId=${spaceId}, parentId=${parentId || "根目录"}`);
			const params = { maxResults: 50 };
			if (parentId) params.parentDentryId = parentId;
			const docs = ((await dingtalkHttp.get(`https://api.dingtalk.com/v1.0/doc/spaces/${spaceId}/dentries`, {
				headers,
				params,
				timeout: 1e4
			})).data?.items || []).map((item) => ({
				docId: item.dentryUuid || item.docId || "",
				title: item.name || "",
				docType: item.docType || item.dentryType || "unknown",
				creatorId: item.creatorId,
				updatedAt: item.updatedAt
			}));
			this.log?.info?.(`[DingTalk][Docs] 列出 ${docs.length} 个文档/目录`);
			return docs;
		} catch (err) {
			this.log?.error?.(`[DingTalk][Docs] 列出文档失败: ${err.message}`);
			return [];
		}
	}
};
//#endregion
//#region src/gateway-methods.ts
/**
* Warn when accountId is not explicitly provided and multiple accounts exist.
* Returns the resolved account (unchanged), but emits a log warning so that
* callers (typically AI agents) learn to pass accountId explicitly.
*/
function warnIfAccountIdMissing(cfg, accountId, method, log) {
	if (accountId) return;
	const allIds = listDingtalkAccountIds(cfg);
	if (allIds.length > 1) log?.warn?.(`[Gateway][${method}] accountId not specified but ${allIds.length} accounts configured (${allIds.join(", ")}). Falling back to default account. To use the correct bot, pass accountId explicitly.`);
}
/**
* 注册所有 Gateway Methods
*/
function registerGatewayMethods(api) {
	const log = api.logger;
	/**
	* 主动发送单聊消息
	* 
	* @example
	* ```typescript
	* await gateway.call('dingtalk-connector.sendToUser', {
	*   userId: 'user123',
	*   content: '任务已完成！',
	*   useAICard: true
	* });
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.sendToUser", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { userId, userIds, content, msgType, title, useAICard, fallbackToNormal, accountId, atDingtalkIds, atUserIds, atAccountIds, atAll } = params || {};
			warnIfAccountIdMissing(cfg, accountId, "sendToUser", log);
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			const targetUserIds = userIds || (userId ? [userId] : []);
			if (targetUserIds.length === 0) return respond(false, { error: "userId or userIds is required" });
			if (!content) return respond(false, { error: "content is required" });
			const target = targetUserIds.length === 1 ? { userId: targetUserIds[0] } : { userIds: targetUserIds };
			const prepared = prepareMultiBotMentions({
				cfg,
				content: String(content),
				atAccountIds,
				atDingtalkIds
			});
			if (prepared.missingAccountIds.length > 0) log?.warn?.(`[Gateway][sendToUser] atAccountIds 未配置 chatbotUserId，已跳过: ${prepared.missingAccountIds.join(", ")}`);
			const result = await sendProactive(account.config, target, prepared.content, {
				msgType,
				title,
				log,
				useAICard: useAICard !== false,
				fallbackToNormal: fallbackToNormal !== false,
				atDingtalkIds: prepared.atDingtalkIds,
				atUserIds,
				atAll
			});
			respond(result.ok, {
				...result,
				usedAccountId: account.accountId,
				resolvedAtDingtalkIds: prepared.atDingtalkIds,
				missingAtAccountIds: prepared.missingAccountIds
			});
		} catch (err) {
			log?.error?.(`[Gateway][sendToUser] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 主动发送群聊消息
	* 
	* @example
	* ```typescript
	* await gateway.call('dingtalk-connector.sendToGroup', {
	*   openConversationId: 'cid123',
	*   content: '构建失败，请检查日志',
	*   useAICard: true
	* });
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.sendToGroup", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { openConversationId, content, msgType, title, useAICard, fallbackToNormal, accountId, atDingtalkIds, atUserIds, atAccountIds, atAll } = params || {};
			warnIfAccountIdMissing(cfg, accountId, "sendToGroup", log);
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!openConversationId) return respond(false, { error: "openConversationId is required" });
			if (!content) return respond(false, { error: "content is required" });
			const prepared = prepareMultiBotMentions({
				cfg,
				content: String(content),
				atAccountIds,
				atDingtalkIds
			});
			if (prepared.missingAccountIds.length > 0) log?.warn?.(`[Gateway][sendToGroup] atAccountIds 未配置 chatbotUserId，已跳过: ${prepared.missingAccountIds.join(", ")}。请让该 bot 先收一条消息，抓 [BotIdentity] 日志后回填 accounts.<id>.chatbotUserId`);
			const result = await sendProactive(account.config, { openConversationId }, prepared.content, {
				msgType,
				title,
				log,
				useAICard: useAICard !== false,
				fallbackToNormal: fallbackToNormal !== false,
				atDingtalkIds: prepared.atDingtalkIds,
				atUserIds,
				atAll
			});
			respond(result.ok, {
				...result,
				usedAccountId: account.accountId,
				resolvedAtDingtalkIds: prepared.atDingtalkIds,
				missingAtAccountIds: prepared.missingAccountIds
			});
		} catch (err) {
			log?.error?.(`[Gateway][sendToGroup] 错误: ${err.message}`);
			console.error(err);
			respond(false, { error: err.message });
		}
	});
	api.registerGatewayMethod("dingtalk-connector.send", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { target, content, message, msgType, title, useAICard, fallbackToNormal, accountId, atDingtalkIds, atUserIds, atAccountIds, atAll } = params || {};
			const actualContent = content || message;
			warnIfAccountIdMissing(cfg, accountId, "send", log);
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			log?.info?.(`[Gateway][send] 收到请求: target=${target}, contentLen=${typeof actualContent === "string" ? actualContent.length : 0}, accountId=${account.accountId}`);
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!target) return respond(false, { error: "target is required (format: user:<userId> or group:<openConversationId>)" });
			if (!actualContent) return respond(false, { error: "content is required" });
			const targetStr = String(target);
			let sendTarget;
			if (targetStr.startsWith("user:")) sendTarget = { userId: targetStr.slice(5) };
			else if (targetStr.startsWith("group:")) sendTarget = { openConversationId: targetStr.slice(6) };
			else sendTarget = { userId: targetStr };
			const prepared = prepareMultiBotMentions({
				cfg,
				content: String(actualContent),
				atAccountIds,
				atDingtalkIds
			});
			if (prepared.missingAccountIds.length > 0) log?.warn?.(`[Gateway][send] atAccountIds 未配置 chatbotUserId，已跳过: ${prepared.missingAccountIds.join(", ")}`);
			const result = await sendProactive(account.config, sendTarget, prepared.content, {
				msgType,
				title,
				log,
				useAICard: useAICard !== false,
				fallbackToNormal: fallbackToNormal !== false,
				atDingtalkIds: prepared.atDingtalkIds,
				atUserIds,
				atAll
			});
			respond(result.ok, {
				...result,
				usedAccountId: account.accountId,
				resolvedAtDingtalkIds: prepared.atDingtalkIds,
				missingAtAccountIds: prepared.missingAccountIds
			});
		} catch (err) {
			log?.error?.(`[Gateway][send] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	api.registerGatewayMethod("dingtalk-connector.docs.read", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { docId, operatorId: rawOperatorId, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!docId) return respond(false, { error: "docId is required" });
			if (!rawOperatorId) return respond(false, { error: "operatorId (unionId or staffId) is required" });
			let operatorId = rawOperatorId;
			if (!rawOperatorId.includes("$")) {
				const resolved = await getUnionId(rawOperatorId, account.config, log);
				if (resolved) operatorId = resolved;
			}
			const content = await new DingtalkDocsClient(account.config, log).readDoc(docId, operatorId);
			if (content !== null) respond(true, { content });
			else respond(false, { error: "Failed to read document node" });
		} catch (err) {
			log?.error?.(`[Gateway][docs.read] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 创建钉钉文档
	* 
	* @example
	* ```typescript
	* const result = await gateway.call('dingtalk-connector.docs.create', {
	*   spaceId: 'workspace123',
	*   title: '会议纪要',
	*   content: '今天讨论了...'
	* });
	* console.log('文档ID:', result.docId);
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.docs.create", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { spaceId, title, content, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!spaceId || !title) return respond(false, { error: "spaceId and title are required" });
			const doc = await new DingtalkDocsClient(account.config, log).createDoc(spaceId, title, content);
			if (doc) respond(true, doc);
			else respond(false, { error: "Failed to create document" });
		} catch (err) {
			log?.error?.(`[Gateway][docs.create] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 向钉钉文档追加内容
	* 
	* @example
	* ```typescript
	* await gateway.call('dingtalk-connector.docs.append', {
	*   docId: 'doc123',
	*   content: '补充内容...'
	* });
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.docs.append", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { docId, content, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!docId || !content) return respond(false, { error: "docId and content are required" });
			const ok = await new DingtalkDocsClient(account.config, log).appendToDoc(docId, content);
			respond(ok, ok ? { success: true } : { error: "Failed to append to document" });
		} catch (err) {
			log?.error?.(`[Gateway][docs.append] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 搜索钉钉文档
	* 
	* @example
	* ```typescript
	* const result = await gateway.call('dingtalk-connector.docs.search', {
	*   keyword: '项目规范',
	*   spaceId: 'workspace123'  // 可选
	* });
	* console.log('找到文档:', result.docs);
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.docs.search", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { keyword, spaceId, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!keyword) return respond(false, { error: "keyword is required" });
			respond(true, { docs: await new DingtalkDocsClient(account.config, log).searchDocs(keyword, spaceId) });
		} catch (err) {
			log?.error?.(`[Gateway][docs.search] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 列出空间下的文档
	* 
	* @example
	* ```typescript
	* const result = await gateway.call('dingtalk-connector.docs.list', {
	*   spaceId: 'workspace123',
	*   parentId: 'folder456'  // 可选，不传则列出根目录
	* });
	* console.log('文档列表:', result.docs);
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.docs.list", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { spaceId, parentId, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!spaceId) return respond(false, { error: "spaceId is required" });
			respond(true, { docs: await new DingtalkDocsClient(account.config, log).listDocs(spaceId, parentId) });
		} catch (err) {
			log?.error?.(`[Gateway][docs.list] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	api.registerGatewayMethod("dingtalk-connector.status", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const accountId = params?.accountId;
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			const hasClientId = !!account.config?.clientId;
			const hasClientSecret = !!account.config?.clientSecret;
			respond(true, {
				configured: hasClientId && hasClientSecret,
				enabled: account.enabled,
				accountId: account.accountId,
				clientId: hasClientId ? String(account.config.clientId).substring(0, 8) + "..." : void 0
			});
		} catch (err) {
			log?.error?.(`[Gateway][status] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 修复卡住的 AI Card 和/或残留的🤔表情标签
	*
	* 使用场景：Gateway 重启导致流式响应中断，AI Card 停留在"思考中"状态，
	* 或用户消息上的🤔表情标签未被自动撤回。
	*
	* @example 修复卡住的 AI Card
	* ```typescript
	* await gateway.call('dingtalk-connector.fixStuckCards', {
	*   cardInstanceId: 'card_1713600000000_abc12345',
	*   content: '（回复中断，请重新提问）'
	* });
	* ```
	*
	* @example 撤回残留的🤔表情
	* ```typescript
	* await gateway.call('dingtalk-connector.fixStuckCards', {
	*   msgId: 'msgXXX',
	*   conversationId: 'cidXXX'
	* });
	* ```
	*
	* @example 同时修复两者
	* ```typescript
	* await gateway.call('dingtalk-connector.fixStuckCards', {
	*   cardInstanceId: 'card_1713600000000_abc12345',
	*   msgId: 'msgXXX',
	*   conversationId: 'cidXXX'
	* });
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.fixStuckCards", async ({ context, params, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const { cardInstanceId, content, msgId, conversationId, accountId } = params || {};
			const account = resolveDingtalkAccount({
				cfg,
				accountId
			});
			if (!account.config?.clientId) return respond(false, { error: "DingTalk not configured" });
			if (!cardInstanceId && !msgId) return respond(false, {
				error: "At least one of cardInstanceId or msgId is required",
				usage: {
					cardInstanceId: "(optional) AI Card outTrackId, found in logs like \"outTrackId=card_...\"",
					content: "(optional) Final card content, defaults to \"（回复中断，请重新提问）\"",
					msgId: "(optional) Message ID for emotion recall, found in logs like \"msgId=...\"",
					conversationId: "(optional) Required together with msgId for emotion recall"
				}
			});
			const results = {};
			if (cardInstanceId) try {
				const { getAccessToken } = await import("./utils-legacy-CFYDBM4r.mjs");
				const token = await getAccessToken(account.config);
				await finishAICard({
					cardInstanceId: String(cardInstanceId),
					accessToken: token,
					tokenExpireTime: Date.now() + 7200 * 1e3,
					inputingStarted: true
				}, String(content || "（回复中断，请重新提问）"), account.config, log);
				results.card = { ok: true };
				log?.info?.(`[Gateway][fixStuckCards] AI Card 修复成功: ${cardInstanceId}`);
			} catch (err) {
				results.card = {
					ok: false,
					error: err.message
				};
				log?.error?.(`[Gateway][fixStuckCards] AI Card 修复失败: ${err.message}`);
			}
			if (msgId && conversationId) try {
				await recallEmotionReply(account.config, {
					msgId,
					conversationId,
					robotCode: account.config.clientId
				}, log);
				results.emotion = { ok: true };
				log?.info?.(`[Gateway][fixStuckCards] 表情撤回成功: msgId=${msgId}`);
			} catch (err) {
				results.emotion = {
					ok: false,
					error: err.message
				};
				log?.error?.(`[Gateway][fixStuckCards] 表情撤回失败: ${err.message}`);
			}
			else if (msgId && !conversationId) results.emotion = {
				ok: false,
				error: "conversationId is required together with msgId"
			};
			respond(Object.values(results).every((r) => r.ok), results);
		} catch (err) {
			log?.error?.(`[Gateway][fixStuckCards] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 列出所有已配置的钉钉机器人账号（含元数据），供多 Agent 协作时查询"队友机器人"使用。
	*
	* 返回字段：
	* - accountId: 在 openclaw.json 里 accounts 配置的 key（用于 sendToGroup 的 accountId 参数）
	* - name: 友好显示名（accounts.<id>.name）
	* - chatbotUserId: 该机器人加密 ID（如配置在 accounts.<id>.chatbotUserId 里），可用于 atDingtalkIds
	* - clientId: AppKey（脱敏前 8 位）
	*
	* @example
	* ```typescript
	* const r = await gateway.call('dingtalk-connector.listAccounts');
	* // -> [{ accountId: 'main-bot', name: '主助手机器人', chatbotUserId: '$:LWCP_v1:xxx', ... }, ...]
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.listAccounts", async ({ context, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const root = cfg.channels?.["dingtalk-connector"];
			const accountsMap = root?.accounts || {};
			const mentionTable = buildBotMentionTable(cfg);
			const mentionByAccountId = new Map(mentionTable.map((e) => [e.accountId, e]));
			respond(true, { accounts: Object.keys(accountsMap).map((id) => {
				const a = accountsMap[id] || {};
				const cid = String(a.clientId ?? root?.clientId ?? "");
				const mention = mentionByAccountId.get(id);
				return {
					accountId: id,
					name: a.name || id,
					enabled: a.enabled !== false,
					chatbotUserId: a.chatbotUserId || void 0,
					chatbotCorpId: a.chatbotCorpId || void 0,
					clientId: cid ? cid.substring(0, 8) + "..." : void 0,
					agentIds: mention?.agentIds || [],
					aliases: mention?.aliases || [],
					mentionReady: !!a.chatbotUserId
				};
			}) });
		} catch (err) {
			log?.error?.(`[Gateway][listAccounts] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	/**
	* 多 bot 协作自检：检查每个 account 是否具备在群里互 @ 的能力。
	*
	* 一个 bot 能被其它 bot @ 的前提：
	*   1. `accounts.<id>.chatbotUserId` / `chatbotCorpId` 已填（从 `[BotIdentity]` 日志抓回来）
	*   2. bot 当前 enabled 且配了 clientId / clientSecret
	*
	* 返回的报告可以直接贴给用户，告诉他下一步该干什么
	* （比如"给 dev-bot 发一条消息后回填 chatbotUserId"）。
	*
	* @example
	* ```typescript
	* const r = await gateway.call('dingtalk-connector.bootstrapBotIdentity');
	* // -> {
	* //   ready: false,
	* //   totalAccounts: 2,
	* //   readyAccounts: 1,
	* //   missingChatbotUserId: ['dev-bot'],
	* //   report: '...'
	* // }
	* ```
	*/
	api.registerGatewayMethod("dingtalk-connector.bootstrapBotIdentity", async ({ context, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const accountsMap = (cfg.channels?.["dingtalk-connector"])?.accounts || {};
			const ids = Object.keys(accountsMap);
			const missingChatbotUserId = [];
			const missingCredentials = [];
			const disabled = [];
			const ready = [];
			for (const id of ids) {
				const a = accountsMap[id] || {};
				if (a.enabled === false) {
					disabled.push(id);
					continue;
				}
				const hasCreds = !!(a.clientId && a.clientSecret);
				if (!hasCreds) missingCredentials.push(id);
				if (!a.chatbotUserId) missingChatbotUserId.push(id);
				else if (hasCreds) ready.push({
					accountId: id,
					name: a.name,
					chatbotUserId: a.chatbotUserId
				});
			}
			const reportLines = [];
			reportLines.push(`[BotIdentity] 已配置 ${ids.length} 个账号，其中 ${ready.length} 个可参与多 bot 互相 @`);
			if (ready.length > 0) reportLines.push("[OK] Ready: " + ready.map((r) => `${r.accountId}(${r.name || ""})`).join(", "));
			if (missingChatbotUserId.length > 0) reportLines.push(`[WARN] 缺少 chatbotUserId: ${missingChatbotUserId.join(", ")} — 请让这些 bot 在钉钉里各收一条消息，然后在终端 grep "[BotIdentity]" 抓到加密 ID 后回填到 openclaw.json 对应 account`);
			if (missingCredentials.length > 0) reportLines.push(`[ERR] 缺少 clientId/clientSecret: ${missingCredentials.join(", ")}`);
			if (disabled.length > 0) reportLines.push(`[PAUSED] 已禁用: ${disabled.join(", ")}`);
			respond(true, {
				ready: missingChatbotUserId.length === 0 && missingCredentials.length === 0 && ready.length > 0,
				totalAccounts: ids.length,
				readyAccounts: ready.length,
				readyList: ready,
				missingChatbotUserId,
				missingCredentials,
				disabled,
				report: reportLines.join("\n")
			});
		} catch (err) {
			log?.error?.(`[Gateway][bootstrapBotIdentity] 错误: ${err.message}`);
			respond(false, { error: err.message });
		}
	});
	api.registerGatewayMethod("dingtalk-connector.probe", async ({ context, respond }) => {
		const { loadConfig } = await import("openclaw/plugin-sdk/config-runtime");
		const cfg = loadConfig();
		try {
			const account = resolveDingtalkAccount({ cfg });
			if (!account.config?.clientId || !account.config?.clientSecret) return respond(false, { error: "Not configured" });
			const { getAccessToken } = await import("./utils-legacy-CFYDBM4r.mjs");
			await getAccessToken(account.config);
			respond(true, {
				ok: true,
				details: { clientId: account.config.clientId }
			});
		} catch (err) {
			log?.error?.(`[Gateway][probe] 错误: ${err.message}`);
			respond(false, {
				ok: false,
				error: err.message
			});
		}
	});
}
//#endregion
export { registerGatewayMethods as t };
