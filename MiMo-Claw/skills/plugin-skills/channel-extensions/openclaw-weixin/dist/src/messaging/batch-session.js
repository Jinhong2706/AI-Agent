import crypto from "node:crypto";
import { onAgentEvent, } from "openclaw/plugin-sdk/agent-harness-runtime";
import { MessageItemType } from "../api/types.js";
import { logger } from "../util/logger.js";
/** Max chars for a tool result summary before truncation. */
const TOOL_OUTPUT_CHAR_LIMIT = 120_000;
/** Default size budget for a single batch sendMessage (bytes, JSON estimate). */
export const BATCH_SIZE_LIMIT_BYTES = 200 * 1024;
function estimateSizeBytes(items) {
    try {
        return Buffer.byteLength(JSON.stringify(items), "utf8");
    }
    catch {
        return 0;
    }
}
function truncateText(text, limit) {
    if (text.length <= limit)
        return text;
    return `${text.slice(0, limit)}\n\n… truncated (${text.length} chars, showing first ${limit}).`;
}
function formatToolOutput(value) {
    if (value === null || value === undefined)
        return "";
    if (typeof value === "number" || typeof value === "boolean")
        return String(value);
    let text;
    if (typeof value === "string") {
        text = value;
    }
    else {
        if (typeof value === "object") {
            const rec = value;
            if (typeof rec.text === "string") {
                text = rec.text;
            }
            else if (Array.isArray(rec.content)) {
                const parts = rec.content
                    .map((item) => {
                    if (item && typeof item === "object") {
                        const e = item;
                        if (e.type === "text" && typeof e.text === "string")
                            return e.text;
                    }
                    return null;
                })
                    .filter((p) => p !== null);
                text = parts.length > 0 ? parts.join("\n") : JSON.stringify(value, null, 2);
            }
            else {
                text = JSON.stringify(value, null, 2);
            }
        }
        else {
            text = String(value);
        }
    }
    return truncateText(text, TOOL_OUTPUT_CHAR_LIMIT);
}
function tryStringifyArgs(args) {
    if (args === undefined)
        return undefined;
    try {
        return JSON.stringify(args);
    }
    catch {
        return undefined;
    }
}
/**
 * BatchSession — accumulates thinking, tool calls, and text payloads during
 * an AI turn and sends them all in a single sendMessage at finalize time.
 *
 * Drop priority when item_list > BATCH_SIZE_LIMIT_BYTES:
 *   1. Drop ThinkingItem (largest, optional for client UX)
 *   2. Drop all ToolCallStart/Result items
 *   3. Always keep TextItem(s) — the actual reply
 *
 * Usage:
 *   const session = new BatchSession({ onSendBatch });
 *   // spread replyCallbacks + runId into replyOptions
 *   replyOptions = { ...replyOptions, runId: session.runId, ...session.replyCallbacks }
 *   // in deliver(): session.addTextPayload(text)
 *   // after dispatchReplyFromConfig: await session.finalize()
 *   // on error: await session.abort()
 */
export class BatchSession {
    /** Run id this session listens for on the global agent event bus. */
    runId;
    thinkingText = null;
    toolStarts = [];
    toolResults = [];
    textPayloads = [];
    done = false;
    unsubscribeAgentEvent;
    onSendBatch;
    constructor(deps) {
        this.runId = deps.runId ?? crypto.randomUUID();
        this.onSendBatch = deps.onSendBatch;
        this.unsubscribeAgentEvent = onAgentEvent((evt) => this.handleRawAgentEvent(evt));
        logger.debug(`BatchSession.ctor: runId=${this.runId} agentEventListener=registered`);
    }
    /**
     * Spread into replyOptions so the SDK delivers thinking/tool events here.
     * Also set `replyOptions.runId = session.runId` so agent events carry the
     * matching runId.
     */
    get replyCallbacks() {
        return {
            onReasoningStream: (payload) => this.handleReasoningStream(payload),
            onReasoningEnd: () => { },
        };
    }
    /**
     * Store a text payload from deliver(). Each call appends one TextItem to the
     * final item_list in call order. Skips empty strings.
     */
    addTextPayload(text) {
        if (!text.trim())
            return;
        this.textPayloads.push(text);
        logger.debug(`BatchSession.addTextPayload: len=${text.length} total=${this.textPayloads.length}`);
    }
    // ---- private callbacks --------------------------------------------------
    handleReasoningStream(payload) {
        if (this.done)
            return;
        const text = typeof payload.text === "string" ? payload.text : "";
        if (text) {
            this.thinkingText = text;
        }
    }
    handleRawAgentEvent(evt) {
        if (this.done)
            return;
        if (evt.runId !== this.runId)
            return;
        if (evt.stream !== "tool")
            return;
        const data = evt.data;
        if (typeof data.toolCallId !== "string" || !data.toolCallId)
            return;
        if (data.phase === "start") {
            this.toolStarts.push({
                tool_call_id: data.toolCallId,
                tool_name: typeof data.name === "string" && data.name ? data.name : "tool",
                args_json: tryStringifyArgs(data.args),
            });
            logger.debug(`BatchSession: tool_call_start tool=${data.name ?? "?"} id=${data.toolCallId}` +
                ` totalStarts=${this.toolStarts.length}`);
            return;
        }
        if (data.phase === "result") {
            this.toolResults.push({
                tool_call_id: data.toolCallId,
                summary: formatToolOutput(data.result),
            });
            logger.debug(`BatchSession: tool_call_result id=${data.toolCallId}` +
                ` totalResults=${this.toolResults.length}`);
        }
    }
    // ---- item_list assembly -------------------------------------------------
    /**
     * Build the item_list applying the 200 KB budget.
     *
     * Order: [ThinkingItem?, ToolCallStart+Result pairs..., TextItem(s)...]
     *
     * If full list > maxBytes:
     *   - drop ThinkingItem and retry
     *   - if still > maxBytes, drop all tool items too
     *   - TextItem(s) are always kept
     */
    buildItemList(maxBytes = BATCH_SIZE_LIMIT_BYTES) {
        const textItems = this.textPayloads.map((t) => ({
            type: MessageItemType.TEXT,
            text_item: { text: t },
        }));
        const toolItems = [];
        for (const start of this.toolStarts) {
            toolItems.push({
                type: MessageItemType.TOOL_CALL_START,
                tool_call_start_item: {
                    tool_name: start.tool_name,
                    tool_call_id: start.tool_call_id,
                    args_json: start.args_json,
                },
            });
            const result = this.toolResults.find((r) => r.tool_call_id === start.tool_call_id);
            if (result) {
                toolItems.push({
                    type: MessageItemType.TOOL_CALL_RESULT,
                    tool_call_result_item: {
                        tool_call_id: result.tool_call_id,
                        summary: result.summary,
                    },
                });
            }
        }
        const thinkingItem = this.thinkingText
            ? { type: MessageItemType.THINKING, thinking_item: { text: this.thinkingText } }
            : null;
        // Attempt 1: full list
        const full = [
            ...(thinkingItem ? [thinkingItem] : []),
            ...toolItems,
            ...textItems,
        ];
        if (full.length === 0)
            return [];
        const fullSize = estimateSizeBytes(full);
        logger.debug(`BatchSession.buildItemList: items=${full.length} size=${fullSize}B` +
            ` thinking=${thinkingItem !== null} tools=${this.toolStarts.length}` +
            ` texts=${this.textPayloads.length}`);
        if (fullSize <= maxBytes)
            return full;
        // Attempt 2: drop thinking
        logger.warn(`BatchSession.buildItemList: size=${fullSize}B > limit=${maxBytes}B,` +
            ` dropping ThinkingItem (len=${this.thinkingText?.length ?? 0} chars).` +
            ` Full thinking content is in the log: ${logger.getLogFilePath()}`);
        const withoutThinking = [...toolItems, ...textItems];
        if (withoutThinking.length === 0)
            return [];
        const noThinkingSize = estimateSizeBytes(withoutThinking);
        if (noThinkingSize <= maxBytes)
            return withoutThinking;
        // Attempt 3: drop tool items too
        logger.warn(`BatchSession.buildItemList: size=${noThinkingSize}B still > limit=${maxBytes}B,` +
            ` dropping ${this.toolStarts.length} tool call(s) (${toolItems.length} items).` +
            ` Full tool content is in the log: ${logger.getLogFilePath()}`);
        return textItems.length > 0 ? textItems : [];
    }
    // ---- lifecycle ----------------------------------------------------------
    /**
     * Assemble item_list, call onSendBatch once, then clean up. Idempotent.
     */
    async finalize() {
        if (this.done)
            return;
        this.done = true;
        this.cleanup();
        const items = this.buildItemList();
        if (items.length === 0) {
            logger.debug("BatchSession.finalize: item_list empty, skipping send");
            return;
        }
        logger.debug(`BatchSession.finalize: sending ${items.length} item(s)` +
            ` thinking=${this.thinkingText !== null}` +
            ` toolStarts=${this.toolStarts.length}` +
            ` texts=${this.textPayloads.length}`);
        await this.onSendBatch(items);
    }
    /**
     * Discard all buffered data, release event listener. Does not send. Idempotent.
     */
    async abort() {
        if (this.done)
            return;
        this.done = true;
        this.cleanup();
        logger.debug("BatchSession.abort: discarded without send");
    }
    cleanup() {
        try {
            this.unsubscribeAgentEvent();
        }
        catch (err) {
            logger.warn(`BatchSession.cleanup: unsubscribe failed err=${String(err)}`);
        }
    }
}
//# sourceMappingURL=batch-session.js.map