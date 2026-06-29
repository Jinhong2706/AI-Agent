# 视频反编译规格

## 分析维度详解

dimension_F-DYNAMIC:
  name: "动态描述"
  aspects:
    subject_motion: "主体运动（位移/旋转/形变）"
    env_motion: "环境变化（风吹/水流/云动/粒子）"
    effect_motion: "特效运动（爆炸/闪光/魔法）"
  output: "分层次描述各元素运动状态"

dimension_F-LENS:
  name: "镜头语言"
  types:
    push_in: "推镜（靠近主体）"
    pull_out: "拉镜（远离主体）"
    pan: "横摇（左右扫视）"
    tilt: "俯仰（上下扫视）"
    tracking: "跟拍（追焦移动主体）"
    static: "固定镜头"
    drone: "航拍视角"
    dolly: "移动轨"
    handheld: "手持晃动感"
  output: "镜头运动类型 + 速度"

dimension_F-TRANS:
  name: "转场节奏"
  types:
    cut: "瞬切（无过渡）"
    fade: "渐变（淡入淡出）"
    dissolve: "叠化"
    wipe: "擦除"
    effect: "特效转场"
  output: "转场类型 + 时长"

dimension_F-TEMPO:
  name: "时长感"
  types:
    slow: "慢节奏（氛围营造）"
    normal: "匀速叙事"
    fast: "快节奏（动感/紧张）"
    variable: "变速（慢动作/快动作）"
  output: "整体节奏描述"

dimension_F-STYL:
  name: "视觉风格"
  aspects:
    - "色调倾向"
    - "光影风格"
    - "运镜连贯性"
    - "画面锐度"
  output: "视觉风格描述"

dimension_F-TECH:
  name: "技术特征"
  markers:
    - "帧率特征（24/30/60fps）"
    - "稳定器痕迹"
    - "特效合成痕迹"
    - "AI生成特征（如有）"
  output: "技术特征列表"

## 输出格式

output_template: |
  动态描述：{F-DYNAMIC}
  镜头语言：{F-LENS}
  转场节奏：{F-TRANS}
  时长感：{F-TEMPO}
  视觉风格：{F-STYL}
  技术特征：{F-TECH}
  ---
  可选操作：
  1. 基于此描述生成新视频
  2. 以此为参考进行图生视频
  3. 仅保存描述

## 备注

disclaimer: "此描述为基于视觉理解的视频分析，无法还原原始生成参数，仅供参考与二次创作。"
