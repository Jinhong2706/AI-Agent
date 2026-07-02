import { MessageItemType } from "../api/types.js";
import { downloadMediaFromItem } from "../media/media-download.js";
import { logger } from "../util/logger.js";
const MAX_DEPTH = 5;
function formatTimestamp(ms) {
    if (!ms)
        return "";
    const d = new Date(ms);
    const pad = (n) => String(n).padStart(2, "0");
    const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    const time = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    const tz = new Intl.DateTimeFormat("en", { timeZoneName: "short" })
        .formatToParts(d)
        .find((p) => p.type === "timeZoneName")?.value ?? "";
    return `${date} ${time}${tz ? ` ${tz}` : ""}`;
}
function formatSubItemContent(item) {
    switch (item.type) {
        case MessageItemType.TEXT:
            return item.text_item?.text ?? "";
        case MessageItemType.VOICE:
            if (item.voice_item?.text)
                return item.voice_item.text;
            return undefined;
        case MessageItemType.UNSUPPORTED:
            return item.unsupported_item?.text || "[不支持的消息类型]";
        default:
            return undefined;
    }
}
async function formatMediaContent(item, deps) {
    const downloaded = await downloadMediaFromItem(item, {
        cdnBaseUrl: deps.cdnBaseUrl,
        saveMedia: deps.saveMedia,
        log: deps.log,
        errLog: deps.errLog,
        label: "merged-record",
    });
    const filePath = downloaded.decryptedPicPath ??
        downloaded.decryptedVideoPath ??
        downloaded.decryptedFilePath ??
        downloaded.decryptedVoicePath;
    let text;
    let mediaType;
    switch (item.type) {
        case MessageItemType.IMAGE:
            text = filePath ? `![图片](${filePath})` : "[图片]";
            mediaType = "image/*";
            break;
        case MessageItemType.VIDEO:
            text = filePath ? `[视频](${filePath})` : "[视频]";
            mediaType = "video/mp4";
            break;
        case MessageItemType.FILE: {
            const name = item.file_item?.file_name;
            if (name && filePath)
                text = `[${name}](${filePath})`;
            else if (name)
                text = `[文件: ${name}]`;
            else if (filePath)
                text = `[文件](${filePath})`;
            else
                text = "[文件]";
            mediaType = downloaded.fileMediaType ?? "application/octet-stream";
            break;
        }
        case MessageItemType.VOICE:
            text = filePath ? `[语音](${filePath})` : "[语音]";
            mediaType = downloaded.voiceMediaType ?? "audio/wav";
            break;
        default:
            text = "[不支持的消息]";
            break;
    }
    return { text, mediaPath: filePath, mediaType: filePath ? mediaType : undefined };
}
/**
 * Format a MergedRecordItem into a readable text body with nested structure.
 *
 * Each nesting level is represented by `│ ` prefixes. Media sub-items are
 * downloaded via CDN; the body contains text placeholders (e.g. `[图片]`)
 * while actual file paths are returned in `mediaPaths` / `mediaTypes`
 * for populating `ctx.MediaPaths` / `ctx.MediaTypes`.
 */
export async function formatMergedRecordBody(record, deps, depth = 0) {
    const title = record.title ?? "聊天记录";
    const lines = [`[合并转发: ${title}]`];
    const mediaPaths = [];
    const mediaTypes = [];
    if (depth >= MAX_DEPTH) {
        lines.push("│ [嵌套层级过深，省略]");
        return { body: lines.join("\n"), mediaPaths, mediaTypes };
    }
    for (const sub of record.sub_item_list ?? []) {
        const nick = sub.from_nick_name ?? "未知";
        const item = sub.item;
        if (!item)
            continue;
        const ts = formatTimestamp(item.create_time_ms);
        const header = ts ? `${nick} (${ts}):` : `${nick}:`;
        if (item.type === MessageItemType.MERGED_RECORD && item.merged_record) {
            lines.push(`│ ${header}`);
            const nested = await formatMergedRecordBody(item.merged_record, deps, depth + 1);
            for (const nestedLine of nested.body.split("\n")) {
                lines.push(`│ ${nestedLine}`);
            }
            mediaPaths.push(...nested.mediaPaths);
            mediaTypes.push(...nested.mediaTypes);
        }
        else {
            const syncContent = formatSubItemContent(item);
            if (syncContent !== undefined) {
                lines.push(`│ ${header}`);
                for (const contentLine of syncContent.split("\n")) {
                    lines.push(`│ ${contentLine}`);
                }
            }
            else if (item.type === MessageItemType.IMAGE ||
                item.type === MessageItemType.VIDEO ||
                item.type === MessageItemType.FILE ||
                item.type === MessageItemType.VOICE) {
                try {
                    const media = await formatMediaContent(item, deps);
                    lines.push(`│ ${header}`);
                    lines.push(`│ ${media.text}`);
                    if (media.mediaPath && media.mediaType) {
                        mediaPaths.push(media.mediaPath);
                        mediaTypes.push(media.mediaType);
                    }
                }
                catch (err) {
                    logger.error(`merged-record: media format failed: ${String(err)}`);
                    lines.push(`│ ${header}`);
                    lines.push("│ [媒体加载失败]");
                }
            }
            else {
                lines.push(`│ ${header}`);
                lines.push("│ [不支持的消息]");
            }
        }
        lines.push("│");
    }
    if (lines.length > 1 && lines[lines.length - 1] === "│") {
        lines.pop();
    }
    return { body: lines.join("\n"), mediaPaths, mediaTypes };
}
//# sourceMappingURL=merged-record.js.map