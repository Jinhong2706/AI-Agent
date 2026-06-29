# Page Schema

Use this reference when interpreting or extending the output of `recognize_ppt_deck.py`.

## Deck Output

```json
{
  "source_file": "",
  "slide_count": 0,
  "deck_outline": [],
  "slides": [],
  "vision_tasks": [],
  "screenshot_status": {}
}
```

## Per-Slide Output

```json
{
  "slide_number": 0,
  "page_type": "",
  "title": "",
  "hierarchy": [],
  "layout_intent": {},
  "connectors": [],
  "structured_payload": {},
  "all_visible_text": [],
  "main_text": [],
  "metrics": [],
  "labels": [],
  "footer": [],
  "instruction_text": [],
  "supplement": [],
  "ocr_residue": [],
  "missing_risk": [],
  "vision_tasks": [],
  "confidence": 0.0,
  "reason": ""
}
```

## `vision_tasks`

When native OOXML extraction is insufficient, the recognizer can emit explicit visual follow-up tasks for a host IDE / agent.

These tasks are intermediate execution work for the host model. If the current model supports vision, it should consume these tasks automatically instead of returning them to the user as the final stopping point.
They must not be shown as an optional decision like "Do you want me to process these tasks?" unless the current model lacks vision support.

```json
{
  "slide_number": 0,
  "page_type": "",
  "task_type": "",
  "goal": "",
  "image_path": "",
  "host_capability": "vision",
  "prompt": "",
  "expected_schema": {},
  "merge_strategy": ""
}
```

Typical `task_type` values:

- `timeline_recovery`
- `logo_wall_group_recovery`
- `people_chart_recovery`
- `awards_and_investors_recovery`
- `cover_footer_recovery`

## `vision_task_results`

When a host IDE / agent finishes one or more `vision_tasks`, it can return either:

- a top-level array
- or an object with `vision_task_results`, `task_results`, `completed_tasks`, or `results`

Each entry should look like:

```json
{
  "slide_number": 0,
  "task_type": "",
  "task_payload": {}
}
```

`task_payload` must match the originating task's `expected_schema`.

## Host Vision Result Contract

When a host IDE or agent completes one emitted `vision_task`, it should return one JSON result per task:

- task JSON is written to stdin
- stdout must be valid JSON
- stdout may be either:

```json
{
  "slide_number": 0,
  "task_type": "",
  "task_payload": {}
}
```

or just:

```json
{}
```

In the second form, the host treats the JSON as the raw `task_payload` for the current task.

## `layout_intent`

Required keys:

- `direction`
- `panel_count`
- `has_connectors`
- `narrative`
- `dominant_visual`
- `parent_label`

## `connectors`

Each connector uses:

```json
{
  "scope": "global",
  "type": "arrow",
  "from": "",
  "to": "",
  "panel": "",
  "meaning": "progression"
}
```

Common meanings:

- `progression`
- `comparison`
- `integration`
- `grouping`
- `containment`
- `flow`
- `interaction`

## `structured_payload` by Page Family

### `timeline`

```json
{
  "parent_label": "",
  "periods": [
    {
      "period": "",
      "headline": "",
      "capability_tag": "",
      "scenario": "",
      "target_domain": "",
      "supporting_labels": [],
      "panel_connectors": []
    }
  ]
}
```

### `people-matrix`

```json
{
  "section_title": "",
  "groups": [
    {
      "group_title": "",
      "people": [],
      "metrics": [],
      "updated_metrics": []
    }
  ],
  "chart_breakdown": {
    "display_total": "",
    "segments": [
      {
        "label": "",
        "value": "",
        "percentage": ""
      }
    ]
  },
  "footer_lines": []
}
```

### `logo-wall`

```json
{
  "section_title": "",
  "groups": [
    {
      "group_title": "",
      "items": [],
      "entries": [
        {
          "name": "",
          "system": ""
        }
      ]
    }
  ],
  "summary": "",
  "footer_lines": []
}
```

### `awards-patents`

```json
{
  "metric_blocks": [],
  "awards": [],
  "investors": []
}
```

### `metrics`

```json
{
  "metric_blocks": [
    {
      "label": "",
      "value": "",
      "unit": "",
      "supporting_text": []
    }
  ]
}
```

### `peer-panels`

```json
{
  "section_title": "",
  "parent_label": "",
  "panels": [
    {
      "panel_title": "",
      "panel_role": "",
      "items": [],
      "supporting_lines": []
    }
  ],
  "metric_blocks": []
}
```

Use this family for equal-status side-by-side or multi-panel topics. Typical `panel_role` values can express semantic contrast such as `company-profile`, `product-profile`, `civil-business`, or `industrial-business`.

### `image-text`

```json
{
  "blocks": [
    {
      "heading": "",
      "body": [],
      "image_subject": ""
    }
  ]
}
```

### `chapter`

```json
{
  "primary_title": "",
  "secondary_title": "",
  "paired_lines": []
}
```

### `toc`

```json
{
  "entries": []
}
```

### `cover`

```json
{
  "brand_title": "",
  "subtitle": "",
  "english_subtitle": "",
  "footer_lines": []
}
```

### `fallback`

```json
{
  "blocks": [
    {
      "role": "",
      "text": []
    }
  ]
}
```

## `instruction_text`

Use this bucket for visible authoring notes, drawing prompts, edit reminders, and revision comments that appear on the source slide but are not meant to render in the final rebuilt PPT.

## Fidelity Expectation

The output should be faithful to the source slide:

- important visible information should not appear only in audit buckets if downstream generation needs it
- `structured_payload` should preserve hierarchy and semantic grouping whenever the page family supports it
- `all_visible_text` is an audit bucket, not a substitute for missing structure
- avoid flattening paired or stacked cell content into a single opaque string when the relationship matters
- if the slide visibly contains two conflicting datasets, preserve both explicitly and mark the inconsistency in `missing_risk`

## `missing_risk`

Use this bucket for explicit warnings about likely incomplete extraction. This is especially important for logo walls, project-image pages, flattened diagrams, or pages where large visual regions contain non-editable content that may not survive structure-only parsing.
