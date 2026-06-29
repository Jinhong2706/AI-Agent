# RAG增强模式

## 触发时机

trigger_conditions:
  repeat_request:
    description: "用户重复类似需求"
    check: "主体相似度>70% OR 风格相同且平台相同"
    action: "优先检索历史成功案例，复用参数包"

  new_platform:
    description: "冷门平台首次生成"
    check: "平台未在用户历史中出现"
    action: "检索platform_notes，获取该平台踩坑记录"

  reference_past:
    description: "用户明确引用历史"
    keywords: ["类似之前", "跟上次差不多", "风格参考", "还是那个"]
    action: "检索该用户最近3次成功案例"

  low_confidence:
    description: "模型置信度低于阈值"
    threshold: 0.6
    action: "检索相似案例增强参考"

  teach_mode:
    description: "教学模式案例支撑"
    action: "检索prompt_templates提供多样化示例"

## 增强流程

enhance_flow:
  step1: "用户输入 → 判定是否触发RAG"
  step2: "命中则检索 → 返回Top3候选"
  step3: "匹配度>80% → 直接复用，提示「参考历史风格」"
  step4: "匹配度60-80% → 基于检索结果微调"
  step5: "匹配度<60% → 正常生成，标记为冷启动"

## 检索字段权重

retrieval_weights:
  user_id: 0.3
  platform: 0.25
  style: 0.25
  subject_type: 0.15
  mood: 0.05

## 缓存策略

cache_strategy:
  ttl: "永久（用户偏好）/ 30天（通用模板）"
  invalidation: "用户主动说「换个风格」或「不要这个」"
  warm_up: "用户首次使用时预加载最近5次记录"
