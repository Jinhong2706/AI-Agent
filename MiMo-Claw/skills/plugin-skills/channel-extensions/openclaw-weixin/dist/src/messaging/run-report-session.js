import { MessageItemType } from "../api/types.js";
import { logger } from "../util/logger.js";
import { sendMessageItemWeixin } from "./send.js";
function normalizeToolStatus(status) {
    if (status === "completed")
        return "completed";
    if (status === "failed")
        return "failed";
    if (status === "blocked")
        return "blocked";
    return "unknown";
}
export class RunReportSession {
    runId;
    to;
    accountId;
    opts;
    thinkingText = "";
    thinkingSent = false;
    finalized = false;
    sendChain = Promise.resolve();
    constructor(deps) {
        this.runId = deps.runId;
        this.to = deps.to;
        this.accountId = deps.accountId;
        this.opts = { ...deps.opts, runId: deps.runId };
    }
    get replyOptions() {
        return {
            runId: this.runId,
            suppressDefaultToolProgressMessages: true,
            onReasoningStream: (payload) => this.handleReasoningStream(payload),
            onReasoningEnd: () => this.handleReasoningEnd(),
            onItemEvent: (payload) => this.handleToolItemEvent(payload),
        };
    }
    enqueueSend(item, label) {
        if (this.finalized)
            return;
        this.sendChain = this.sendChain
            .then(async () => {
            await sendMessageItemWeixin({
                to: this.to,
                item,
                opts: this.opts,
                label,
            });
        })
            .catch((err) => {
            logger.warn(`${label}: failed to=${this.to} accountId=${this.accountId} runId=${this.runId} err=${String(err)}`);
        });
    }
    handleReasoningStream(payload) {
        if (this.finalized)
            return;
        const text = typeof payload.text === "string" ? payload.text : "";
        if (text) {
            this.thinkingText = text;
        }
    }
    handleReasoningEnd() {
        this.sendThinkingIfNeeded();
    }
    sendThinkingIfNeeded() {
        if (this.finalized || this.thinkingSent)
            return;
        const text = this.thinkingText.trim();
        if (!text)
            return;
        this.thinkingSent = true;
        this.enqueueSend({
            type: MessageItemType.THINKING,
            is_completed: true,
            thinking_item: { text },
        }, "sendThinkingReport");
    }
    handleToolItemEvent(payload) {
        if (this.finalized)
            return;
        if (payload.kind !== "tool")
            return;
        if (payload.phase !== "start" && payload.phase !== "end")
            return;
        const now = Date.now();
        const toolName = payload.name?.trim() || payload.title?.trim() || "tool";
        const toolCallId = payload.itemId?.trim() || undefined;
        if (payload.phase === "start") {
            this.enqueueSend({
                type: MessageItemType.TOOL_CALL_START,
                create_time_ms: now,
                is_completed: false,
                tool_call_start_item: {
                    tool_name: toolName,
                    tool_call_id: toolCallId,
                },
            }, "sendToolCallStartReport");
            return;
        }
        this.enqueueSend({
            type: MessageItemType.TOOL_CALL_RESULT,
            create_time_ms: now,
            is_completed: true,
            tool_call_result_item: {
                tool_name: toolName,
                tool_call_id: toolCallId,
                status: normalizeToolStatus(payload.status),
            },
        }, "sendToolCallResultReport");
    }
    async finalize() {
        if (this.finalized)
            return;
        this.sendThinkingIfNeeded();
        this.finalized = true;
        try {
            await this.sendChain;
        }
        catch (err) {
            logger.warn(`RunReportSession.finalize: send drain failed runId=${this.runId} err=${String(err)}`);
        }
    }
}
//# sourceMappingURL=run-report-session.js.map