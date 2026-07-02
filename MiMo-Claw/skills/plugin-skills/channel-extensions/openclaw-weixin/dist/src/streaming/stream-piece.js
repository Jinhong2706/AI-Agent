/**
 * Stream piece JSON schema — what gets base64-encoded into PieceItem.piece_data
 * and pushed onto the ilink uplink stream.
 *
 * The protocol distinguishes 7 `kind`s:
 *
 *   Lifecycle (streaming, accumulative — multiple pieces per node):
 *     - "result"            agent's final reply text stream
 *     - "thinking"          agent's reasoning block stream
 *
 *   Discrete (single-frame — exactly 1 piece per occurrence):
 *     - "tool_call_start"   tool invocation start snapshot
 *     - "tool_call_result"  tool invocation result snapshot
 *
 *   Piece-only (no companion sendMessage / KV write):
 *     - "tool_progress"     command stdout slices / patch file list
 *     - "compaction_start"  context compaction begin signal
 *     - "compaction_end"    context compaction end signal
 *
 * Each piece carries `client_id` (the renderer node id; equals the companion
 * sendMessage's client_id when one exists), `root_id` (= the stream_start
 * signal's client_id, shared across the whole stream), and an optional
 * `parent_id` (subagent only, unused this iteration).
 *
 * Field naming follows pb conventions (snake_case) so the same wire format is
 * readable on every consumer language.
 */
/**
 * Parse the SDK's `itemId` (as seen on `onItemEvent`) and extract the
 * `tool_call_id` + `item_kind` so the channel can build a `tool_progress` piece.
 *
 * The SDK encodes the source kind as a prefix:
 *   - "command:<callId>" → command output progress
 *   - "patch:<callId>"   → apply_patch file list summary
 *
 * Other prefixes (e.g. "tool:..." / "search:..." / "analysis:...") and
 * unprefixed values return null — the caller MUST then no-op (skip the piece)
 * to honor the "only command + patch" filter described in the plan.
 */
export function parseToolCallIdFromItemId(itemId) {
    if (typeof itemId !== "string" || itemId.length === 0)
        return null;
    const m = /^(command|patch):(.+)$/.exec(itemId);
    if (!m)
        return null;
    return { item_kind: m[1], tool_call_id: m[2] };
}
/**
 * Encode a `StreamPiece` to the base64 string consumed by `PieceItem.piece_data`.
 */
export function encodeStreamPiece(piece) {
    return Buffer.from(JSON.stringify(piece), "utf-8").toString("base64");
}
//# sourceMappingURL=stream-piece.js.map