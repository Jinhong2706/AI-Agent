/**
 * Shared button normalisation helpers used by both the channel action handler
 * (channel.ts) and the inbound message dispatch path (process-message.ts).
 */
import { logger } from "../util/logger.js";
import { findFenceSpanAt, parseFenceSpans } from "../util/markdown-fences.js";
/**
 * Normalize a single button-like object to {text, callback_data, style?}.
 * Handles field name variants: label→text, value/callbackData→callback_data.
 */
export function normalizeButtonObject(b) {
    const text = String(b.text ?? b.label ?? "");
    const callbackData = String(b.callback_data ?? b.callbackData ?? b.value ?? b.action ?? b.data ?? "");
    if (!text && !callbackData)
        return null;
    const style = typeof b.style === "string" && b.style ? b.style : undefined;
    return style
        ? { text, callback_data: callbackData, style }
        : { text, callback_data: callbackData };
}
/**
 * Normalize any button-like value to the canonical [[{text, callback_data}]] format.
 * Handles all known AI malformations:
 *   - [[{text, callback_data}]]  → already correct
 *   - [{text, callback_data}]    → flat array, wrap into single row
 *   - {text, callback_data}      → single button object
 *   - {buttons: [...]}           → unwrap .buttons
 *   - [{type:"button", label, value}] → normalize fields
 */
export function normalizeButtonsParam(raw) {
    if (raw == null)
        return undefined;
    if (Array.isArray(raw)) {
        if (raw.length === 0)
            return undefined;
        if (Array.isArray(raw[0])) {
            return raw;
        }
        const flatButtons = raw.filter((b) => b != null && typeof b === "object" && !Array.isArray(b));
        if (flatButtons.length === 0)
            return undefined;
        const row = flatButtons.map(normalizeButtonObject).filter(Boolean);
        return row.length > 0 ? [row] : undefined;
    }
    if (typeof raw === "object") {
        const obj = raw;
        if (Array.isArray(obj.buttons)) {
            return normalizeButtonsParam(obj.buttons);
        }
        const btn = normalizeButtonObject(obj);
        return btn ? [[btn]] : undefined;
    }
    return undefined;
}
/**
 * Parse and strip the inline WEIXIN_BUTTONS marker from outbound text.
 *
 * Agents writing plain-text responses (deliver / cron / streaming) can embed
 * buttons by appending a line of the form:
 *
 *   WEIXIN_BUTTONS:[{"label":"Yes","value":"yes"},{"label":"No","value":"no"}]
 *
 * Returns:
 *   - `cleanText`: the original text with the marker line removed and any
 *     resulting extra blank lines collapsed.
 *   - `buttons`:   the normalised button array (canonical [[{text,callback_data}]]
 *     form) ready to pass to sendMessageWeixin / sendFinalMessageWithStreamId,
 *     or undefined when no valid marker is found.
 */
const INLINE_BUTTONS_RE = /^WEIXIN_BUTTONS:(\[[\s\S]*?\])\s*$/gm;
export function parseInlineButtons(text) {
    // Mirror openclaw core's MEDIA: handling: a marker that lives inside a
    // fenced code block is treated as literal documentation, not a directive.
    const fenceSpans = parseFenceSpans(text);
    const re = new RegExp(INLINE_BUTTONS_RE.source, INLINE_BUTTONS_RE.flags);
    let match;
    while ((match = re.exec(text)) !== null) {
        if (findFenceSpanAt(fenceSpans, match.index))
            continue;
        try {
            const parsed = JSON.parse(match[1]);
            const buttons = normalizeButtonsParam(parsed);
            const cleanText = text
                .replace(match[0], "")
                .replace(/\n{3,}/g, "\n\n")
                .trim();
            logger.debug(`parseInlineButtons: extracted ${buttons?.length ?? 0} button rows from inline marker`);
            return { cleanText, buttons };
        }
        catch {
            logger.warn(`parseInlineButtons: JSON parse failed, keeping marker as-is`);
            return { cleanText: text, buttons: undefined };
        }
    }
    return { cleanText: text, buttons: undefined };
}
/**
 * Unified outbound helper: strip any inline WEIXIN_BUTTONS marker from `text`
 * and merge the resulting buttons with any explicitly-provided buttons.
 *
 * Explicit buttons always win over marker-parsed buttons — an agent that calls
 * the `message` tool with a structured `buttons` param is making a more
 * deliberate choice than one that embeds a marker in free-text.
 *
 * Every outbound entry point (sendText / sendMedia / sendPayload / handleAction
 * / streaming deliver) should route text through this helper so the marker is
 * never leaked to the wire regardless of which code path delivered it.
 */
export function resolveOutboundButtons(text, explicitButtons) {
    const explicitNormalised = explicitButtons != null ? normalizeButtonsParam(explicitButtons) : undefined;
    const { cleanText, buttons: inlineButtons } = parseInlineButtons(text);
    return {
        text: cleanText,
        buttons: explicitNormalised ?? inlineButtons,
    };
}
//# sourceMappingURL=buttons.js.map