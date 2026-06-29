# 图生图规格

## 一、核心运行流程

run_mode:
  step1: 用户范围确认
  step2: 精准调度 rules/spec
  step3: 内容生成
  step4: 自检
  step5: 输出

skip_rule: >
  只调度当前任务涉及的模块，未涉及的一律跳过
  不调用全局完整规则集

## 二、用户范围确认

scope_confirm:
  trigger: 上传参考图后，或用户说"图生图""重绘""参考"

  theme: >
    用户想生成什么？（基于上传图或描述推断）
    示例：同款风格/人物写真/产品展示/场景重建

  platform: >
    目标平台是？
    若用户未指定，根据参考图特征推断（国内平台倾向中文描述）

  model: >
    使用什么模型？
    常见：SDXL/SD15/ComfyUI工作流/即梦/千问/其他

  habit: >
    用户偏好？（可跳过）
    示例：权重习惯/负面词偏好/特定参数设置

## 三、精准调度矩阵

dispatch_matrix:

  sd_platform:
    rules:
      - positive-build.md（句式结构）
      - negative-build.md（反向词）
    spec:
      - image-fields.md（字段激活规则）
    skip:
      - platform-syntax.md（SD全兼容，跳过平台特化）

  qwen_platform:
    rules:
      - positive-build.md（句式结构）
      - negative-build.md（反向词）
    spec:
      - image-fields.md（字段激活规则）
      - platform-syntax.md（国内平台语法：去除权重，中文描述）
    special:
      - qwen-plus-specific.md（如存在）

  dalle_platform:
    rules:
      - positive-build.md（句式结构）
    spec:
      - image-fields.md（字段激活规则）
    skip:
      - negative-build.md（DALL-E不适用反向词）
      - platform-syntax.md（DALL-E无需特化语法）

  custom_workflow:
    rules:
      - 按用户指定的工作流读取对应规则
    spec:
      - 按模型需求选择性加载
    note: 用户提供自定义工作流时，按其结构调度

## 四、图生图参数体系

param_fields:

  ref_type:
    name: 参考类型
    options:
      - "风格参考"（颜色/光影/氛围）
      - "构图参考"（视角/景深/布局）
      - "主体参考"（角色/物体外观）
      - "综合参考"（全部）

  ref_weight:
    name: 参考强度
    range: "0.1-1.0"
    default: "0.7"
    description: >
      0.1-0.3：轻微影响，保留大量创作自由度
      0.4-0.6：平衡型，原图特征明显
      0.7-1.0：强参考，贴近原图特征

  ref_stop:
    name: 参考终止点
    range: "0-100"
    default: "80"
    description: >
      何时停止参考图影响
      较低值：后期更自由发挥
      较高值：全程参考

  redraw_scale:
    name: 重绘幅度
    range: "0-1.0"
    default: "0.5"
    description: >
      0-0.3：微调，保留原图主体结构
      0.4-0.6：中等，原图元素大幅变化
      0.7-1.0：大幅，保留概念但几乎全新生成

  lora_blend:
    name: LoRA融合度
    range: "0-1.0"
    default: "1.0"
    note: 仅当使用LoRA时有效

  ip_adapter:
    name: IP-Adapter强度
    range: "0-1.0"
    default: "0.8"
    note: 仅当使用IP-Adapter时有效

## 五、参数推荐模板

param_preset:

  style_transfer:
    ref_type: "风格参考"
    ref_weight: "0.4-0.6"
    ref_stop: "60-70"
    redraw_scale: "0.5-0.7"
    use_case: "换风格不换主体"

  composition_keep:
    ref_type: "构图参考"
    ref_weight: "0.5-0.7"
    ref_stop: "50-60"
    redraw_scale: "0.4-0.6"
    use_case: "保留构图，换内容"

  character_consistent:
    ref_type: "主体参考"
    ref_weight: "0.7-0.9"
    ref_stop: "70-80"
    redraw_scale: "0.3-0.5"
    use_case: "角色一致性场景"

  creative_remix:
    ref_type: "综合参考"
    ref_weight: "0.3-0.5"
    ref_stop: "40-50"
    redraw_scale: "0.7-1.0"
    use_case: "高度创作自由度"

## 六、输出格式

output_format:

  header: >
    图生图提示词

  params_display:
    - "参考类型：{ref_type}"
    - "参考强度：{ref_weight}"
    - "重绘幅度：{redraw_scale}"
    - "参考终止：{ref_stop}"

  positive: >
    正向提示词：{内容}

  negative: >
    反向提示词：{内容}

  note: >
    提示：实际效果受模型和参数影响，建议先用低强度测试再调整

## 七、自检清单

self_check:
  must:
    - "参数组合合理（ref_weight与redraw_scale不冲突）"
    - "参考类型与用户需求匹配"
    - "平台语法规格已适配"
    - "输出格式符合规范"

  quality:
    - "提示词长度适中"
    - "无矛盾描述"
    - "安全校验通过"

  skip_verify: >
    未调度的模块不参与自检
