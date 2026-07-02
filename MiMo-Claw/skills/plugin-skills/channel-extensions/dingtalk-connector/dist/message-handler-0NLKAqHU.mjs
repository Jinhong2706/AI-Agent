import { u as uploadMediaToDingTalk } from "./media-BViJQGgb.mjs";
import { a as resolveDingtalkAccount } from "./accounts-CF4oK_HZ.mjs";
import { r as CHANNEL_ID, t as getDingtalkRuntime } from "./runtime-BCFW2-1B.mjs";
import { n as createLoggerFromConfig } from "./logger-BDWwViGT.mjs";
import { t as dingtalkHttp } from "./http-client-DFWZgO1n.mjs";
import { n as groupChatLacksVisibleRepliesAutomatic, r as pickEmptyReplyFallbackText, s as getOapiAccessToken, t as emptyGroupReplyLogHint } from "./utils-DgNm1Ek_.mjs";
import { a as sendTextMessage, d as isQpsLimitError, f as streamAICard, i as sendProactive, l as createAICardForTarget, r as sendMessage, t as sendMarkdownMessage, u as finishAICard } from "./messaging-C2zJ8O-o.mjs";
import { a as QUEUE_BUSY_ACK_PHRASES, n as normalizeSlashCommand, t as buildSessionContext } from "./session-DJ4jYqPv.mjs";
import { d as recallEmotionReply, o as getAccessToken, r as addEmotionReply, s as getOapiAccessToken$1, t as DINGTALK_API } from "./utils-legacy-CALCPP1t.mjs";
import "./chunk-upload-6p9cf3UB.mjs";
import { a as VIDEO_MARKER_PATTERN, i as LOCAL_IMAGE_RE, o as toLocalPath, r as FILE_MARKER_PATTERN, s as uploadMediaToDingTalk$1, t as AUDIO_MARKER_PATTERN } from "./common-BGJlWkEp.mjs";
import * as fs from "fs";
import * as path from "path";
import * as os from "node:os";
import * as path$1 from "node:path";
//#region src/utils/agent.ts
/**
* Agent 相关工具函数
* 
* 提供 Agent 配置解析、工作空间路径解析等功能
*/
/**
* 解析 Agent 工作空间路径
* 
* 参考 OpenClaw SDK 的 resolveAgentWorkspaceDir 实现逻辑：
* 1. 优先从 agents.list 中查找用户配置的 workspace
* 2. 如果没有配置，使用默认路径规则：
*    - 默认 Agent (main): ~/.openclaw/workspace
*    - 其他 Agent: ~/.openclaw/workspace-{agentId}
* 
* @param cfg - OpenClaw 配置对象
* @param agentId - Agent ID
* @returns Agent 工作空间的绝对路径
* 
* @example
* ```typescript
* // 用户自定义工作空间
* const cfg = {
*   agents: {
*     list: [{ id: 'bot1', workspace: '~/my-workspace' }]
*   }
* };
* resolveAgentWorkspaceDir(cfg, 'bot1'); // => '/Users/xxx/my-workspace'
* 
* // 默认 Agent
* resolveAgentWorkspaceDir(cfg, 'main'); // => '/Users/xxx/.openclaw/workspace'
* 
* // 其他 Agent
* resolveAgentWorkspaceDir(cfg, 'bot2'); // => '/Users/xxx/.openclaw/workspace-bot2'
* ```
*/
function resolveAgentWorkspaceDir(cfg, agentId) {
	const agentConfig = cfg.agents?.list?.find((a) => a.id === agentId);
	if (agentConfig?.workspace) return agentConfig.workspace.startsWith("~") ? path$1.join(os.homedir(), agentConfig.workspace.slice(1)) : agentConfig.workspace;
	if (agentId === "main" || agentId === cfg.defaultAgent) return path$1.join(os.homedir(), ".openclaw", "workspace");
	return path$1.join(os.homedir(), ".openclaw", `workspace-${agentId}`);
}
//#endregion
//#region src/services/media/image.ts
/**
* 扫描内容中的本地图片路径，上传到钉钉并替换为标准 Markdown 图片语法
*
* 上传本地文件到钉钉媒体服务，获取 mediaId 后，
* 使用 ![文案](mediaId) 格式替换原始本地路径。
*/
async function processLocalImages(content, oapiToken, log) {
	if (!oapiToken) {
		log?.warn?.(`[DingTalk][Media] 无 oapiToken，跳过图片后处理`);
		return content;
	}
	let result = content;
	const mdMatches = [...content.matchAll(LOCAL_IMAGE_RE)];
	if (mdMatches.length > 0) {
		log?.info?.(`[DingTalk][Media] 检测到 ${mdMatches.length} 个 markdown 图片，开始上传...`);
		for (const match of mdMatches) {
			const [fullMatch, alt, rawPath] = match;
			const { mediaId } = await uploadMediaToDingTalk(rawPath.replace(/\\ /g, " "), "image", oapiToken, 20 * 1024 * 1024, log);
			if (mediaId) {
				const replacement = `![${alt}](${mediaId})`;
				result = result.replace(fullMatch, replacement);
				log?.info?.(`[DingTalk][Media] 图片已替换为 Markdown 格式: ${replacement}`);
			}
		}
	}
	return result;
}
//#endregion
//#region src/services/media/video.ts
/**
* 提取视频标记并发送视频消息
*/
async function processVideoMarkers(content, sessionWebhook, config, oapiToken, log, useProactiveApi = false, target) {
	const logPrefix = useProactiveApi ? "[DingTalk][Video][Proactive]" : "[DingTalk][Video]";
	if (!oapiToken) {
		log?.warn?.(`${logPrefix} 无 oapiToken，跳过视频处理`);
		return content;
	}
	const matches = [...content.matchAll(VIDEO_MARKER_PATTERN)];
	if (matches.length === 0) {
		log?.info?.(`${logPrefix} 未检测到视频标记，跳过处理`);
		return content;
	}
	const videoInfos = [];
	const invalidVideos = [];
	for (const match of matches) try {
		const rawPath = JSON.parse(match[1]).path;
		const absPath = toLocalPath(rawPath);
		videoInfos.push({ path: absPath });
	} catch (err) {
		log?.warn?.(`${logPrefix} 解析视频标记失败：${match[1]}`);
		invalidVideos.push(match[1]);
	}
	if (videoInfos.length === 0) {
		if (invalidVideos.length > 0) {
			log?.warn?.(`${logPrefix} 检测到无效视频标记，已忽略并移除`);
			return content.replaceAll(VIDEO_MARKER_PATTERN, "").trim();
		}
		return content;
	}
	log?.info?.(`${logPrefix} 检测到 ${videoInfos.length} 个视频，开始上传...`);
	let result = content;
	for (const match of matches) {
		const full = match[0];
		try {
			const absPath = toLocalPath(JSON.parse(match[1]).path);
			if (!fs.existsSync(absPath)) {
				log?.warn?.(`${logPrefix} 视频文件不存在：${absPath}`);
				result = result.replace(full, "⚠️ 视频文件不存在");
				continue;
			}
			const mediaId = await uploadMediaToDingTalk$1(absPath, "video", oapiToken, 20 * 1024 * 1024, log);
			result = result.replace(full, mediaId ? `[视频已上传：${mediaId}]` : "⚠️ 视频上传失败");
		} catch {
			log?.warn?.(`${logPrefix} 解析视频标记失败：${match[1]}`);
			result = result.replace(full, "");
		}
	}
	return result;
}
//#endregion
//#region src/services/media/audio.ts
/**
* 提取音频标记并发送音频消息
*/
async function processAudioMarkers(content, sessionWebhook, config, oapiToken, log, useProactiveApi = false, target) {
	const logPrefix = useProactiveApi ? "[DingTalk][Audio][Proactive]" : "[DingTalk][Audio]";
	if (!oapiToken) {
		log?.warn?.(`${logPrefix} 无 oapiToken，跳过音频处理`);
		return content;
	}
	const matches = [...content.matchAll(AUDIO_MARKER_PATTERN)];
	if (matches.length === 0) return content;
	log?.info?.(`${logPrefix} 检测到 ${matches.length} 个音频，开始上传...`);
	let result = content;
	for (const match of matches) {
		const full = match[0];
		try {
			const absPath = toLocalPath(JSON.parse(match[1]).path);
			if (!fs.existsSync(absPath)) {
				log?.warn?.(`${logPrefix} 音频文件不存在：${absPath}`);
				result = result.replace(full, "⚠️ 音频文件不存在");
				continue;
			}
			const uploadResult = await uploadMediaToDingTalk$1(absPath, "voice", oapiToken, 20 * 1024 * 1024, log);
			result = result.replace(full, uploadResult ? `[音频已上传：${uploadResult}]` : "⚠️ 音频上传失败");
		} catch {
			log?.warn?.(`${logPrefix} 解析音频标记失败：${match[1]}`);
			result = result.replace(full, "");
		}
	}
	return result.trim();
}
//#endregion
//#region src/services/media/file.ts
/**
* 提取文件标记，上传文件到钉钉，并用文本替换标记。
* 
* 注意：此函数只做「上传 + 文本替换」，不会发送独立的文件消息。
* 如果需要上传后再发送独立文件消息，请使用 media.ts 中的 processFileMarkers。
* 
* 调用方：reply-dispatcher.ts、message-handler.ts（通过 media/index.ts 导入）
*/
async function uploadAndReplaceFileMarkers(content, sessionWebhook, config, oapiToken, log, useProactiveApi = false, target) {
	const logPrefix = useProactiveApi ? "[DingTalk][File][Proactive]" : "[DingTalk][File]";
	if (!oapiToken) {
		log?.warn?.(`${logPrefix} 无 oapiToken，跳过文件处理`);
		return content;
	}
	const matches = [...content.matchAll(FILE_MARKER_PATTERN)];
	if (matches.length === 0) return content;
	log?.info?.(`${logPrefix} 检测到 ${matches.length} 个文件，开始上传...`);
	let result = content;
	for (const match of matches) {
		const full = match[0];
		try {
			const uploadResult = await uploadMediaToDingTalk$1(toLocalPath(JSON.parse(match[1]).path), "file", oapiToken, 20 * 1024 * 1024, log);
			result = result.replace(full, uploadResult ? `[文件已上传：${uploadResult}]` : "⚠️ 文件上传失败");
		} catch {
			log?.warn?.(`${logPrefix} 解析文件标记失败：${match[1]}`);
			result = result.replace(full, "");
		}
	}
	return result;
}
//#endregion
//#region src/reply-dispatcher.ts
const { createReplyPrefixOptions, createTypingCallbacks, logTypingFailure } = await import("openclaw/plugin-sdk/channel-runtime");
function createDingtalkReplyDispatcher(params) {
	const core = getDingtalkRuntime();
	const { cfg, agentId, conversationId, senderId, isDirect, accountId, sessionWebhook, asyncMode = false, preCreatedCard } = params;
	const account = resolveDingtalkAccount({
		cfg,
		accountId
	});
	const { onModelSelected, ...prefixOptions } = createReplyPrefixOptions({
		cfg,
		agentId,
		channel: CHANNEL_ID,
		accountId
	});
	const log = createLoggerFromConfig(account.config, `DingTalk:${accountId}`);
	let currentCardTarget = null;
	let accumulatedText = "";
	const deliveredFinalTexts = /* @__PURE__ */ new Set();
	/** 本轮是否已向用户发出过可见回复（final / 流式更新 / 错误兜底等） */
	let outboundUserVisibleThisTurn = false;
	/** 防止 onIdle / onError 重复发送 visibleReplies 配置指引 */
	let idleConfigNudgeSent = false;
	let asyncModeFullResponse = "";
	const detectedDwsProducts = /* @__PURE__ */ new Set();
	const DWS_PRODUCT_PATTERN = /\bdws\s+(aitable|calendar|chat|contact|todo|approval|attendance|report|ding|workbench|devdoc)\b/;
	let lastUpdateTime = 0;
	const updateInterval = 800;
	const deliveredErrorTypes = /* @__PURE__ */ new Set();
	let lastErrorTime = 0;
	const ERROR_COOLDOWN = 6e4;
	/**
	* 发送兜底错误消息，确保用户始终能收到反馈
	*/
	const sendFallbackErrorMessage = async (errorType, originalError, forceSend = false) => {
		const now = Date.now();
		const errorKey = `${errorType}:${conversationId}:${senderId}`;
		if (!forceSend && deliveredErrorTypes.has(errorKey)) {
			log.debug(`[DingTalk][Fallback] 跳过重复错误消息：${errorType}`);
			return;
		}
		if (!forceSend && now - lastErrorTime < ERROR_COOLDOWN) {
			log.debug(`[DingTalk][Fallback] 冷却时间内，跳过错误消息`);
			return;
		}
		const errorMessage = {
			mediaProcess: "⚠️ 媒体文件处理失败，已发送文字回复",
			sendMessage: "⚠️ 消息发送失败，请稍后重试",
			unknown: "⚠️ 抱歉，处理您的请求时出错，请稍后重试"
		}[errorType];
		log.warn(`[DingTalk][Fallback] ${errorMessage}, error: ${originalError}`);
		try {
			await sendMessage(account.config, sessionWebhook, errorMessage, {
				useMarkdown: false,
				log: params.runtime.log
			});
			deliveredErrorTypes.add(errorKey);
			lastErrorTime = now;
			outboundUserVisibleThisTurn = true;
			log.info(`[DingTalk][Fallback] ✅ 错误消息发送成功`);
		} catch (fallbackErr) {
			log.error(`[DingTalk][Fallback] ❌ 错误消息发送失败：${fallbackErr.message}`);
		}
	};
	const typingCallbacks = createTypingCallbacks({
		start: async () => {},
		stop: async () => {},
		onStartError: (err) => logTypingFailure({
			log: (message) => params.runtime.log?.(message),
			channel: CHANNEL_ID,
			action: "start",
			error: err
		}),
		onStopError: (err) => logTypingFailure({
			log: (message) => params.runtime.log?.(message),
			channel: CHANNEL_ID,
			action: "stop",
			error: err
		})
	});
	const textChunkLimit = core.channel.text.resolveTextChunkLimit(cfg, CHANNEL_ID, accountId, { fallbackLimit: 4e3 });
	const chunkMode = core.channel.text.resolveChunkMode(cfg, CHANNEL_ID);
	const groupReplyMode = account.config?.groupReplyMode || "aicard";
	const isTextMode = !isDirect && (groupReplyMode === "text" || groupReplyMode === "markdown");
	if (isTextMode) log.info(`[DingTalk] 群聊回复模式: ${groupReplyMode}，禁用 AI Card，使用 ${groupReplyMode} 发送`);
	const streamingEnabled = !isTextMode && account.config?.streaming !== false;
	let cardCreationPromise = null;
	const startStreaming = () => {
		if (cardCreationPromise) return cardCreationPromise;
		if (currentCardTarget) return Promise.resolve();
		cardCreationPromise = (async () => {
			if (asyncMode) {
				log.info(`[DingTalk][startStreaming] 异步模式，跳过 AI Card 创建`);
				return;
			}
			if (!streamingEnabled) {
				log.info(`[DingTalk][startStreaming] 流式功能被禁用，跳过 AI Card 创建`);
				return;
			}
			if (preCreatedCard) {
				log.info(`[DingTalk][startStreaming] 复用预创建 AI Card，cardInstanceId=${preCreatedCard.cardInstanceId}`);
				currentCardTarget = preCreatedCard;
				accumulatedText = "";
				outboundUserVisibleThisTurn = true;
				return;
			}
			log.info(`[DingTalk][startStreaming] 开始创建 AI Card...`);
			try {
				const target = isDirect ? {
					type: "user",
					userId: senderId
				} : {
					type: "group",
					openConversationId: conversationId
				};
				log.info(`[DingTalk][startStreaming] 目标：${JSON.stringify(target)}`);
				const card = await createAICardForTarget(account.config, target, log);
				currentCardTarget = card;
				accumulatedText = "";
				if (card) log.info(`[DingTalk][startStreaming] ✅ AI Card 创建成功`);
				else log.warn(`[DingTalk][startStreaming] AI Card 创建返回 null，静默降级到普通消息模式`);
			} catch (error) {
				log.error(`[DingTalk][startStreaming] ❌ AI Card 创建失败：${error?.message || String(error)}，静默降级到普通消息模式`);
				currentCardTarget = null;
			} finally {
				cardCreationPromise = null;
			}
		})();
		return cardCreationPromise;
	};
	const closeStreaming = async () => {
		const cardSnapshot = currentCardTarget;
		if (!cardSnapshot) {
			log.info(`[DingTalk][closeStreaming] 无 AI Card，跳过关闭`);
			return;
		}
		currentCardTarget = null;
		log.info(`[DingTalk][closeStreaming] 开始关闭 AI Card...`);
		try {
			let finalText = accumulatedText;
			if (!finalText.trim()) {
				const isGroup = !isDirect;
				finalText = pickEmptyReplyFallbackText(isGroup);
				log.info(`[DingTalk][closeStreaming] 累积文本为空，使用默认提示文案 (isGroup=${isGroup})`);
				if (isGroup) log.warn?.(`[DingTalk][closeStreaming] ${emptyGroupReplyLogHint()}`);
			}
			const oapiToken = await getOapiAccessToken(account.config);
			const target = isDirect ? {
				type: "user",
				userId: senderId
			} : {
				type: "group",
				openConversationId: conversationId
			};
			log.info(`[DingTalk][closeStreaming] 开始处理媒体文件，target=${JSON.stringify(target)}`);
			if (oapiToken) {
				finalText = await processLocalImages(finalText, oapiToken, log);
				finalText = await processVideoMarkers(finalText, "", account.config, oapiToken, log, true, target);
				finalText = await processAudioMarkers(finalText, "", account.config, oapiToken, log, true, target);
				finalText = await uploadAndReplaceFileMarkers(finalText, "", account.config, oapiToken, log, true, target);
				log.info(`[DingTalk][closeStreaming] 准备调用 processRawMediaPaths`);
				const { processRawMediaPaths } = await import("./media-CIO05hZn.mjs");
				finalText = await processRawMediaPaths(finalText, account.config, oapiToken, log, target);
				log.info(`[DingTalk][closeStreaming] processRawMediaPaths 处理完成`);
			} else log.warn(`[DingTalk][closeStreaming] oapiToken 为空，跳过媒体处理`);
			try {
				const productsToProcess = new Set(detectedDwsProducts);
				if (productsToProcess.size === 0) {
					const dwsProductMatch = finalText.match(/(?:^|\n)\s*(?:>?\s*)?(?:`\s*)?dws\s+(aitable|calendar|chat|contact|todo|approval|attendance|report|ding|workbench|devdoc)\b/m);
					if (dwsProductMatch && !finalText.includes("command not found: dws") && !finalText.includes("请先执行 dws login")) {
						productsToProcess.add(dwsProductMatch[1]);
						log.info(`[DingTalk][closeStreaming] 养成系统：正则兜底匹配到产品=${dwsProductMatch[1]}`);
					}
				} else log.info(`[DingTalk][closeStreaming] 养成系统：onCommandOutput 监听到 ${productsToProcess.size} 个 dws 产品: ${[...productsToProcess].join(", ")}`);
				if (productsToProcess.size > 0) {
					const { GamificationEngine } = await import("./game-xiyou-DxRHjOIJ.mjs");
					const engine = GamificationEngine.getInstanceForUser(senderId);
					if (engine.isEnabled()) {
						const primaryProduct = [...productsToProcess][0];
						const allProducts = [...productsToProcess].join("+");
						const gamificationBlock = engine.onDwsCommandResult(primaryProduct, true, `dws ${allProducts}`);
						if (gamificationBlock) {
							finalText += "\n" + gamificationBlock;
							log.info(`[DingTalk][closeStreaming] ✅ 养成系统渲染已追加，主产品=${primaryProduct}，涉及产品=${allProducts}`);
						}
					}
				}
				detectedDwsProducts.clear();
			} catch (gamErr) {
				log.warn(`[DingTalk][closeStreaming] 养成系统处理失败（不影响主流程）: ${gamErr?.message || gamErr}`);
			}
			log.info(`[DingTalk][closeStreaming] 准备调用 finishAICard，文本长度=${finalText.length}`);
			log.debug(`[DingTalk][closeStreaming] 最终发送内容长度=${finalText.length}`);
			await finishAICard(cardSnapshot, finalText, account.config, log);
			outboundUserVisibleThisTurn = true;
			log.info(`[DingTalk][closeStreaming] ✅ AI Card 关闭成功`);
		} catch (error) {
			log.error(`[DingTalk][closeStreaming] ❌ AI Card 关闭失败：${error?.message || String(error)}`);
			await sendFallbackErrorMessage("mediaProcess", error?.message || String(error));
			if (accumulatedText.trim()) try {
				log.info(`[DingTalk][closeStreaming] 降级发送普通消息`);
				await sendMessage(account.config, sessionWebhook, accumulatedText, {
					useMarkdown: true,
					log: params.runtime.log
				});
				outboundUserVisibleThisTurn = true;
				log.info(`[DingTalk][closeStreaming] ✅ 降级发送成功`);
			} catch (sendErr) {
				log.error(`[DingTalk][closeStreaming] ❌ 降级发送失败：${sendErr.message}`);
			}
		} finally {
			accumulatedText = "";
		}
	};
	/**
	* 群聊且 OpenClaw 未配置 `messages.groupChat.visibleReplies=automatic` 时，
	* 若本轮结束时仍没有任何用户可见输出（上游可能未调用空 final 的 deliver），
	* 补发与空 final 一致的配置指引，避免只有「思考中」却无声。
	*/
	const maybeSendGroupVisibleRepliesIdleNudge = async () => {
		if (isDirect) return;
		if (!groupChatLacksVisibleRepliesAutomatic(cfg)) return;
		if (asyncMode) return;
		if (outboundUserVisibleThisTurn) return;
		if (idleConfigNudgeSent) return;
		idleConfigNudgeSent = true;
		log.info(`[DingTalk][idleNudge] 本轮无用户可见回复且群聊未启用 visibleReplies=automatic，发送配置指引`);
		try {
			const text = pickEmptyReplyFallbackText(true);
			log.warn(`[DingTalk][idleNudge] ${emptyGroupReplyLogHint()}`);
			for (const chunk of core.channel.text.chunkTextWithMode(text, textChunkLimit, chunkMode)) if (isTextMode) if (groupReplyMode === "markdown") await sendMarkdownMessage(account.config, sessionWebhook, chunk.split("\n")[0]?.replace(/^[#*\s\->]+/, "").slice(0, 20) || "Message", chunk, {
				cfg,
				detectBareAliases: true
			});
			else await sendTextMessage(account.config, sessionWebhook, chunk, {
				cfg,
				detectBareAliases: true
			});
			else await sendMessage(account.config, sessionWebhook, chunk, {
				useMarkdown: true,
				log: params.runtime.log,
				cfg,
				detectBareAliases: true
			});
			outboundUserVisibleThisTurn = true;
			log.info(`[DingTalk][idleNudge] ✅ 配置指引已发送`);
		} catch (e) {
			log.error(`[DingTalk][idleNudge] 发送失败: ${e?.message || e}`);
		}
	};
	const { dispatcher, replyOptions, markDispatchIdle } = core.channel.reply.createReplyDispatcherWithTyping({
		...prefixOptions,
		humanDelay: core.channel.reply.resolveHumanDelayConfig(cfg, agentId),
		onReplyStart: () => {
			log.info(`[DingTalk][onReplyStart] 开始回复，流式 enabled=${streamingEnabled}`);
			deliveredFinalTexts.clear();
			outboundUserVisibleThisTurn = false;
			idleConfigNudgeSent = false;
			if (streamingEnabled) startStreaming();
			typingCallbacks.onActive?.();
		},
		deliver: async (payload, info) => {
			let text = payload.text ?? "";
			log.info(`[DingTalk][deliver] 被调用：kind=${info?.kind}, textLength=${text.length}, hasText=${Boolean(text.trim())}`);
			log.debug(`[DingTalk][deliver] payload keys=${Object.keys(payload).join(",")}, info.kind=${info?.kind}`);
			if (info?.kind === "final" && text.trim()) {
				const target = isDirect ? {
					type: "user",
					userId: senderId
				} : {
					type: "group",
					openConversationId: conversationId
				};
				try {
					const oapiToken = await getOapiAccessToken(account.config);
					if (oapiToken) {
						log.info(`[DingTalk][deliver] 检测到 final 响应，准备处理裸露文件路径`);
						const { processRawMediaPaths } = await import("./media-CIO05hZn.mjs");
						text = await processRawMediaPaths(text, account.config, oapiToken, log, target);
						log.info(`[DingTalk][deliver] 裸露文件路径处理完成`);
					}
				} catch (err) {
					log.error(`[DingTalk][deliver] 处理裸露文件路径失败：${err.message}`);
				}
			}
			const hasText = Boolean(text.trim());
			const skipTextForDuplicateFinal = info?.kind === "final" && hasText && deliveredFinalTexts.has(text);
			if (info?.kind === "final" && !hasText) {
				const isGroup = !isDirect;
				text = pickEmptyReplyFallbackText(isGroup);
				log.info(`[DingTalk][deliver] final 响应无文本，使用默认提示文案 (isGroup=${isGroup})`);
				if (isGroup) log.warn?.(`[DingTalk][deliver] ${emptyGroupReplyLogHint()}`);
			}
			if (!(Boolean(text.trim()) && !skipTextForDuplicateFinal)) {
				log.info(`[DingTalk][deliver] 跳过发送：hasText=${hasText}, skipTextForDuplicateFinal=${skipTextForDuplicateFinal}`);
				return;
			}
			if (asyncMode) {
				log.info(`[DingTalk][deliver] 异步模式，累积响应`);
				asyncModeFullResponse = text;
				return;
			}
			if (info?.kind === "block") {
				if (!streamingEnabled) {
					log.info(`[DingTalk][deliver] block 消息，流式未启用，丢弃`);
					return;
				}
				log.info(`[DingTalk][deliver] block 消息，追加到流式 AI Card，文本长度=${text.length}`);
				await startStreaming();
				if (currentCardTarget) {
					const now = Date.now();
					if (now - lastUpdateTime >= updateInterval) {
						lastUpdateTime = now;
						try {
							await streamAICard(currentCardTarget, text, false, account.config, log);
							outboundUserVisibleThisTurn = true;
							log.info(`[DingTalk][deliver] ✅ block 更新到 AI Card 成功`);
						} catch (streamErr) {
							log.error(`[DingTalk][deliver] ❌ block 更新 AI Card 失败：${streamErr.message}`);
						}
					}
				} else log.warn(`[DingTalk][deliver] block 消息：AI Card 创建失败，丢弃该 block`);
				return;
			}
			if (info?.kind === "final" && streamingEnabled) {
				log.info(`[DingTalk][deliver] final 响应，流式模式`);
				await startStreaming();
				if (currentCardTarget) {
					accumulatedText = text;
					log.info(`[DingTalk][deliver] 调用 closeStreaming 完成 AI Card`);
					await closeStreaming();
					deliveredFinalTexts.add(text);
					return;
				} else log.warn(`[DingTalk][deliver] ⚠️ AI Card 创建失败，降级到非流式发送`);
			}
			if (info?.kind === "final") {
				log.info(`[DingTalk][deliver] 降级到非流式发送，文本长度=${text.length}, isTextMode=${isTextMode}, groupReplyMode=${groupReplyMode}`);
				try {
					for (const chunk of core.channel.text.chunkTextWithMode(text, textChunkLimit, chunkMode)) if (isTextMode) if (groupReplyMode === "markdown") await sendMarkdownMessage(account.config, sessionWebhook, chunk.split("\n")[0]?.replace(/^[#*\s\->]+/, "").slice(0, 20) || "Message", chunk, {
						cfg,
						detectBareAliases: true
					});
					else await sendTextMessage(account.config, sessionWebhook, chunk, {
						cfg,
						detectBareAliases: true
					});
					else await sendMessage(account.config, sessionWebhook, chunk, {
						useMarkdown: true,
						log: params.runtime.log,
						cfg,
						detectBareAliases: true
					});
					outboundUserVisibleThisTurn = true;
					log.info(`[DingTalk][deliver] ✅ 非流式发送成功`);
					deliveredFinalTexts.add(text);
				} catch (error) {
					log.error(`[DingTalk][deliver] ❌ 非流式发送失败：${error.message}`);
					params.runtime.error?.(`dingtalk[${account.accountId}]: non-streaming delivery failed: ${String(error)}`);
					await sendFallbackErrorMessage("sendMessage", error.message);
				}
				return;
			}
		},
		onError: async (error, info) => {
			log.error(`[DingTalk][onError] ${info.kind} reply failed: ${String(error)}`);
			params.runtime.error?.(`dingtalk[${account.accountId}] ${info.kind} reply failed: ${String(error)}`);
			await closeStreaming();
			typingCallbacks.onIdle?.();
			await maybeSendGroupVisibleRepliesIdleNudge();
		},
		onIdle: async () => {
			log.info(`[DingTalk][onIdle] 回复空闲，关闭 AI Card`);
			typingCallbacks.onIdle?.();
			await closeStreaming();
			await maybeSendGroupVisibleRepliesIdleNudge();
		},
		onCleanup: () => {
			log.info(`[DingTalk][onCleanup] 清理回调`);
			typingCallbacks.onCleanup?.();
		}
	});
	return {
		dispatcher,
		replyOptions: {
			...replyOptions,
			onModelSelected,
			...streamingEnabled && { onPartialReply: async (payload) => {
				log.info(`[DingTalk][onPartialReply] 被调用，payload.text=${payload.text ? payload.text.length : "null"}`);
				log.debug(`[DingTalk][onPartialReply] textLength=${payload.text?.length ?? 0}`);
				if (!payload.text) {
					log.debug(`[DingTalk][onPartialReply] 空文本，跳过`);
					return;
				}
				log.debug(`[DingTalk][onPartialReply] 收到部分响应，文本长度=${payload.text.length}`);
				if (asyncMode) {
					log.debug(`[DingTalk][onPartialReply] 异步模式，累积响应`);
					asyncModeFullResponse = payload.text;
					return;
				}
				await startStreaming();
				if (currentCardTarget) {
					accumulatedText = payload.text;
					const now = Date.now();
					if (now - lastUpdateTime >= updateInterval) {
						const { FILE_MARKER_PATTERN, VIDEO_MARKER_PATTERN, AUDIO_MARKER_PATTERN } = await import("./common-CGPC5bYt.mjs");
						const displayContent = accumulatedText.replace(FILE_MARKER_PATTERN, "").replace(VIDEO_MARKER_PATTERN, "").replace(AUDIO_MARKER_PATTERN, "").trim();
						log.debug(`[DingTalk][onPartialReply] 更新 AI Card，显示文本长度=${displayContent.length}`);
						lastUpdateTime = now;
						try {
							await streamAICard(currentCardTarget, displayContent, false, account.config, log);
							outboundUserVisibleThisTurn = true;
							log.debug(`[DingTalk][onPartialReply] ✅ AI Card 更新成功`);
						} catch (err) {
							if (isQpsLimitError(err)) log.warn(`[DingTalk][onPartialReply] AI Card 流式更新遇到 QPS 限流，已在内部退避重试；本次跳过，等待下一次 partial 更新补齐内容`);
							else {
								log.error(`[DingTalk][onPartialReply] ❌ AI Card 更新失败：${err.message}`);
								await sendFallbackErrorMessage("sendMessage", err.message);
							}
						}
					} else log.debug(`[DingTalk][onPartialReply] 节流控制，跳过本次更新（距离上次更新 ${now - lastUpdateTime}ms）`);
				} else log.warn(`[DingTalk][onPartialReply] ⚠️ AI Card 不存在，跳过更新`);
			} },
			onCommandOutput: (payload) => {
				const dwsMatch = (payload.title || payload.name || "").match(DWS_PRODUCT_PATTERN) || payload.output?.match(DWS_PRODUCT_PATTERN);
				if (dwsMatch) {
					const product = dwsMatch[1];
					if (!(payload.phase === "end" && payload.exitCode !== null && payload.exitCode !== 0)) {
						detectedDwsProducts.add(product);
						log.info(`[DingTalk][onCommandOutput] 检测到 dws 产品: ${product}，phase=${payload.phase}, exitCode=${payload.exitCode}`);
					} else log.info(`[DingTalk][onCommandOutput] dws 命令执行失败，跳过: ${product}，exitCode=${payload.exitCode}`);
				}
			}
		},
		markDispatchIdle,
		getAsyncModeResponse: () => asyncModeFullResponse
	};
}
//#endregion
//#region src/core/message-handler.ts
/**
* 会话消息队列管理
* 用于确保同一会话+agent的消息按顺序处理，避免并发冲突导致AI返回空响应
* 队列键格式：{sessionId}:{agentId}
* 这样不同 agent 可以并发处理，同一 agent 的同一会话串行处理
*/
const sessionQueues = /* @__PURE__ */ new Map();
/**
* 清理过期的会话队列（超过5分钟没有新消息的会话+agent）
*/
const sessionLastActivity = /* @__PURE__ */ new Map();
const SESSION_QUEUE_TTL = 300 * 1e3;
function cleanupExpiredSessionQueues() {
	const now = Date.now();
	for (const [queueKey, lastActivity] of sessionLastActivity.entries()) if (now - lastActivity > SESSION_QUEUE_TTL) {
		sessionQueues.delete(queueKey);
		sessionLastActivity.delete(queueKey);
	}
}
setInterval(cleanupExpiredSessionQueues, 6e4);
/**
* 解析 data.content 字段：可能是对象，也可能是 JSON 字符串（钉钉部分 API 版本会将 content 序列化为字符串）。
* 返回解析后的对象，或 null（字段不存在 / 无法解析）。
*/
function resolveContent(data) {
	const raw = data?.content;
	if (raw == null) return null;
	if (typeof raw === "object") return raw;
	if (typeof raw === "string") try {
		const parsed = JSON.parse(raw);
		if (parsed && typeof parsed === "object") return parsed;
	} catch {}
	return null;
}
/**
* 从消息的内容容器（data.text 或 data.content）中提取引用消息文本，最多递归 maxDepth 层。
* 对齐 Rust chatbot.rs 的 extract_quoted_msg_text 逻辑。
*
* 钉钉引用消息结构：
* { isReplyMsg: true, repliedMsg: { msgType, content, msgId, senderId } }
*/
function extractQuotedMsgText(container, maxDepth) {
	if (maxDepth <= 0 || !container) return null;
	if (!container.isReplyMsg) return null;
	const repliedMsg = container.repliedMsg;
	if (!repliedMsg) return null;
	const msgType = repliedMsg.msgType || "text";
	let contentObj = null;
	const rawContent = repliedMsg.content;
	if (rawContent && typeof rawContent === "object") contentObj = rawContent;
	else if (typeof rawContent === "string") try {
		const parsed = JSON.parse(rawContent);
		if (parsed && typeof parsed === "object") contentObj = parsed;
	} catch {}
	let bodyText = "";
	switch (msgType) {
		case "text":
			bodyText = contentObj?.text?.trim() || repliedMsg.text?.trim() || "";
			if (contentObj?.isReplyMsg) {
				const nested = extractQuotedMsgText(contentObj, maxDepth - 1);
				if (nested) bodyText = bodyText ? `${bodyText}\n${nested}` : nested;
			}
			break;
		case "richText":
			bodyText = (contentObj?.richText || []).filter((item) => item.text && item.msgType !== "skill" && !item.skillData).map((item) => item.text).join("");
			break;
		case "picture":
			bodyText = "[图片]";
			break;
		case "video":
			bodyText = "[视频]";
			break;
		case "audio":
			bodyText = contentObj?.recognition || "[语音消息]";
			break;
		case "file":
			bodyText = `[文件: ${contentObj?.fileName || "unknown"}]`;
			break;
		case "markdown":
			bodyText = contentObj?.text?.trim() || "[markdown消息]";
			break;
		case "interactiveCard": {
			const cardUrl = contentObj?.biz_custom_action_url || repliedMsg.biz_custom_action_url || "";
			bodyText = cardUrl ? `收到交互式卡片链接：${cardUrl}` : "[interactiveCard消息]";
			break;
		}
		default: bodyText = `[${msgType}消息]`;
	}
	if (!bodyText) return null;
	return `[引用] ${bodyText}`;
}
/**
* 从 richText 列表中提取媒体附件（图片 downloadCode）。
* 兼容新结构（content.richText）和旧结构（richText.richTextList）。
*/
function extractRichTextMediaAttachments(data, content) {
	const imageUrls = [];
	const downloadCodes = [];
	const fileNames = [];
	const richList = content?.richText || data?.richText?.richTextList || [];
	for (const item of richList) {
		if (item.pictureUrl) imageUrls.push(item.pictureUrl);
		if (item.downloadCode) {
			const itemType = item.type || "";
			if (itemType === "picture" || !itemType) imageUrls.push(`downloadCode:${item.downloadCode}`);
			else if (itemType === "video") {
				downloadCodes.push(item.downloadCode);
				fileNames.push(item.fileName || "video.mp4");
			} else if (itemType === "audio") {
				downloadCodes.push(item.downloadCode);
				fileNames.push(item.fileName || "audio.amr");
			} else if (itemType === "file") {
				downloadCodes.push(item.downloadCode);
				fileNames.push(item.fileName || "文件");
			}
		}
	}
	return {
		imageUrls,
		downloadCodes,
		fileNames
	};
}
/**
* 从 repliedMsg 中提取媒体附件（用于 reply 类型消息）。
*/
function extractRepliedMsgMediaAttachments(repliedMsg) {
	const imageUrls = [];
	const downloadCodes = [];
	const fileNames = [];
	if (!repliedMsg) return {
		imageUrls,
		downloadCodes,
		fileNames
	};
	const msgType = repliedMsg.msgType || "text";
	let contentObj = null;
	const rawContent = repliedMsg.content;
	if (rawContent && typeof rawContent === "object") contentObj = rawContent;
	else if (typeof rawContent === "string") try {
		const parsed = JSON.parse(rawContent);
		if (parsed && typeof parsed === "object") contentObj = parsed;
	} catch {}
	switch (msgType) {
		case "picture":
		case "video":
		case "audio": {
			const code = contentObj?.downloadCode;
			if (code) if (msgType === "picture") imageUrls.push(`downloadCode:${code}`);
			else {
				downloadCodes.push(code);
				fileNames.push(contentObj?.fileName || (msgType === "video" ? "video.mp4" : "audio.amr"));
			}
			break;
		}
		case "file": {
			const code = contentObj?.downloadCode;
			if (code) {
				downloadCodes.push(code);
				fileNames.push(contentObj?.fileName || "文件");
			}
			break;
		}
		case "richText": {
			const richList = contentObj?.richText || [];
			for (const item of richList) if (item.downloadCode) imageUrls.push(`downloadCode:${item.downloadCode}`);
			break;
		}
		default: break;
	}
	return {
		imageUrls,
		downloadCodes,
		fileNames
	};
}
function extractMessageContent(data) {
	const msgtype = data.msgtype || "text";
	switch (msgtype) {
		case "text": {
			const atDingtalkIds = data.text?.at?.atDingtalkIds || [];
			const atMobiles = data.text?.at?.atMobiles || [];
			const bodyText = data.text?.content?.trim() || "";
			const hasReply = !!data.text?.isReplyMsg;
			const quotedText = extractQuotedMsgText(data.text, 3);
			const text = quotedText ? `${bodyText}\n${quotedText}` : bodyText;
			const repliedMsgInText = data.text?.repliedMsg;
			const { imageUrls, downloadCodes, fileNames } = extractRepliedMsgMediaAttachments(repliedMsgInText);
			let interactiveCardUrl;
			if (hasReply && repliedMsgInText) {
				const extractedUrl = extractFirstUrlFromText((typeof repliedMsgInText.content === "object" ? repliedMsgInText.content : (() => {
					try {
						return JSON.parse(repliedMsgInText.content);
					} catch {
						return null;
					}
				})())?.text || repliedMsgInText.text || "");
				if (extractedUrl) interactiveCardUrl = extractedUrl;
			}
			return {
				text,
				messageType: hasReply ? "reply" : "text",
				imageUrls,
				downloadCodes,
				fileNames,
				atDingtalkIds,
				atMobiles,
				interactiveCardUrl
			};
		}
		case "richText": {
			const content = resolveContent(data);
			const textParts = [];
			const richList = content?.richText || data?.richText?.richTextList || [];
			for (const item of richList) {
				const isSkillItem = item.type === "skill" || !!item.skillData;
				if (item.text && !isSkillItem) textParts.push(item.text);
				if (isSkillItem && item.skillData) {
					const skillId = item.skillData.skillId || "";
					const displayName = item.skillData.displayName || "";
					const iconUrl = item.skillData.iconUrl || "";
					const skillTag = iconUrl ? `<skill data-id="${skillId}" data-name="${displayName}" icon="${iconUrl}">` : `<skill data-id="${skillId}" data-name="${displayName}">`;
					textParts.push(skillTag);
				}
				if (item.pictureUrl) {}
			}
			const hasReply = !!content?.isReplyMsg;
			const quotedText = extractQuotedMsgText(content, 3);
			if (quotedText) textParts.push(quotedText);
			const richTextMedia = extractRichTextMediaAttachments(data, content);
			const repliedMsgInRichText = content?.repliedMsg;
			const repliedMedia = extractRepliedMsgMediaAttachments(repliedMsgInRichText);
			const imageUrls = [...richTextMedia.imageUrls, ...repliedMedia.imageUrls];
			const downloadCodes = [...richTextMedia.downloadCodes, ...repliedMedia.downloadCodes];
			const fileNames = [...richTextMedia.fileNames, ...repliedMedia.fileNames];
			return {
				text: textParts.join("") || (imageUrls.length > 0 ? "[图片]" : downloadCodes.length > 0 ? "[媒体文件]" : "[富文本消息]"),
				messageType: hasReply ? "reply" : "richText",
				imageUrls,
				downloadCodes,
				fileNames,
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "picture": {
			const content = resolveContent(data);
			const downloadCode = content?.downloadCode || "";
			const pictureUrl = content?.pictureUrl || "";
			const imageUrls = [];
			const downloadCodes = [];
			if (pictureUrl) imageUrls.push(pictureUrl);
			if (downloadCode) downloadCodes.push(downloadCode);
			return {
				text: "[图片]",
				messageType: "picture",
				imageUrls,
				downloadCodes,
				fileNames: [],
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "audio": {
			const content = resolveContent(data);
			const recognition = content?.recognition || data?.audio?.recognition || "[语音消息]";
			const audioDownloadCode = content?.downloadCode || "";
			const audioFileName = content?.fileName || "audio.amr";
			const downloadCodes = [];
			const fileNames = [];
			if (audioDownloadCode) {
				downloadCodes.push(audioDownloadCode);
				fileNames.push(audioFileName);
			}
			return {
				text: recognition,
				messageType: "audio",
				imageUrls: [],
				downloadCodes,
				fileNames,
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "video": {
			const content = resolveContent(data);
			const videoDownloadCode = content?.downloadCode || "";
			const videoFileName = content?.fileName || "video.mp4";
			const downloadCodes = [];
			const fileNames = [];
			if (videoDownloadCode) {
				downloadCodes.push(videoDownloadCode);
				fileNames.push(videoFileName);
			}
			return {
				text: "[视频]",
				messageType: "video",
				imageUrls: [],
				downloadCodes,
				fileNames,
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "file": {
			const content = resolveContent(data);
			const fileName = content?.fileName || data?.file?.fileName || "文件";
			const downloadCode = content?.downloadCode || "";
			const downloadCodes = [];
			const fileNames = [];
			if (downloadCode) {
				downloadCodes.push(downloadCode);
				fileNames.push(fileName);
			}
			return {
				text: `[文件: ${fileName}]`,
				messageType: "file",
				imageUrls: [],
				downloadCodes,
				fileNames,
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "markdown": return {
			text: data.text?.content?.trim() || resolveContent(data)?.text?.trim() || "[markdown消息]",
			messageType: "markdown",
			imageUrls: [],
			downloadCodes: [],
			fileNames: [],
			atDingtalkIds: [],
			atMobiles: []
		};
		case "actionCard": {
			const content = resolveContent(data);
			const title = content?.title?.trim() || "";
			const body = content?.text?.trim() || "";
			const actionUrls = (content?.actionUrlItemList || []).map((item) => item.actionUrl?.trim()).filter((url) => !!url);
			const sections = [];
			if (title) sections.push(title);
			if (body) sections.push(body);
			if (actionUrls.length > 0) {
				const linkSection = actionUrls.length === 1 ? `操作链接：${actionUrls[0]}` : `操作链接：\n- ${actionUrls.join("\n- ")}`;
				sections.push(linkSection);
			}
			return {
				text: sections.length > 0 ? sections.join("\n\n") : "[actionCard消息]",
				messageType: "actionCard",
				imageUrls: [],
				downloadCodes: [],
				fileNames: [],
				atDingtalkIds: [],
				atMobiles: [],
				actionCardUrl: actionUrls.length === 1 ? actionUrls[0] : void 0
			};
		}
		case "interactiveCard": {
			const interactiveCardUrl = (resolveContent(data)?.biz_custom_action_url || data?.biz_custom_action_url || "").trim() || void 0;
			if (interactiveCardUrl) return {
				text: `收到交互式卡片链接：${interactiveCardUrl}`,
				messageType: "interactiveCard",
				imageUrls: [],
				downloadCodes: [],
				fileNames: [],
				atDingtalkIds: [],
				atMobiles: [],
				interactiveCardUrl
			};
			return {
				text: "[interactiveCard消息]",
				messageType: "interactiveCard",
				imageUrls: [],
				downloadCodes: [],
				fileNames: [],
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		case "reply": {
			const replyContainer = data.text || resolveContent(data);
			const bodyText = data.text?.content?.trim() || "";
			const quotedText = extractQuotedMsgText(replyContainer, 3);
			const text = quotedText ? `${bodyText}\n${quotedText}` : bodyText || "[引用消息]";
			const { imageUrls, downloadCodes, fileNames } = extractRepliedMsgMediaAttachments(data.text?.repliedMsg || resolveContent(data)?.repliedMsg);
			return {
				text,
				messageType: "reply",
				imageUrls,
				downloadCodes,
				fileNames,
				atDingtalkIds: [],
				atMobiles: []
			};
		}
		default: return {
			text: data.text?.content?.trim() || `[${msgtype}消息]`,
			messageType: msgtype,
			imageUrls: [],
			downloadCodes: [],
			fileNames: [],
			atDingtalkIds: [],
			atMobiles: []
		};
	}
}
/**
* 从文本内容中提取第一个 HTTP/HTTPS URL。
* 用于处理引用消息文本里直接粘贴链接的场景（如引用一条含 alidocs 链接的文本消息）。
*/
function extractFirstUrlFromText(text) {
	const urlMatch = text.match(/https?:\/\/[^\s\u3000\u3001\uff0c\u3002\uff01\uff1f"'<>]+/);
	return urlMatch ? urlMatch[0].trim() : null;
}
/**
* 根据消息中的 interactiveCardUrl / actionCardUrl 构建链接路由 system prompt。
* 对齐 Rust agent_support.rs 的 build_link_routing_prompt 逻辑：
* - alidocs.dingtalk.com → 使用 dws skill 的 doc 能力读取
* - 其他 URL → 使用 read_url 读取
* 返回 null 表示无需注入额外 prompt。
*/
function buildLinkRoutingPrompt(content) {
	const interactiveCardUrl = content.interactiveCardUrl?.trim();
	const actionCardUrl = content.actionCardUrl?.trim();
	const linkUrl = interactiveCardUrl || actionCardUrl;
	if (!linkUrl) return null;
	const cardKind = interactiveCardUrl ? "interactive card" : "action card";
	let host = null;
	try {
		host = new URL(linkUrl).hostname;
	} catch {}
	if (host === "alidocs.dingtalk.com") return [
		`The inbound DingTalk message is an ${cardKind} with a document link.`,
		`Linked URL: ${linkUrl}`,
		`This URL is hosted on \`alidocs.dingtalk.com\`.`,
		`You MUST inspect and summarize it via the \`dws\` skill using its \`doc\` product capability.`,
		`If \`dws\` is not already visible in the skill snapshot, call \`search_skills\` to locate it, then call \`use_skill\` with the exact id.`,
		`Never switch to browser-based reading for this link. Browser incompatibility or markdown export limitations are not final answers.`,
		`Do not use \`read_url\` for this link.`,
		`Reply to the DingTalk user with a concise summary of the linked document content.`
	].join("\n");
	return [
		`The inbound DingTalk message is an ${cardKind} with a link.`,
		`Linked URL: ${linkUrl}`,
		`For this URL, you MUST use \`read_url\` to inspect the linked content before answering.`,
		`Do not use the \`dws\` skill for this link.`,
		`Reply to the DingTalk user with a concise summary of the linked content.`
	].join("\n");
}
async function downloadImageToFile(downloadUrl, agentWorkspaceDir, log) {
	try {
		log?.info?.(`开始下载图片: ${downloadUrl.slice(0, 100)}...`);
		const resp = await dingtalkHttp.get(downloadUrl, {
			proxy: false,
			headers: { "Content-Type": void 0 },
			responseType: "arraybuffer",
			timeout: 3e4
		});
		const buffer = Buffer.from(resp.data);
		const contentType = resp.headers["content-type"] || "image/jpeg";
		const ext = contentType.includes("png") ? ".png" : contentType.includes("gif") ? ".gif" : contentType.includes("webp") ? ".webp" : ".jpg";
		const mediaDir = path.join(agentWorkspaceDir, "media", "inbound");
		fs.mkdirSync(mediaDir, { recursive: true });
		const tmpFile = path.join(mediaDir, `openclaw-media-${Date.now()}-${Math.random().toString(36).slice(2, 8)}${ext}`);
		fs.writeFileSync(tmpFile, buffer);
		log?.info?.(`图片下载成功: size=${buffer.length} bytes, type=${contentType}, path=${tmpFile}`);
		return tmpFile;
	} catch (err) {
		log?.error?.(`图片下载失败: ${err.message}`);
		return null;
	}
}
async function downloadMediaByCode(downloadCode, config, agentWorkspaceDir, log) {
	try {
		const token = await getAccessToken(config);
		log?.info?.(`通过 downloadCode 下载媒体: ${downloadCode.slice(0, 30)}...`);
		const resp = await dingtalkHttp.post(`${DINGTALK_API}/v1.0/robot/messageFiles/download`, {
			downloadCode,
			robotCode: String(config.clientId)
		}, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 3e4
		});
		const downloadUrl = resp.data?.downloadUrl;
		if (!downloadUrl) {
			log?.warn?.(`downloadCode 换取 downloadUrl 失败: ${JSON.stringify(resp.data)}`);
			return null;
		}
		return downloadImageToFile(downloadUrl, agentWorkspaceDir, log);
	} catch (err) {
		log?.error?.(`downloadCode 下载失败: ${err.message}`);
		return null;
	}
}
async function getFileDownloadUrl(downloadCode, fileName, config, log) {
	try {
		const token = await getAccessToken(config);
		log?.info?.(`获取文件下载链接: ${fileName}`);
		const resp = await dingtalkHttp.post(`${DINGTALK_API}/v1.0/robot/messageFiles/download`, {
			downloadCode,
			robotCode: String(config.clientId)
		}, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 3e4
		});
		const downloadUrl = resp.data?.downloadUrl;
		if (!downloadUrl) {
			log?.warn?.(`downloadCode 换取 downloadUrl 失败: ${JSON.stringify(resp.data)}`);
			return null;
		}
		log?.info?.(`获取下载链接成功: ${fileName}`);
		return downloadUrl;
	} catch (err) {
		log?.error?.(`获取下载链接失败: ${err.message}`);
		return null;
	}
}
/**
* 下载文件到本地
*/
async function downloadFileToLocal(downloadUrl, fileName, agentWorkspaceDir, log) {
	try {
		log?.info?.(`开始下载文件: ${fileName}`);
		const resp = await dingtalkHttp.get(downloadUrl, {
			proxy: false,
			headers: { "Content-Type": void 0 },
			responseType: "arraybuffer",
			timeout: 6e4
		});
		const buffer = Buffer.from(resp.data);
		const mediaDir = path.join(agentWorkspaceDir, "media", "inbound");
		fs.mkdirSync(mediaDir, { recursive: true });
		const sanitizeFileName = (name) => {
			let safe = name.replace(/[/\\]/g, "_");
			safe = safe.replace(/[<>:"|?*\x00-\x1f]/g, "_");
			safe = safe.replace(/^\.+/, "");
			if (safe.length > 200) {
				const ext = path.extname(safe);
				safe = path.basename(safe, ext).substring(0, 200 - ext.length) + ext;
			}
			if (!safe) safe = "unnamed_file";
			return safe;
		};
		const ext = path.extname(fileName);
		const baseName = path.basename(fileName, ext);
		const timestamp = Date.now();
		const safeFileName = `${sanitizeFileName(baseName)}-${timestamp}${ext}`;
		const localPath = path.join(mediaDir, safeFileName);
		fs.writeFileSync(localPath, buffer);
		log?.info?.(`文件下载成功: ${fileName}, size=${buffer.length} bytes, path=${localPath}`);
		return localPath;
	} catch (err) {
		log?.error?.(`downloadFileToLocal 异常: ${err.message}\n${err.stack}`);
		return null;
	}
}
/**
* 解析 Word 文档 (.docx)
*/
async function parseDocxFile(filePath, log) {
	try {
		log?.info?.(`开始解析 Word 文档: ${filePath}`);
		let mammoth;
		try {
			mammoth = (await import("mammoth")).default;
		} catch {
			log?.warn?.("mammoth 库未安装，无法解析 .docx 文件。请运行: npm install mammoth");
			return null;
		}
		const buffer = fs.readFileSync(filePath);
		const text = (await mammoth.extractRawText({ buffer })).value.trim();
		if (text) {
			log?.info?.(`Word 文档解析成功: ${filePath}, 文本长度=${text.length}`);
			return text;
		} else {
			log?.warn?.(`Word 文档解析结果为空: ${filePath}`);
			return null;
		}
	} catch (err) {
		log?.error?.(`Word 文档解析失败: ${filePath}, error=${err.message}`);
		return null;
	}
}
/**
* 解析 PDF 文档
*/
async function parsePdfFile(filePath, log) {
	try {
		log?.info?.(`开始解析 PDF 文档: ${filePath}`);
		let pdfParseV1;
		let pdfParseV2;
		try {
			const mod = await import("pdf-parse");
			if (mod.PDFParse) pdfParseV2 = mod.PDFParse;
			else if (mod.default) pdfParseV1 = mod.default;
			else throw new Error("pdf-parse module format not recognized");
		} catch {
			log?.warn?.("pdf-parse 库未安装，无法解析 .pdf 文件。请运行: npm install pdf-parse");
			return null;
		}
		const buffer = fs.readFileSync(filePath);
		let text;
		let numPages;
		if (pdfParseV2) {
			const parser = new pdfParseV2({ data: buffer });
			const result = await parser.getText();
			text = (result.text ?? "").trim();
			numPages = result.total;
			parser.destroy?.();
		} else {
			const data = await pdfParseV1(buffer);
			text = (data.text ?? "").trim();
			numPages = data.numpages;
		}
		if (text) {
			log?.info?.(`PDF 文档解析成功: ${filePath}, 文本长度=${text.length}, 页数=${numPages}`);
			return text;
		} else {
			log?.warn?.(`PDF 文档解析结果为空: ${filePath}`);
			return null;
		}
	} catch (err) {
		log?.error?.(`PDF 文档解析失败: ${filePath}, error=${err.message}`);
		return null;
	}
}
/**
* 读取纯文本文件
*/
async function readTextFile(filePath, log) {
	try {
		log?.info?.(`开始读取文本文件: ${filePath}`);
		const text = fs.readFileSync(filePath, "utf-8").trim();
		if (text) {
			log?.info?.(`文本文件读取成功: ${filePath}, 文本长度=${text.length}`);
			return text;
		} else {
			log?.warn?.(`文本文件内容为空: ${filePath}`);
			return null;
		}
	} catch (err) {
		log?.error?.(`文本文件读取失败: ${filePath}, error=${err.message}`);
		return null;
	}
}
/**
* 根据文件类型解析文件内容
*/
async function parseFileContent(filePath, fileName, log) {
	const ext = path.extname(fileName).toLowerCase();
	if ([".docx", ".doc"].includes(ext)) return {
		content: await parseDocxFile(filePath, log),
		type: "text"
	};
	if (ext === ".pdf") return {
		content: await parsePdfFile(filePath, log),
		type: "text"
	};
	if ([
		".txt",
		".md",
		".json",
		".xml",
		".yaml",
		".yml",
		".csv",
		".log",
		".js",
		".ts",
		".py",
		".java",
		".c",
		".cpp",
		".h",
		".sh",
		".bat"
	].includes(ext)) return {
		content: await readTextFile(filePath, log),
		type: "text"
	};
	return {
		content: null,
		type: "binary"
	};
}
/**
* 内部消息处理函数（实际执行消息处理逻辑）
*/
async function handleDingTalkMessageInternal(params) {
	const { accountId, config, data, sessionWebhook, runtime, cfg } = params;
	const log = createLoggerFromConfig(config, `DingTalk:${accountId}`);
	const content = extractMessageContent(data);
	if (!content.text && content.imageUrls.length === 0 && content.downloadCodes.length === 0) return;
	const isDirect = data.conversationType === "1";
	const senderId = data.senderStaffId || data.senderId;
	const senderName = data.senderNick || "Unknown";
	if (isDirect) {
		const dmPolicy = config.dmPolicy || "open";
		const allowFrom = config.allowFrom || [];
		if (dmPolicy === "pairing") log?.warn?.(`dmPolicy="pairing" 暂不支持，将按 "open" 策略处理`);
		if (dmPolicy === "allowlist") {
			if (!senderId) {
				log?.warn?.(`DM 被拦截: senderId 为空`);
				return;
			}
			const normalizedSenderId = String(senderId);
			const normalizedAllowFrom = allowFrom.map((id) => String(id));
			if (normalizedAllowFrom.length === 0) {
				log?.warn?.(`[DingTalk] DM 被拦截: allowFrom 白名单为空，拒绝所有请求`);
				try {
					await sendProactive(config, { userId: senderId }, "抱歉，此机器人的访问白名单配置有误。请联系管理员检查配置。", {
						msgType: "text",
						useAICard: false,
						fallbackToNormal: true,
						log
					});
				} catch (err) {
					log?.error?.(`[DingTalk] 发送 DM 配置错误提示失败: ${err.message}`);
				}
				return;
			}
			if (!normalizedAllowFrom.includes(normalizedSenderId)) {
				log?.warn?.(`DM 被拦截: senderId=${senderId} (${senderName}) 不在白名单中`);
				try {
					await sendProactive(config, { userId: senderId }, "抱歉，您暂无权限使用此机器人。如需开通权限，请联系管理员。", {
						msgType: "text",
						useAICard: false,
						fallbackToNormal: true,
						log
					});
				} catch (err) {
					log?.error?.(`发送 DM 拦截提示失败: ${err.message}`);
				}
				return;
			}
		}
	}
	if (!isDirect) {
		const groupPolicy = config.groupPolicy || "open";
		const conversationId = data.conversationId;
		const groupAllowFrom = config.groupAllowFrom || [];
		if (groupPolicy === "disabled") {
			log?.warn?.(`群聊被拦截: groupPolicy=disabled`);
			try {
				await sendProactive(config, { openConversationId: conversationId }, "抱歉，此机器人暂不支持群聊功能。", {
					msgType: "text",
					useAICard: false,
					fallbackToNormal: true,
					log
				});
			} catch (err) {
				log?.error?.(`发送群聊 disabled 提示失败: ${err.message}`);
			}
			return;
		}
		if (groupPolicy === "allowlist") {
			if (!conversationId) {
				log?.warn?.(`群聊被拦截: conversationId 为空`);
				return;
			}
			const normalizedConversationId = String(conversationId);
			const normalizedGroupAllowFrom = groupAllowFrom.map((id) => String(id));
			if (normalizedGroupAllowFrom.length === 0) {
				log?.warn?.(`群聊被拦截: groupAllowFrom 白名单为空，拒绝所有请求`);
				try {
					await sendProactive(config, { openConversationId: conversationId }, "抱歉，此机器人的群组访问白名单配置有误。请联系管理员检查配置。", {
						msgType: "text",
						useAICard: false,
						fallbackToNormal: true,
						log
					});
				} catch (err) {
					log?.error?.(`发送群聊配置错误提示失败: ${err.message}`);
				}
				return;
			}
			if (!normalizedGroupAllowFrom.includes(normalizedConversationId)) {
				log?.warn?.(`群聊被拦截: conversationId=${conversationId} 不在 groupAllowFrom 白名单中`);
				try {
					await sendProactive(config, { openConversationId: conversationId }, "抱歉，此群组暂无权限使用此机器人。如需开通权限，请联系管理员。", {
						msgType: "text",
						useAICard: false,
						fallbackToNormal: true,
						log
					});
				} catch (err) {
					log?.error?.(`发送群聊 allowlist 提示失败: ${err.message}`);
				}
				return;
			}
		}
	}
	const sessionContext = buildSessionContext({
		accountId,
		senderId,
		senderName,
		conversationType: data.conversationType,
		conversationId: data.conversationId,
		groupSubject: data.conversationTitle,
		separateSessionByConversation: config.separateSessionByConversation,
		groupSessionScope: config.groupSessionScope,
		sharedMemoryAcrossConversations: config.sharedMemoryAcrossConversations
	});
	let matchedAgentId = null;
	if (cfg.bindings && cfg.bindings.length > 0) for (const binding of cfg.bindings) {
		const match = binding.match;
		if (match.channel && match.channel !== "dingtalk-connector") continue;
		if (match.accountId && match.accountId !== accountId) continue;
		if (match.peer) {
			if (match.peer.kind && match.peer.kind !== sessionContext.chatType) continue;
			if (match.peer.id && match.peer.id !== "*" && match.peer.id !== sessionContext.peerId) continue;
		}
		matchedAgentId = binding.agentId;
		break;
	}
	if (!matchedAgentId) matchedAgentId = cfg.defaultAgent || "main";
	const agentWorkspaceDir = resolveAgentWorkspaceDir(cfg, matchedAgentId);
	log?.info?.(`Agent 工作空间路径: ${agentWorkspaceDir}`);
	const rawText = content.text || "";
	let userContent = normalizeSlashCommand(rawText) || (content.imageUrls.length > 0 ? "请描述这张图片" : "");
	try {
		const { GamificationEngine, isGamificationCommand } = await import("./game-xiyou-DxRHjOIJ.mjs");
		if (isGamificationCommand(rawText)) {
			const engine = GamificationEngine.getInstanceForUser(senderId);
			if (rawText.trim().startsWith("/西游") || engine.isEnabled()) {
				const response = engine.handleCommand(rawText);
				if (response) {
					log?.info?.(`[DingTalk][Gamification] 处理养成系统命令: ${rawText.slice(0, 20)}`);
					await sendProactive(config, isDirect ? { userId: senderId } : { openConversationId: data.conversationId }, response, {
						useAICard: true,
						fallbackToNormal: true,
						log
					});
					return;
				}
			}
		}
	} catch (gamErr) {
		log?.warn?.(`[DingTalk][Gamification] 命令处理失败: ${gamErr?.message || gamErr}`);
	}
	const imageLocalPaths = [];
	log?.info?.(`处理消息: accountId=${accountId}, data= ${JSON.stringify(data, null, 2)}, sender=${senderName}, text=${content.text.slice(0, 50)}...`);
	for (let i = 0; i < content.imageUrls.length; i++) {
		const url = content.imageUrls[i];
		try {
			log?.info?.(`处理图片 ${i + 1}/${content.imageUrls.length}: ${url.slice(0, 50)}...`);
			if (url.startsWith("downloadCode:")) {
				const localPath = await downloadMediaByCode(url.slice(13), config, agentWorkspaceDir, log);
				if (localPath) {
					imageLocalPaths.push(localPath);
					log?.info?.(`图片下载成功 ${i + 1}/${content.imageUrls.length}`);
				} else log?.warn?.(`图片下载失败 ${i + 1}/${content.imageUrls.length}`);
			} else {
				const localPath = await downloadImageToFile(url, agentWorkspaceDir, log);
				if (localPath) {
					imageLocalPaths.push(localPath);
					log?.info?.(`图片下载成功 ${i + 1}/${content.imageUrls.length}`);
				} else log?.warn?.(`图片下载失败 ${i + 1}/${content.imageUrls.length}`);
			}
		} catch (err) {
			log?.error?.(`图片下载异常 ${i + 1}/${content.imageUrls.length}: ${err.message}`);
		}
	}
	for (let i = 0; i < content.downloadCodes.length; i++) {
		const code = content.downloadCodes[i];
		if (!content.fileNames[i]) try {
			log?.info?.(`处理 downloadCode 图片 ${i + 1}/${content.downloadCodes.length}`);
			const localPath = await downloadMediaByCode(code, config, agentWorkspaceDir, log);
			if (localPath) {
				imageLocalPaths.push(localPath);
				log?.info?.(`downloadCode 图片下载成功 ${i + 1}/${content.downloadCodes.length}`);
			} else log?.warn?.(`downloadCode 图片下载失败 ${i + 1}/${content.downloadCodes.length}`);
		} catch (err) {
			log?.error?.(`downloadCode 图片下载异常 ${i + 1}/${content.downloadCodes.length}: ${err.message}`);
		}
	}
	log?.info?.(`图片下载完成: 成功=${imageLocalPaths.length}, 总数=${content.imageUrls.length + content.downloadCodes.filter((_, i) => !content.fileNames[i]).length}`);
	const fileContentParts = [];
	for (let i = 0; i < content.downloadCodes.length; i++) {
		const code = content.downloadCodes[i];
		const fileName = content.fileNames[i];
		if (!fileName) continue;
		try {
			log?.info?.(`处理文件附件 ${i + 1}/${content.downloadCodes.length}: ${fileName}`);
			const downloadUrl = await getFileDownloadUrl(code, fileName, config, log);
			if (!downloadUrl) {
				fileContentParts.push(`⚠️ 文件获取失败: ${fileName}`);
				continue;
			}
			const localPath = await downloadFileToLocal(downloadUrl, fileName, agentWorkspaceDir, log);
			if (!localPath) {
				fileContentParts.push(`⚠️ 文件下载失败: ${fileName}\n🔗 [点击下载](${downloadUrl})`);
				continue;
			}
			const ext = path.extname(fileName).toLowerCase();
			let fileType = "文件";
			if ([
				".mp4",
				".avi",
				".mov",
				".mkv",
				".flv",
				".wmv",
				".webm"
			].includes(ext)) fileType = "视频";
			else if ([
				".mp3",
				".wav",
				".aac",
				".ogg",
				".m4a",
				".flac",
				".wma"
			].includes(ext)) fileType = "音频";
			else if ([
				".jpg",
				".jpeg",
				".png",
				".gif",
				".bmp",
				".webp"
			].includes(ext)) fileType = "图片";
			else if ([
				".txt",
				".md",
				".json",
				".xml",
				".yaml",
				".yml",
				".csv",
				".log",
				".js",
				".ts",
				".py",
				".java",
				".c",
				".cpp",
				".h",
				".sh",
				".bat"
			].includes(ext)) fileType = "文本文件";
			else if ([".docx", ".doc"].includes(ext)) fileType = "Word 文档";
			else if (ext === ".pdf") fileType = "PDF 文档";
			else if ([".xlsx", ".xls"].includes(ext)) fileType = "Excel 表格";
			else if ([".pptx", ".ppt"].includes(ext)) fileType = "PPT 演示文稿";
			else if ([
				".zip",
				".rar",
				".7z",
				".tar",
				".gz"
			].includes(ext)) fileType = "压缩包";
			const parseResult = await parseFileContent(localPath, fileName, log);
			if (parseResult.type === "text" && parseResult.content) {
				const contentPreview = parseResult.content.length > 200 ? parseResult.content.slice(0, 200) + "..." : parseResult.content;
				fileContentParts.push(`📄 **${fileType}**: ${fileName}\n✅ 已解析文件内容（${parseResult.content.length} 字符）\n💾 已保存到本地: ${localPath}\n📝 内容预览:\n\`\`\`\n${contentPreview}\n\`\`\`\n\n📋 完整内容:\n${parseResult.content}`);
				log?.info?.(`文件解析成功: ${fileName}, 内容长度=${parseResult.content.length}`);
			} else if (parseResult.type === "text" && !parseResult.content) {
				fileContentParts.push(`📄 **${fileType}**: ${fileName}\n⚠️ 文件解析失败，已保存到本地\n💾 本地路径: ${localPath}\n🔗 [点击下载](${downloadUrl})`);
				log?.warn?.(`文件解析失败: ${fileName}`);
			} else {
				if (fileType === "音频" && content.text && content.text !== "[语音消息]") fileContentParts.push(`🎤 **${fileType}**: ${fileName}\n📝 语音识别: ${content.text}\n💾 已保存到本地: ${localPath}\n🔗 [点击下载](${downloadUrl})`);
				else fileContentParts.push(`📎 **${fileType}**: ${fileName}\n💾 已保存到本地: ${localPath}\n🔗 [点击下载](${downloadUrl})`);
				log?.info?.(`二进制文件已保存: ${fileName}, path=${localPath}`);
			}
		} catch (err) {
			log?.error?.(`文件处理异常: ${fileName}, error=${err.message}`);
			fileContentParts.push(`⚠️ 文件处理失败: ${fileName}`);
		}
	}
	if (fileContentParts.length > 0) {
		const fileText = fileContentParts.join("\n\n");
		userContent = userContent ? `${userContent}\n\n${fileText}` : fileText;
	}
	if (!userContent && imageLocalPaths.length === 0) return;
	if (!params.emotionAlreadyAdded) addEmotionReply(config, data, log).catch((err) => {
		log?.warn?.(`贴表情失败: ${err.message}`);
	});
	const asyncMode = config.asyncMode === true;
	log?.info?.(`asyncMode 检测: config.asyncMode=${config.asyncMode}, asyncMode=${asyncMode}`);
	const proactiveTarget = isDirect ? { userId: senderId } : { openConversationId: data.conversationId };
	if (asyncMode) {
		log?.info?.(`进入异步模式分支`);
		const ackText = config.ackText || "🫡 任务已接收，处理中...";
		try {
			await sendProactive(config, proactiveTarget, ackText, {
				msgType: "text",
				useAICard: false,
				fallbackToNormal: true,
				log
			});
		} catch (ackErr) {
			log?.warn?.(`Failed to send acknowledgment: ${ackErr?.message || ackErr}`);
		}
	}
	try {
		const core = getDingtalkRuntime();
		let finalContent = userContent;
		if (imageLocalPaths.length > 0) {
			const imageMarkdown = imageLocalPaths.map((p) => `![image](file://${p})`).join("\n");
			finalContent = finalContent ? `${finalContent}\n\n${imageMarkdown}` : imageMarkdown;
		}
		const envelopeOptions = core.channel.reply.resolveEnvelopeFormatOptions(cfg);
		const envelopeFrom = isDirect ? senderId : `${data.conversationId}:${senderId}`;
		const body = core.channel.reply.formatAgentEnvelope({
			channel: "DingTalk",
			from: envelopeFrom,
			timestamp: /* @__PURE__ */ new Date(),
			envelope: envelopeOptions,
			body: finalContent
		});
		const matchedBy = matchedAgentId !== (cfg.defaultAgent || "main") ? "binding" : "default";
		const dmScope = cfg.session?.dmScope || "per-channel-peer";
		log?.info?.(`🔍 构建 sessionKey 前的参数: agentId=${matchedAgentId}, channel=dingtalk-connector, accountId=${accountId}, chatType=${sessionContext.chatType}, sessionPeerId=${sessionContext.sessionPeerId}, dmScope=${dmScope}`);
		const sessionKey = core.channel.routing.buildAgentSessionKey({
			agentId: matchedAgentId,
			channel: "dingtalk-connector",
			accountId,
			peer: {
				kind: sessionContext.chatType,
				id: sessionContext.sessionPeerId
			},
			dmScope
		});
		log?.info?.(`路由解析完成: agentId=${matchedAgentId}, sessionKey=${sessionKey}, matchedBy=${matchedBy}`);
		log?.info?.(`开始构建 inbound context...`);
		const toField = isDirect ? senderId : data.conversationId;
		log?.info?.(`构建 inbound context: isDirect=${isDirect}, senderId=${senderId}, conversationId=${data.conversationId}, To=${toField}`);
		const ctxPayload = core.channel.reply.finalizeInboundContext({
			Body: body,
			BodyForAgent: finalContent,
			RawBody: userContent,
			CommandBody: userContent,
			From: senderId,
			To: toField,
			SessionKey: sessionKey,
			AccountId: accountId,
			ChatType: sessionContext.chatType,
			GroupSubject: isDirect ? void 0 : data.conversationTitle,
			SenderName: senderName,
			SenderId: senderId,
			Provider: "dingtalk-connector",
			Surface: "dingtalk-connector",
			MessageSid: data.msgId,
			Timestamp: Date.now(),
			CommandAuthorized: true,
			OriginatingChannel: "dingtalk-connector",
			OriginatingTo: toField,
			BotChatbotUserId: data.chatbotUserId,
			BotChatbotCorpId: data.chatbotCorpId
		});
		const { dispatcher, replyOptions, markDispatchIdle, getAsyncModeResponse } = createDingtalkReplyDispatcher({
			cfg,
			agentId: matchedAgentId,
			runtime,
			conversationId: data.conversationId,
			senderId,
			isDirect,
			accountId,
			messageCreateTimeMs: Date.now(),
			sessionWebhook: data.sessionWebhook,
			asyncMode,
			preCreatedCard: params.preCreatedCard
		});
		if (config.clientId) {
			const botIdentityHint = `[DingTalk Bot Context] Current bot clientId: ${String(config.clientId)}. When executing \`dws chat message send-by-bot\`, always pass \`--client-id ${String(config.clientId)}\` to ensure messages are sent from the correct bot.`;
			finalContent = finalContent ? `${finalContent}\n\n${botIdentityHint}` : botIdentityHint;
		}
		const linkRoutingPrompt = buildLinkRoutingPrompt(content);
		if (linkRoutingPrompt) {
			finalContent = finalContent ? `${finalContent}\n\n${linkRoutingPrompt}` : linkRoutingPrompt;
			log?.info?.(`注入卡片链接路由指令: ${linkRoutingPrompt.slice(0, 100)}...`);
		}
		const { queuedFinal, counts } = await core.channel.reply.withReplyDispatcher({
			dispatcher,
			onSettled: () => {
				markDispatchIdle();
			},
			run: async () => {
				return await core.channel.reply.dispatchReplyFromConfig({
					ctx: ctxPayload,
					cfg,
					dispatcher,
					replyOptions
				});
			}
		});
		log.info?.(`[DingTalk][dispatch] dispatchReplyFromConfig 完成: queuedFinal=${queuedFinal}, counts=${JSON.stringify(counts)}`);
		if (asyncMode) try {
			const fullResponse = getAsyncModeResponse();
			const oapiToken = await getOapiAccessToken$1(config);
			let finalText = fullResponse;
			if (oapiToken) {
				finalText = await processLocalImages(finalText, oapiToken, log);
				const mediaTarget = isDirect ? {
					type: "user",
					userId: senderId
				} : {
					type: "group",
					openConversationId: data.conversationId
				};
				finalText = await processVideoMarkers(finalText, "", config, oapiToken, log, true, mediaTarget);
				finalText = await processAudioMarkers(finalText, "", config, oapiToken, log, true, mediaTarget);
				finalText = await uploadAndReplaceFileMarkers(finalText, "", config, oapiToken, log, true, mediaTarget);
				const { processRawMediaPaths } = await import("./media-CIO05hZn.mjs");
				finalText = await processRawMediaPaths(finalText, config, oapiToken, log, mediaTarget);
			}
			let textToSend = finalText.trim();
			if (!textToSend) {
				const isGroup = !isDirect;
				textToSend = pickEmptyReplyFallbackText(isGroup);
				if (isGroup) log?.warn?.(`[DingTalk][asyncMode] ${emptyGroupReplyLogHint()}`);
			}
			const title = textToSend.split("\n")[0]?.replace(/^[#*\s\->]+/, "").trim() || "消息";
			await sendProactive(config, proactiveTarget, textToSend, {
				msgType: "markdown",
				title,
				useAICard: false,
				fallbackToNormal: true,
				log
			});
		} catch (asyncErr) {
			const errMsg = `⚠️ 任务执行失败: ${asyncErr?.message || asyncErr}`;
			try {
				await sendProactive(config, proactiveTarget, errMsg, {
					msgType: "text",
					useAICard: false,
					fallbackToNormal: true,
					log
				});
			} catch (sendErr) {
				log?.error?.(`错误通知发送失败: ${sendErr?.message || sendErr}`);
			}
		}
	} catch (err) {
		log?.error?.(`SDK dispatch 失败: ${err.message}`);
		try {
			const token = await getAccessToken(config);
			const body = {
				msgtype: "text",
				text: { content: `抱歉，处理请求时出错: ${err.message}` }
			};
			if (!isDirect) body.at = {
				atUserIds: [senderId],
				isAtAll: false
			};
			await dingtalkHttp.post(sessionWebhook, body, { headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			} });
		} catch (fallbackErr) {
			log?.error?.(`错误消息发送也失败: ${fallbackErr.message}`);
		}
	}
	try {
		await recallEmotionReply(config, data, log);
	} catch (err) {
		log?.warn?.(`撤回表情异常: ${err.message}`);
	}
}
/**
* 消息处理入口函数（带队列管理）
* 确保同一会话+agent的消息按顺序处理，避免并发冲突
*/
async function handleDingTalkMessage(params) {
	const { accountId, config, data, log, cfg } = params;
	const isDirect = data.conversationType === "1";
	const senderId = data.senderStaffId || data.senderId;
	const conversationId = data.conversationId;
	const queueSessionContext = buildSessionContext({
		accountId,
		senderId,
		conversationType: data.conversationType,
		conversationId,
		separateSessionByConversation: config.separateSessionByConversation,
		groupSessionScope: config.groupSessionScope,
		sharedMemoryAcrossConversations: config.sharedMemoryAcrossConversations
	});
	const baseSessionId = queueSessionContext.sessionPeerId;
	if (!baseSessionId) {
		log?.warn?.("无法构建会话标识，跳过队列管理");
		return handleDingTalkMessageInternal(params);
	}
	let matchedAgentId = null;
	if (cfg.bindings && cfg.bindings.length > 0) for (const binding of cfg.bindings) {
		const match = binding.match;
		if (match.channel && match.channel !== "dingtalk-connector") continue;
		if (match.accountId && match.accountId !== accountId) continue;
		if (match.peer) {
			if (match.peer.kind && match.peer.kind !== queueSessionContext.chatType) continue;
			if (match.peer.id && match.peer.id !== "*" && match.peer.id !== queueSessionContext.peerId) continue;
		}
		matchedAgentId = binding.agentId;
		break;
	}
	if (!matchedAgentId) matchedAgentId = cfg.defaultAgent || "main";
	const queueKey = `${baseSessionId}:${matchedAgentId}`;
	try {
		sessionLastActivity.set(queueKey, Date.now());
		const isQueueBusy = sessionQueues.has(queueKey);
		const previousTask = sessionQueues.get(queueKey) || Promise.resolve();
		let preCreatedCard;
		if (isQueueBusy) {
			const ackPhrases = QUEUE_BUSY_ACK_PHRASES;
			const ackText = ackPhrases[Math.floor(Math.random() * ackPhrases.length)];
			const groupReplyMode = config.groupReplyMode || "aicard";
			if (!isDirect && (groupReplyMode === "text" || groupReplyMode === "markdown")) try {
				await sendProactive(config, { openConversationId: data.conversationId }, ackText, {
					msgType: "text",
					useAICard: false,
					fallbackToNormal: true
				});
				log?.info?.(`[队列] 队列繁忙，已发送普通文本 ACK（groupReplyMode=${groupReplyMode}）`);
			} catch (ackErr) {
				log?.warn?.(`[队列] 发送普通 ACK 失败: ${ackErr?.message || ackErr}`);
			}
			else {
				const cardTarget = isDirect ? {
					type: "user",
					userId: senderId
				} : {
					type: "group",
					openConversationId: data.conversationId
				};
				try {
					const card = await createAICardForTarget(config, cardTarget, log);
					if (card) {
						await streamAICard(card, ackText, false, config, log);
						preCreatedCard = card;
						log?.info?.(`[队列] 队列繁忙，已创建排队 ACK Card，cardInstanceId=${card.cardInstanceId}`);
					} else log?.warn?.(`[队列] 创建排队 ACK Card 失败（返回 null），跳过 ACK`);
					addEmotionReply(config, data, log).catch((err) => {
						log?.warn?.(`[队列] 贴排队表情失败: ${err.message}`);
					});
				} catch (ackErr) {
					log?.warn?.(`[队列] 创建排队 ACK Card 异常: ${ackErr?.message || ackErr}`);
				}
			}
		}
		const currentTask = previousTask.then(async () => {
			log?.info?.(`[队列] 开始处理消息，queueKey=${queueKey}`);
			await handleDingTalkMessageInternal({
				...params,
				preCreatedCard,
				emotionAlreadyAdded: isQueueBusy
			});
			log?.info?.(`[队列] 消息处理完成，queueKey=${queueKey}`);
		}).catch((err) => {
			log?.error?.(`[队列] 消息处理异常，queueKey=${queueKey}, error=${err.message}`);
		}).finally(() => {
			if (sessionQueues.get(queueKey) === currentTask) {
				sessionQueues.delete(queueKey);
				log?.info?.(`[队列] 队列已清空，queueKey=${queueKey}`);
			}
		});
		sessionQueues.set(queueKey, currentTask);
	} catch (err) {
		log?.error?.(`[队列] 队列管理异常，直接处理: ${err.message}`);
		handleDingTalkMessageInternal(params);
	}
}
//#endregion
export { downloadFileToLocal, downloadImageToFile, downloadMediaByCode, extractMessageContent, getFileDownloadUrl, handleDingTalkMessage, handleDingTalkMessageInternal };
