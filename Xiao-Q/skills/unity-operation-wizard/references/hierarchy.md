# Hierarchy 窗口

**打开方式：** `Window > General > Hierarchy`，快捷键 `Ctrl+4`

Hierarchy 显示当前 Scene 中所有 GameObject 的层级结构。

---

## 基本操作

| 操作 | 方法 |
|------|------|
| **选中** | 单击 GameObject 名称 |
| **多选** | Ctrl+单击 / Shift+单击（范围选择） |
| **创建父子关系** | 拖拽子物体到父物体上 |
| **解除父子关系** | 拖拽子物体到 Hierarchy 空白区域 |
| **复制** | Ctrl+D（原地复制）或 Ctrl+C/V |
| **删除** | 选中后按 Delete |
| **重命名** | 单击已选中的名称，或按 F2 |

---

## 右键菜单

在 Hierarchy 中右键单击 GameObject：

| 菜单项 | 说明 |
|--------|------|
| Copy / Paste / Duplicate / Delete | 常规操作 |
| Rename | 重命名 |
| Select Children | 选中所有子物体 |
| Create Empty | 创建空子物体 |
| 3D Object / 2D Object / UI / etc. | 创建各类子物体 |
| Set as First Sibling | 移到同级第一位 |
| Set as Last Sibling | 移到同级最后一位 |
| Prefab ▶ | 预制体相关操作（Unpack / Open / Select Asset 等） |

---

## 搜索功能

Hierarchy 顶部的搜索栏支持：
- **名称搜索：** 直接输入
- **组件类型搜索：** 输入 `t:组件名`，如 `t:Collider` 找出所有带碰撞体的物体
- **标签搜索：** 输入 `tag:标签名`
- **层级搜索：** 输入 `layer:层名`

---

## 排序

默认按创建顺序排列。点击 Hierarchy 顶部名称栏可按字母排序（暂时）。

---

## 可见性与锁定

| 控件 | 功能 |
|------|------|
| **眼睛图标**（左侧） | 切换 Scene 视图中的可见性（不影响 Game 视图渲染） |
| **手形图标** | 锁定物体，防止在 Scene 视图中误选 |

这些控件在 Hierarchy 右上角可全局开关显示。

---

## 颜色标签

右键 GameObject → 选择彩色标签，用于视觉分组（如红色=敌人，蓝色=玩家等）。仅在 Hierarchy 中可见，不影响渲染。

---

## 图标显示

右侧可设置 GameObject 图标（灰/蓝/绿/黄等），用于快速定位重要物体。在 Scene 视图中也会显示对应图标。
