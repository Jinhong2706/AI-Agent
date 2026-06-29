# 图片字段体系规格

## P0核心字段

field_p0:
  F-SUBJ:
    name: "主体描述"
    weight: "1.0-1.3"
    ratio: "25-35%"
    priority: "永不裁剪"

  F-STYL:
    name: "风格定位"
    weight: "1.0"
    ratio: "15-20%"
    priority: "永不裁剪"

  F-ENV:
    name: "环境背景"
    weight: "0.9-1.1"
    ratio: "15-20%"

  F-COMP:
    name: "构图视角"
    weight: "0.8-1.0"
    ratio: "5-10%"

## P1扩展字段

field_p1:
  F-LIGHT:
    name: "光影氛围"
    weight: "0.9-1.2"
    ratio: "10-15%"

  F-TEXTURE:
    name: "材质质感"
    weight: "0.9-1.1"
    ratio: "5-10%"

  F-TECH:
    name: "画质技术词"
    weight: "1.0-1.2"
    ratio: "3-5%"

  F-MOOD:
    name: "情绪氛围"
    weight: "0.8-1.0"
    ratio: "3-5%"

  F-COLOR:
    name: "色彩方案"
    weight: "0.8-1.0"
    ratio: "3-5%"

  F-DEPTH:
    name: "景深描述"
    weight: "0.8-1.0"
    ratio: "3-5%"

## P2增强字段

field_p2:
  F-ATMOS:
    name: "大气效果"
    trigger: "二级按需激活，一级跳过"

  F-SYMBOL:
    name: "象征元素"
    trigger: "二级按需激活，一级跳过"

  F-DETAIL:
    name: "微距细节"
    trigger: "二级按需激活，一级跳过"

  F-REF:
    name: "参考锚点"
    trigger: "二级按需激活，一级跳过"

## 画风类别判定

style_category:
  B_style:
    keywords: ["二次元", "动漫", "动漫风", "anime", "赛璐璐", "立绘", "手游", "原神", "碧蓝", "方舟"]
    category: "B类二次元"

  D_style:
    keywords: ["信息图", "图表", "流程图", "infographic", "科学", "示意图"]
    category: "D类信息图"

  C_style:
    keywords: ["混合", "创意", "拼贴"]
    category: "C类创意"

  A_style:
    default: true
    category: "A类写实"
