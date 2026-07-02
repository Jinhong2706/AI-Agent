import { i as checkAndMarkDingtalkMessage } from "./utils-legacy-CALCPP1t.mjs";
import * as fs from "fs";
//#region src/core/connection.ts
/**
* 钉钉 WebSocket 连接层
*
* 职责：
* - 管理单个钉钉账号的 WebSocket 连接
* - 实现应用层心跳检测（10 秒间隔，20 秒超时）
* - 处理连接重连逻辑，带指数退避
* - 消息去重（内置 Map，5 分钟 TTL）
*
* 核心特性：
* - 关闭 SDK 内置 keepAlive，使用自定义心跳
* - 详细的消息接收日志（三阶段：接收、解析、处理）
* - 连接统计和监控（每分钟输出）
*/
/** 心跳间隔（毫秒） */
const HEARTBEAT_INTERVAL = 10 * 1e3;
/** 超时阈值（毫秒） */
const TIMEOUT_THRESHOLD = 20 * 1e3;
/** 基础退避时间（毫秒） */
const BASE_BACKOFF_DELAY = 1e3;
/** 最大退避时间（毫秒） */
const MAX_BACKOFF_DELAY = 30 * 1e3;
let _streamNoiseSilenced = false;
function silenceDingtalkStreamConsoleNoise() {
	if (_streamNoiseSilenced) return;
	_streamNoiseSilenced = true;
	const origConsoleInfo = console.info.bind(console);
	console.info = (...args) => {
		const first = args[0];
		if (typeof first === "string") {
			if (first === "Disconnecting.") return;
			if (/^\[[^\]]+\] connect success$/.test(first)) return;
		}
		return origConsoleInfo(...args);
	};
}
let _connectionNoticePrinted = false;
function printConnectionNoticeOnce() {
	if (_connectionNoticePrinted) return;
	_connectionNoticePrinted = true;
	console.log("[dingtalk-connector] ℹ️  上游 dingtalk-stream SDK 的 `Disconnecting.` / `connect success` 日志已由本插件过滤；真实重连（网络抖动、服务端推 disconnect 等）由 connector 自动处理。正常运行下不应看到高频（≤30s）周期性重连，如有请提 issue。");
}
async function monitorSingleAccount(opts) {
	const { cfg, account, runtime, abortSignal, messageHandler, onStatusChange } = opts;
	const { accountId } = account;
	silenceDingtalkStreamConsoleNoise();
	const clawdbotConfig = cfg;
	const log = runtime?.log;
	const { createLoggerFromConfig } = await import("./logger-BeHWErmX.mjs");
	const logger = createLoggerFromConfig(account.config, `DingTalk:${accountId}`);
	if (!account.clientId || !account.clientSecret) throw new Error(`[DingTalk][${accountId}] Missing credentials: clientId=${account.clientId ? "present" : "MISSING"}, clientSecret=${account.clientSecret ? "present" : "MISSING"}. Please check your configuration in channels.dingtalk-connector.`);
	const clientIdStr = String(account.clientId);
	const clientSecretStr = String(account.clientSecret);
	if (clientIdStr.length < 10 || clientSecretStr.length < 10) throw new Error(`[DingTalk][${accountId}] Invalid credentials format: clientId length=${clientIdStr.length}, clientSecret length=${clientSecretStr.length}. Credentials appear to be too short or invalid.`);
	if (process.platform === "darwin") for (const stdioFd of [
		0,
		1,
		2
	]) try {
		fs.fstatSync(stdioFd);
	} catch (fdError) {
		if (fdError.code === "EBADF") {
			logger.warn(`[LaunchAgent] 检测到 fd ${stdioFd} 无效（EBADF），重定向到 /dev/null 以防止 TCP socket 创建失败`);
			try {
				fs.openSync("/dev/null", stdioFd === 0 ? "r" : "w");
			} catch (openError) {
				logger.warn(`[LaunchAgent] 无法修复 fd ${stdioFd}: ${openError.message}`);
			}
		}
	}
	logger.info(`Starting DingTalk Stream client...`);
	logger.info(`Initializing with clientId: ${clientIdStr.substring(0, 8)}...`);
	logger.info(`WebSocket keepAlive: false (using application-layer heartbeat)`);
	const dingtalkStreamModule = await import("dingtalk-stream");
	const DWClient = dingtalkStreamModule.DWClient;
	const { TOPIC_ROBOT } = dingtalkStreamModule;
	if (!DWClient) throw new Error("Failed to import DWClient from dingtalk-stream module");
	const client = new DWClient({
		clientId: account.clientId,
		clientSecret: account.clientSecret,
		debug: account.config.debug,
		endpoint: account.config.endpoint || "https://api.dingtalk.com",
		autoReconnect: false,
		keepAlive: false
	});
	let lastSocketAvailableTime = Date.now();
	let connectionEstablishedTime = Date.now();
	let isReconnecting = false;
	let reconnectAttempts = 0;
	let keepAliveTimer = null;
	let isStopped = false;
	let activeMessageProcessing = false;
	let messageProcessingKeepAliveTimer = null;
	/**
	* 标记消息处理开始，启动定期更新机制
	* 在消息处理期间，定时刷新 lastSocketAvailableTime
	* 防止长时间处理（如复杂的 AI 任务）触发心跳超时
	*/
	function markMessageProcessingStart() {
		activeMessageProcessing = true;
		lastSocketAvailableTime = Date.now();
		if (messageProcessingKeepAliveTimer) clearInterval(messageProcessingKeepAliveTimer);
		messageProcessingKeepAliveTimer = setInterval(() => {
			if (activeMessageProcessing) {
				lastSocketAvailableTime = Date.now();
				logger.debug(`📝 消息处理中，更新 socket 可用时间`);
			}
		}, 15 * 1e3);
		logger.debug(`📝 消息处理开始，启动活跃标记定时器`);
	}
	/**
	* 标记消息处理结束，停止定期更新机制
	*/
	function markMessageProcessingEnd() {
		activeMessageProcessing = false;
		if (messageProcessingKeepAliveTimer) {
			clearInterval(messageProcessingKeepAliveTimer);
			messageProcessingKeepAliveTimer = null;
		}
		lastSocketAvailableTime = Date.now();
		logger.debug(`✅ 消息处理结束，清理活跃标记定时器`);
	}
	/** 计算指数退避延迟（带抖动） */
	function calculateBackoffDelay(attempt) {
		const exponentialDelay = BASE_BACKOFF_DELAY * Math.pow(2, attempt);
		const jitter = Math.random() * 1e3;
		return Math.min(exponentialDelay + jitter, MAX_BACKOFF_DELAY);
	}
	/** 统一重连函数，带指数退避（无限重连） */
	async function doReconnect(immediate = false) {
		if (isReconnecting || isStopped) {
			logger.debug(`正在重连中或已停止，跳过`);
			return;
		}
		isReconnecting = true;
		if (!immediate && reconnectAttempts > 0) {
			const delay = calculateBackoffDelay(reconnectAttempts);
			logger.info(`⏳ 等待 ${Math.round(delay / 1e3)} 秒后重连 (尝试 ${reconnectAttempts + 1})`);
			await new Promise((resolve) => setTimeout(resolve, delay));
		}
		try {
			if (client.socket?.readyState === 1 || client.socket?.readyState === 3) {
				await client.disconnect();
				logger.info(`已断开旧连接`);
			}
			await client.connect();
			setupPongListener();
			setupMessageListener();
			setupCloseListener();
			if (!await new Promise((resolve) => {
				const timeout = setTimeout(() => {
					resolve(false);
				}, 1e4);
				if (client.socket?.readyState === 1) {
					clearTimeout(timeout);
					resolve(true);
					return;
				}
				const onOpen = () => {
					clearTimeout(timeout);
					client.socket?.removeListener("open", onOpen);
					client.socket?.removeListener("error", onError);
					resolve(true);
				};
				const onError = (err) => {
					clearTimeout(timeout);
					client.socket?.removeListener("open", onOpen);
					client.socket?.removeListener("error", onError);
					logger.warn(`连接建立失败: ${err.message}`);
					resolve(false);
				};
				client.socket?.once("open", onOpen);
				client.socket?.once("error", onError);
			})) throw new Error(`连接建立超时或失败`);
			lastSocketAvailableTime = Date.now();
			connectionEstablishedTime = Date.now();
			reconnectAttempts = 0;
			onStatusChange?.({
				connected: true,
				lastConnectedAt: Date.now()
			});
			logger.info(`✅ 重连成功 (socket 状态=${client.socket?.readyState})`);
		} catch (err) {
			reconnectAttempts++;
			logger.error(`重连失败：${err.message} (尝试 ${reconnectAttempts})`);
			throw err;
		} finally {
			isReconnecting = false;
		}
	}
	/** 监听 pong 响应（更新 socket 可用时间） */
	function setupPongListener() {
		client.socket?.on("pong", () => {
			lastSocketAvailableTime = Date.now();
			logger.debug(`收到 PONG 响应`);
		});
	}
	/** 监听 WebSocket message 事件，收到 disconnect 消息时立即触发重连 */
	function setupMessageListener() {
		client.socket?.on("message", (data) => {
			try {
				const msg = JSON.parse(data);
				if (msg.type === "SYSTEM" && msg.headers?.topic === "disconnect") {
					logger.debug(`收到服务端 disconnect topic，即将重连`);
					if (!isStopped && !isReconnecting) doReconnect(true).catch((err) => {
						logger.error(`[${accountId}] 重连失败：${err.message}`);
					});
				}
			} catch (e) {}
		});
	}
	/** 监听 WebSocket close 事件，服务端主动断开时立即触发重连 */
	function setupCloseListener() {
		client.socket?.on("close", (code, reason) => {
			logger.info(`WebSocket close: code=${code}, reason=${reason || "未知"}, isStopped=${isStopped}`);
			onStatusChange?.({ connected: false });
			if (isStopped) return;
			setTimeout(() => {
				doReconnect(true).catch((err) => {
					logger.error(`重连失败：${err.message}`);
				});
			}, 0);
		});
	}
	/**
	* 启动 keepAlive 机制（单定时器 + 指数退避）
	*
	* 业界最佳实践：
	* - 单定时器：每 10 秒检查一次，同时完成心跳和超时检测
	* - 使用 WebSocket 原生 Ping
	* - 指数退避重连：避免雪崩效应
	*/
	function startKeepAlive() {
		logger.debug(`🚀 启动 keepAlive 定时器，间隔=${HEARTBEAT_INTERVAL / 1e3}秒`);
		keepAliveTimer = setInterval(async () => {
			if (isStopped) {
				if (keepAliveTimer) clearInterval(keepAliveTimer);
				return;
			}
			try {
				const elapsed = Date.now() - lastSocketAvailableTime;
				if (elapsed > TIMEOUT_THRESHOLD) {
					logger.info(`⚠️ 超时检测：已 ${Math.round(elapsed / 1e3)} 秒未确认 socket 可用，触发重连...`);
					await doReconnect();
					return;
				}
				const socketState = client.socket?.readyState;
				const timeSinceConnection = Date.now() - connectionEstablishedTime;
				logger.debug(`心跳检测：socket 状态=${socketState}, elapsed=${Math.round(elapsed / 1e3)}s, 连接已建立=${Math.round(timeSinceConnection / 1e3)}s`);
				if (socketState !== 1) {
					if (timeSinceConnection < 15e3) {
						logger.debug(`⏳ 连接建立中（已 ${Math.round(timeSinceConnection / 1e3)}s），跳过状态检查`);
						return;
					}
					logger.info(`⚠️ 心跳检测：socket 状态=${socketState}，触发重连...`);
					await doReconnect(true);
					return;
				}
				try {
					client.socket?.ping();
					logger.debug(`💓 发送 PING 心跳成功`);
				} catch (err) {
					logger.warn(`发送 PING 失败：${err.message}`);
				}
			} catch (err) {
				logger.error(`keepAlive 检测失败：${err.message}`);
			}
		}, HEARTBEAT_INTERVAL);
		logger.debug(`✅ keepAlive 定时器已启动`);
		return () => {
			if (keepAliveTimer) clearInterval(keepAliveTimer);
			keepAliveTimer = null;
			logger.debug(`keepAlive 定时器已清理`);
		};
	}
	/** 停止并清理所有资源 */
	function stop() {
		isStopped = true;
		if (keepAliveTimer) clearInterval(keepAliveTimer);
		keepAliveTimer = null;
		if (messageProcessingKeepAliveTimer) {
			clearInterval(messageProcessingKeepAliveTimer);
			messageProcessingKeepAliveTimer = null;
		}
		if (client.socket) client.socket.removeAllListeners();
		logger.debug(`Connection 已停止`);
	}
	return new Promise(async (resolve, reject) => {
		if (abortSignal) {
			const onAbort = async () => {
				logger.info(`Abort signal received, stopping...`);
				stop();
				try {
					if (client.socket && client.socket.readyState === 1) await client.disconnect();
				} catch (err) {
					logger.warn(`断开连接时出错：${err.message}`);
				}
				resolve();
			};
			abortSignal.addEventListener("abort", onAbort, { once: true });
		}
		let receivedCount = 0;
		let processedCount = 0;
		let lastMessageTime = Date.now();
		const statsInterval = setInterval(() => {
			const timeSinceLastMessage = Math.round((Date.now() - lastMessageTime) / 1e3);
			logger.info(`统计：收到=${receivedCount}, 处理=${processedCount}, 丢失=${receivedCount - processedCount}, 距上次消息=${timeSinceLastMessage}s`);
		}, 6e4);
		client.registerCallbackListener(TOPIC_ROBOT, async (res) => {
			receivedCount++;
			lastMessageTime = Date.now();
			onStatusChange?.({ lastInboundAt: Date.now() });
			const messageId = res.headers?.messageId;
			const timestamp = (/* @__PURE__ */ new Date()).toISOString();
			logger.info(`\n========== 收到新消息 ==========`);
			logger.info(`时间：${timestamp}`);
			logger.info(`MessageId: ${messageId || "N/A"}`);
			logger.info(`Headers: ${JSON.stringify(res.headers || {})}`);
			logger.info(`Data 长度：${res.data?.length || 0} 字符`);
			if (messageId) {
				client.socketCallBackResponse(messageId, { success: true });
				logger.info(`✅ 已立即确认回调：messageId=${messageId}`);
			} else logger.warn(`⚠️ 警告：消息没有 messageId`);
			if (messageId && checkAndMarkDingtalkMessage(accountId, messageId, void 0)) {
				processedCount++;
				logger.warn(`⚠️ 检测到重复消息（协议层），跳过处理：messageId=${messageId} (${processedCount}/${receivedCount})`);
				logger.info(`========== 消息处理结束（重复） ==========\n`);
				return;
			}
			markMessageProcessingStart();
			try {
				let data;
				try {
					data = JSON.parse(res.data);
				} catch (parseError) {
					logger.error("Failed to parse response data as JSON:", {
						error: parseError instanceof Error ? parseError.message : String(parseError),
						rawData: typeof res.data === "string" ? res.data.substring(0, 500) : res.data,
						dataType: typeof res.data
					});
					throw new Error(`Invalid JSON response from DingTalk API. Error: ${parseError instanceof Error ? parseError.message : String(parseError)}. Raw data (first 100 chars): ${String(res.data).substring(0, 100)}`);
				}
				logger.info(`\n----- 消息详情 -----`);
				logger.info(`消息类型：${data.msgtype || "unknown"}`);
				logger.info(`会话类型：${data.conversationType === "1" ? "DM (单聊)" : data.conversationType === "2" ? "Group (群聊)" : data.conversationType}`);
				logger.info(`发送者：${data.senderNick || "unknown"} (${data.senderStaffId || data.senderId || "unknown"})`);
				logger.info(`会话 ID: ${data.conversationId || "N/A"}`);
				logger.info(`消息 ID: ${data.msgId || "N/A"}`);
				logger.info(`SessionWebhook: ${data.sessionWebhook ? "已提供" : "未提供"}`);
				logger.info(`RobotCode: ${data.robotCode || account.config?.clientId || "N/A"}`);
				if (data.chatbotUserId || data.chatbotCorpId) console.log(`[DingTalk:${accountId}] [BotIdentity] accountId=${accountId} chatbotUserId=${data.chatbotUserId || "N/A"} chatbotCorpId=${data.chatbotCorpId || "N/A"}`);
				data.msgId;
				let contentPreview = "N/A";
				if (data.text?.content) contentPreview = data.text.content.length > 100 ? data.text.content.substring(0, 100) + "..." : data.text.content;
				else if (data.content) contentPreview = JSON.stringify(data.content).substring(0, 100) + "...";
				logger.info(`消息内容预览：${contentPreview}`);
				logger.info(`完整数据字段：${Object.keys(data).join(", ")}`);
				logger.info(`----- 消息详情结束 -----\n`);
				logger.info(`🚀 开始处理消息...`);
				await messageHandler({
					accountId,
					config: account.config,
					data,
					sessionWebhook: data.sessionWebhook,
					runtime,
					log,
					cfg: clawdbotConfig
				});
				processedCount++;
				logger.info(`✅ 消息处理完成 (${processedCount}/${receivedCount})`);
				logger.info(`========== 消息处理结束（成功） ==========\n`);
			} catch (error) {
				processedCount++;
				const errorMsg = `❌ 处理消息异常 (${processedCount}/${receivedCount}): ${error?.message || "未知错误"}`;
				const errorStack = error?.stack || "无堆栈信息";
				logger.error(errorMsg);
				logger.error(`错误堆栈:\n${errorStack}`);
				logger.info(`========== 消息处理结束（失败） ==========\n`);
			} finally {
				markMessageProcessingEnd();
			}
		});
		const cleanup = () => {
			clearInterval(statsInterval);
			stop();
		};
		try {
			await client.connect();
			setupPongListener();
			setupMessageListener();
			setupCloseListener();
			logger.info(`Connected to DingTalk Stream successfully`);
			logger.info(`PID: ${process.pid}`);
			logger.info(`✅ 自定义 keepAlive: true (10 秒心跳，20 秒超时), 指数退避重连`);
			printConnectionNoticeOnce();
			onStatusChange?.({
				connected: true,
				lastConnectedAt: Date.now()
			});
			const cleanupKeepAlive = startKeepAlive();
			const enhancedCleanup = () => {
				cleanupKeepAlive();
				clearInterval(statsInterval);
				stop();
			};
			process.once("exit", enhancedCleanup);
			process.once("SIGINT", enhancedCleanup);
			process.once("SIGTERM", enhancedCleanup);
		} catch (error) {
			cleanup();
			logger.info(`连接失败，错误详情：`);
			logger.info(`  - error.message: ${error.message}`);
			logger.info(`  - error.response?.status: ${error.response?.status}`);
			logger.info(`  - error.response?.data: ${JSON.stringify(error.response?.data || {})}`);
			logger.info(`  - error.code: ${error.code}`);
			logger.info(`  - error.stack: ${error.stack?.split("\n").slice(0, 3).join("\n")}`);
			if (error.response?.status === 400 || error.message?.includes("status code 400") || error.message?.includes("400")) {
				reject(/* @__PURE__ */ new Error(`[DingTalk][${accountId}] Bad Request (400):\n  - clientId or clientSecret format is invalid\n  - clientId: ${clientIdStr} (type: ${typeof account.clientId}, length: ${clientIdStr.length})\n  - clientSecret: ****** (type: ${typeof account.clientSecret}, length: ${clientSecretStr.length})\n  - Common issues:\n    1. clientId/clientSecret must be strings, not numbers\n    2. Remove any quotes or special characters\n    3. Ensure credentials are from the correct DingTalk app\n    4. Check if clientId starts with 'ding' prefix\n  - Error details: ${error.message}\n  - Response data: ${JSON.stringify(error.response?.data || {})}`));
				return;
			}
			if (error.response?.status === 401 || error.message?.includes("401")) {
				reject(/* @__PURE__ */ new Error(`[DingTalk][${accountId}] Authentication failed (401 Unauthorized):\n  - Your clientId or clientSecret is invalid, expired, or revoked\n  - clientId: ${clientIdStr.substring(0, 8)}...\n  - Please verify your credentials at DingTalk Developer Console\n  - Error details: ${error.message}`));
				return;
			}
			reject(/* @__PURE__ */ new Error(`[DingTalk][${accountId}] Failed to connect to DingTalk Stream: ${error.message}`));
			return;
		}
		client.on("error", (err) => {
			logger.error(`Connection error: ${err.message}`);
		});
		client.on("reconnect", () => {
			logger.info(`SDK reconnecting...`);
		});
		client.on("reconnected", () => {
			logger.info(`✅ SDK reconnected successfully`);
		});
	});
}
function resolveReactionSyntheticEvent(event) {
	return null;
}
//#endregion
export { monitorSingleAccount, resolveReactionSyntheticEvent };
