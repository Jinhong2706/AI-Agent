export function parseFenceSpans(buffer) {
    const spans = [];
    let open;
    let offset = 0;
    while (offset <= buffer.length) {
        const nextNewline = buffer.indexOf("\n", offset);
        const lineEnd = nextNewline === -1 ? buffer.length : nextNewline;
        const line = buffer.slice(offset, lineEnd);
        const match = /^( {0,3})(`{3,}|~{3,})(.*)$/.exec(line);
        if (match) {
            const marker = match[2];
            const markerChar = marker[0];
            const markerLen = marker.length;
            if (!open) {
                open = { start: offset, markerChar, markerLen };
            }
            else if (open.markerChar === markerChar && markerLen >= open.markerLen) {
                spans.push({ start: open.start, end: lineEnd });
                open = undefined;
            }
        }
        if (nextNewline === -1)
            break;
        offset = nextNewline + 1;
    }
    if (open) {
        spans.push({ start: open.start, end: buffer.length });
    }
    return spans;
}
/**
 * Return the fence span containing `index`, or undefined if `index` is not
 * inside any fence. Spans are assumed to be sorted by `start` (which is the
 * natural output of parseFenceSpans).
 */
export function findFenceSpanAt(spans, index) {
    let low = 0;
    let high = spans.length - 1;
    while (low <= high) {
        const mid = (low + high) >>> 1;
        const span = spans[mid];
        if (index < span.start) {
            high = mid - 1;
            continue;
        }
        if (index >= span.end) {
            low = mid + 1;
            continue;
        }
        return span;
    }
    return undefined;
}
//# sourceMappingURL=markdown-fences.js.map