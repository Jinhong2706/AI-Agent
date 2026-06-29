# Changelog

## [0.7.0] - 2026-06-05

### Added
- Xiaohongshu (小红书) platform support: platform option in intake, a dedicated Platform Rules section (image-first cover, title/body/tags conventions, soft-promotion norms), output format and key-rule updates, and Chinese-by-default behavior.
- New Step 7 "Decide Whether An Image Helps" with an image brief, plus a "Rendering Text/Data Graphics" subsection for HTML/CSS + headless Chrome rendering and a decision rule for when to render vs. use an image model vs. a real screenshot. Xiaohongshu always requires a cover.
- Rendering tooling: `scripts/render-image.js` (Puppeteer, with system-Chrome and manual fallback), `scripts/package.json`, `render-image-setup.md`, and example templates `assets/xiaohongshu-cover.html`, `assets/data-card.html`.

### Changed
- Renumbered the review step (Score And Revise) to Step 8 and added an "Image fit" rubric row. Updated the skill description and README to cover Xiaohongshu and image rendering.

## [0.6.0] - 2026-06-02
- Initial release of `saas-founder-content-writer`: a self-contained skill that turns founder product updates, user pain points, technical lessons, and observations into high-signal posts for X, Reddit, and LinkedIn.
- Four-phase workflow (Intake → Choose the angle → Draft → Review) with a portable product profile, 8 content angles, six writing principles with before/after examples, per-platform rules (X / Reddit / LinkedIn), a review rubric, and safety boundaries against fabricated claims.
