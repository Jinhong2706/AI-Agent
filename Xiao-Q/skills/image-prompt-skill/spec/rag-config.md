# RAG配置规格

## 入库内容

rag_corpus:
  prompt_templates:
    type: "优质提示词模板"
    fields: "[主题/风格/平台/正向词/反向词/评分/使用次数]"
    source: "用户确认的生成结果 >80分"

  style_packages:
    type: "风格参数包"
    fields: "[风格名/核心关键词/P0权重/推荐平台/适用场景]"
    source: "教学模式下沉淀的风格方案"

  platform_notes:
    type: "平台踩坑记录"
    fields: "[平台/模型/问题描述/解决方案/规避词]"
    source: "生成失败/效果差的修正记录"

  user_preferences:
    type: "用户习惯库"
    fields: "[用户ID/常用平台/偏好风格/规避词/默认参数]"
    source: "多次交互中归纳的偏好模式"

## 检索策略

retrieval_strategy:
  semantic_match:
    enabled: true
    threshold: 0.75
    top_k: 3

  keyword_match:
    enabled: true
    fields: "[平台, 风格, 主体类型]"

  hybrid:
    weight_semantic: 0.6
    weight_keyword: 0.4

## 更新机制

update_trigger:
  positive_feedback: "用户说「效果好」「保存」「这个风格不错」"
  negative_feedback: "用户说「不对」「重来」「不是这个感觉」→ 记录问题特征"

  auto_archive: "生成结果评分>=85分 → 自动入库"
  manual_save: "用户说「保存这个风格」→ 手动入库"
