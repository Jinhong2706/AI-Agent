# 平台语法规格

## 平台分类

platform_category:
  en_platform:
    - "Midjourney"
    - "Stable Diffusion"
    - "Flux"
    - "DALL-E"

  zh_platform:
    - "千问"
    - "豆包"
    - "即梦"
    - "文心一格"
    - "混元"
    - "可灵"
    - "Sora"
    - "Runway"
    - "Pika"
    - "Kling"

## 图片平台语法

### Midjourney

mj_syntax:
  language: "英文"
  format: "自然语言 + 参数后缀"
  bracket: "不用括号权重"
  common_params:
    - "--ar 宽高比"
    - "--q 画质"
    - "--s 风格化"
    - "--style raw"
    - "--niji 二次元"
  negative: "反向提示词不用权重"

### Stable Diffusion

sd_syntax:
  language: "英文"
  format: "完整兼容括号权重"
  bracket_basic: "括号表示基本权重"
  bracket_precise: "冒号+数字精确权重如(1.5)"
  negative: "反向提示词不添加权重"

### Flux

flux_syntax:
  language: "英文"
  format: "完整自然语言长句，叙事性为主"
  bracket: "括号权重有限"
  weight_method: "权重通过前置排序实现"

### DALL-E

dalle_syntax:
  language: "英文"
  format: "叙事性自然语言，完整句式"
  special: "移除所有特殊语法"

### 国内图片平台

domestic_image_syntax:
  language: "全部中文"
  bracket: "移除所有权重符号，转为自然语言描述"
  convert_rule:
    single_bracket: "比较/较为"
    double_bracket: "非常/很"
    triple_bracket: "极其/极度"

## 视频平台语法

### 国际视频平台

intl_video_syntax:
  language: "英文为主"
  format: "自然叙事句"
  bracket: "不用括号"
  weight: "不用数值权重"
  symbol: "不用特殊符号"
  sep: "逗号分隔关键元素，句号分段"

### 国内视频平台

zh_video_syntax:
  language: "全中文描述"
  format: "自然叙事句"
  bracket: "不用括号"
  weight: "不用数值权重"
  symbol: "不用特殊符号"
  english: "不堆英文关键词"
  sep: "逗号分隔关键元素，句号分段"

## 权重转换对照

weight_convert:
  en_sd:
    "(word)": "单层权重"
    "((word))": "双层权重"
    "(((word)))": "三层权重"
    "(word:1.5)": "精确权重"

  zh_domestic:
    "(word)": "比较/较为"
    "((word))": "非常/很"
    "(((word)))": "极其/极度"
