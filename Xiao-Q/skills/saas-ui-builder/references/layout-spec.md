# 布局规范 (Layout Spec)

## 整体布局

页面采用 Header + Sidebar + Main 的经典 SaaS 布局：

```
┌─────────────────────────────────────────────────────────────┐
│                        Header (70px)                         │
├──────────────┬──────────────────────────────────────────────┤
│              │                   Breadcrumb                  │
│   Sidebar    ├──────────────────────────────────────────────┤
│   (220px)    │                                               │
│              │                   Main Content                 │
│              │                   (flex: 1)                   │
│              │                                               │
└──────────────┴──────────────────────────────────────────────┘
```

## CSS 布局实现（Flex 布局）

### 外层布局
```css
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}
```

### Body 区域
```css
.body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}
```

> **重要**：使用 Flex 布局而不是 Grid 布局，以确保 Header 和 Body 的空间分配计算稳定可靠。

## Header 顶栏

- **高度**：70px
- **背景**：白色 (#FFFFFF)
- **下边框**：1px solid #D9D9D9
- **Logo 位置**：左侧，padding 0 20px，Logo 尺寸 147×33px
- **Logo 图片**：`/header-logo.png`（源文件：skill 的 `assets/header-logo.png`，生成页面时复制到目标项目 `public/`）
- **用户未要求更换时必须使用此默认路径**

### Header 元素排列（右到左）
- 用户信息区（头像 + 公司名称）
  - **用户头像**：`40×40px` 圆形，默认图片 `/user-avatar.png`
  - **公司名称**：`16px/500 #3D3D3D`，默认文字 **「江苏擎天工业互联网有限公司」**
- 功能按钮（帮助、消息）
- 导航下拉（产品库、工具、企业信息）
- 工作台按钮

### Header 样式

```css
.header {
  flex-shrink: 0;
  width: 100%;
  height: 70px;
  background-color: #ffffff;
  border-bottom: 1px solid #D9D9D9;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-sizing: border-box;
}

.headerRight {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 20px;
}

.workbenchBtn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 96px;
  height: 32px;
  border-radius: 9999px;
  border: none;
  background: #EEF3FF;
  color: #294CFF;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 0 12px;
  line-height: 1;
}

.headerSelectGroup {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 32px;
  padding: 0 10px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  background: transparent;
  white-space: nowrap;
  box-sizing: border-box;
  cursor: pointer;
  border: none;
  font-family: inherit;
}
```

## Sidebar 侧边栏

- **宽度**：220px
- **背景**：白色 (#FFFFFF)
- **右边框**：1px solid #D9D9D9
- **flex-shrink**: 0（不压缩）

### 顶部 Logo 区域
- **高度**：68px
- **内边距**：16px 36px
- **Logo 尺寸**：36×36px
- **Logo 图片**：`/logo-brand.png`
- **标题**：「产品碳足迹3.0」，18px Bold，#333333

### 导航菜单列表
- **容器**：flex column，gap 4px
- **内边距**：12px 0
- **溢出处理**：overflow-y: auto
- **菜单项**：220×48px
- **图标**：20×20px，左边距 16px
- **文字**：14px，距图标 12px（总左边距 48px）

### 选中态
- **父菜单**：默认不显示蓝色背景，仅保持展开状态
- **子菜单**：选中时背景色 rgba(34, 73, 248, 0.12)，文字 #2249F8
- **单选规则**：同时只能有一个子菜单被选中状态
- **下拉箭头**：16×16，展开时旋转90°

### 底部收起导航
- **高度**：48px
- **上边框**：1px solid #D9D9D9
- **文案**：「收起导航」，14px，#666666

### Sidebar 样式

```css
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #FFFFFF;
  border-right: 1px solid #D9D9D9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebarHeader {
  height: 68px;
  padding: 16px 36px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #D9D9D9;
  box-sizing: border-box;
}

.navList {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 0;
  overflow-y: auto;
}

.navItem {
  position: relative;
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  padding-left: 24px;
  padding-right: 8px;
  cursor: pointer;
  transition: background 150ms ease;
  box-sizing: border-box;
}

.navItem:hover {
  background: rgba(34, 73, 248, 0.06);
}

.subMenu {
  display: none;
  padding-left: 36px;
}

.subMenu.open {
  display: block;
}

.subMenuItem {
  height: 40px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 150ms ease;
  border-radius: 4px;
  margin: 2px 0;
  padding: 0 12px;
}

.subMenuItem.subActive {
  background: rgba(34, 73, 248, 0.12);
}

.subMenuItem.subActive .subMenuItemLabel {
  color: #2249F8;
  font-weight: 600;
}
```

## 主内容列

### 面包屑
- **高度**：22px
- **字体**：14px，#666666
- **当前页**：#333333，font-weight: 500

### 主内容画布
- **背景**：#F2F2F6（页面背景）
- **内边距**：16px 24px
- **溢出处理**：overflow: auto

### 内容卡片
- **背景**：白色
- **内边距**：24px
- **圆角**：8px
- **阴影**：0 1px 3px rgba(0, 0, 0, 0.1)

### 主内容样式

```css
.mainColumn {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 16px 24px;
  background: #F2F2F6;
  overflow: auto;
}

.mainContent {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #FFFFFF;
  border-radius: 8px;
  padding: 24px;
  margin-top: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: auto;
}

.pageHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.pageTitle {
  margin: 0;
  font-size: 24px;
  line-height: 32px;
  font-weight: 700;
  color: #333333;
}
```

## 按钮规范

### 主按钮
```css
.btnPrimary {
  height: 32px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  background: #2249F8;
  color: #FFFFFF;
  border: none;
}
```

### 次要按钮
```css
.btnSecondary {
  height: 32px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  background: #F5F7FF;
  color: #2249F8;
  border: 1px solid #2249F8;
}
```

## 筛选区规范

### 筛选行
```css
.filterRow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 60px 16px;
}
```

### 筛选字段
```css
.filterField {
  display: flex;
  align-items: stretch;
  height: 32px;
  min-width: 240px;
  border: 1px solid #EEEEEE;
  border-radius: 2px;
  overflow: hidden;
}
```

### 筛选标签
```css
.filterLabel {
  width: 72px;
  padding: 0 8px;
  background: #FAFAFA;
  font-size: 14px;
  color: #666666;
  border-right: 1px solid #EEEEEE;
}
```
