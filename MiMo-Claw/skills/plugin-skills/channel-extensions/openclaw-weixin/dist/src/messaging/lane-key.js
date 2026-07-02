import { isAbortRequestText } from "openclaw/plugin-sdk/reply-runtime";
import { MessageItemType } from "../api/types.js";
/**
 * Lane key for Weixin message scheduling.
 *
 * Mirrors the Telegram channel's `getTelegramSequentialKey` (see
 * extensions/telegram/src/sequential-key.ts in the openclaw main repo).
 *
 * Design:
 * - Different users get different lane keys -> processed concurrently.
 * - Same user, regular messages -> share `wx:<account>:<user>` lane,
 *   processed strictly in arrival order so AI replies, typing state and
 *   inbound session writes do not interleave.
 * - Abort requests (e.g. "stop", "中止") are routed to a separate
 *   `wx:<account>:<user>:control` lane so they can run immediately even when
 *   the main lane is occupied by a long-running tool turn. The actual
 *   "stopping" is implemented via the abort-fence mechanism (see
 *   `abort-fence.ts`).
 */
function extractFirstTextBody(itemList) {
    if (!itemList?.length)
        return "";
    for (const item of itemList) {
        if (item.type === MessageItemType.TEXT && item.text_item?.text != null) {
            return String(item.text_item.text);
        }
    }
    return "";
}
/** Extract text body suitable for abort detection from an inbound message. */
export function extractTextBodyForLane(msg) {
    return extractFirstTextBody(msg.item_list);
}
/** Returns true when the message text is an abort intent (stop / 中止 / ...). */
export function isWeixinAbortMessage(msg) {
    const text = extractTextBodyForLane(msg);
    if (!text)
        return false;
    return isAbortRequestText(text);
}
/**
 * Compute the lane key used by the per-key scheduler. Abort requests get the
 * `:control` suffix to bypass the main lane.
 *
 * Note: the fallback `unknown` user happens for malformed payloads. Keep them
 * on a shared lane so they cannot fan out and exhaust resources.
 */
export function getWeixinLaneKey(ctx) {
    const userId = ctx.msg.from_user_id?.trim() || "unknown";
    const baseKey = `wx:${ctx.accountId}:${userId}`;
    if (isWeixinAbortMessage(ctx.msg)) {
        return `${baseKey}:control`;
    }
    return baseKey;
}
/**
 * Per-user fence key shared by all dispatches that should be aborted as a
 * group when the user sends an abort. This is intentionally the *base* key
 * (without `:control`) so that an abort dispatched on the control lane bumps
 * the same generation that the long-running main-lane dispatch is checking.
 */
export function getWeixinFenceKey(ctx) {
    const userId = ctx.msg.from_user_id?.trim() || "unknown";
    return `wx:${ctx.accountId}:${userId}`;
}
//# sourceMappingURL=lane-key.js.map