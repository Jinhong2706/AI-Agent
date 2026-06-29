# 图片反编译规格

## 分析维度详解

dimension_F-SUBJ:
  name: "主体识别"
  focus:
    - "人物外观特征（发色/瞳色/体型/表情）"
    - "物体核心形态（形状/材质/比例）"
    - "场景核心构成元素"
  output: "一段完整的自然语言描述"

dimension_F-STYL:
  name: "风格判定"
  categories:
    realistic: "写实摄影（相机拍摄质感）"
    anime: "二次元（动漫/立绘/赛璐璐）"
    oil: "油画风格（笔触感/光油层）"
    watercolor: "水彩风格（透明感/晕染）"
    illustration: "商业插画（精致细节）"
    concept: "概念设计（氛围感）"
    pixel: "像素风格"
  output: "主风格 + 可能的混合风格"

dimension_F-ENV:
  name: "环境背景"
  aspects:
    - "室内/室外"
    - "自然/人工"
    - "具体场景类型"
    - "背景元素丰富度"
  output: "一句话环境描述"

dimension_F-COMP:
  name: "构图视角"
  types:
    eye_level: "平视"
    high_angle: "俯视"
    low_angle: "仰视"
    close_up: "特写"
    full_shot: "全景"
    bust: "半身"
    waist: "腰部以上"
    knee: "膝部以上"
    full: "全身"
  output: "构图类型 + 主体位置"

dimension_F-LIGHT:
  name: "光影氛围"
  types:
    warm: "暖光（2700K-3500K）"
    cool: "冷光（5500K以上）"
    back: "逆光（轮廓光）"
    soft: "柔光（散射光）"
    hard: "硬光（直射光）"
    rim: "边缘光"
    volumetric: "体积光"
  output: "光源方向 + 光质"

dimension_F-COLOR:
  name: "配色方案"
  analysis:
    - "主色调"
    - "辅助色"
    - "对比色使用"
    - "饱和度高低"
  output: "配色描述 + 色块占比"

dimension_F-TECH:
  name: "技术特征"
  markers:
    - "笔触风格（精细/粗犷/涂抹）"
    - "纹理特征（光滑/粗糙/颗粒）"
    - "噪点风格（胶片/数字/AI特征）"
    - "后期痕迹（HDR/调色痕迹）"
  output: "技术特征列表"

## 输出格式

output_template: |
  主体描述：{F-SUBJ}
  风格定位：{F-STYL}
  环境背景：{F-ENV}
  构图视角：{F-COMP}
  光影氛围：{F-LIGHT}
  配色方案：{F-COLOR}
  技术特征：{F-TECH}
  ---
  可选操作：
  1. 基于此描述生成新图
  2. 以此为参考图进行图生图
  3. 仅保存描述

## 备注

disclaimer: "此提示词为基于视觉理解的描述，无法还原原始生成参数，仅供参考与二次创作。"
