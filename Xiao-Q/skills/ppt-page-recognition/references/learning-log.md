# Learning Log

## 2026-04-01

- Parallel side-by-side topics such as company introduction and core product should be recognized as `peer-panels`, not flattened into a generic chapter page.
- Visible authoring directions like drawing prompts or update notes must stay in `instruction_text` so downstream rendering does not print them as final copy.
- Image-heavy pages such as logo walls and project galleries need stronger `missing_risk` notes when extraction may be incomplete, especially in lower visual regions.
- Downstream template matching improves when recognition preserves panel count, panel roles, and connector meaning instead of only emitting raw text.

## 2026-04-02

- Recognition quality should be judged by semantic fidelity: understand the slide meaning and hierarchy, keep it complete, and avoid inventing or dropping visible information.
- Small footer lines and similar secondary text can still matter to downstream generation and should not be ignored by default.
- `peer-panels` pages with a centered brand hub should preserve that hub in generation-ready structure, not only in audit text buckets.
- Two-line logo-wall cells often encode a client and a system pair; flattening them into one opaque string loses reconstructable structure.
- When a page visibly contains conflicting metric sets, both sets should be preserved structurally and paired with an explicit inconsistency warning.
- Recognition improvements should land in a reusable normalization layer instead of repeated hand edits to `master_deck.json`.
- Deck aggregation should discover `slide_*_result.json` dynamically and emit stable deck metadata such as `slide_count` and `deck_outline`.
- Keep instruction notes in `instruction_text`; if a post-processing step temporarily promotes them, move them back out before final aggregation.
- Geometry matters for semantic fidelity on visual layouts: some sector grids and customer walls can only be split correctly by reading PPT coordinates, not by line order alone.
- When a section heading is visible but its contents remain unreadable, the recognizer should keep the empty section and attach a precise `missing_risk` instead of guessing names.
- Whole-slide screenshots can outperform extracted image assets for cover footers, narrow customer-wall columns, and other details that are easy to miss when vision only sees one embedded picture.
- A constrained second-pass screenshot prompt is better than manual guessing when the remaining gap is narrow and well-scoped, such as one footer line, one side column, or one chart mapping.
