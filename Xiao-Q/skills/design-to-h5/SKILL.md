---
title: 多源设计H5生成器
description: 参考页面布局截图、文案文档（PPT/txt/doc/pdf）、标注文案图片素材，生成带动画的响应式H5网页。支持PC端UI界面、移动端页面、图片淡入淡出、文字呼吸效果。触发词：设计转H5、截图转网页、文档生成H5、图片标注转H5、参考图生成网页、多源素材H5、设计稿还原、平面设计H5
summary: 支持多种输入源（截图、文案文档、图片素材）生成带动画效果的响应式H5网页，自动实现移动端+PC端自适应，支持淡入淡出、文字呼吸等动效。
author: WorkBuddy
version: 1.0.0
tags: [H5, 响应式, 多源输入, 截图识别, 文档解析, 图片素材, 动效, PC端, 移动端, 淡入淡出, 呼吸效果, 设计还原]
trigger_priority: 100
allowed-file-types: [.png, .jpg, .jpeg, .ppt, .pptx, .txt, .doc, .docx, .pdf]
output-format: [html, css, js]
---

# 多源设计H5生成器 Skill v1.0

## 版本更新

- **v1.0**: 首发版本，支持多源输入、响应式布局、动画效果

---

## 功能概述

本Skill支持多种输入源生成带动画效果的响应式H5网页：

| 功能模块 | 说明 |
|---------|------|
| 多源输入解析 | 支持截图、文案文档（PPT/txt/doc/pdf）、标注文案图片 |
| 布局识别 | 从截图识别页面结构、元素位置、层级关系 |
| 文案提取 | 从文档和图片素材中提取文案内容 |
| 响应式设计 | PC端UI界面 + 移动端页面自适应 |
| 动画效果 | 图片淡入淡出、文字鼠标滑过呼吸感 |
| 素材整理 | 自动整理图片素材、字体、图标资源 |

---

## 使用方法

### 基本语法

```
@skill://design-to-h5 @[截图路径] @[文案文档路径] @[标注图片路径] [动效选项]
```

### 示例

| 用户输入 | 效果 |
|---------|------|
| `@skill://design-to-h5 @screenshot.png` | 基于截图生成H5 |
| `@skill://design-to-h5 @screenshot.png @copy.txt` | 截图+文案生成 |
| `@skill://design-to-h5 @layout.png @doc.pptx @annotated.jpg` | 多源素材完整生成 |
| `@skill://design-to-h5 @design.png 移动端优先` | 移动端优先响应式 |
| `@skill://design-to-h5 @mockup.png 呼吸动效` | 添加文字呼吸效果 |

---

## 输入源处理

### 1. 截图/设计稿处理

对于页面布局截图，系统会进行以下处理：

```
┌─────────────────────────────────────────────────────────────┐
│                    截图解析流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │ 1.截图   │───▶│ 2.布局   │───▶│ 3.元素   │───▶│ 4.位置 │ │
│  │ 上传    │    │ 识别    │    │ 提取    │    │ 映射   │ │
│  └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│                                                             │
│  识别内容：背景色、文本区域、图片位置、按钮、图标、层级结构  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

布局识别策略：

- **背景色提取**：分析截图主色调作为页面背景
- **内容区域检测**：识别主体内容边界和留白区域
- **元素分类**：区分背景图、装饰图、文字区块、按钮等
- **网格系统**：建立响应式网格辅助定位

### 2. 文案文档解析

支持的文档格式及解析方式：

| 格式 | 解析方法 | 输出内容 |
|------|---------|---------|
| PPT/PPTX | 提取每页标题、正文、备注 | 标题文案、分点内容 |
| TXT | 直接读取文件内容 | 纯文本段落 |
| DOC/DOCX | 读取段落文本和标题样式 | 结构化文本 |
| PDF | 提取文本内容（图片PDF提取失败） | 纯文本内容 |

文档内容映射规则：

```javascript
// 文案映射配置
const copyMapping = {
    mainTitle: ['h1', '标题', '主标题', '#'],
    subTitle: ['h2', '副标题', 'subtitle'],
    bodyText: ['p', '正文', '段落', 'content'],
    button: ['按钮', 'button', 'cta'],
    caption: ['caption', '注释', '说明']
};

// 典型文案结构
const documentStructure = {
    hero: {           // 首屏大图区域
        title: '主标题文案',
        subtitle: '副标题文案',
        description: '描述文字'
    },
    features: [      // 特色/功能区块
        { title: '标题1', desc: '描述1' },
        { title: '标题2', desc: '描述2' }
    ],
    cta: {            // 行动号召
        text: '按钮文字',
        link: '#contact'
    },
    footer: {         // 页脚
        copyright: '版权信息'
    }
};
```

### 3. 标注图片素材处理

对于标注有文案信息的图片素材：

```
识别规则：
1. 图片文件名 → 区域标识（如 banner.jpg、feature-1.png）
2. 标注层级 → 内容优先级
3. 组合素材 → 多图轮播/画廊
```

---

## 核心算法

### 1. 布局网格系统

```javascript
// 响应式网格配置
const gridConfig = {
    mobile: {
        columns: 4,
        gutter: 16,      // px
        margin: 16,
        maxWidth: 375    // 移动端基准宽度
    },
    tablet: {
        columns: 8,
        gutter: 24,
        margin: 24,
        maxWidth: 768
    },
    desktop: {
        columns: 12,
        gutter: 24,
        margin: 32,
        maxWidth: 1440
    }
};

// 容器宽度断点
const breakpoints = {
    sm: '576px',    // 大手机
    md: '768px',    // 平板
    lg: '1024px',   // 小桌面
    xl: '1280px',   // 大桌面
    xxl: '1536px'   // 超大屏
};
```

### 2. 响应式布局算法

```javascript
// 布局类型识别
const layoutTypes = {
    SINGLE_COLUMN: '单列布局',      // 移动端优先
    TWO_COLUMN: '双列布局',         // 左右分栏
    GRID: '网格布局',               // 多项目排列
    HERO: 'Hero大图布局',           // 首屏突出
    CARDS: '卡片布局'               // 均等卡片
};

// 元素响应式策略
function getResponsiveStrategy(element) {
    // 优先级：移动端优先
    const mobile = element.mobile || element;
    const tablet = element.tablet || element;
    const desktop = element.desktop || element;

    return {
        width: {
            mobile: mobile.width || '100%',
            tablet: tablet.width || 'calc(50% - 12px)',
            desktop: desktop.width || element.width || 'auto'
        },
        flexGrow: mobile.flex || 0,
        flexShrink: mobile.shrink || 1
    };
}
```

### 3. 动画效果配置

```javascript
// ==================== 淡入淡出效果配置 ====================
const fadeConfig = {
    duration: 600,                    // 动画时长(ms)
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    staggerDelay: 150,               // 交错延迟(ms)
    threshold: 0.1,                   // 触发阈值（进入可视区域）
    once: true                        // 是否只触发一次
};

// 淡入动画关键帧
const fadeKeyframes = {
    opacity: [0, 1],
    transform: ['translateY(20px)', 'translateY(0)']
};

// 触发时机
const triggerEvents = ['scroll', 'touchmove', 'resize'];
```

```javascript
// ==================== 呼吸效果配置 ====================
const breathConfig = {
    duration: 2500,                   // 单次呼吸周期(ms)
    scaleRange: [1, 1.03],            // 缩放范围
    filterRange: ['brightness(1)', 'brightness(1.1)'],
    easing: 'ease-in-out',
    hoverOnly: true                   // 仅悬停触发
};

// 呼吸动画关键帧
const breathKeyframes = {
    '0%, 100%': {
        transform: 'scale(1)',
        filter: 'brightness(1)',
        textShadow: 'none'
    },
    '50%': {
        transform: 'scale(1.03)',
        filter: 'brightness(1.1)',
        textShadow: '0 0 20px rgba(255,255,255,0.3)'
    }
};
```

---

## 动画效果模板

### 1. 图片淡入淡出 (FadeIn)

```css
/* ==================== 淡入淡出动画 ==================== */

/* 入场淡入淡出 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 交错入场动画类 */
.animate-fade-in {
    opacity: 0;
    animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* 交错延迟 */
.animate-delay-1 { animation-delay: 0.1s; }
.animate-delay-2 { animation-delay: 0.2s; }
.animate-delay-3 { animation-delay: 0.3s; }
.animate-delay-4 { animation-delay: 0.4s; }
.animate-delay-5 { animation-delay: 0.5s; }

/* 滚动触发的淡入 */
.fade-in-on-scroll {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s ease, transform 0.6s ease;
}

.fade-in-on-scroll.visible {
    opacity: 1;
    transform: translateY(0);
}

/* 移动端触摸触发 */
@media (hover: none) {
    .fade-in-on-scroll.visible {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### 2. 文字呼吸效果 (Breath on Hover)

```css
/* ==================== 文字呼吸动效 ==================== */

/* 基础呼吸效果 */
@keyframes textBreath {
    0%, 100% {
        transform: scale(1);
        text-shadow: none;
    }
    50% {
        transform: scale(1.02);
        text-shadow: 0 0 10px currentColor;
    }
}

/* 悬停呼吸类 */
.text-breath:hover {
    animation: textBreath 2.5s ease-in-out infinite;
}

/* 呼吸+发光效果 */
@keyframes textGlow {
    0%, 100% {
        text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
        transform: scale(1);
    }
    50% {
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.6),
                     0 0 30px rgba(255, 255, 255, 0.4);
        transform: scale(1.03);
    }
}

.text-glow:hover {
    animation: textGlow 2s ease-in-out infinite;
}

/* 标题专用呼吸 */
.title-breath:hover {
    animation: textBreath 2.5s ease-in-out infinite;
    color: #3B82F6;
    transition: color 0.3s ease;
}

/* 按钮文字呼吸 */
.btn-text-breath:hover {
    animation: textBreath 2s ease-in-out infinite;
    letter-spacing: 0.05em;
}
```

### 3. 图片悬停效果

```css
/* ==================== 图片悬停效果 ==================== */

/* 图片淡入淡出+缩放 */
.image-hover-fade {
    position: relative;
    overflow: hidden;
}

.image-hover-fade::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.5), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.image-hover-fade:hover::after {
    opacity: 1;
}

.image-hover-fade img {
    transition: transform 0.5s ease, opacity 0.5s ease;
}

.image-hover-fade:hover img {
    transform: scale(1.05);
    opacity: 0.9;
}

/* 图片切换淡入淡出 */
.image-switch {
    position: relative;
}

.image-switch img {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.5s ease;
}

.image-switch img:first-child {
    opacity: 1;
}

.image-switch:hover img:first-child {
    opacity: 0;
}

.image-switch:hover img:last-child {
    opacity: 1;
}
```

### 4. 综合动效组合

```css
/* ==================== 综合动效 ==================== */

/* 卡片悬停综合效果 */
.card-hover {
    transition: transform 0.3s ease, 
                box-shadow 0.3s ease,
                opacity 0.3s ease;
}

.card-hover:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.card-hover:hover .card-image {
    animation: fadeInScale 0.5s ease forwards;
}

.card-hover:hover .card-title {
    animation: textBreath 2s ease-in-out infinite;
}

/* 按钮综合效果 */
.btn-hover {
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.btn-hover::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(45deg, transparent, rgba(255,255,255,0.2), transparent);
    transform: translateX(-100%);
    transition: transform 0.5s ease;
}

.btn-hover:hover::before {
    transform: translateX(100%);
}

.btn-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.btn-hover:hover .btn-text {
    animation: textBreath 2s ease-in-out infinite;
}
```

---

## 响应式模板

### 1. 移动端优先断点系统

```css
/* ==================== 响应式断点 ==================== */

/* 基础（移动端） */
.container {
    width: 100%;
    max-width: 100%;
    padding: 0 16px;
}

/* 平板 (≥768px) */
@media (min-width: 768px) {
    .container {
        max-width: 720px;
        padding: 0 24px;
    }
}

/* 桌面 (≥1024px) */
@media (min-width: 1024px) {
    .container {
        max-width: 960px;
        padding: 0 32px;
    }
}

/* 大桌面 (≥1280px) */
@media (min-width: 1280px) {
    .container {
        max-width: 1200px;
    }
}
```

### 2. 移动端布局

```css
/* ==================== 移动端布局 ==================== */

.h5-mobile-layout {
    /* 单列流式布局 */
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* 全宽图片 */
.mobile-full-image {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
}

/* 全宽区块 */
.mobile-full-section {
    width: 100%;
    padding: 24px 16px;
    margin: 0;
}

/* 移动端间距 */
.mobile-spacing {
    padding: 20px 16px;
    gap: 12px;
}

/* 移动端字号 */
.mobile-text {
    font-size: 14px;
    line-height: 1.6;
}

.mobile-title {
    font-size: 20px;
    font-weight: 600;
}
```

### 3. PC端布局

```css
/* ==================== PC端布局 ==================== */

.h5-desktop-layout {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 24px;
    max-width: 1440px;
    margin: 0 auto;
}

/* 常见布局 */
.desktop-hero {
    grid-column: 1 / -1;  /* 全宽 */
}

.desktop-sidebar {
    grid-column: 1 / 4;    /* 左侧边栏 */
}

.desktop-content {
    grid-column: 4 / 13;   /* 主内容区 */
}

/* 双列布局 */
.desktop-two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
}

/* 三列布局 */
.desktop-three-col {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 32px;
}

/* PC端间距 */
.desktop-spacing {
    padding: 48px 32px;
    gap: 24px;
}

/* PC端字号 */
.desktop-text {
    font-size: 16px;
    line-height: 1.8;
}

.desktop-title {
    font-size: 32px;
    font-weight: 700;
}
```

### 4. 响应式隐藏/显示

```css
/* ==================== 响应式显示控制 ==================== */

/* 默认隐藏移动端内容 */
.hide-mobile { display: none; }

/* 移动端隐藏 */
@media (max-width: 767px) {
    .hide-mobile { display: block; }
    .show-mobile-only { display: none; }
}

/* 桌面隐藏 */
@media (min-width: 768px) {
    .show-mobile-only { display: block; }
    .hide-desktop { display: none; }
}
```

---

## 完整HTML模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>多源设计H5 - 响应式动效页面</title>
    <style>
        /* ==================== CSS变量定义 ==================== */
        :root {
            /* 颜色系统 */
            --color-primary: #3B82F6;
            --color-secondary: #1E293B;
            --color-text: #333333;
            --color-text-light: #666666;
            --color-bg: #ffffff;
            --color-bg-alt: #f8fafc;

            /* 间距系统 */
            --spacing-xs: 8px;
            --spacing-sm: 12px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;

            /* 动画配置 */
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
            --breath-duration: 2.5s;
            --fade-duration: 0.6s;
        }

        /* ==================== 基础重置 ==================== */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--color-text);
            line-height: 1.6;
            background: var(--color-bg);
            -webkit-font-smoothing: antialiased;
        }

        /* ==================== 容器系统 ==================== */
        .container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 var(--spacing-md);
        }

        @media (min-width: 768px) {
            .container {
                padding: 0 var(--spacing-lg);
            }
        }

        /* ==================== 动画基础类 ==================== */
        /* 淡入淡出动画 */
        .fade-in {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity var(--fade-duration) ease,
                        transform var(--fade-duration) ease;
        }

        .fade-in.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* 交错延迟 */
        .delay-1 { transition-delay: 0.1s; }
        .delay-2 { transition-delay: 0.2s; }
        .delay-3 { transition-delay: 0.3s; }
        .delay-4 { transition-delay: 0.4s; }
        .delay-5 { transition-delay: 0.5s; }

        /* ==================== 文字呼吸效果 ==================== */
        .text-breath {
            display: inline-block;
            transition: color var(--transition-fast);
        }

        .text-breath:hover {
            animation: breath var(--breath-duration) ease-in-out infinite;
            color: var(--color-primary);
        }

        @keyframes breath {
            0%, 100% {
                transform: scale(1);
                text-shadow: none;
            }
            50% {
                transform: scale(1.03);
                text-shadow: 0 0 15px currentColor;
            }
        }

        /* 标题呼吸 */
        .title-breath {
            transition: color var(--transition-normal);
        }

        .title-breath:hover {
            animation: breath var(--breath-duration) ease-in-out infinite;
        }

        /* ==================== 图片效果 ==================== */
        .img-fade {
            transition: opacity var(--transition-normal),
                        transform var(--transition-slow);
        }

        .img-fade:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }

        .img-hover-zoom {
            overflow: hidden;
        }

        .img-hover-zoom img {
            transition: transform var(--transition-slow);
        }

        .img-hover-zoom:hover img {
            transform: scale(1.08);
        }

        /* ==================== Hero区域 ==================== */
        .hero {
            position: relative;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--color-secondary) 0%, #334155 100%);
            overflow: hidden;
        }

        .hero-content {
            position: relative;
            z-index: 2;
            text-align: center;
            padding: var(--spacing-lg);
            max-width: 800px;
        }

        .hero-title {
            font-size: clamp(32px, 8vw, 64px);
            font-weight: 700;
            color: white;
            margin-bottom: var(--spacing-md);
            animation: fadeInUp 0.8s ease forwards;
        }

        .hero-title:hover {
            animation: breath 2.5s ease-in-out infinite;
        }

        .hero-subtitle {
            font-size: clamp(16px, 3vw, 20px);
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: var(--spacing-xl);
            animation: fadeInUp 0.8s ease 0.2s forwards;
            opacity: 0;
        }

        .hero-cta {
            animation: fadeInUp 0.8s ease 0.4s forwards;
            opacity: 0;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ==================== 按钮样式 ==================== */
        .btn {
            display: inline-block;
            padding: var(--spacing-sm) var(--spacing-lg);
            font-size: 16px;
            font-weight: 600;
            text-align: center;
            text-decoration: none;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all var(--transition-normal);
        }

        .btn-primary {
            background: var(--color-primary);
            color: white;
        }

        .btn-primary:hover {
            background: #2563eb;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:hover .btn-text {
            animation: breath 2s ease-in-out infinite;
        }

        /* ==================== 特色区块 ==================== */
        .features {
            padding: var(--spacing-2xl) 0;
            background: var(--color-bg-alt);
        }

        .section-title {
            text-align: center;
            font-size: clamp(28px, 5vw, 40px);
            font-weight: 700;
            color: var(--color-secondary);
            margin-bottom: var(--spacing-2xl);
        }

        .section-title:hover {
            animation: breath 2.5s ease-in-out infinite;
            color: var(--color-primary);
        }

        .features-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: var(--spacing-lg);
        }

        @media (min-width: 768px) {
            .features-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (min-width: 1024px) {
            .features-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        .feature-card {
            background: white;
            border-radius: 16px;
            padding: var(--spacing-lg);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: transform var(--transition-normal),
                        box-shadow var(--transition-normal);
        }

        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
        }

        .feature-card:hover .feature-title {
            animation: breath 2s ease-in-out infinite;
        }

        .feature-card:hover .feature-img img {
            animation: fadeInScale 0.5s ease forwards;
        }

        @keyframes fadeInScale {
            from {
                opacity: 0.8;
                transform: scale(1);
            }
            to {
                opacity: 1;
                transform: scale(1.05);
            }
        }

        .feature-img {
            width: 100%;
            height: 200px;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: var(--spacing-md);
        }

        .feature-img img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform var(--transition-slow);
        }

        .feature-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--color-secondary);
            margin-bottom: var(--spacing-sm);
            transition: color var(--transition-fast);
        }

        .feature-desc {
            font-size: 14px;
            color: var(--color-text-light);
            line-height: 1.7;
        }

        /* ==================== 响应式隐藏/显示 ==================== */
        .mobile-only {
            display: block;
        }

        .desktop-only {
            display: none;
        }

        @media (min-width: 768px) {
            .mobile-only {
                display: none;
            }
            .desktop-only {
                display: block;
            }
        }

        /* ==================== 页脚 ==================== */
        .footer {
            background: var(--color-secondary);
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
            padding: var(--spacing-xl) var(--spacing-md);
        }

        .footer-link {
            color: white;
            text-decoration: none;
            transition: color var(--transition-fast);
        }

        .footer-link:hover {
            animation: breath 2s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <!-- Hero区域 -->
    <section class="hero">
        <div class="hero-content">
            <h1 class="hero-title title-breath">多源设计H5生成器</h1>
            <p class="hero-subtitle">支持截图、文档、图片素材，一键生成响应式动效页面</p>
            <div class="hero-cta">
                <a href="#features" class="btn btn-primary">
                    <span class="btn-text text-breath">开始使用</span>
                </a>
            </div>
        </div>
    </section>

    <!-- 特色区块 -->
    <section class="features" id="features">
        <div class="container">
            <h2 class="section-title">核心功能</h2>
            <div class="features-grid">
                <div class="feature-card fade-in">
                    <div class="feature-img img-hover-zoom">
                        <img src="assets/feature-1.jpg" alt="多源输入" loading="lazy">
                    </div>
                    <h3 class="feature-title">多源输入</h3>
                    <p class="feature-desc">支持截图、PPT、文档、图片等多种素材格式</p>
                </div>
                <div class="feature-card fade-in delay-1">
                    <div class="feature-img img-hover-zoom">
                        <img src="assets/feature-2.jpg" alt="响应式设计" loading="lazy">
                    </div>
                    <h3 class="feature-title">响应式设计</h3>
                    <p class="feature-desc">自动适配移动端和PC端，提供最佳浏览体验</p>
                </div>
                <div class="feature-card fade-in delay-2">
                    <div class="feature-img img-hover-zoom">
                        <img src="assets/feature-3.jpg" alt="动效丰富" loading="lazy">
                    </div>
                    <h3 class="feature-title">动效丰富</h3>
                    <p class="feature-desc">淡入淡出、呼吸效果、悬停交互应有尽有</p>
                </div>
            </div>
        </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
        <p>&copy; 2026 <a href="#" class="footer-link">多源设计H5</a>. All rights reserved.</p>
    </footer>

    <script>
        // ==================== 滚动动画触发 ====================
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const fadeInObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        // 观察所有需要淡入的元素
        document.querySelectorAll('.fade-in').forEach(el => {
            fadeInObserver.observe(el);
        });

        // ==================== 移动端触摸效果 ====================
        // 在移动端使用 touchstart 模拟 hover
        if ('ontouchstart' in window) {
            document.querySelectorAll('.img-fade, .img-hover-zoom').forEach(el => {
                el.addEventListener('touchstart', function() {
                    this.classList.add('touch-active');
                });
                el.addEventListener('touchend', function() {
                    this.classList.remove('touch-active');
                });
            });
        }

        // ==================== 平滑滚动 ====================
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // ==================== 图片懒加载 ====================
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.style.opacity = '0';
                        img.style.transition = 'opacity 0.5s ease';
                        img.onload = () => {
                            img.style.opacity = '1';
                        };
                        imageObserver.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        }
    </script>
</body>
</html>
```

---

## 工作流程

```
┌────────────────────────────────────────────────────────────────┐
│                    多源设计H5生成流程                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │ 1.素材   │───▶│ 2.布局   │───▶│ 3.内容   │───▶│ 4.动效   │ │
│  │ 收集    │    │ 分析    │    │ 提取    │    │ 设计    │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│       │               │               │               │        │
│       ▼               ▼               ▼               ▼        │
│  截图/文档/图片   区域划分      文案/图片/样式    淡入/呼吸      │
│                                                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│  │ 5.响应式 │───▶│ 6.生成   │───▶│ 7.预览   │                 │
│  │ 设计    │    │ 代码    │    │ 测试    │                 │
│  └──────────┘    └──────────┘    └──────────┘                 │
│       │               │               │                        │
│       ▼               ▼               ▼                        │
│  移动端/PC端     HTML/CSS/JS    浏览器验证                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| 截图模糊无法识别 | 提供高清截图（≥2x分辨率） |
| 文档编码乱码 | 确认文档编码为UTF-8 |
| 移动端动画不流畅 | 使用transform/opacity优化性能 |
| 文字呼吸效果触发延迟 | 使用will-change预提示浏览器 |
| 图片加载闪烁 | 使用blur-up或skeleton占位 |

---

## 扩展功能

### 1. 分享功能（可选）

```javascript
// 分享组件配置
const shareConfig = {
    title: '多源设计H5',
    desc: '使用多源设计H5生成器创建的精美页面',
    imgUrl: 'assets/share.jpg',
    platforms: ['weixin', 'weibo', 'qq', 'copy']
};
```

### 2. 统计埋点（可选）

```javascript
// 页面统计配置
const analyticsConfig = {
    pageView: true,           // 页面浏览
    clickHeatmap: true,        // 点击热力图
    scrollDepth: true,         // 滚动深度
    animationTrigger: true     // 动画触发统计
};
```

---

## 依赖环境

### Python环境（用于文档解析）

```bash
pip install python-pptx python-docx PyPDF2 Pillow
```

### Node.js（可选，用于本地预览）

```bash
npx serve .
```

---

## 示例输出

基于截图+文案生成的H5页面包含：

- 响应式布局（移动端+PC端自适应）
- 图片淡入淡出效果
- 文字鼠标滑过呼吸感
- 悬停交互动画
- 平滑滚动过渡
- 懒加载优化
