import { t as createLogger } from "./logger-BDWwViGT.mjs";
import { n as dingtalkOapiHttp } from "./http-client-DFWZgO1n.mjs";
import * as fs from "fs";
import * as path from "path";
import FormData from "form-data";
//#region src/services/media/chunk-upload.ts
/**
* 钉钉文件分块上传模块
* 支持大文件（>20MB）的分块上传
* 
* API 文档：
* - 开启事务：https://open.dingtalk.com/document/development/enable-upload-transaction
* - 上传块：https://open.dingtalk.com/document/development/upload-file-blocks
* - 提交事务：https://open.dingtalk.com/document/development/submit-a-file-upload-transaction
*/
const DINGTALK_OAPI = "https://oapi.dingtalk.com";
/** 分块上传配置 */
const CHUNK_CONFIG = {
	MIN_CHUNK_SIZE: 100 * 1024,
	MAX_CHUNK_SIZE: 8 * 1024 * 1024,
	DEFAULT_CHUNK_SIZE: 5 * 1024 * 1024,
	SIZE_THRESHOLD: 20 * 1024 * 1024
};
/**
* 步骤一：开启分块上传事务
* @param oapiToken 钉钉 access_token
* @param fileName 文件名
* @param fileSize 文件大小（字节）
* @param log 日志对象
*/
async function enableUploadTransaction(oapiToken, fileName, fileSize, debug = false) {
	const log = createLogger(debug, "DingTalk][ChunkUpload");
	try {
		log.info(`开启上传事务：${fileName}, 大小：${(fileSize / 1024 / 1024).toFixed(2)}MB`);
		const form = new FormData();
		form.append("file_name", fileName);
		form.append("file_size", fileSize.toString());
		const resp = await dingtalkOapiHttp.post(`${DINGTALK_OAPI}/file/upload/transaction/enable`, form, {
			params: { access_token: oapiToken },
			headers: form.getHeaders(),
			timeout: 6e4
		});
		if (resp.data.errcode === 0) {
			log.info(`事务开启成功，upload_id: ${resp.data.upload_id}`);
			return resp.data.upload_id;
		} else {
			log.error(`开启事务失败：${resp.data.errmsg}`);
			return null;
		}
	} catch (err) {
		log.error(`开启事务异常：${err.message}`);
		console.error(`开启事务异常详情:`, err.response?.data || err);
		return null;
	}
}
/**
* 步骤二：上传文件块
* @param oapiToken 钉钉 access_token
* @param uploadId 上传事务 ID
* @param chunkData 文件块数据
* @param chunkNumber 块编号（从 1 开始）
* @param totalChunks 总块数
* @param log 日志对象
*/
async function uploadFileBlock(oapiToken, uploadId, chunkData, chunkNumber, totalChunks, debug = false) {
	const log = createLogger(debug, "DingTalk][ChunkUpload");
	try {
		log.info(`上传块 ${chunkNumber}/${totalChunks}, 大小：${(chunkData.length / 1024).toFixed(2)}KB`);
		const form = new FormData();
		form.append("upload_id", uploadId);
		form.append("chunk_number", chunkNumber.toString());
		form.append("total_chunks", totalChunks.toString());
		form.append("file", chunkData, {
			filename: `chunk_${chunkNumber}`,
			contentType: "application/octet-stream"
		});
		const resp = await dingtalkOapiHttp.post(`${DINGTALK_OAPI}/file/upload/chunk`, form, {
			params: { access_token: oapiToken },
			headers: form.getHeaders(),
			timeout: 6e4
		});
		if (resp.data.errcode === 0) {
			log.info(`块 ${chunkNumber} 上传成功`);
			return true;
		} else {
			log.error(`块 ${chunkNumber} 上传失败：${resp.data.errmsg}`);
			return false;
		}
	} catch (err) {
		log.error(`块 ${chunkNumber} 上传异常：${err.message}`);
		return false;
	}
}
/**
* 步骤三：提交分块上传事务
* @param oapiToken 钉钉 access_token
* @param uploadId 上传事务 ID
* @param fileName 文件名
* @param log 日志对象
*/
async function submitUploadTransaction(oapiToken, uploadId, fileName, debug = false) {
	const log = createLogger(debug, "DingTalk][ChunkUpload");
	try {
		log.info(`提交上传事务：${uploadId}`);
		const resp = await dingtalkOapiHttp.get(`${DINGTALK_OAPI}/file/upload/transaction/submit`, {
			params: {
				access_token: oapiToken,
				upload_id: uploadId,
				file_name: fileName
			},
			timeout: 6e4
		});
		if (resp.data.errcode === 0) {
			log.info(`事务提交成功，file_id: ${resp.data.file_id}, download_code: ${resp.data.download_code}`);
			return {
				fileId: resp.data.file_id,
				downloadCode: resp.data.download_code
			};
		} else {
			log.error(`事务提交失败：${resp.data.errmsg}`);
			return null;
		}
	} catch (err) {
		log.error(`事务提交异常：${err.message}`);
		return null;
	}
}
/**
* 计算分块参数
*/
function calculateChunkParams(fileSize) {
	let chunkSize = CHUNK_CONFIG.DEFAULT_CHUNK_SIZE;
	if (fileSize > 100 * 1024 * 1024) chunkSize = CHUNK_CONFIG.MAX_CHUNK_SIZE;
	else if (fileSize > 50 * 1024 * 1024) chunkSize = 6 * 1024 * 1024;
	const totalChunks = Math.ceil(fileSize / chunkSize);
	return {
		chunkSize,
		totalChunks
	};
}
/**
* 分块上传大文件（>20MB）
* @param filePath 文件路径
* @param mediaType 媒体类型：video, file
* @param oapiToken 钉钉 access_token
* @param log 日志对象
* @returns download_code 或 null
*/
async function uploadLargeFileByChunks(filePath, mediaType, oapiToken, debug = false) {
	const log = createLogger(debug, "DingTalk][ChunkUpload");
	try {
		const absPath = path.resolve(filePath);
		if (!fs.existsSync(absPath)) {
			log.warn(`文件不存在：${absPath}`);
			return null;
		}
		const fileSize = fs.statSync(absPath).size;
		const fileName = path.basename(absPath);
		const fileSizeMB = (fileSize / 1024 / 1024).toFixed(2);
		log.info(`开始分块上传：${fileName}, 大小：${fileSizeMB}MB, 类型：${mediaType}`);
		const uploadId = await enableUploadTransaction(oapiToken, fileName, fileSize, debug);
		if (!uploadId) {
			log.error(`开启事务失败，终止上传`);
			return null;
		}
		const { chunkSize, totalChunks } = calculateChunkParams(fileSize);
		log.info(`分块参数：chunkSize=${(chunkSize / 1024 / 1024).toFixed(2)}MB, totalChunks=${totalChunks}`);
		const fileBuffer = fs.readFileSync(absPath);
		let successCount = 0;
		for (let i = 0; i < totalChunks; i++) {
			const start = i * chunkSize;
			const end = Math.min(start + chunkSize, fileSize);
			if (!await uploadFileBlock(oapiToken, uploadId, fileBuffer.slice(start, end), i + 1, totalChunks, debug)) {
				log.error(`块 ${i + 1} 上传失败，终止上传`);
				return null;
			}
			successCount++;
			log.info(`进度：${successCount}/${totalChunks} (${(successCount / totalChunks * 100).toFixed(1)}%)`);
		}
		const result = await submitUploadTransaction(oapiToken, uploadId, fileName, debug);
		if (!result || !result.downloadCode) {
			log.error(`提交事务失败`);
			return null;
		}
		log.info(`分块上传完成：${fileName}, download_code: ${result.downloadCode}`);
		return result.downloadCode;
	} catch (err) {
		log.error(`分块上传异常：${err.message}`);
		return null;
	}
}
//#endregion
export { uploadLargeFileByChunks as a, uploadFileBlock as i, enableUploadTransaction as n, submitUploadTransaction as r, CHUNK_CONFIG as t };
