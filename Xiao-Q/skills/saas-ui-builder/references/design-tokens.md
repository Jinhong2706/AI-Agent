# 设计令牌 (Design Tokens)

## 颜色 (Colors)

### 品牌色
| Token | 值 | 用途 |
|-------|-----|------|
| brand.primary | #2249F8 | 主色（碳擎蓝） |
| brand.primaryHover | #647FFA | 主色悬停 |
| brand.primaryPressed | #1B3AC6 | 主色按下 |
| brand.primaryDisabled | #90A4FB | 主色禁用 |
| brand.secondary | #35C476 | 次要色（绿色） |
| brand.light | #EEF3FF | 浅色背景 |
| brand.lightHover | #E0E9FF | 浅色悬停 |

### 语义色
| Token | 值 | 用途 |
|-------|-----|------|
| text.primary | #333333 | 主文字 |
| text.secondary | #666666 | 次要文字 |
| text.tertiary | #999999 | 三级文字 |
| text.placeholder | #CCCCCC | 占位符 |
| text.white | #FFFFFF | 白色文字 |
| text.link | #2249F8 | 链接文字 |
| border.default | #DDDDDD | 默认边框 |
| border.muted | #CCCCCC | 弱边框 |
| border.input | #D9D9D9 | 输入框边框 |
| border.hover | #EEEEEE | 悬停边框 |
| surface.page | #F2F2F6 | 页面背景 |
| surface.card | #FFFFFF | 卡片背景 |
| surface.filterBg | #FAFAFA | 筛选区背景 |
| surface.hover | rgba(34, 73, 248, 0.06) | 悬停背景 |
| surface.active | rgba(34, 73, 248, 0.12) | 激活背景 |
| status.success | #35C476 | 成功状态 |
| status.warning | #F79E36 | 警告状态 |
| status.error | #E41121 | 错误状态 |
| status.info | #2249F8 | 信息状态 |

## 字体 (Typography)

### 字体族
```css
font-family: "Microsoft YaHei", "PingFang SC", -apple-system, BlinkMacSystemFont, sans-serif;
```

### 字号
| Token | 值 | 用途 |
|-------|-----|------|
| fontSize.12 | 12px | 辅助说明 |
| fontSize.14 | 14px | 正文/说明 |
| fontSize.16 | 16px | 正文 |
| fontSize.18 | 18px | 正文大 |
| fontSize.20 | 20px | 标题 |
| fontSize.24 | 24px | 章节标题 |
| fontSize.32 | 32px | 大标题 |

### 字重
| Token | 值 | 用途 |
|-------|-----|------|
| fontWeight.400 | 400 | Regular |
| fontWeight.500 | 500 | Medium |
| fontWeight.700 | 700 | Bold |

### 行高
| Token | 值 |
|-------|-----|
| lineHeight.20 | 20px |
| lineHeight.22 | 22px |
| lineHeight.24 | 24px |
| lineHeight.26 | 26px |
| lineHeight.32 | 32px |

### 文字样式组合
```css
/* 大标题 */
.title32Bold {
  font-size: 32px;
  line-height: 32px;
  font-weight: 700;
}

/* 页面标题 */
.title24Bold {
  font-size: 24px;
  line-height: 32px;
  font-weight: 700;
  color: #333333;
}

/* 卡片标题 */
.title18Bold {
  font-size: 18px;
  line-height: 26px;
  font-weight: 600;
  color: #333333;
}

/* 正文 */
.body16 {
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
}

/* 说明文字 */
.body14 {
  font-size: 14px;
  line-height: 22px;
  font-weight: 400;
  color: #666666;
}

/* 说明文字加粗 */
.body14Bold {
  font-size: 14px;
  line-height: 22px;
  font-weight: 700;
  color: #333333;
}

/* 辅助说明 */
.body12 {
  font-size: 12px;
  line-height: 20px;
  color: #999999;
}
```

## 间距 (Spacing)

### 基础间距
| Token | 值 |
|-------|-----|
| spacing.xs | 4px |
| spacing.sm | 8px |
| spacing.md | 12px |
| spacing.lg | 16px |
| spacing.xl | 20px |
| spacing.xxl | 28px |

### 布局尺寸
| Token | 值 | 用途 |
|-------|-----|------|
| sidebarWidth | 220px | 侧边栏宽度 |
| headerHeight | 70px | 顶栏高度 |
| sidebarHeaderHeight | 68px | 侧边栏头部高度 |
| navItemHeight | 48px | 菜单项高度 |
| navItemGap | 8px | 菜单项间距 |
| subNavItemHeight | 40px | 子菜单项高度 |
| buttonHeight | 32px | 按钮高度 |
| inputHeight | 32px | 输入框高度 |
| iconBtnSize | 40px | 图标按钮尺寸 |
| logoSize.header | 147×33px | Header Logo 尺寸 |
| logoSize.brand | 36×36px | Sidebar Logo 尺寸 |
| avatarSize | 40px | 头像尺寸 |

### 筛选区间距
| Token | 值 |
|-------|-----|
| filter.inputHeight | 32px |
| filter.labelWidth | 72px |
| filter.gapBetweenInputs | 60px |
| filter.gapBetweenRows | 16px |

### 内容区内边距
| Token | 值 |
|-------|-----|
| content.padding | 24px |
| content.marginTop | 8px |
| content.gap | 16px |

## 圆角 (Border Radius)

| Token | 值 | 用途 |
|-------|-----|------|
| radius.sm | 2px | 小圆角（按钮、输入框） |
| radius.md | 4px | 中圆角 |
| radius.lg | 8px | 大圆角（卡片） |
| radius.full | 9999px | 圆形（胶囊按钮、头像） |

## 阴影 (Shadow)

| Token | 值 | 用途 |
|-------|-----|------|
| shadow.card | 0 1px 3px rgba(0, 0, 0, 0.1) | 卡片阴影 |
| shadow.cardHover | 0 4px 24px rgba(15, 23, 42, 0.06) | 卡片悬停阴影 |
| shadow.modal | 0 20px 25px -5px rgba(0, 0, 0, 0.1) | 弹窗阴影 |

## 过渡动画 (Transition)

| Token | 值 | 用途 |
|-------|-----|------|
| transition.fast | 150ms ease | 快速过渡（按钮、图标） |
| transition.normal | 200ms ease | 正常过渡 |
| transition.slow | 300ms ease | 慢速过渡（展开收起） |

## 图标尺寸 (Icon Sizes)

| Token | 值 | 用途 |
|-------|-----|------|
| icon.sm | 10px | 小图标（箭头） |
| icon.md | 16px | 中图标 |
| icon.lg | 20px | 大图标（导航菜单） |
| icon.xl | 48px | 大图标（空状态） |
