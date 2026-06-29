# 反向提示词生成规则

## 图片三层结构

### 第一层：基础屏蔽

base_image:
  always:
    - "模糊"
    - "低分辨率"
    - "畸变"
    - "多余肢体"
    - "文字水印"
    - "丑陋"
    - "失真"

### 第二层：画风专属

style_image:
  A_class:
    name: "写实摄影"
    add:
      - "过曝"
      - "欠曝"
      - "噪点"
      - "杂乱元素"
      - "结构崩坏"

  B_class:
    name: "二次元插画"
    add:
      - "3D render"
      - "realistic"
      - "photorealistic"
      - "photograph"
      - "bad anatomy"
      - "bad hands"
      - "missing fingers"

  C_class:
    name: "创意混合"
    add: "继承A类+B类"

  D_class:
    name: "信息图"
    add:
      - "cluttered labels"
      - "missing annotations"
      - "wrong arrows"
      - "confusing colors"
      - "unreadable text"
      - "incorrect science"

### 第三层：用户规避

user_avoid:
  condition: "用户明确不要的元素"
  action: "按需追加"

## 安全追加

safety_always:
  - "copyrighted character"
  - "celebrity likeness"
  - "political content"
  - "explicit content"
  - "violent content"

## 总量控制

count_control:
  image: "去重后10-25组"
  video: "去重后10-20组"

## 视频四层结构

### 第一层：基础视觉伪影

base_video:
  - "模糊"
  - "抖动"
  - "噪点"
  - "色块"

### 第二层：运动逻辑伪影

motion_artifact:
  add:
    - "不自然运动"
    - "物体穿模"
    - "物理逻辑错误"
    - "动作僵硬"

### 第三层：类型专属

type_video:
  select_by_class:
    - "按A/B/C/D类选择"

### 第四层：用户规避

user_avoid_video:
  condition: "用户明确不要的元素"
  action: "按需追加"
