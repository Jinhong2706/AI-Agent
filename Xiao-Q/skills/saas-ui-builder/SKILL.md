---
name: saas-ui-builder
description: 用于生成碳擎 SaaS 系统页面的 skill。当用户需要创建表单页面、列表页面、详情页、仪表盘、聊天界面等各种业务页面时使用。该 skill 提供统一的设计系统规范、布局模板和组件代码，确保所有生成的页面风格与碳擎产品碳足迹3.0系统一致。
---

# SaaS UI Builder

用于生成碳擎 SaaS 系统页面的 skill，确保所有页面风格统一。

## 目录结构

```
saas-ui-builder/
├── assets/
│   ├── layout-template.tsx        # 页面布局模板（React）
│   ├── layout-template.module.css # 布局样式模板
│   ├── header-logo.png            # Header Logo 图片
│   ├── logo-brand.png             # Sidebar 品牌图标
│   └── user-avatar.png            # 用户头像占位图
├── references/
│   ├── design-tokens.md            # 颜色、字体、间距等设计令牌
│   ├── layout-spec.md             # 页面布局规范
│   └── components.md              # 组件样式规范
└── SKILL.md                       # 本文件
```

## 使用流程

### 1. 理解需求

与用户确认以下信息：
- 页面类型：表单/列表/详情/仪表盘/聊天等
- 业务功能和数据字段
- 左侧导航菜单项

### 2. 应用布局模板

1. 复制 `assets/layout-template.tsx` 到目标目录（重命名为 `page.tsx`）
2. 复制 `assets/layout-template.module.css` 到目标目录（重命名为 `page.module.css`）
3. **重要**：复制 `assets/*.png` 到目标项目的 `public/` 目录
4. 根据需求修改：
   - 左侧导航菜单项（名称、数量）
   - 面包屑导航
   - 内容区页面标题和按钮
   - 内容区组件

### 3. 实现内容区

根据页面类型实现内容区：
- 表单页面：使用 `references/components.md` 中的表单组件规范
- 列表页面：使用表格组件规范
- 仪表盘：使用卡片组件规范

### 4. 严格遵循设计令牌

所有颜色、字体、间距必须使用 `references/design-tokens.md` 中定义的值。

## Logo 和图片资源

本 skill 使用 **public 目录** 方式引用图片，这是 Next.js 的标准静态资源处理方式。

### 图片资源说明

| 资源名 | 尺寸 | 用途 | CSS 类名 |
|--------|------|------|----------|
| `header-logo.png` | 147×33px | Header 左侧品牌 Logo | `.headerLogo` |
| `logo-brand.png` | 36×36px | Sidebar 顶部产品图标 | `.logoIcon` |
| `user-avatar.png` | 40×40px | 用户头像占位符 | `.userAvatar` |

### 使用方式

```tsx
// 在 layout-template.tsx 中已预定义组件
const HeaderLogoImg = () => (
  <img src="/header-logo.png" alt="碳擎 Logo" className={styles.headerLogo} />
);

const BrandLogoImg = () => (
  <img src="/logo-brand.png" alt="Brand Logo" className={styles.logoIcon} />
);

const UserAvatarImg = () => (
  <img src="/user-avatar.png" alt="User Avatar" className={styles.userAvatar} />
);
```

### 更换规则

- 用户要求更换 Logo/图标时，提示用户提供替换图片
- 用户未提出更换要求时，使用默认图片路径
- **重要**：生成页面时必须同时复制图片文件到目标项目的 `public/` 目录

## 默认文字

- **公司名称**：页眉右上角默认显示 **「江苏擎天工业互联网有限公司」**

## 布局结构

```
┌─────────────────────────────────────────────────────────────┐
│                        Header (70px)                         │
│   [Logo]      [工作台] [产品库] [工具] [企业信息] [?] [🔔]  │
├───────────────┬─────────────────────────────────────────────┤
│               │  Breadcrumb                                   │
│   Sidebar     ├─────────────────────────────────────────────┤
│   (220px)     │                                              │
│               │  Main Content Area                           │
│  [Logo区域]   │  - 页面标题 + 操作按钮                        │
│  [导航菜单]   │  - 筛选区域（可选）                           │
│  [收起导航]   │  - 内容区（表单/列表/详情/图表）               │
└───────────────┴─────────────────────────────────────────────┘
```

### CSS 布局方式

使用 **Flex 布局**，这是经过验证的稳定方案：

```css
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}
```

## 侧边栏导航菜单规范

- 菜单项高度：48px
- 菜单项间距：8px
- 图标尺寸：20×20px，左边距 16px
- 文字左边距：48px（16 + 20 + 12）

### 选中态

- **父菜单**：默认不显示选中/高亮效果，仅保持展开状态
- **子菜单**：选中时蓝色背景(#2249F8)，白字，204×48px
- **单选规则**：同时只能有一个子菜单被选中（通过 `activeSubItem` state 控制）
- 右侧下拉箭头（16×16），展开时旋转90°

## 组件层级

```
.layout                          # 页面根节点 (flex column)
├── .header                      # 顶栏（70px，flex-shrink: 0）
└── .body                        # 内容区（flex: 1）
    ├── .sidebar                 # 侧边栏（220px，flex-shrink: 0）
    └── .mainColumn              # 主内容列（flex: 1）
        ├── .breadcrumb          # 面包屑
        └── .mainContent         # 主内容
            ├── .pageHeader      # 页面标题区
            ├── .filterPanel     # 筛选区（可选）
            └── .contentArea     # 内容区
```

## 页面文件命名

页面文件放在 `app/` 目录下：
- 页面组件：`page.tsx`
- 页面样式：`page.module.css`
- 图片资源：放在项目根目录的 `public/` 文件夹下

目录结构示例：
```
app/
├── products/
│   ├── page.tsx       # 产品列表页
│   ├── page.module.css
│   ├── [id]/
│   │   └── page.tsx   # 产品详情页
│   └── new/
│       └── page.tsx   # 新建产品页
└── dashboard/
    └── page.tsx       # 仪表盘页

public/
├── header-logo.png    # 必须包含
├── logo-brand.png     # 必须包含
└── user-avatar.png    # 必须包含
```

## 常见问题

### Q: 为什么用 Flex 布局而不是 Grid？

Grid 布局在某些情况下会导致 Header 和 Body 的空间分配计算问题，Flex 布局更稳定可靠。

### Q: 图片为什么放 public 目录？

Next.js 的 `public/` 目录是处理静态资源的标准方式，使用绝对路径 `/xxx.png` 引用简单可靠。

### Q: 分享项目时需要注意什么？

确保 `public/` 目录下的图片文件一起分发，否则 Logo 和头像将无法显示。
