# Inspector 窗口

**打开方式：** `Window > General > Inspector`，或在 Hierarchy/Scene 中选中 GameObject 后自动显示

---

## 窗口布局

选中一个 GameObject 时，Inspector 从上到下显示：
1. **GameObject 头部** — 名称、激活状态复选框、Static 标记、Layer 下拉、Tag 下拉
2. **Transform / RectTransform** — 每个物体必有的组件，不可移除
3. **附加组件** — Mesh Renderer、Collider、Rigidbody、脚本等，按添加顺序排列
4. **Add Component 按钮** — 底部，添加新组件

---

## 属性编辑

### 值类型（Value）
| 类型 | 编辑方式 |
|------|---------|
| 数值字段 | 直接输入，或点击拖拽标签微调 |
| 复选框 | 点击切换开关 |
| 下拉菜单 | 从预定义选项中选择 |
| 滑条 | 拖动滑块或输入数值 |
| 颜色选择器 | 点击打开颜色面板 |
| 曲线 | 点击打开曲线编辑器 |

### 引用类型（Reference）
- 拖拽资源/GameObject 到字段上赋值
- 点击字段右侧的 **小圆圈图标**（Object Picker）——打开选择器浏览并选择
- 引用为空时显示 `None（类型名）`

---

## 顶部控件

| 控件 | 说明 |
|------|------|
| **锁图标** | 锁定 Inspector，选中其他物体时保持当前显示不变（对比两个物体时常用） |
| **⋮ 菜单** | Ping（在 Hierarchy/Project 中定位）、Properties/Debug 模式切换 |
| **名称字段** | GameObject 名称，可直接编辑 |
| **激活复选框** | 最左侧，勾选=激活，取消=失活（等同于 SetActive） |
| **Static 复选框** | 标记为静态物体（影响光照烘焙、导航网格等） |
| **Layer 下拉** | 设置物体所在层（用于碰撞过滤、渲染分层等） |
| **Tag 下拉** | 设置标签（用于 FindWithTag 等查找） |

---

## Debug 模式 vs Normal 模式

通过 Inspector 右上角 `⋮` 菜单切换：

| 属性 | Normal 模式 | Debug 模式 |
|------|------------|-----------|
| 显示内容 | 仅序列化公有字段 + [SerializeField] 私有字段 | 所有字段（含私有成员） |
| 数值显示 | 格式化显示 | 原始值，可查看/修改私有变量 |
| 用途 | 日常编辑 | 调试、排查值异常 |

---

## 组件操作

| 操作 | 如何做 |
|------|--------|
| **折叠/展开** | 点击组件标题栏左侧的三角 |
| **排序** | 组件标题栏右侧 `⋮` 菜单 → Move Up / Move Down，或直接拖拽组件标题栏 |
| **复制组件** | 组件标题栏右侧 `⋮` 菜单 → Copy Component |
| **粘贴值**（同名组件） | 目标组件 `⋮` 菜单 → Paste Component Values |
| **粘贴为新组件** | 目标 GameObject 右上角 `⋮` 菜单 → Paste Component As New |
| **移除组件** | 组件标题栏右侧 `⋮` 菜单 → Remove Component |
| **重置组件** | 组件标题栏右侧 `⋮` 菜单 → Reset（恢复到默认值） |

---

## 多选编辑

同时选中多个 GameObject 时，Inspector 显示共有属性：
- **数值相同** → 显示值
- **数值不同** → 显示短横线 `-`
- **右键属性** → "Set to Value of [Name]" 将其他物体统一为选中物体值

---

## 各组件的 Inspector 面板

### Transform（变换组件）
每个 GameObject 必有，不可移除。

| 属性 | 说明 |
|------|------|
| **Position（位置）** | X, Y, Z。相对于父物体的坐标（无父物体时为世界坐标） |
| **Rotation（旋转）** | X, Y, Z。欧拉角，以度为单位 |
| **Scale（缩放）** | X, Y, Z。默认 1=原始大小。0 会导致物体不可见并破坏物理 |

Transform 标题栏右侧 `⋮` 菜单：**Reset**（Position/Rotation 归零，Scale 归 1）

### RectTransform（UI 变换）
UI 物体使用，继承自 Transform，额外包含：

| 属性 | 说明 |
|------|------|
| **Pos X/Y** | 相对于锚点的位置 |
| **Width/Height** | 矩形宽高 |
| **Anchors（锚点）** | Min/Max——控制相对父 Canvas 的对齐方式 |
| **Pivot（轴心）** | 旋转和缩放的中心点（0.5,0.5=中心） |
| **Rotation/Scale** | 同 Transform |
| **Blueprint Mode** | 编辑时忽略自身旋转和缩放 |
| **Raw Edit Mode** | 编辑时忽略锚点和轴心 |

> 点击左上角锚点可视化按钮（矩形图标），可从预设快速设置锚点（如拉伸填充、左对齐等）

---

### MeshFilter（网格过滤器）
包含可用网格——定义物体的**形状**。

| 属性 | 说明 |
|------|------|
| **Mesh** | 引用的网格资源（如 Cube、Sphere、自定义模型） |

---

### MeshRenderer（网格渲染器）
获取 MeshFilter 的形状并**绘制**显示。

| 属性分组 | 属性 | 说明 |
|---------|------|------|
| **Materials** | Size | 材质数量 |
| | Element 0, 1, 2... | 对应子网格的材质 |
| **Lighting** | Cast Shadows | On/Off/Two Sided/Shadows Only |
| | Receive Shadows | 是否接收阴影 |
| | Contribute Global Illumination | 是否参与全局光照 |
| **Light Probes** | Light Probes | Blend Probes / Use Proxy Volume / Off |
| **Reflection Probes** | Reflection Probes | Blend Probes / Blend Probes And Skybox / Simple / Off |
| **Additional Settings** | Motion Vectors | 运动矢量（用于 Motion Blur、TAA） |
| | Dynamic Occlusion | 动态遮挡 |
| | Sorting Layer / Order | 2D 排序 |

---

### Collider（碰撞体）系列
定义物体的**物理边界**形状。

#### Box Collider（盒子碰撞体）
| 属性 | 说明 |
|------|------|
| **Is Trigger** | 勾选后变为触发器（无物理碰撞，触发 OnTriggerEnter 等事件） |
| **Material** | Physic Material 物理材质——定义摩擦力和弹性 |
| **Center** | 碰撞体中心相对物体原点的偏移 |
| **Size** | 盒子的 XYZ 尺寸 |

#### Sphere Collider（球形碰撞体）
| 属性 | 说明 |
|------|------|
| **Is Trigger** | 同上 |
| **Material** | 同上 |
| **Center** | 同上 |
| **Radius** | 球体半径 |

#### Capsule Collider（胶囊碰撞体，常用于角色）
| 属性 | 说明 |
|------|------|
| Is Trigger | 同上 |
| Material | 同上 |
| Center | 同上 |
| Radius | 胶囊半径 |
| Height | 胶囊总高度（不含两端半球） |
| Direction | 胶囊长轴方向（X/Y/Z） |

#### Mesh Collider（网格碰撞体）
| 属性 | 说明 |
|------|------|
| Is Trigger / Material | 同上 |
| **Mesh** | 引用的网格（按实际几何形状碰撞，性能消耗更大） |
| **Convex** | 勾选后碰撞体变为凸壳（Convex Hull），才能与其他 Mesh Collider 碰撞 |
| **Cooking Options** | 烘焙选项，控制生成方式 |

---

### Rigidbody（刚体）
赋予物体物理运动能力。挂上后受重力影响、可受力移动。

| 属性 | 说明 |
|------|------|
| **Mass** | 质量（kg）。影响碰撞互动和浮力 |
| **Drag** | 移动阻力（空气阻力）。0=无阻力 |
| **Angular Drag** | 旋转阻力 |
| **Use Gravity** | 是否受重力影响 |
| **Is Kinematic** | 运动学模式——不受物理力，仅通过 Transform 或脚本控制移动 |
| **Interpolate** | 移动插值模式：None / Interpolate（平滑上一帧）/ Extrapolate（预测下一帧） |
| **Collision Detection** | Discrete（离散）/ Continuous（连续）/ Continuous Dynamic / Continuous Speculative |
| **Constraints** | 冻结某个轴的移动或旋转（如冻结 Y 轴旋转用于 2.5D 游戏） |

---

### Character Controller（角色控制器）
用于控制角色移动（替代 Rigidbody 的角色方案）：

| 属性 | 说明 |
|------|------|
| **Height** | 角色高度 |
| **Radius** | 角色碰撞半径 |
| **Slope Limit** | 最大可攀爬坡度（度） |
| **Step Offset** | 最大可跨台阶高度 |
| **Skin Width** | 皮肤宽度——碰撞穿透容忍值 |
| **Min Move Distance** | 最小移动距离（低于此值不移动） |
| **Center** | 碰撞体中心偏移 |

---

### Camera（摄像机）
| 属性 | 说明 |
|------|------|
| **Clear Flags** | Skybox / Solid Color / Depth Only / Don't Clear |
| **Background** | 背景色（Solid Color 模式时） |
| **Culling Mask** | 渲染层级遮罩——只渲染指定 Layer 的物体 |
| **Projection** | Perspective（透视）/ Orthographic（正交/2D） |
| **Field of View** | FOV 视角（透视模式） |
| **Size** | 视野大小（正交模式） |
| **Clipping Planes** | Near/Far——近裁剪面和远裁剪面距离 |
| **Viewport Rect** | 视口矩形（分屏时调整 XYWH 实现画面分割） |
| **Depth** | 渲染深度（值越大越靠后渲染，即覆盖在低深度画面上） |
| **Target Texture** | 渲染目标纹理（Render Texture） |
| **Allow MSAA** | 允许多重采样抗锯齿 |
| **Allow Dynamic Resolution** | 允许动态分辨率 |

---

### Light（光源）
#### Directional Light（方向光，太阳光）
| 属性 | 说明 |
|------|------|
| Type | Directional / Point / Spot / Area |
| Color | 光源颜色 |
| Mode | Realtime / Mixed / Baked |
| Intensity | 光照强度 |
| Indirect Multiplier | 间接光倍数 |
| Shadow Type | No Shadows / Hard Shadows / Soft Shadows |
| Culling Mask | 只照亮指定 Layer |

#### Point Light（点光源，灯泡）
比 Directional Light 多：
| 属性 | 说明 |
|------|------|
| Range | 光照范围半径 |
| Cookie | 光照纹理遮罩 |

#### Spot Light（聚光灯）
与 Point Light 类似，多：
| 属性 | 说明 |
|------|------|
| Spot Angle | 聚光锥角度 |

---

### 自定义脚本组件
显示所有 `public` 字段和标有 `[SerializeField]` 的 `private` 字段。
- 数值/字符串/布尔 → 可编辑
- GameObject/Transform/组件引用 → 拖拽赋值或 Object Picker
- 枚举 → 下拉菜单
- 如果脚本有自定义 Editor（CustomEditor），显示自定义 Inspector 面板

---

## 资源 Inspector 预览

在 Project 窗口选中资源时，Inspector 显示该资源的导入设置：
- **纹理：** Texture Type、Wrap Mode、Filter Mode、Max Size、压缩格式等
- **音频：** Load Type、Compression Format、Quality、Sample Rate 等
- **模型：** Scale Factor、Mesh Compression、Animation 导入设置、Materials 映射等
- **脚本：** 不可编辑，显示脚本内容预览
