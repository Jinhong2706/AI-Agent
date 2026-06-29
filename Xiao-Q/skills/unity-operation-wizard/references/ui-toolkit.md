# UI 相关面板（UGUI + Canvas）

---

## 创建 UI 的关键对象

创建任何 UI 元素（`GameObject > UI > ...`）时，Unity 自动创建以下结构：

### Canvas（画布）
所有 UI 元素必须作为 Canvas 的子物体。Canvas 负责将 UI 渲染到屏幕。

| 属性 | 说明 |
|------|------|
| **Render Mode** | 渲染模式（最重要配置） |
| — Screen Space - Overlay | UI 覆盖在整个屏幕最上层（无需摄像机，自动适配分辨率） |
| — Screen Space - Camera | UI 渲染在指定摄像机前方（可被 3D 物体遮挡） |
| — World Space | UI 放置在 3D 世界中（如头顶血条、浮字） |
| **Pixel Perfect** | 像素完美渲染（锐利清晰） |
| **Render Camera** | 渲染 UI 的摄像机（Camera 模式时） |
| **Plane Distance** | Canvas 距摄像机距离（Camera 模式） |
| **Sorting Layer/Order** | 与 Sprite 的排序层和顺序 |
| **Scale Factor / Reference Pixels Per Unit** | 缩放参数 |

### Canvas Scaler（画布缩放器）
控制 UI 元素在不同分辨率下的缩放方式。

| 属性 | 说明 |
|------|------|
| **UI Scale Mode** | Constant Pixel Size（固定像素）/ Scale With Screen Size（根据屏幕缩放）/ Constant Physical Size（根据物理尺寸） |
| **Reference Resolution** | 设计基准分辨率（Scale With Screen Size 模式，如 1920x1080） |
| **Screen Match Mode** | Match Width Or Height（权衡宽度和高度）/ Expand / Shrink |
| **Match** | 0=按宽度缩放，1=按高度缩放，0.5=取中间 |

### Graphic Raycaster（图形射线检测器）
处理 UI 的鼠标/触摸点击。必须挂在 Canvas 上才能让 UI 按钮等交互。

| 属性 | 说明 |
|------|------|
| **Ignore Reversed Graphics** | 忽略翻转的图像 |
| **Blocking Objects** | 阻挡 UI 射线的 2D/3D 物体 |
| **Blocking Mask** | 阻挡物体所在的 Layer |

### Event System（事件系统）
场景中每个 Canvas 需要对应一个 EventSystem。自动创建，管理输入事件的触发。

| 组件 | 功能 |
|------|------|
| **Event System** | 管理所有 UI 事件 |
| **Standalone Input Module** | 桌面平台输入处理 |

---

## 核心 UI 组件

### Image（图片）
显示 Sprite 的 UI 组件。

| 属性 | 说明 |
|------|------|
| **Source Image** | 引用的 Sprite 图片 |
| **Color** | 颜色（可调透明度——Alpha 值） |
| **Material** | 材质（支持自定义 UI Shader） |
| **Raycast Target** | 勾选时可被点击检测到 |
| **Image Type** | Simple / Sliced（九宫格）/ Tiled（平铺）/ Filled（填充） |
| — Fill Method | Filled 模式下：Horizontal / Vertical / Radial 90/180/360 |
| — Fill Amount | 填充比例（0-1）——常做血条/进度条 |
| **Preserve Aspect** | 保持原始宽高比 |

### Raw Image（原始图片）
显示非 Sprite 类型的纹理（如 Render Texture 实时画面）。

### Text（文本—旧版，建议用 TextMeshPro）
| 属性 | 说明 |
|------|------|
| **Text** | 显示的字符串 |
| **Font** | 字体 |
| **Font Size** | 字号 |
| **Color** | 颜色 |
| **Alignment** | 对齐方式 |
| **Best Fit** | 自适应缩小到可容纳区域 |
| **Raycast Target** | 可点击（需谨慎——非按钮的文本也开启会影响性能） |

### TextMeshPro - Text（推荐文本）
功能远强于旧版 Text，支持 SDF 字体、渐变、富文本。需要导入 TextMeshPro 包。

### Button（按钮）
复合组件，包含 Image + Button 脚本。

| 属性 | 说明 |
|------|------|
| **Interactable** | 是否可交互（灰色=不可点击） |
| **Transition** | None / Color Tint / Sprite Swap / Animation |
| **Target Graphic** | 过渡效果应用的目标 Image |
| **On Click()** | 绑定的点击事件（拖入 GameObject + 选方法） |

### Toggle（复选框/开关）
| 属性 | 说明 |
|------|------|
| **Is On** | 初始开关状态 |
| **Toggle Transition** | None / Fade |
| **Group** | Toggle Group——同一组内只能选一个 |
| **On Value Changed（事件）** | 值变化时触发的回调 |

### Slider（滑块）
| 属性 | 说明 |
|------|------|
| **Min Value / Max Value** | 最小值/最大值 |
| **Value** | 当前值 |
| **Whole Numbers** | 仅整数 |
| **Direction** | 方向（LeftToRight / RightToLeft / TopToBottom / BottomToTop） |
| **Fill Rect / Handle Rect** | 填充区域和滑块手柄（Image 引用） |
| **On Value Changed** | 值变化事件 |

### Input Field（输入框）
| 属性 | 说明 |
|------|------|
| **Text Component** | 关联的文本组件 |
| **Content Type** | Standard / Autocorrected / Integer / Decimal / Alphanumeric / Name / Email / Password / Pin / Custom |
| **Placeholder** | 占位提示文字 |
| **Character Limit** | 最大字符数 |
| **On Value Changed / On End Edit** | 事件 |

### Scroll View（滚动视图）
ScrollRect 组件控制的滚动区域。

| 属性 | 说明 |
|------|------|
| **Content** | 滚动内容（需有 RectTransform） |
| **Horizontal / Vertical** | 是否可水平/垂直滚动 |
| **Movement Type** | Unrestricted / Elastic / Clamped |
| **Inertia** | 惯性滚动 |
| **Scroll Sensitivity** | 滚轮灵敏度 |
| **Viewport** | 视口——可见区域的 GameObject |

### Dropdown（下拉菜单）
| 属性 | 说明 |
|------|------|
| **Options** | 下拉选项文本列表 |
| **Value** | 当前选中索引 |
| **On Value Changed** | 值变化事件 |

---

## Anchor（锚点）系统

### 锚点 Presets
选中 RectTransform 后，Inspector 左上角的矩形图标可快速设置锚点：
- **左上角/右上角/左下角/右下角**：固定到对应角
- **Stretch**：拉伸填满父物体
- **Center / Middle-Left / Middle-Right**：居中/左中/右中

### 快捷键设置锚点
- 按住 **Ctrl** 的同时选择锚点 Preset = 同步设置轴心点
- 按住 **Alt** 的同时选择 = 同步移动物体位置

---

## RectTransform 核心属性

| 属性 | 含义 |
|------|------|
| **Pos X/Y** | 相对锚点的位置 |
| **Width/Height** | 矩形宽高 |
| **Anchors Min/Max** | 锚点范围（0-1，相对于父）。4个值可不等=拉伸模式 |
| **Pivot** | 轴心点（0-1，0.5,0.5=中心） |
| **Rotation** | 旋转 |
| **Scale** | 缩放 |

属性与锚点设置的交互：
- 锚点分离时（Min≠Max），宽高显示为 **Left/Right/Top/Bottom**（边距）
- 锚点集中时，显示为 Pos X/Y + Width/Height

---

## UI 性能关键

- Minimize Canvas 重建：Canvas 上任何变化会导致整个 Canvas 重绘
- 频繁变化的 UI 元素放在**独立 Canvas**上（如血条、计时器）
- 静态 UI 放一个 Canvas，动态 UI 另放一个 Canvas
- 非按钮的 Text/Image 取消 **Raycast Target** 复选框
- 合理设置 Canvas Scaler 避免过多重绘
