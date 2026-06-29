---
name: ppt-page-recognition
description: 读取本地 PowerPoint `.pptx`，恢复页面结构与语义，并输出可用于后续生成的标准 JSON。在正式识别前，先检查是否存在同名 PDF；如果没有，必须明确提醒用户补充 PDF，或让用户确认接受仅用 PPT 继续识别的较低视觉覆盖率。默认使用当前 IDE 或智能体自身的视觉能力完成图片页补全；如果当前模型不支持视觉，必须先提醒用户切换到支持视觉的模型。
---

# PPT 页面识别

当输入是本地 `.pptx`，目标是恢复整套 PPT 多页的页面类型、层级结构、布局语义、连接关系和结构化内容时，使用这个 Skill。

## 核心原则

识别结果必须忠实还原原始 PPT 的语义与组织方式：

- 理解页面含义和层级，而不只是拷贝文字
- 保留并列、父子、分组、阶段演进等结构关系
- 避免遗漏有意义的可见信息，也避免重复
- 不得编造源页面中不存在的内容
- 如果某个可见区域无法可靠恢复，必须在 `missing_risk` 中诚实标明风险

## 识别前检查

在正式识别开始前，必须先检查目标 PPTX 同目录下是否存在同名 PDF。

- 如果 PDF 存在，继续执行，并优先利用 PDF 导出的整页截图支持视觉补全。
- 如果 PDF 不存在，不允许静默继续。必须先高亮提醒用户，并让用户二选一：
  - 先补 PDF，再继续
  - 仅用 PPT 继续识别
- 在正式识别前，还要检查当前模型是否支持看图。如果当前模型不支持视觉，不能静默继续，必须先提醒用户切换到支持视觉的模型。
- 如果用户选择仅用 PPT 继续识别，仍然可以继续，但必须明确说明：时间线、logo 墙、图表、奖项、投资人、封面页脚等图片型区域的恢复完整度可能下降。
- 不允许先完整跑一轮识别，再回头询问是否补 PDF；确认动作必须发生在主识别前。

## 快速开始

先执行原生结构识别：

```bash
python3 scripts/recognize_ppt_deck.py /absolute/path/to/file.pptx --vision-mode off
```

如果已经拿到视觉补全结果，再合并回最终 JSON：

```bash
python3 scripts/apply_vision_tasks.py \
  /absolute/path/to/master_deck_with_tasks.json \
  /absolute/path/to/vision_task_results.json \
  --output /absolute/path/to/master_deck_merged.json \
  --source-ppt /absolute/path/to/file.pptx \
  --pretty
```

成功生成最终 JSON 后，清理中间产物：

```bash
python3 scripts/cleanup_intermediate_outputs.py \
  --directory /absolute/path/to/output_or_workdir \
  --final-json /absolute/path/to/master_deck_merged.json
```

如果需要开发期排查识别遗漏，再单独运行审计：

```bash
python3 scripts/audit_recognition_output.py \
  /absolute/path/to/file.pptx \
  /absolute/path/to/master_deck_merged.json
```

## 产出结构

整套 PPT 的 JSON 顶层通常包含：

- `source_file`
- `slide_count`
- `deck_outline`
- `slides`
- 可选 `vision_tasks`

单页 slide 结构通常包含：

- `page_type`
- `title`
- `hierarchy`
- `layout_intent`
- `connectors`
- `structured_payload`
- 审计辅助字段，例如 `all_visible_text`、`labels`、`metrics`、`missing_risk`

字段含义和页面家族定义见 [references/page-schema.md](references/page-schema.md)。
可复用规则见 [references/learned-rules.json](references/learned-rules.json)。

## 标准工作流

1. 先检查同名 PDF 是否存在；如果缺失，先提醒用户确认是否继续。
2. 再检查当前模型是否支持视觉；如果不支持，先提醒用户切换模型。
3. 运行 `scripts/recognize_ppt_deck.py --vision-mode off`，先完成原生识别。
4. 识别器会自动检查同名 PDF，并导出 `output/screenshots/slide_N.png` 供视觉补全使用；不要依赖人工先运行截图导出脚本。
5. 如果识别结果中出现 `vision_tasks`，并且当前模型支持视觉，则必须直接查看对应截图并完成这些任务。
   - 对低文本覆盖率、图片占比高、`structured_payload` 为空或带有 `image-heavy` 风险的页面，识别器会发出 `slide_visual_recovery` 通用整页视觉任务。
   - `slide_visual_recovery` 必须补全整页主要可见文字、层级、指标、连接关系、页面类型和结构化 payload；不能只返回标题。
   - 专项任务例如 `timeline_recovery`、`logo_wall_group_recovery` 仍然优先保留，通用任务作为兜底补全整页遗漏。
6. 将视觉任务结果写入临时的 `vision_task_results.json`。
7. 运行 `scripts/apply_vision_tasks.py` 合并视觉结果，得到最终 merged JSON。
8. 运行 `scripts/cleanup_intermediate_outputs.py` 删除中间文件。
9. 默认只把这一份最终 JSON 作为交付结果返回给用户。

## 单轮完成要求

对于正常用户请求，不允许只停在第一次识别结果。

必须按下面顺序继续完成：

1. 先跑原生识别。
2. 如果 `vision_tasks` 非空，并且当前模型支持视觉，就立刻处理对应截图；尤其要完成 `slide_visual_recovery`，否则图片型页面会只剩标题。
3. 合并任务结果，生成最终 JSON。
4. 删除中间 JSON、任务结果 JSON 和默认不需要的审计文件。
5. 在同一轮中把最终 JSON 作为结果交付。

只有下面两种情况可以在完成前停下：

- 当前模型不支持视觉，必须先让用户切换模型
- 用户明确接受“没有 PDF、仅用 PPT 继续”的较低覆盖率

如果模型已经支持视觉，不允许再问用户：

- “要不要我继续处理 vision_tasks？”
- “要不要我使用视觉能力补全？”

这些都属于必须自动继续完成的步骤，而不是可选下一步。

## 输出约束

- 默认面向用户的最终输出必须只有一份 merged JSON。
- 不允许默认同时向用户交付多份 JSON，例如：
  - 审计 JSON
  - 中间识别 JSON
  - baseline JSON
  - diff JSON
- 任务结果 JSON
- `vision_task_results.json`、原始 task payload、审计报告、diff 报告都属于内部临时产物。
- 这些文件可以在执行过程中存在，但除非用户明确要求，否则不能作为最终交付物展示给用户。
- 当最终 merged JSON 已生成后，应默认删除这些中间文件，而不是把它们留在工作区作为并列结果。

## 硬性规则

- 除非用户明确要求，否则忽略 speaker notes。
- 优先使用原生 OOXML 结构，而不是 OCR。
- 对图片型页面，默认优先走 host vision 补全，不要求用户额外点头确认。
- 如果当前模型不支持视觉，必须在识别前提醒用户切换，不允许静默继续。
- 如果 PPT 没有同名 PDF，必须在识别前提醒用户是否继续，不允许静默继续。
- 如果已经发出了 `vision_tasks`，而当前模型支持视觉，模型必须自己继续完成，不得把它抛回给用户决策。
- 当最终 JSON 已成功生成后，默认要清理中间文件，避免工作区中同时留下多份阶段性 JSON。
- 不允许把时间线、并列分栏、logo 分组墙压平成普通列表。
- 不允许把两行一组的客户名 / 系统名单元静默压扁成无法恢复的普通字符串。
- 小页脚、小标签、底部区域、侧边窄列，只要有语义价值，就不能因为字小而丢掉。
- 如果页面中同时存在冲突数据集，必须显式并行保留，不能偷偷只保留一个版本。
- 如果下游生成结果不完整，应先修识别结果，而不是让生成阶段瞎猜。
- 不要停在 `vision_tasks`、中间 JSON 或临时结果上；只要环境支持，就继续完成并返回最终 merged JSON。

## Host Vision 协作协议

当使用 `--vision-mode off` 时，识别器应尽量先完成原生恢复，然后发出明确的 `vision_tasks`。

推荐的 host 工作流如下：

1. 检查当前模型是否支持视觉；如果不支持，先提醒用户切换。
2. 检查同名 PDF 是否存在；如果没有，先提醒用户是否继续。
3. 运行 `scripts/recognize_ppt_deck.py --vision-mode off`。
4. 把每个 `vision_task` 连同对应截图交给当前 IDE / 智能体自身处理；`slide_visual_recovery` 是整页兜底恢复任务，必须按截图重建该页的主要文本和结构语义。
5. 要求视觉侧只返回符合 `expected_schema` 的 JSON payload。
6. 将这些结果保存到内部临时文件 `vision_task_results.json`。
7. 运行 `scripts/apply_vision_tasks.py`，合并出最终 JSON。
8. 运行 `scripts/cleanup_intermediate_outputs.py`，删除中间 JSON、任务结果文件和审计文件，只保留最终 merged JSON。

`apply_vision_tasks.py` 支持以下几种结果格式：

- 顶层数组
- 或对象中包含以下任一键：
  - `vision_task_results`
  - `task_results`
  - `completed_tasks`
  - `results`

## 给宿主 IDE 的推荐说明

通过宿主智能体调用这个 Skill 时，建议使用类似下面的中文说明：

```text
请使用这个 Skill 完整识别目标 PPT。
在正式识别前，先检查你当前使用的模型是否支持视觉；如果不支持，请先提醒我切换到支持视觉的模型。
然后检查是否存在同名 PDF；如果缺失，请先提醒我补充 PDF，或让我确认是否接受仅用 PPT 继续识别。
如果识别过程中产生了 vision_tasks，且你当前模型支持视觉，请直接查看对应截图并继续完成视觉补充，不要停在中间结果。
默认最后只输出一份最终 merged JSON，不要额外输出 audit JSON、vision_task_results.json 或其他中间 JSON，除非我明确要求。
当最终 JSON 已经生成后，请顺手删除中间文件，避免用户在工作区看到 4 到 5 份阶段性 JSON。
```

## 当前支持的页面家族

识别器目前输出这些页面类型：

- `people-matrix`
- `timeline`
- `logo-wall`
- `awards-patents`
- `metrics`
- `peer-panels`
- `image-text`
- `chapter`
- `toc`
- `cover`
- `fallback`

## 适用边界

这个 Skill 最适合可编辑的 `.pptx`，也就是文字还保留在 OOXML 结构中的场景。

如果一整套 PPT 大多是：

- 截图页
- 扁平化图示
- 扫描页

那么：

- 文本覆盖率可能会下降
- connector 推断会更依赖视觉判断
- 仍然需要多模态补全

## 持续更新建议

当识别失败模式具有复用价值时，应沉淀成可复用规则。

优先记录这些问题：

- 页面类型误判模式
- connector 或 hierarchy 错误
- instruction_text 泄漏到正式内容
- 图片型页面遗漏的高发模式
- 某些页面应视为 `peer-panels` 而不是 `chapter` 的判别信号
