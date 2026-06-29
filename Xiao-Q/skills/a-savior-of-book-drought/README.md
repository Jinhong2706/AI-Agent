# Novel Finder - Smart Book Recommendation

> Tell me what kind of novel you want, I'll search across platforms and generate a personalized reading list.

## Features

- **Cross-platform Search**: Qidian, Fanqie, Qimao, Douban, Zhihu book lists
- **Rich Details**: Rating, word count, status, synopsis, reader reviews, read links
- **No Spoilers**: All descriptions are spoiler-free
- **Warm Design**: Book-themed HTML report with virtual covers and serif typography
- **Smart Picks**: Most Exciting / Most Brainy / Most Touching / Ultimate Pick

## File Structure

```
~/.workbuddy/skills/novel-finder/
|-- SKILL.md
|-- scripts/
|   |-- generate_novel_report.py    <- HTML report generator
|-- README.md
```

## Usage

```
"Recommend some mystery novels, logic-heavy like Lord of Mysteries"
"I want wuxia novels, completed, over 1 million words"
"Book drought! Recommend some urban fantasy novels"
```

## System Requirements

| Item | Requirement |
|------|-------------|
| Python | 3.10+ |
| Dependencies | None (stdlib only) |
| Network | Required (for searching novel data) |

## Notes

- All searches done in real-time, no stale data
- Descriptions are spoiler-free
- Reader reviews are attributed to source platforms
- Always links to official/authorized reading platforms
