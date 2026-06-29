# 视频字段体系规格

## P0核心字段

field_p0:
  V-SUBJ:
    name: "主体加运动"
    weight: "1.0-1.3"
    note: "包含主体描述和运动状态"

  V-CAM:
    name: "运镜描述"
    weight: "1.0-1.2"
    note: "镜头运动方式"

  V-ENV:
    name: "环境与交互"
    weight: "0.9-1.1"
    note: "背景环境和主体交互"

  V-LIGHT:
    name: "光影与氛围"
    weight: "0.9-1.2"
    note: "光线和整体氛围"

## P1扩展字段

field_p1:
  V-DUR:
    name: "时长节奏"
    note: "视频时长和节奏感"

  V-TRANS:
    name: "转场方式"
    note: "镜头切换方式"

  V-FOCUS:
    name: "焦点变化"
    note: "对焦变化"

  V-TEXTURE:
    name: "材质质感"
    note: "表面质感"

  V-TECH:
    name: "画质技术词"
    note: "渲染/拍摄技术"

  V-MOOD:
    name: "情绪氛围"
    note: "情感传达"

## P2增强字段

field_p2:
  V-ATMOS:
    name: "大气效果"
    trigger: "三级按需激活"

  V-SYMBOL:
    name: "象征元素"
    trigger: "三级按需激活"

  V-SOUND:
    name: "声音暗示"
    trigger: "三级按需激活"

  V-REF:
    name: "参考锚点"
    trigger: "三级按需激活"

## 动态检测

dynamic_check:
  keywords:
    - "奔跑"
    - "跳跃"
    - "旋转"
    - "战斗"
    - "子弹时间"
    - "飘动"
    - "流动"
    - "爆发"
    - "挥舞"
    - "冲刺"
    - "坠落"

  default:
    video_mode: true
    note: "视频模式默认含动态"

  user_input:
    has_dynamic: "用户输入含动态关键词"
    no_dynamic: "用户未提及则按需判断"
