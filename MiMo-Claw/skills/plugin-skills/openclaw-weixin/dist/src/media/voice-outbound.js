import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { logger } from "../util/logger.js";
const execFileAsync = promisify(execFile);
const OGG_CAPTURE = Buffer.from("OggS");
const OPUS_HEAD_MAGIC = Buffer.from("OpusHead");
const GP_UNKNOWN = 0xffffffffffffffffn;
/** Weixin `VoiceItem.encode_type`: 6=silk (README: inbound SILK). */
export const VOICE_ENCODE_SILK = 6;
/** Ogg container (used for Opus-in-Ogg outbound). */
export const VOICE_ENCODE_OGG_SPEEX = 8;
/**
 * Extensions always treated as outbound voice (upload + VOICE item).
 * `.ogg` is handled separately: only when the file is Ogg Opus (see {@link isWeixinVoiceOutboundPath}).
 */
const VOICE_EXTENSIONS = new Set([".opus", ".silk", ".slk"]);
const AUDIO_AS_VOICE_EXTENSIONS = new Set([
    ".aac",
    ".amr",
    ".m4a",
    ".mp3",
    ".oga",
    ".ogg",
    ".opus",
    ".silk",
    ".slk",
    ".wav",
]);
function readUint32LE(buf, o) {
    return buf.readUInt32LE(o);
}
/**
 * Parse one Ogg page starting at `start`. Returns next byte offset after this page, or null if invalid.
 */
function skipOggPage(buf, start) {
    if (start + 27 > buf.length)
        return null;
    if (!buf.subarray(start, start + 4).equals(OGG_CAPTURE))
        return null;
    const nsegs = buf[start + 26];
    if (start + 27 + nsegs > buf.length)
        return null;
    let bodySize = 0;
    for (let i = 0; i < nsegs; i++) {
        bodySize += buf[start + 27 + i];
    }
    const end = start + 27 + nsegs + bodySize;
    if (end > buf.length)
        return null;
    return end;
}
/**
 * First Ogg page whose first packet payload starts with OpusHead defines the Opus logical stream serial.
 */
function findOpusStreamSerial(buf) {
    let off = 0;
    while (off < buf.length) {
        const idx = buf.indexOf(OGG_CAPTURE, off);
        if (idx < 0)
            return null;
        const end = skipOggPage(buf, idx);
        if (end === null) {
            off = idx + 1;
            continue;
        }
        const nsegs = buf[idx + 26];
        const bodyStart = idx + 27 + nsegs;
        const firstSegLen = nsegs > 0 ? buf[idx + 27] : 0;
        if (firstSegLen >= OPUS_HEAD_MAGIC.length &&
            bodyStart + firstSegLen <= buf.length) {
            const payload = buf.subarray(bodyStart, bodyStart + firstSegLen);
            if (payload.subarray(0, OPUS_HEAD_MAGIC.length).equals(OPUS_HEAD_MAGIC)) {
                return readUint32LE(buf, idx + 14);
            }
        }
        off = end;
    }
    return null;
}
function maxGranuleForSerial(buf, targetSerial) {
    let off = 0;
    let maxGp = 0n;
    while (off < buf.length) {
        const idx = buf.indexOf(OGG_CAPTURE, off);
        if (idx < 0)
            break;
        const end = skipOggPage(buf, idx);
        if (end === null) {
            off = idx + 1;
            continue;
        }
        const serial = readUint32LE(buf, idx + 14);
        if (serial === targetSerial) {
            const gp = buf.readBigUInt64LE(idx + 6);
            if (gp !== GP_UNKNOWN && gp > maxGp)
                maxGp = gp;
        }
        off = end;
    }
    return maxGp;
}
/**
 * Opus granule position counts 48 kHz PCM samples (RFC 7845). Duration in ms = gp * 1000 / 48000.
 */
export function playtimeMsFromOpusGranule(maxGp) {
    if (maxGp <= 0n)
        return 0;
    const ms = (maxGp * 1000n) / 48000n;
    return Number(ms);
}
export function parseOggOpusPlaytimeMs(buf) {
    const serial = findOpusStreamSerial(buf);
    if (serial === null)
        return null;
    const maxGp = maxGranuleForSerial(buf, serial);
    if (maxGp <= 0n)
        return null;
    const ms = playtimeMsFromOpusGranule(maxGp);
    return ms > 0 ? ms : null;
}
export function bufferLooksLikeOggOpus(buf) {
    return findOpusStreamSerial(buf) !== null;
}
async function silkPlaytimeMsWithOptionalWasm(buf) {
    try {
        const { decode } = await import("silk-wasm");
        const result = await decode(buf, 24_000);
        const d = result.duration;
        if (typeof d !== "number" || !Number.isFinite(d) || d <= 0)
            return null;
        return Math.round(d);
    }
    catch (err) {
        logger.debug(`voice-outbound: silk-wasm decode unavailable or failed err=${String(err)}`);
        return null;
    }
}
async function ffprobePlaytimeMs(filePath) {
    try {
        const { stdout } = await execFileAsync("ffprobe", [
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filePath,
        ]);
        const seconds = Number.parseFloat(stdout.trim());
        if (!Number.isFinite(seconds) || seconds <= 0)
            return null;
        return Math.round(seconds * 1000);
    }
    catch (err) {
        logger.debug(`voice-outbound: ffprobe duration unavailable err=${String(err)}`);
        return null;
    }
}
const WEIXIN_VOICE_TRANSCODE_SAMPLE_RATE = 48_000;
const WEIXIN_VOICE_TRANSCODE_BITRATE = "64k";
const WEIXIN_VOICE_TRANSCODE_MAX_SECS = 60;
/**
 * Transcode a generic audio file to Ogg/Opus for Weixin voice messages using ffmpeg.
 * Returns the transcoded buffer on success, or null if ffmpeg is unavailable or fails.
 * The caller should check the returned buffer with resolveWeixinOutboundVoiceMeta
 * before uploading; if that also fails, degrade to a file attachment.
 */
export async function transcodeToWeixinVoiceOpus(filePath) {
    const tmpPath = path.join(os.tmpdir(), `weixin-voice-${Date.now()}-${Math.random().toString(36).slice(2)}.ogg`);
    try {
        await execFileAsync("ffmpeg", [
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            filePath,
            "-vn",
            "-sn",
            "-dn",
            "-t",
            String(WEIXIN_VOICE_TRANSCODE_MAX_SECS),
            "-ar",
            String(WEIXIN_VOICE_TRANSCODE_SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "libopus",
            "-b:a",
            WEIXIN_VOICE_TRANSCODE_BITRATE,
            "-f",
            "ogg",
            tmpPath,
        ]);
        return await fs.readFile(tmpPath);
    }
    catch (err) {
        logger.warn(`voice-outbound: transcodeToWeixinVoiceOpus failed filePath=${filePath} err=${String(err)}`);
        return null;
    }
    finally {
        await fs.unlink(tmpPath).catch(() => { });
    }
}
export function isWeixinAudioAsVoiceOutboundPath(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return AUDIO_AS_VOICE_EXTENSIONS.has(ext);
}
export async function isWeixinVoiceOutboundPath(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    if (VOICE_EXTENSIONS.has(ext))
        return true;
    if (ext !== ".ogg")
        return false;
    const head = Buffer.allocUnsafe(65536);
    const fh = await fs.open(filePath, "r");
    try {
        const { bytesRead } = await fh.read(head, 0, head.length, 0);
        if (bytesRead <= 0)
            return false;
        return bufferLooksLikeOggOpus(head.subarray(0, bytesRead));
    }
    finally {
        await fh.close();
    }
}
/**
 * Compute voice playtime (ms) and encoding hints for Weixin VOICE item.
 * Returns null if duration cannot be determined (caller should send as file).
 */
export async function resolveWeixinOutboundVoiceMeta(filePath, opts = {}) {
    const ext = path.extname(filePath).toLowerCase();
    const buf = await fs.readFile(filePath);
    if (ext === ".opus" || ext === ".ogg") {
        const ms = parseOggOpusPlaytimeMs(buf);
        if (ms == null || ms <= 0) {
            logger.warn(`voice-outbound: cannot resolve playtime for ${ext} file — parseOggOpusPlaytimeMs returned ${ms} (not a valid Ogg Opus stream?) filePath=${filePath} size=${buf.length}`);
            return null;
        }
        return {
            playtimeMs: ms,
            encode_type: VOICE_ENCODE_OGG_SPEEX,
            sample_rate: 48_000,
        };
    }
    if (ext === ".silk" || ext === ".slk") {
        const ms = await silkPlaytimeMsWithOptionalWasm(buf);
        if (ms == null || ms <= 0) {
            logger.warn(`voice-outbound: cannot resolve playtime for ${ext} file — silk-wasm decode returned ${ms} (wasm missing, or invalid SILK bitstream?) filePath=${filePath} size=${buf.length}`);
            return null;
        }
        return {
            playtimeMs: ms,
            encode_type: VOICE_ENCODE_SILK,
            sample_rate: 24_000,
        };
    }
    if (opts.allowGenericAudio && AUDIO_AS_VOICE_EXTENSIONS.has(ext)) {
        const ms = await ffprobePlaytimeMs(filePath);
        if (ms == null || ms <= 0) {
            logger.warn(`voice-outbound: cannot resolve playtime for audioAsVoice ${ext} file via ffprobe filePath=${filePath} size=${buf.length}`);
            return null;
        }
        return {
            playtimeMs: ms,
        };
    }
    logger.warn(`voice-outbound: unsupported voice extension '${ext}' for filePath=${filePath}`);
    return null;
}
//# sourceMappingURL=voice-outbound.js.map