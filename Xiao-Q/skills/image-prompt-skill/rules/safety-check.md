# 安全校验规则

## 校验矩阵

check_matrix:
  portrait:
    condition: "真人照片/名人面容"
    level: P0
    action: "拒绝"
    message: "涉及肖像权，无法生成"

  violence:
    condition: "暴力内容"
    level: P0
    action: "拒绝"

  sexual:
    condition: "色情/性感内容"
    level: P0
    action: "拒绝"

  political:
    condition: "政治敏感"
    level: P0
    action: "拒绝"

  copyright:
    condition: "指定品牌标志/受版权角色"
    level: P1
    action: "改为通用描述替代"

  impossible:
    condition: "物理不可能的描述"
    level: P2
    action: "提示不阻断"
    message: "该描述可能无法准确生成"

## 执行流程

check_flow:
  step1: "肖像权检查"
  step2: "敏感内容检查"
  step3: "版权风险检查"
  step4: "生成可行性检查"
  step5: "通过则进入生成流程"

## 拒绝处理

reject:
  response: >
    根据问题类型输出对应message
    不提供替代方案
    终止后续流程
