import { StreamingMarkdownFilter } from "../messaging/markdown-filter.js";
import { findFenceSpanAt, parseFenceSpans } from "../util/markdown-fences.js";
/**
 * Matches every line starting with `WEIXIN_BUTTONS:` in the text. Kept in
 * sync with INLINE_BUTTONS_RE in messaging/buttons.ts so the streaming
 * suppressor drops exactly what parseInlineButtons later strips at deliver
 * — including the fence-aware skip (a marker inside a code block is treated
 * as literal documentation, never suppressed and never stripped).
 */
const MARKER_LINE_START_RE = /^WEIXIN_BUTTONS:/gm;
function stripReasoningFormat(text) {
    let s = text;
    if (s.startsWith("Reasoning:\n"))
        s = s.slice("Reasoning:\n".length);
    else if (s.startsWith("Reasoning:"))
        s = s.slice("Reasoning:".length);
    else
        return text;
    return s.split("\n").map((line) => {
        if (line.startsWith("_") && line.endsWith("_") && line.length >= 2) {
            return line.slice(1, -1);
        }
        if (line.startsWith("_"))
            return line.slice(1);
        if (line.endsWith("_"))
            return line.slice(0, -1);
        return line;
    }).join("\n");
}
/**
 * Thin synchronous adapter that converts SDK callbacks into pipeline commands.
 *
 * Handles only text-processing concerns (delta extraction, markdown filtering,
 * reasoning format stripping).  All async protocol work is delegated to the
 * StreamPipeline via `push()`.
 */
export class StreamSession {
    pipeline;
    log;
    // -- text processing (synchronous) --
    prevReasoningText = "";
    prevPartialText = "";
    thinkingMdFilter = new StreamingMarkdownFilter();
    resultMdFilter = new StreamingMarkdownFilter();
    resultFilteredAccum = "";
    // -- WEIXIN_BUTTONS suppression for streaming --
    _buttonsLineSuppressed = false;
    // -- debug/logging --
    thinkingSegments = [];
    // -- deliver payload (managed locally, not a pipeline command) --
    _lastDeliverPayload;
    _finalTextCache;
    // -- TEMP DEBUG: track MEDIA: directive presence in raw stream --
    _mediaDebugSeenAt;
    _mediaDebugFirstSnippet;
    constructor(opts) {
        this.pipeline = opts.pipeline;
        this.log = opts.log;
    }
    /** Reply callbacks to spread into replyOptions. */
    get replyCallbacks() {
        return {
            onReasoningStream: (p) => this.onReasoningStream(p),
            onReasoningEnd: () => this.onReasoningEnd(),
            onToolStart: (p) => this.onToolStart(p),
            onAssistantMessageStart: () => this.onAssistantMessageStart(),
            onPartialReply: (p) => this.onPartialReply(p),
        };
    }
    bufferDeliverPayload(payload) {
        this._lastDeliverPayload = payload;
        this._finalTextCache = undefined;
    }
    get lastDeliverPayload() { return this._lastDeliverPayload; }
    get streamId() { return this.pipeline.resultStreamId; }
    get hadStreaming() { return this.pipeline.hadStreaming; }
    /**
     * One-shot markdown-filtered version of the deliver text.
     * Result is memoized; invalidated when bufferDeliverPayload is called.
     */
    getFinalText() {
        if (!this._lastDeliverPayload)
            return "";
        if (this._finalTextCache !== undefined)
            return this._finalTextCache;
        const f = new StreamingMarkdownFilter();
        this._finalTextCache = f.feed(this._lastDeliverPayload.text) + f.flush();
        return this._finalTextCache;
    }
    /** Flush filters, push finalize command, and wait for the pipeline to drain. */
    async finalize() {
        this.log.debug(`stream-cb: finalize hadDeliver=${this._lastDeliverPayload != null} resultAccumLen=${this.resultFilteredAccum.length} prevPartialLen=${this.prevPartialText.length}`);
        // [MEDIA-DEBUG] Dump the tail of the raw accumulated text so we can compare
        // against the deliver payload (which has MEDIA: stripped by the host).
        {
            const raw = this.prevPartialText;
            const tail = raw.slice(-300).replaceAll("\n", "\\n");
            const hasMedia = /\bmedia:/i.test(raw);
            const allMediaMatches = hasMedia
                ? Array.from(raw.matchAll(/\bMEDIA:[^\n]*/gi)).map((m) => m[0])
                : [];
            this.log.info(`[media-debug] finalize rawLen=${raw.length} hasMediaInRaw=${hasMedia} mediaLines=${JSON.stringify(allMediaMatches)} tail="${tail}"`);
            if (this._lastDeliverPayload) {
                const dt = this._lastDeliverPayload.text ?? "";
                this.log.info(`[media-debug] finalize deliver payload textLen=${dt.length} mediaUrl=${this._lastDeliverPayload.mediaUrl ?? "none"} deliverHasMedia=${/\bmedia:/i.test(dt)} deliverTail="${dt.slice(-300).replaceAll("\n", "\\n")}"`);
            }
            else {
                this.log.info(`[media-debug] finalize no deliver payload buffered`);
            }
        }
        // Thinking filter is flushed by onReasoningEnd(); we don't flush it again
        // here to avoid pushing stale thinking text into a result-phase pipeline.
        if (this.prevReasoningText) {
            this.thinkingSegments.push({ type: "text", text: this.prevReasoningText });
            this.prevReasoningText = "";
        }
        this.log.debug(`stream: thinking segments=${JSON.stringify(this.thinkingSegments)}`);
        // Flush result markdown filter → push remaining as result text
        const resultRemaining = this.resultMdFilter.flush();
        if (resultRemaining) {
            this.resultFilteredAccum += resultRemaining;
            this.pipeline.push({ kind: "result", text: resultRemaining });
        }
        // Check for gap between streamed accum and one-shot filtered deliver text.
        // Only fill the gap when some result text was already streamed — otherwise
        // (e.g. synchronous command replies like /models) pushing a fresh "result"
        // would force the pipeline to start a brand-new streaming phase for a
        // single buffered payload, costing ~2s of extra HTTP round-trips.  In the
        // thinking-only → deliver case the pipeline's doFinalize handles the
        // late thinking→result transition via its own _hadStreaming branch.
        if (this._lastDeliverPayload && this.resultFilteredAccum.length > 0) {
            const fullFiltered = this.getFinalText();
            if (fullFiltered.length > this.resultFilteredAccum.length &&
                fullFiltered.startsWith(this.resultFilteredAccum)) {
                const gap = fullFiltered.slice(this.resultFilteredAccum.length);
                this.pipeline.push({ kind: "result", text: gap });
            }
        }
        this.pipeline.push({
            kind: "finalize",
            deliverText: this.getFinalText() || undefined,
        });
        await this.pipeline.drain();
    }
    async abort(errorMsg) {
        await this.pipeline.abort(errorMsg);
    }
    // ---- SDK callbacks (all synchronous, just push commands) ----
    onReasoningStream(payload) {
        const rawText = payload.text ?? "";
        const stripped = stripReasoningFormat(rawText);
        if (stripped === this.prevReasoningText)
            return;
        const isRefresh = !stripped.startsWith(this.prevReasoningText);
        const delta = isRefresh ? stripped : stripped.slice(this.prevReasoningText.length);
        this.prevReasoningText = stripped;
        if (!delta)
            return;
        if (isRefresh) {
            this.thinkingMdFilter = new StreamingMarkdownFilter();
        }
        const filtered = this.thinkingMdFilter.feed(delta);
        if (!filtered)
            return;
        if (isRefresh) {
            this.pipeline.push({ kind: "thinking_refresh", text: filtered });
        }
        else {
            this.pipeline.push({ kind: "thinking", text: filtered });
        }
    }
    onReasoningEnd() {
        this.log.debug(`stream-cb: onReasoningEnd`);
        const remaining = this.thinkingMdFilter.flush();
        if (remaining) {
            this.pipeline.push({ kind: "thinking", text: remaining });
        }
        if (this.prevReasoningText) {
            this.thinkingSegments.push({ type: "text", text: this.prevReasoningText });
            this.prevReasoningText = "";
        }
    }
    onToolStart(payload) {
        this.log.debug(`stream-cb: onToolStart name=${payload.name ?? "?"} phase=${payload.phase ?? "?"}`);
        const phase = payload.phase === "complete" ? "end"
            : payload.phase === "running" ? "continue"
                : "start";
        if (phase === "start") {
            this.thinkingSegments.push({ type: "tool_calling", name: payload.name });
        }
        this.pipeline.push({ kind: "tool_call", name: payload.name, phase: phase });
    }
    onAssistantMessageStart() {
        this.log.debug(`stream-cb: onAssistantMessageStart`);
        this.prevPartialText = "";
        this.resultFilteredAccum = "";
        this.resultMdFilter = new StreamingMarkdownFilter();
        this._buttonsLineSuppressed = false;
    }
    onPartialReply(payload) {
        const fullText = payload.text ?? "";
        if (this._buttonsLineSuppressed) {
            this.prevPartialText = fullText;
            return;
        }
        const prevLen = this.prevPartialText.length;
        const rawDelta = fullText.slice(prevLen);
        this.prevPartialText = fullText;
        if (!rawDelta)
            return;
        // [MEDIA-DEBUG] Detect MEDIA: directive appearance in raw stream so we can
        // verify whether the host strips it before deliver. Logs once per stream.
        if (this._mediaDebugSeenAt === undefined && /\bmedia:/i.test(fullText)) {
            this._mediaDebugSeenAt = fullText.search(/\bmedia:/i);
            const start = Math.max(0, this._mediaDebugSeenAt - 40);
            const end = Math.min(fullText.length, this._mediaDebugSeenAt + 200);
            this._mediaDebugFirstSnippet = fullText.slice(start, end).replaceAll("\n", "\\n");
            this.log.info(`[media-debug] MEDIA: seen in raw stream at offset=${this._mediaDebugSeenAt} fullLen=${fullText.length} snippet="${this._mediaDebugFirstSnippet}"`);
        }
        // Detect WEIXIN_BUTTONS: marker anywhere in the accumulated text. We mirror
        // the recognition rule used by parseInlineButtons (/^WEIXIN_BUTTONS:/m —
        // start of any line, fence-aware), so whatever gets stripped at deliver-time
        // also gets suppressed in the live stream, regardless of whether the marker
        // is at the tail, followed by trailing newline, or followed by more content.
        // Markers inside an (open or closed) markdown code fence are treated as
        // literal documentation and never suppressed.
        const fenceSpans = parseFenceSpans(fullText);
        const re = new RegExp(MARKER_LINE_START_RE.source, MARKER_LINE_START_RE.flags);
        let markerStart = -1;
        let m;
        while ((m = re.exec(fullText)) !== null) {
            if (!findFenceSpanAt(fenceSpans, m.index)) {
                markerStart = m.index;
                break;
            }
        }
        if (markerStart >= 0) {
            this._buttonsLineSuppressed = true;
            // Push the portion of the delta that lies BEFORE the marker start.
            // Anything from markerStart onwards (marker itself + any future tokens)
            // is dropped from the stream.
            const deltaCutoff = Math.max(0, markerStart - prevLen);
            const deltaBeforeMarker = rawDelta.slice(0, deltaCutoff);
            if (deltaBeforeMarker) {
                const filteredDelta = this.resultMdFilter.feed(deltaBeforeMarker);
                if (filteredDelta) {
                    this.resultFilteredAccum += filteredDelta;
                    this.pipeline.push({ kind: "result", text: filteredDelta });
                }
            }
            return;
        }
        const filteredDelta = this.resultMdFilter.feed(rawDelta);
        if (filteredDelta) {
            this.resultFilteredAccum += filteredDelta;
            this.pipeline.push({ kind: "result", text: filteredDelta });
        }
    }
}
//# sourceMappingURL=stream-session.js.map