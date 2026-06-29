# SaaS Founder Content Writer

**Platforms:** Claude · Openclaw · Codex
**Domain:** Writing

## Purpose

A content editor for SaaS founders, indie hackers, and product builders. It turns what a founder actually knows — product updates, support tickets, technical lessons, usage data, and personal observations — into high-signal posts for X, Reddit, LinkedIn, and Xiaohongshu (小红书). It refuses to write generic marketing copy: posts earn attention by being specific, honest, and useful to the reader first.

## When to Use

- When you have a product update, launch, or changelog and want a post that leads with what users can now do
- When a user pain point, support pattern, or piece of feedback could become a useful public post
- When you want to share a build-in-public metric, a lesson learned, or a market opinion
- When you need a feedback request that people will actually answer
- When you want the same material adapted to X, Reddit, LinkedIn, or Xiaohongshu norms
- When you need an image — a Xiaohongshu cover, quote card, or data card — rendered from HTML/CSS

It is **not** for ad creative, generic brand copy, or posts with no underlying substance.

## What It Does

**Phase 1: Intake**
1. Captures a portable product profile (category, users, pain point, optional house themes) — never hardcoded
2. Captures the assignment (raw material, platform, format) and refuses to draft without real material
3. Sets the goal and reader takeaway

**Phase 2: Choose the angle**
4. Selects from 8 founder content angles (problem-led, build-in-public, demo-led, lesson learned, opinion, user pain analysis, launch/changelog, feedback request)

**Phase 3: Draft**
5. Applies six writing principles (specific, useful-before-promotional, honest, scene-first, no forced profundity, no hype) with before/after examples
6. Applies platform rules for X, Reddit, LinkedIn, and Xiaohongshu
7. Decides whether an image helps (Xiaohongshu always needs a cover) and, for text/data graphics, renders it from HTML/CSS
8. Writes an open that earns the next line

**Phase 4: Review**
9. Scores against a rubric (not-an-ad, specific, angle clear, platform fit, honest, human voice, strong open, image fit) and revises

## Image Generation

For text- and data-driven graphics — Xiaohongshu covers and image cards, quote cards, data/metric cards, frameworks, comparisons, changelog cards — the skill can render a PNG from HTML/CSS using headless Chrome (`scripts/render-image.js`, Puppeteer-based). This is deterministic and batchable. Photographic images and real product screenshots are out of scope for the renderer. First-time setup is in [`render-image-setup.md`](render-image-setup.md); example templates live in `assets/`.

## Notes

This skill is self-contained and does not depend on other skills. For general-purpose X drafting from any source material (not founder-specific), see [x-post-strategist](../x-post-strategist/README.md).

Reddit self-promotion rules vary by subreddit; the skill always reminds you to check the target subreddit's rules before posting. Xiaohongshu penalizes hard ads and off-platform redirection, so the skill keeps promotion soft and reminds you to check the platform's rules. The skill never invents metrics, quotes, or results, and never posts on your behalf.

## Feedback & Contributions

Found a gap or have a suggestion? [Open an issue or PR](https://github.com/archlab-space/open-skill-hub/issues) — improvements are welcome.
