# 正向提示词构建规则

## A类写实摄影

syntax_a:
  structure:
    - "主体描述 + 姿态动作于环境描述中，环境细节"
    - "摄影品类语义，构图视角，镜头焦段语义，景深描述"
    - "光影氛围，材质质感"
    - "风格定位，画质技术词"

  components:
    subject: "人物/物体 + 核心特征 + 姿态/动作"
    environment: "背景环境 + 环境细节"
    technique: "摄影类型 + 构图 + 焦段 + 景深"
    atmosphere: "光影 + 质感"
    style: "风格定位 + 画质词"

## B类二次元插画

syntax_b:
  structure:
    - "主体描述 + 角色外观部件，位于环境描述，细节描述"
    - "风格定位，构图视角"
    - "光影氛围，色彩方案"
    - "画质技术词"

  components:
    character: "角色名称/类型 + 外观特征 + 服装/配饰"
    environment: "位于 + 环境描述 + 细节"
    style: "风格定位 + 构图视角"
    mood: "光影氛围 + 色彩方案"
    quality: "画质技术词"

## C类聚焦特写

syntax_c:
  structure:
    - "主体描述的细节特写，微观质感描述"
    - "构图视角，景深描述"
    - "光影氛围，材质质感"
    - "风格定位，画质技术词"

  components:
    detail: "主体 + 特写角度 + 细节放大"
    texture: "微观质感 + 表面特征"
    composition: "构图 + 景深"
    atmosphere: "光影 + 质感"
    style: "风格 + 画质"

## D类信息图

syntax_d:
  structure:
    - "独立句式，信息图专用结构"
    - "含标注、箭头、图例等描述"

  components:
    layout: "整体布局 + 信息层级"
    elements: "标注 + 箭头 + 图例 + 颜色编码"
    data: "数据类型 + 可视化形式"

## 视频通用句式

syntax_video:
  structure:
    - "主体加运动描述"
    - "镜头视角描述"
    - "环境与交互描述"
    - "光影与氛围描述"
    - "风格与画质描述"

  format:
    - "自然叙事句"
    - "逗号分隔元素"
    - "句号分段逻辑"

## 组合描述规范

combination:
  required: "使用「主体 + 位于/处于 + 环境 + 环境细节」句式"
  forbidden: "禁止将主体与环境写成独立句子"

## 空间占比

proportion:
  contrast: "对比型主体占15-30%"
  balanced: "均衡型居中偏位"
  focus: "聚焦型特写不写占比"
