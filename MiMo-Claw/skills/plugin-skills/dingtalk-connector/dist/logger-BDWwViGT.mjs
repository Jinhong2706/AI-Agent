//#region src/utils/logger.ts
/**
* 日志工具模块
* 根据 debug 配置控制日志输出
*/
/**
* 创建日志记录器
* @param debug - 是否启用 debug 模式
* @param prefix - 日志前缀
* @returns 日志记录器对象
*/
function createLogger(debug = false, prefix = "") {
	return {
		info(...args) {
			if (debug) if (prefix) console.log(`[${prefix}]`, ...args);
			else console.log(...args);
		},
		warn(...args) {
			if (prefix) console.warn(`[${prefix}]`, ...args);
			else console.warn(...args);
		},
		error(...args) {
			if (prefix) console.error(`[${prefix}]`, ...args);
			else console.error(...args);
		},
		debug(...args) {
			if (debug) if (prefix) console.log(`[DEBUG][${prefix}]`, ...args);
			else console.log("[DEBUG]", ...args);
		}
	};
}
/**
* 从配置中创建日志记录器
* @param config - 包含 debug 配置的对象（可选）
* @param prefix - 日志前缀
* @returns 日志记录器对象
*/
function createLoggerFromConfig(config, prefix = "") {
	return createLogger(!!config?.debug, prefix);
}
//#endregion
export { createLoggerFromConfig as n, createLogger as t };
