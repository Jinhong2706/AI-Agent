import crypto from "node:crypto";
import { StreamAction, StreamType } from "../api/types.js";
import { sendStreamSignalWeixin } from "../messaging/send.js";
import { logger } from "../util/logger.js";
import { WeixinStreamSender } from "./stream.js";
const DEFAULT_THROTTLE_MS = 1000;
const DEFAULT_MIN_INITIAL_CHARS = 10;
const DEFAULT_MAX_PIECE_BYTES = 16 * 1024;
function unicodeLength(str) {
    let n = 0;
    for (const _ of str)
        n++;
    return n;
}
function unicodeSlice(str, start, end) {
    let result = "";
    let i = 0;
    for (const ch of str) {
        if (i >= end)
            break;
        if (i >= start)
            result += ch;
        i++;
    }
    return result;
}
function escapeNewlines(text) {
    return text.includes("\n") ? text.replaceAll("\n", "\\n") : text;
}
function splitUtf8Chunks(encoded, maxBytes) {
    if (encoded.length <= maxBytes)
        return [encoded.toString("utf-8")];
    const result = [];
    let offset = 0;
    while (offset < encoded.length) {
        let end = Math.min(offset + maxBytes, encoded.length);
        if (end < encoded.length) {
            while (end > offset && (encoded[end] & 0xC0) === 0x80)
                end--;
            if (end === offset) {
                end = offset + maxBytes;
                while (end < encoded.length && (encoded[end] & 0xC0) === 0x80)
                    end++;
            }
        }
        result.push(encoded.subarray(offset, end).toString("utf-8"));
        offset = end;
    }
    return result;
}
export class StreamPipeline {
    // -- config --
    opts;
    throttleMs;
    minInitialChars;
    maxPieceBytes;
    log;
    // -- phase state (single variable) --
    phase = "idle";
    msgStreamId;
    stream;
    _resultStreamId;
    // True once any streaming phase (thinking or result) has actually been started.
    _hadStreaming = false;
    // Set to true when initStream fails for a given phase.  Once set, the
    // pipeline stops attempting to open new streams for that phase so subsequent
    // pieces are silently dropped.  Thinking and result are tracked independently.
    thinkingInitFailed = false;
    resultInitFailed = false;
    // True while we have buffered result text but haven't yet successfully started
    // the result phase.  Used to preserve text across startPhase("result") failures
    // so subsequent result cmds append instead of overwrite.
    resultStartPending = false;
    // -- text buffer + throttle --
    textBuf = "";
    lastSendAt = 0;
    // -- serial queue --
    queue = [];
    running = false;
    aborted = false;
    wakeResolve;
    drainResolvers = [];
    constructor(opts) {
        this.opts = opts;
        this.throttleMs = opts.throttleMs ?? DEFAULT_THROTTLE_MS;
        this.minInitialChars = opts.minInitialChars ?? DEFAULT_MIN_INITIAL_CHARS;
        this.maxPieceBytes = opts.maxPieceBytes ?? DEFAULT_MAX_PIECE_BYTES;
        this.log = opts.log ?? logger;
        this.msgStreamId = `${opts.accountId}:${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
        this._resultStreamId = this.msgStreamId;
    }
    /** Push a command.  Starts the run loop if it isn't already running. */
    push(cmd) {
        if (this.aborted)
            return;
        this.queue.push(cmd);
        if (cmd.kind !== "thinking" && cmd.kind !== "result") {
            this.wakeResolve?.();
        }
        if (!this.running) {
            this.running = true;
            void this.run();
        }
    }
    /** Wait until the queue is fully drained and the run loop exits. */
    async drain() {
        if (!this.running && this.queue.length === 0)
            return;
        return new Promise((resolve) => this.drainResolvers.push(resolve));
    }
    /** Immediately cancel all pending work and abort active streams. */
    async abort(errorMsg) {
        this.aborted = true;
        this.queue.length = 0;
        this.textBuf = "";
        this.wakeResolve?.();
        const stream = this.stream;
        this.stream = undefined;
        if (stream && !stream.isEnded) {
            try {
                await stream.abort(errorMsg);
            }
            catch (err) {
                this.log.warn(`pipeline: abort failed err=${String(err)}`);
            }
        }
        for (const r of this.drainResolvers)
            r();
        this.drainResolvers = [];
    }
    get resultStreamId() {
        return this._resultStreamId;
    }
    /** True once any streaming phase (thinking or result) has actually been started. */
    get hadStreaming() {
        return this._hadStreaming;
    }
    // ======================================================================
    // Run loop — the single serial executor
    // ======================================================================
    async run() {
        try {
            while (true) {
                while (this.queue.length > 0 && !this.aborted) {
                    await this.process(this.queue.shift());
                }
                if (this.textBuf && !this.aborted && this.phase !== "idle") {
                    const wait = this.throttleMs - (Date.now() - this.lastSendAt);
                    if (wait > 0) {
                        await this.sleep(wait);
                        this.coalesceQueuedText();
                    }
                    if (this.textBuf && !this.aborted) {
                        try {
                            await this.flushText();
                        }
                        catch (err) {
                            this.log.warn(`pipeline: throttle flush failed: ${String(err)}`);
                        }
                    }
                    continue;
                }
                break;
            }
        }
        catch (err) {
            this.log.warn(`pipeline: run loop error: ${String(err)}`);
        }
        finally {
            this.running = false;
            for (const r of this.drainResolvers)
                r();
            this.drainResolvers = [];
        }
    }
    // ======================================================================
    // Command processing — all logic in one switch
    // ======================================================================
    async process(cmd) {
        try {
            switch (cmd.kind) {
                case "thinking":
                    this.textBuf += cmd.text;
                    this.coalesceQueuedTextOfKind("thinking");
                    if (this.phase === "idle") {
                        if (unicodeLength(this.textBuf) < this.minInitialChars)
                            return;
                        await this.startPhase("thinking");
                    }
                    await this.throttledFlush();
                    break;
                case "thinking_refresh":
                    this.textBuf = cmd.text;
                    if (this.phase === "thinking" && this.stream && !this.stream.isEnded) {
                        this.log.debug(`STREAM THINKING REWIND ${escapeNewlines(cmd.text)}`);
                        await this.stream.sendPiece({ type: "text", text: cmd.text, rewind: true, stream_type: "thinking" });
                        this.lastSendAt = Date.now();
                        this.textBuf = "";
                    }
                    break;
                case "tool_call":
                    if (this.phase === "idle")
                        await this.startPhase("thinking");
                    await this.flushText();
                    if (this.stream && !this.stream.isEnded) {
                        this.log.debug(`STREAM THINKING TOOL ${JSON.stringify({ name: cmd.name, phase: cmd.phase })}`);
                        await this.stream.sendPiece({
                            type: "tool_calling",
                            name: cmd.name,
                            phase: cmd.phase,
                            stream_type: "thinking",
                        });
                    }
                    break;
                case "result": {
                    let resultText = cmd.text;
                    while (this.queue.length > 0 && this.queue[0].kind === "result") {
                        resultText += this.queue.shift().text;
                    }
                    if (this.phase !== "result") {
                        await this.endCurrentPhase();
                        const isResultStartRetry = this.resultStartPending;
                        if (isResultStartRetry) {
                            // A previous attempt to start the result phase failed (or was below
                            // minInitialChars): preserve the pending text so it isn't lost.
                            this.textBuf += resultText;
                        }
                        else {
                            // First transition into result: drop any leftover thinking residue.
                            this.textBuf = resultText;
                            this.resultStartPending = true;
                        }
                        const tooShort = unicodeLength(this.textBuf) < this.minInitialChars;
                        // Avoid stalling the result stream when the last buffered chunk is short
                        // (e.g. markdown tail) but `finalize` is already queued — otherwise the
                        // client keeps thinking/placeholder UI and never gets a FINISH + stream_id.
                        const finalizeQueued = this.queue.some((c) => c.kind === "finalize");
                        if (tooShort && !finalizeQueued)
                            return;
                        if (isResultStartRetry) {
                            this.log.info(`pipeline: retrying startPhase(result) bufBytes=${Buffer.byteLength(this.textBuf, "utf-8")}`);
                        }
                        await this.startPhase("result");
                        this.resultStartPending = false;
                    }
                    else {
                        this.textBuf += resultText;
                    }
                    await this.throttledFlush();
                    break;
                }
                case "finalize":
                    await this.doFinalize(cmd.deliverText);
                    break;
            }
        }
        catch (err) {
            this.log.warn(`pipeline: ${cmd.kind} failed phase=${this.phase} queueLen=${this.queue.length} bufBytes=${Buffer.byteLength(this.textBuf, "utf-8")} resultStartPending=${this.resultStartPending} err=${String(err)}`);
        }
    }
    // ======================================================================
    // Phase transitions — the only place phase changes
    // ======================================================================
    async startPhase(target) {
        const failed = target === "thinking" ? this.thinkingInitFailed : this.resultInitFailed;
        if (failed)
            return;
        const stream = new WeixinStreamSender(this.opts);
        try {
            await stream.init();
        }
        catch (err) {
            if (target === "thinking")
                this.thinkingInitFailed = true;
            else
                this.resultInitFailed = true;
            this.log.warn(`pipeline: startPhase(${target}) init failed, disabling ${target} streaming msgStreamId=${this.msgStreamId} bufBytes=${Buffer.byteLength(this.textBuf, "utf-8")} err=${String(err)}`);
            return;
        }
        this.stream = stream;
        const action = target === "thinking" ? StreamAction.THINKING : StreamAction.RESULT;
        const digest = this.textBuf ? unicodeSlice(this.textBuf, 0, 30) : undefined;
        try {
            await sendStreamSignalWeixin({
                to: this.opts.to,
                streamItem: {
                    stream_type: StreamType.TEXT,
                    stream_id: this.msgStreamId,
                    ilink_stream_ticket: stream.ticket,
                    digest,
                    action,
                },
                opts: {
                    baseUrl: this.opts.baseUrl,
                    token: this.opts.token,
                    accountId: this.opts.accountId,
                    contextToken: this.opts.contextToken,
                },
            });
        }
        catch (err) {
            this.log.warn(`pipeline: sendStreamSignal failed target=${target} msgStreamId=${this.msgStreamId} streamId=${stream.streamId} err=${String(err)}`);
            this.stream = undefined;
            try {
                await stream.abort("signal failed");
            }
            catch (abortErr) {
                this.log.debug(`pipeline: best-effort abort after signal failure failed streamId=${stream.streamId} err=${String(abortErr)}`);
            }
            throw err;
        }
        this.phase = target;
        this._hadStreaming = true;
        this.log.info(`pipeline: phase → ${target} streamId=${stream.streamId}`);
    }
    async endCurrentPhase() {
        if (this.phase === "idle" || this.phase === "ended")
            return;
        try {
            await this.flushText();
        }
        catch (err) {
            this.log.warn(`pipeline: flushText in end-${this.phase} failed: ${String(err)}`);
        }
        const prev = this.phase;
        this.phase = "idle";
        const s = this.stream;
        this.stream = undefined;
        if (s && !s.isEnded) {
            try {
                if (s.currentPieceSeq === 0) {
                    await s.abort("no pieces");
                }
                else {
                    await s.end();
                }
                this.log.info(`pipeline: ended ${prev} stream seq=${s.currentPieceSeq}`);
            }
            catch (err) {
                this.log.warn(`pipeline: end-${prev} stream failed: ${String(err)}`);
            }
        }
    }
    async doFinalize(deliverText) {
        if (this.phase === "ended")
            return;
        if (this.phase !== "result" && this._hadStreaming && deliverText) {
            await this.endCurrentPhase();
            this.textBuf = deliverText;
            try {
                await this.startPhase("result");
                await this.flushText();
            }
            catch (err) {
                this.log.warn(`pipeline: late startResult failed: ${String(err)}`);
            }
        }
        await this.endCurrentPhase();
        this.phase = "ended";
    }
    // ======================================================================
    // Text buffer management
    // ======================================================================
    async throttledFlush() {
        if (!this.textBuf)
            return;
        if (Date.now() - this.lastSendAt >= this.throttleMs) {
            await this.flushText();
        }
    }
    async flushText() {
        if (!this.textBuf)
            return;
        if (!this.stream || this.stream.isEnded) {
            const droppedBytes = Buffer.byteLength(this.textBuf, "utf-8");
            this.log.warn(`pipeline: flushText dropping ${droppedBytes} bytes — stream ${this.stream ? "already ended" : "missing"} phase=${this.phase}`);
            this.textBuf = "";
            return;
        }
        const text = this.textBuf;
        this.textBuf = "";
        const logLabel = this.phase === "thinking" ? "THINKING" : "RESULT";
        const streamType = this.phase === "thinking" ? "thinking" : "result";
        const chunks = splitUtf8Chunks(Buffer.from(text, "utf-8"), this.maxPieceBytes);
        for (let i = 0; i < chunks.length; i++) {
            if (this.aborted)
                break;
            const chunk = chunks[i];
            this.log.debug(`STREAM ${logLabel} PIECE ${escapeNewlines(chunk)}`);
            try {
                await this.stream.sendPiece({ type: "text", text: chunk, stream_type: streamType });
            }
            catch (err) {
                // The failed chunk is now tracked inside the stream's pendingPieces and
                // will be retried automatically on the next sendPiece call.  We only
                // need to preserve the *remaining unsent* chunks (i+1 onwards) so the
                // next flush picks them up.  Skip if the pipeline has been aborted
                // (abort() already cleared textBuf; restoring would undo that).
                const remaining = chunks.slice(i + 1).join("");
                if (!this.aborted) {
                    this.textBuf = remaining;
                }
                this.log.warn(`pipeline: flushText chunk ${i + 1}/${chunks.length} failed phase=${this.phase} requeuedBytes=${Buffer.byteLength(remaining, "utf-8")} pendingOnSender=yes err=${String(err)}`);
                throw err;
            }
            this.lastSendAt = Date.now();
        }
    }
    /** Absorb consecutive text commands of a specific kind from the front of the queue. */
    coalesceQueuedTextOfKind(kind) {
        while (this.queue.length > 0 && this.queue[0].kind === kind) {
            this.textBuf += this.queue.shift().text;
        }
    }
    /** Absorb consecutive text commands matching the current phase from the queue. */
    coalesceQueuedText() {
        const kind = this.phase === "result" ? "result" : "thinking";
        this.coalesceQueuedTextOfKind(kind);
    }
    sleep(ms) {
        return new Promise((resolve) => {
            const timer = setTimeout(resolve, ms);
            this.wakeResolve = () => {
                clearTimeout(timer);
                this.wakeResolve = undefined;
                resolve();
            };
        });
    }
}
//# sourceMappingURL=stream-pipeline.js.map