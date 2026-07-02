import { n as dingtalkOapiHttp, t as dingtalkHttp } from "./http-client-DFWZgO1n.mjs";
import { a as DINGTALK_OAPI } from "./utils-DgNm1Ek_.mjs";
import { createRequire } from "node:module";
import * as fs from "fs";
import * as path from "path";
import FormData from "form-data";
//#region \0rolldown/runtime.js
var __defProp = Object.defineProperty;
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
var __require = /* @__PURE__ */ createRequire(import.meta.url);
//#endregion
//#region src/services/media.ts
/**
* 钉钉媒体处理
* 支持图片、视频、音频、文件的上传和下载
*/
/** 视频标记正则表达式 */
const VIDEO_MARKER_PATTERN = /\[DINGTALK_VIDEO\](.*?)\[\/DINGTALK_VIDEO\]/gs;
/**
* 去掉 file:// / MEDIA: / attachment:// 前缀，得到实际的绝对路径
*/
function toLocalPath(raw) {
	let filePath = raw;
	if (filePath.startsWith("file://")) filePath = filePath.replace("file://", "");
	else if (filePath.startsWith("MEDIA:")) filePath = filePath.replace("MEDIA:", "");
	else if (filePath.startsWith("attachment://")) filePath = filePath.replace("attachment://", "");
	try {
		filePath = decodeURIComponent(filePath);
	} catch {}
	return filePath;
}
async function uploadMediaToDingTalk(filePath, mediaType, oapiToken, maxSize = 20 * 1024 * 1024, log) {
	try {
		const absPath = toLocalPath(filePath);
		log?.info?.(`开始上传，文件路径：${absPath}`);
		if (!fs.existsSync(absPath)) {
			log?.warn?.(`文件不存在：${absPath}`);
			return null;
		}
		const stats = fs.statSync(absPath);
		const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
		stats.size;
		log?.info?.(`文件大小：${fileSizeMB}MB`);
		if (stats.size > maxSize) {
			const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0);
			log?.warn?.(`文件过大：${absPath}, 大小：${fileSizeMB}MB, 超过限制 ${maxSizeMB}MB`);
			return null;
		}
		const getContentType = () => {
			const ext = path.extname(absPath).toLowerCase();
			if (mediaType === "image") return ext === ".png" ? "image/png" : "image/jpeg";
			else if (mediaType === "video") return ext === ".mp4" ? "video/mp4" : "video/quicktime";
			else if (mediaType === "voice") return ext === ".mp3" ? "audio/mpeg" : "audio/amr";
			else return "application/octet-stream";
		};
		const form = new FormData();
		form.append("media", fs.createReadStream(absPath), {
			filename: path.basename(absPath),
			contentType: getContentType()
		});
		log?.info?.(`上传文件: ${absPath} (${fileSizeMB}MB)`);
		const resp = await dingtalkOapiHttp.post(`${DINGTALK_OAPI}/media/upload?access_token=${oapiToken}&type=${mediaType === "video" ? "file" : mediaType}`, form, {
			headers: form.getHeaders(),
			timeout: 6e4
		});
		const mediaId = resp.data?.media_id;
		if (mediaId) {
			const cleanMediaId = mediaId.startsWith("@") ? mediaId.substring(1) : mediaId;
			const downloadUrl = `https://down.dingtalk.com/media/${cleanMediaId}`;
			log?.info?.(`上传成功: media_id=${mediaId}, cleanMediaId=${cleanMediaId}, downloadUrl=${downloadUrl}`);
			return {
				mediaId,
				cleanMediaId,
				downloadUrl
			};
		}
		log?.warn?.(`上传返回无 media_id: ${JSON.stringify(resp.data)}`);
		return null;
	} catch (err) {
		log?.error?.(`上传失败: ${err.message}`);
		return null;
	}
}
/**
* 提取视频元数据（时长、分辨率）
*/
async function extractVideoMetadata(filePath, log) {
	try {
		const ffmpeg = __require("fluent-ffmpeg");
		const ffmpegPath = __require("@ffmpeg-installer/ffmpeg").path;
		const ffprobePath = __require("@ffprobe-installer/ffprobe").path;
		ffmpeg.setFfmpegPath(ffmpegPath);
		ffmpeg.setFfprobePath(ffprobePath);
		return new Promise((resolve) => {
			ffmpeg.ffprobe(filePath, (err, metadata) => {
				if (err) {
					log?.warn?.(`ffprobe 执行失败: ${err.message}`);
					resolve(null);
					return;
				}
				try {
					const duration = metadata.format?.duration ? Math.round(parseFloat(metadata.format.duration) * 1e3) : 0;
					const videoStream = metadata.streams?.find((s) => s.codec_type === "video");
					resolve({
						duration,
						width: videoStream?.width || 0,
						height: videoStream?.height || 0
					});
				} catch (err) {
					log?.warn?.(`解析 ffprobe 输出失败`);
					resolve(null);
				}
			});
		});
	} catch (err) {
		log?.warn?.(`提取视频元数据失败: ${err.message}`);
		return null;
	}
}
/**
* 生成视频封面图（第1秒截图）
*/
async function extractVideoThumbnail(videoPath, outputPath, log) {
	try {
		const ffmpeg = __require("fluent-ffmpeg");
		const ffmpegPath = __require("@ffmpeg-installer/ffmpeg").path;
		const path = await import("path");
		ffmpeg.setFfmpegPath(ffmpegPath);
		return new Promise((resolve) => {
			ffmpeg(videoPath).screenshots({
				count: 1,
				folder: path.dirname(outputPath),
				filename: path.basename(outputPath),
				timemarks: ["1"],
				size: "?x360"
			}).on("end", () => {
				log?.info?.(`封面生成成功: ${outputPath}`);
				resolve(outputPath);
			}).on("error", (err) => {
				log?.error?.(`封面生成失败: ${err.message}`);
				resolve(null);
			});
		});
	} catch (err) {
		log?.error?.(`ffmpeg 失败: ${err.message}`);
		return null;
	}
}
/**
* 提取视频标记并发送视频消息
*/
async function processVideoMarkers(content, sessionWebhook, config, oapiToken, log, useProactiveApi = false, target) {
	const logPrefix = useProactiveApi ? "Video[Proactive]" : "Video";
	if (!oapiToken) {
		log?.warn?.(`${logPrefix} 无 oapiToken，跳过视频处理`);
		return content;
	}
	const matches = [...content.matchAll(VIDEO_MARKER_PATTERN)];
	const videoInfos = [];
	const invalidVideos = [];
	const os = await import("os");
	for (const match of matches) try {
		const videoInfo = JSON.parse(match[1]);
		if (videoInfo.path && fs.existsSync(videoInfo.path)) {
			videoInfos.push(videoInfo);
			log?.info?.(`${logPrefix} 提取到视频: ${videoInfo.path}`);
		} else {
			invalidVideos.push(videoInfo.path || "未知路径");
			log?.warn?.(`${logPrefix} 视频文件不存在: ${videoInfo.path}`);
		}
	} catch (err) {
		log?.warn?.(`${logPrefix} 解析标记失败: ${err.message}`);
	}
	if (videoInfos.length === 0 && invalidVideos.length === 0) {
		log?.info?.(`${logPrefix} 未检测到视频标记`);
		return content.replace(VIDEO_MARKER_PATTERN, "").trim();
	}
	let cleanedContent = content.replace(VIDEO_MARKER_PATTERN, "").trim();
	const statusMessages = [];
	for (const invalidPath of invalidVideos) statusMessages.push(`⚠️ 视频文件不存在: ${path.basename(invalidPath)}`);
	if (videoInfos.length > 0) log?.info?.(`${logPrefix} 检测到 ${videoInfos.length} 个视频，开始处理...`);
	for (const videoInfo of videoInfos) {
		const fileName = path.basename(videoInfo.path);
		let thumbnailPath = "";
		try {
			const metadata = await extractVideoMetadata(videoInfo.path, log);
			if (!metadata) {
				log?.warn?.(`${logPrefix} 无法提取元数据: ${videoInfo.path}`);
				statusMessages.push(`⚠️ 视频处理失败: ${fileName}（无法读取视频信息）`);
				continue;
			}
			thumbnailPath = path.join(os.tmpdir(), `thumbnail_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.jpg`);
			log?.info?.(`${logPrefix} 准备生成封面: ${thumbnailPath}`);
			if (!await extractVideoThumbnail(videoInfo.path, thumbnailPath, log)) {
				log?.warn?.(`${logPrefix} 无法生成封面: ${videoInfo.path}`);
				statusMessages.push(`⚠️ 视频处理失败: ${fileName}（无法生成封面）`);
				continue;
			}
			if (fs.existsSync(thumbnailPath)) {
				const stats = fs.statSync(thumbnailPath);
				log?.info?.(`${logPrefix} 封面文件生成完成: ${thumbnailPath}, 大小: ${(stats.size / 1024).toFixed(2)}KB`);
				if (stats.size < 1024) log?.warn?.(`${logPrefix} 封面文件过小，可能存在质量问题`);
			} else {
				log?.error?.(`${logPrefix} 封面文件未生成: ${thumbnailPath}`);
				statusMessages.push(`⚠️ 视频处理失败: ${fileName}（封面文件未生成）`);
				continue;
			}
			const videoUploadResult = await uploadMediaToDingTalk(videoInfo.path, "video", oapiToken, 20 * 1024 * 1024, log);
			if (!videoUploadResult) {
				log?.warn?.(`${logPrefix} 视频上传失败: ${videoInfo.path}`);
				statusMessages.push(`⚠️ 视频上传失败: ${fileName}（文件可能超过 20MB 限制）`);
				continue;
			}
			const videoMediaId = videoUploadResult.mediaId;
			const picUploadResult = await uploadMediaToDingTalk(thumbnailPath, "image", oapiToken, 20 * 1024 * 1024, log);
			if (!picUploadResult) {
				log?.warn?.(`${logPrefix} 封面上传失败: ${thumbnailPath}`);
				statusMessages.push(`⚠️ 视频封面上传失败: ${fileName}`);
				continue;
			}
			const picMediaId = picUploadResult.mediaId;
			if (useProactiveApi && target) await sendVideoProactive(config, target, videoMediaId, picMediaId, metadata, log);
			else await sendVideoMessage(config, sessionWebhook, fileName, videoUploadResult.downloadUrl, log, metadata);
			statusMessages.push(`✅ 视频已发送: ${fileName}`);
			log?.info?.(`${logPrefix} 视频处理完成: ${fileName}`);
		} catch (err) {
			log?.error?.(`${logPrefix} 处理视频失败: ${err.message}`);
			statusMessages.push(`⚠️ 视频处理异常: ${fileName}（${err.message}）`);
		} finally {
			if (thumbnailPath && fs.existsSync(thumbnailPath)) try {
				fs.unlinkSync(thumbnailPath);
				log?.info?.(`${logPrefix} 临时封面已清理: ${thumbnailPath}`);
			} catch (cleanupErr) {
				log?.warn?.(`${logPrefix} 清理临时文件失败: ${cleanupErr?.message || cleanupErr}`);
			}
		}
	}
	if (statusMessages.length > 0) {
		const statusText = statusMessages.join("\n");
		cleanedContent = cleanedContent ? `${cleanedContent}\n\n${statusText}` : statusText;
	}
	return cleanedContent;
}
/**
* 提取音频时长
*
* 使用 fluent-ffmpeg 的 ffprobe API，与 extractVideoMetadata 保持一致，
* 完全避免直接调用 child_process，消除安全扫描误报。
*/
async function extractAudioDuration(filePath, log) {
	try {
		const ffmpeg = __require("fluent-ffmpeg");
		try {
			const ffprobeInstaller = __require("@ffprobe-installer/ffprobe");
			if (ffprobeInstaller?.path) ffmpeg.setFfprobePath(ffprobeInstaller.path);
		} catch {}
		return new Promise((resolve) => {
			ffmpeg.ffprobe(filePath, (err, metadata) => {
				if (err) {
					log?.warn?.(`ffprobe 执行失败: ${err.message}`);
					resolve(null);
					return;
				}
				try {
					resolve(metadata.format?.duration ? Math.round(parseFloat(metadata.format.duration) * 1e3) : 0);
				} catch (parseErr) {
					log?.warn?.(`解析 ffprobe 输出失败`);
					resolve(null);
				}
			});
		});
	} catch (err) {
		log?.warn?.(`提取音频时长失败: ${err.message}`);
		return null;
	}
}
/**
* 发送视频消息（sessionWebhook 模式）
*/
async function sendVideoMessage(config, sessionWebhook, fileName, mediaId, log, metadata) {
	try {
		const token = await (await import("./utils-TpPdfqWr.mjs")).getAccessToken(config);
		const videoMessage = {
			msgtype: "video",
			video: {
				mediaId,
				duration: metadata?.duration.toString() || "60000",
				type: "mp4"
			}
		};
		log?.info?.(`发送视频消息: ${fileName}`);
		const resp = await dingtalkHttp.post(sessionWebhook, videoMessage, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 1e4
		});
		if (resp.data?.success !== false) log?.info?.(`视频消息发送成功: ${fileName}`);
		else log?.error?.(`视频消息发送失败: ${JSON.stringify(resp.data)}`);
	} catch (err) {
		log?.error?.(`发送视频消息异常: ${fileName}, 错误: ${err.message}`);
	}
}
/**
* 发送视频消息（主动 API 模式）
*/
async function sendVideoProactive(config, target, videoMediaId, picMediaId, metadata, log) {
	try {
		const token = await (await import("./utils-TpPdfqWr.mjs")).getAccessToken(config);
		const { DINGTALK_API } = await import("./utils-TpPdfqWr.mjs");
		const msgParam = {
			duration: metadata?.duration.toString() || "60000",
			videoMediaId,
			videoType: "mp4",
			picMediaId: picMediaId || ""
		};
		const body = {
			robotCode: String(config.clientId),
			msgKey: "sampleVideo",
			msgParam: JSON.stringify(msgParam)
		};
		let endpoint;
		if (target.type === "group") {
			body.openConversationId = target.openConversationId;
			endpoint = `${DINGTALK_API}/v1.0/robot/groupMessages/send`;
		} else {
			body.userIds = [target.userId];
			endpoint = `${DINGTALK_API}/v1.0/robot/oToMessages/batchSend`;
		}
		log?.info?.(`Video[Proactive] 发送视频消息`);
		log?.info?.(`Video[Proactive] 请求体: ${JSON.stringify(body, null, 2)}`);
		log?.info?.(`Video[Proactive] endpoint: ${endpoint}`);
		const resp = await dingtalkHttp.post(endpoint, body, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 1e4
		});
		log?.info?.(`Video[Proactive] 钉钉 API 响应: ${JSON.stringify(resp.data, null, 2)}`);
		if (resp.data?.processQueryKey) log?.info?.(`Video[Proactive] 视频消息发送成功`);
		else {
			log?.error?.(`Video[Proactive] 视频消息发送失败: ${JSON.stringify(resp.data)}`);
			throw new Error(`视频消息发送失败: ${JSON.stringify(resp.data)}`);
		}
	} catch (err) {
		log?.error?.(`Video[Proactive] 发送视频消息失败, 错误: ${err.message}`);
	}
}
/**
* 发送音频消息（主动 API 模式）
*/
async function sendAudioProactive(config, target, fileName, mediaId, log, durationMs) {
	try {
		const token = await (await import("./utils-TpPdfqWr.mjs")).getAccessToken(config);
		const { DINGTALK_API } = await import("./utils-TpPdfqWr.mjs");
		const msgParam = {
			mediaId,
			duration: durationMs && durationMs > 0 ? durationMs.toString() : "60000"
		};
		const body = {
			robotCode: String(config.clientId),
			msgKey: "sampleAudio",
			msgParam: JSON.stringify(msgParam)
		};
		let endpoint;
		if (target.type === "group") {
			body.openConversationId = target.openConversationId;
			endpoint = `${DINGTALK_API}/v1.0/robot/groupMessages/send`;
		} else {
			body.userIds = [target.userId];
			endpoint = `${DINGTALK_API}/v1.0/robot/oToMessages/batchSend`;
		}
		log?.info?.(`Audio[Proactive] 发送音频消息: ${fileName}`);
		const resp = await dingtalkHttp.post(endpoint, body, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 1e4
		});
		if (resp.data?.processQueryKey) log?.info?.(`Audio[Proactive] 音频消息发送成功: ${fileName}`);
		else log?.warn?.(`Audio[Proactive] 音频消息发送响应异常: ${JSON.stringify(resp.data)}`);
	} catch (err) {
		log?.error?.(`Audio[Proactive] 发送音频消息失败: ${fileName}, 错误: ${err.message}`);
	}
}
/**
* 发送文件消息（主动 API 模式）
*/
async function sendFileProactive(config, target, fileInfo, mediaId, log) {
	try {
		const token = await (await import("./utils-TpPdfqWr.mjs")).getAccessToken(config);
		const { DINGTALK_API } = await import("./utils-TpPdfqWr.mjs");
		const resolvedFileName = fileInfo.fileName || path.basename(fileInfo.path);
		const msgParam = {
			mediaId,
			fileName: resolvedFileName,
			fileType: fileInfo.fileType || resolvedFileName.split(".").pop() || "file"
		};
		const body = {
			robotCode: String(config.clientId),
			msgKey: "sampleFile",
			msgParam: JSON.stringify(msgParam)
		};
		let endpoint;
		if (target.type === "group") {
			body.openConversationId = target.openConversationId;
			endpoint = `${DINGTALK_API}/v1.0/robot/groupMessages/send`;
		} else {
			body.userIds = [target.userId];
			endpoint = `${DINGTALK_API}/v1.0/robot/oToMessages/batchSend`;
		}
		log?.info?.(`File[Proactive] 发送文件消息: ${fileInfo.fileName}`);
		const resp = await dingtalkHttp.post(endpoint, body, {
			headers: {
				"x-acs-dingtalk-access-token": token,
				"Content-Type": "application/json"
			},
			timeout: 1e4
		});
		if (resp.data?.processQueryKey) log?.info?.(`File[Proactive] 发送成功: processQueryKey=${resp.data.processQueryKey}`);
		else log?.warn?.(`File[Proactive] 发送失败: ${JSON.stringify(resp.data)}`);
	} catch (err) {
		log?.error?.(`File[Proactive] 发送文件消息失败: ${fileInfo.fileName}, 错误: ${err.message}`);
		throw err;
	}
}
async function processRawMediaPaths(content, config, oapiToken, log, target) {
	const logPrefix = "RawMedia";
	const matches = Array.from(content.matchAll(/(?:^|\s)((?:[A-Za-z]:)?[\/\\](?:[^\/\\:\*\?"<>\|\s]+[\/\\])*[^\/\\:\*\?"<>\|\s]+\.(?:mp4|avi|mov|wmv|flv|mkv|webm|mp3|wav|flac|aac|ogg|m4a|wma|pdf|doc|docx|xls|xlsx|ppt|pptx|txt|zip|rar|7z|tar|gz))(?:\s|$)/gi));
	if (matches.length === 0) return content;
	log?.info?.(`${logPrefix} 检测到 ${matches.length} 个裸露的本地文件路径`);
	let processedContent = content;
	const statusMessages = [];
	for (const match of matches) {
		const fullMatch = match[0];
		const filePath = match[1].trim();
		try {
			log?.info?.(`${logPrefix} 开始处理文件: ${filePath}`);
			const ext = filePath.toLowerCase().split(".").pop() || "";
			let mediaType;
			if ([
				"mp4",
				"avi",
				"mov",
				"wmv",
				"flv",
				"mkv",
				"webm"
			].includes(ext)) mediaType = "video";
			else if ([
				"mp3",
				"wav",
				"flac",
				"aac",
				"ogg",
				"m4a",
				"wma"
			].includes(ext)) mediaType = "voice";
			else mediaType = "file";
			const uploadResult = await uploadMediaToDingTalk(filePath, mediaType, oapiToken, 20 * 1024 * 1024, log);
			if (!uploadResult) {
				log?.error?.(`${logPrefix} 文件上传失败: ${filePath}`);
				statusMessages.push(`⚠️ 文件上传失败: ${filePath}`);
				continue;
			}
			const fileName = filePath.split(/[\/\\]/).pop() || "unknown";
			if (mediaType === "video") {
				const metadata = await extractVideoMetadata(filePath, log);
				if (target) await sendVideoProactive(config, target, uploadResult.mediaId, fileName, log, metadata);
				statusMessages.push(`✅ 视频已发送: ${fileName}`);
			} else if (mediaType === "voice") {
				const durationMs = await extractAudioDuration(filePath, log);
				if (target) await sendAudioProactive(config, target, fileName, uploadResult.downloadUrl, log, durationMs ?? void 0);
				statusMessages.push(`✅ 音频已发送: ${fileName}`);
			} else {
				const fileInfo = {
					path: filePath,
					fileName,
					fileType: ext
				};
				if (target) await sendFileProactive(config, target, fileInfo, uploadResult.mediaId, log);
				statusMessages.push(`✅ 文件已发送: ${fileName}`);
			}
			processedContent = processedContent.replace(fullMatch, fullMatch.replace(filePath, ""));
			log?.info?.(`${logPrefix} 文件处理完成: ${fileName}`);
		} catch (err) {
			log?.error?.(`${logPrefix} 处理文件失败: ${filePath}, 错误: ${err.message}`);
			statusMessages.push(`⚠️ 处理失败: ${filePath}`);
		}
	}
	if (statusMessages.length > 0) {
		const statusText = "\n\n" + statusMessages.join("\n");
		processedContent = processedContent.trim() + statusText;
	}
	return processedContent;
}
//#endregion
export { processVideoMarkers as a, sendVideoProactive as c, __exportAll as d, processRawMediaPaths as i, toLocalPath as l, extractVideoMetadata as n, sendAudioProactive as o, extractVideoThumbnail as r, sendFileProactive as s, VIDEO_MARKER_PATTERN as t, uploadMediaToDingTalk as u };
