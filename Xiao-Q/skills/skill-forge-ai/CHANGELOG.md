# Changelog

All notable changes to this project will be documented in this file.

## [3.3.0] - 2026-06-07

### Added
- Security Red Line Check (Step 4a+1): 7-item security scan before delivery
- Do NOT scope in description: "Do NOT use for editing existing skills, skill security vetting, or general coding tasks."

### Changed
- Refined self-validation pipeline: Schema → Security → Trigger → Dogfood
- Improved Phase 2 benchmarking flow with clearer user decision options

## [3.2.0] - 2026-06-06

### Added
- Phase 2: SkillHub Peer Benchmarking — search, rank, and compare against Top 3 peers
- Tencent 9-dimension compliance comparison template
- Quality ranking formula: downloads × 0.4 + installs × 0.3 + stars × 0.3
- Differentiation & gap analysis with Tencent Manual justification
- Progressive Disclosure: moved detailed docs to references/ directory
- benchmarking-guide.md reference

### Changed
- SKILL.md trimmed from 319 lines to ~170 lines (detailed content moved to references/)
- Interview flow extracted to references/interview-flow.md
- Interview methods extracted to references/interview-methods.md

## [3.1.0] - 2026-06-05

### Added
- Adaptive 2-5 round interview (up from fixed 3 rounds)
- B1-B6 interview rules: behavioral probing, Why×1-2, bias detection, contradiction writeback, option-first 3+1, creative option probe
- Recursive search pattern: broad → deepen → precision → verify
- 3-step self-validation: Schema check → Trigger test → Dogfood simulation
- Convergence check after each interview round
- interview-flow.md and interview-methods.md references

### Changed
- Phase 0 intent recognition: element check before deciding interview vs direct creation
- Interview rounds now adaptive based on element convergence

## [3.0.0] - 2026-06-04

### Added
- Phase 0: Intent Recognition — detect whether context is sufficient or interview is needed
- 3-round structured interview for new skill creation
- Element checklist: single scenario / trigger condition / output format / scope boundary / hard constraints

### Changed
- Restructured from flat flow to phased pipeline (Phase 0 → Phase 1)

## [2.0.0] - 2026-06-03

### Added
- Three Iron Rules: Description-first / One-Skill-One-Job / Under 150 lines
- 4-module SKILL.md format: 任务/输出格式/规则/示例
- Useless rule filter: delete "语言简洁"/"保持客观"/"排版整齐" etc.
- Intern Test for rules: if an intern can't execute it, delete it

### Changed
- Complete rewrite from v1 template-based approach to rule-driven approach

## [1.0.0] - 2026-06-01

### Added
- Initial release: basic skill creation template
- SKILL.md frontmatter with name and description
- Simple creation flow without interview or validation
