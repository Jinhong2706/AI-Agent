/**
 * Abort fence (generation barrier) for Weixin message dispatch.
 *
 * When the user sends an "abort" intent (e.g. "stop", "中止", "/abort") we
 * cannot truly cancel the in-flight LLM/tool pipeline because the underlying
 * SDK does not currently propagate an AbortSignal end-to-end. Instead, we
 * adopt the same trick used by the Telegram channel
 * (extensions/telegram/src/bot-message-dispatch.ts in the openclaw main repo):
 *
 * - Each dispatch picks up a fence `generation` at entry.
 * - An abort message bumps the generation (`supersede=true`) and starts its
 *   own dispatch with the new generation.
 * - All outbound side-effects (sendMessage, typing start/stop, debug timing,
 *   etc.) check `isDispatchSuperseded(...)` first; if the generation no longer
 *   matches, they become no-ops.
 *
 * Effect: the old long-running task keeps running in the background but its
 * output is silently dropped, so the user perceives it as cancelled and the
 * new turn begins immediately.
 *
 * The fence is keyed per chat (typically `accountId:userId` for Weixin DMs),
 * so different users do not share state.
 */
const fenceByKey = new Map();
/**
 * Begin a new dispatch and return its generation. When `supersede` is true
 * (i.e. this dispatch is itself an abort request), bump the generation first
 * so all already-running dispatches on this key become superseded.
 */
export function beginAbortFence(params) {
    const existing = fenceByKey.get(params.key);
    const state = existing ?? { generation: 0, activeDispatches: 0 };
    if (params.supersede) {
        state.generation += 1;
    }
    state.activeDispatches += 1;
    fenceByKey.set(params.key, state);
    return state.generation;
}
/**
 * Returns true when the dispatch with `generation` has been superseded by a
 * later abort on `key`. Cheap to call; check before any user-visible side
 * effect.
 */
export function isDispatchSuperseded(params) {
    return (fenceByKey.get(params.key)?.generation ?? 0) !== params.generation;
}
/**
 * Mark a dispatch finished. When the lane goes idle we drop the entry to
 * avoid unbounded growth across many distinct users.
 */
export function endAbortFence(key) {
    const state = fenceByKey.get(key);
    if (!state) {
        return;
    }
    state.activeDispatches -= 1;
    if (state.activeDispatches <= 0) {
        fenceByKey.delete(key);
    }
}
/** Number of tracked fence keys. Exposed for diagnostics and tests. */
export function getAbortFenceSizeForTests() {
    return fenceByKey.size;
}
/** Clear all fence state. Tests only. */
export function resetAbortFenceForTests() {
    fenceByKey.clear();
}
//# sourceMappingURL=abort-fence.js.map