import { t as createLogger } from "./logger-BDWwViGT.mjs";
import { r as dingtalkUploadHttp } from "./http-client-DFWZgO1n.mjs";
import { t as CHUNK_CONFIG } from "./chunk-upload-6p9cf3UB.mjs";
import * as fs from "fs";
import * as path from "path";
import FormData from "form-data";
//#region src/services/media/common.ts
/**
* 媒体处理公共工具和常量
*/
/** 本地图片路径正则表达式（跨平台） */
const LOCAL_IMAGE_RE = /!\[([^\]]*)\]\(((?:file:\/\/|MEDIA:|attachment:\/\/)[^)]+|\/(?:tmp|var|private|Users|home|root)[^)]+|[A-Za-z]:[\\/][^)]+)\)/g;
/** 视频标记正则表达式 */
const VIDEO_MARKER_PATTERN = /\[DINGTALK_VIDEO\](.*?)\[\/DINGTALK_VIDEO\]/gs;
/** 音频标记正则表达式 */
const AUDIO_MARKER_PATTERN = /\[DINGTALK_AUDIO\](.*?)\[\/DINGTALK_AUDIO\]/gs;
/** 文件标记正则表达式 */
const FILE_MARKER_PATTERN = /\[DINGTALK_FILE\](.*?)\[\/DINGTALK_FILE\]/gs;
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
/**
* 谨慎使用，返回的是cleanMediaId
* 后续逐步删除，可用 media.ts
*/
async function uploadMediaToDingTalk(filePath, mediaType, oapiToken, maxSize = 20 * 1024 * 1024, logOrDebug, debug) {
	const debugEnabled = typeof logOrDebug === "boolean" ? logOrDebug === true : debug === true;
	const log = (typeof logOrDebug === "boolean" ? void 0 : logOrDebug) ?? createLogger(debugEnabled, `DingTalk][${mediaType}`);
	log?.info?.(`[uploadMediaToDingTalk] 开始上传，filePath: ${filePath}, mediaType: ${mediaType}, debug: ${debugEnabled}`);
	try {
		const absPath = toLocalPath(filePath);
		log?.info?.(`检查文件是否存在：${absPath}`);
		if (!fs.existsSync(absPath)) {
			log?.warn?.(`文件不存在：${absPath}`);
			return null;
		}
		const stats = fs.statSync(absPath);
		const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
		const fileSize = stats.size;
		if ((mediaType === "video" || mediaType === "file") && fileSize > CHUNK_CONFIG.SIZE_THRESHOLD) {
			log?.info?.(`文件超过 20MB，使用分块上传：${absPath} (${fileSizeMB}MB)`);
			try {
				const { uploadLargeFileByChunks } = await import("./chunk-upload-p9PQRr1H.mjs");
				const downloadCode = await uploadLargeFileByChunks(absPath, mediaType, oapiToken, debugEnabled);
				if (downloadCode) {
					log?.info?.(`分块上传成功：${absPath}, download_code: ${downloadCode}`);
					return downloadCode;
				}
				log?.error?.(`分块上传失败：${absPath}`);
			} catch (chunkErr) {
				log?.error?.(`分块上传异常：${chunkErr.message}`);
			}
			return null;
		}
		if (stats.size > maxSize) {
			const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0);
			log?.warn?.(`文件过大：${absPath}, 大小：${fileSizeMB}MB, 超过限制 ${maxSizeMB}MB`);
			return null;
		}
		const form = new FormData();
		form.append("media", fs.createReadStream(absPath), {
			filename: path.basename(absPath),
			contentType: mediaType === "image" ? "image/jpeg" : "application/octet-stream"
		});
		const uploadType = mediaType;
		log?.info?.(`上传文件：${absPath} (${fileSizeMB}MB), uploadType=${uploadType}`);
		const mediaId = (await dingtalkUploadHttp.post(`${DINGTALK_OAPI}/media/upload`, form, {
			params: {
				access_token: oapiToken,
				type: mediaType
			},
			headers: form.getHeaders(),
			timeout: 6e4,
			maxBodyLength: Infinity
		})).data?.media_id;
		if (mediaId) {
			const cleanMediaId = mediaId.startsWith("@") ? mediaId.substring(1) : mediaId;
			log?.info?.(`上传成功：mediaId=${cleanMediaId}`);
			return cleanMediaId;
		}
		log?.warn?.(`上传返回无 media_id`);
		return null;
	} catch (err) {
		log?.error?.(`上传失败：${err.message}`);
		return null;
	}
}
/** 钉钉 OAPI 常量 */
const DINGTALK_OAPI = "https://oapi.dingtalk.com";
//#endregion
export { VIDEO_MARKER_PATTERN as a, LOCAL_IMAGE_RE as i, DINGTALK_OAPI as n, toLocalPath as o, FILE_MARKER_PATTERN as r, uploadMediaToDingTalk as s, AUDIO_MARKER_PATTERN as t };
