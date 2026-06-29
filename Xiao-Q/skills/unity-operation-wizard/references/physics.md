# Physics Settings + Navigation 窗口

---

## Physics Settings

**路径：** `Edit > Project Settings > Physics`（3D）/ `Edit > Project Settings > Physics 2D`（2D）

---

### Physics（3D）

| 属性 | 说明 |
|------|------|
| **Gravity** | 重力向量（X, Y, Z）。真实重力为负 Y，默认 `(0, -9.81, 0)`。增加重力时可能需增加 Solver Iterations |
| **Default Material** | 默认物理材质——当 Collider 未指定材质时使用 |
| **Bounce Threshold** | 相对速度低于此值不反弹（减少抖动） |
| **Sleep Threshold** | 能量阈值——低于此值 Rigidbody 进入休眠（节省计算） |
| **Default Contact Offset** | 碰撞检测容差（默认 0.01） |
| **Default Solver Iterations** | 物理解算器每帧迭代次数（提高可增加约束精度） |
| **Default Solver Velocity Iterations** | 速度解算迭代次数 |
| **Queries Hit Backfaces** | 射线检测是否命中背面 |
| **Queries Hit Triggers** | 射线检测是否命中触发器 |
| **Enable Adaptive Force** | 自适应力——大质量物体施加的力更准确 |
| **Contacts Generation** | Legacy Contacts Generation / Persistent Contacts Manifold |
| **Auto Simulation** | 自动模拟物理。关闭时需手动调用 Physics.Simulate() |
| **Layer Collision Matrix**（窗口底部） | 层碰撞矩阵。勾选=允许对应两层之间碰撞。可用 Enable All / Disable All 快速配置 |

### Physics 2D（2D 物理）

| 属性 | 说明 |
|------|------|
| **Gravity** | 2D 重力向量 |
| **Default Material** | 默认 2D 物理材质 |
| **Velocity Iterations** | 速度解算迭代次数 |
| **Position Iterations** | 位置解算迭代次数 |
| **Queries Hit Triggers** | 查询是否命中触发器 |
| **Callbacks On Disable** | 组件禁用时是否触发碰撞回调 |
| **Layer Collision Matrix**（独立标签页） | 2D 碰撞矩阵 |

---

## Layer Collision Matrix 用法

1. 在 Inspector 中给 GameObject 分配 Layer
2. 打开 `Edit > Project Settings > Physics`
3. 在底部 Layer Collision Matrix 中：
   - **打勾** = 两层之间允许碰撞
   - **不打勾** = 两层之间永不碰撞（忽略）

**性能建议：** 只启用确实需要碰撞的层对，减少不必要的碰撞检测计算。

---

## Navigation 窗口（AI 导航）

### 重要变化（Unity 2022.3+）
内置的 Navigation 系统（`Window > AI > Navigation`）已**弃用**。需通过 Package Manager 安装 **AI Navigation** 包。

### 安装与打开
1. `Window > Package Manager` → 搜索 "AI Navigation" → Install
2. 打开：`Window > AI > Navigation`

---

### Agents（代理类型）标签页

定义不同角色的导航参数（可添加多种）：

| 参数 | 说明 |
|------|------|
| **Name** | 代理类型名称（如 Humanoid） |
| **Radius** | 代理半径——决定离墙/边的最小距离 |
| **Height** | 代理高度——决定能通过的最低空间 |
| **Step Height** | 最大可跨台阶高度 |
| **Max Slope** | 最大可行走坡度角（度） |

每种 Agent Type 需要独立的 NavMeshSurface 进行烘焙。

---

### Areas（区域）标签页

定义不同区域的寻路代价：

| 参数 | 说明 |
|------|------|
| **Name** | 区域名称（Walkable、Not Walkable、Jump 等，最多 32 种） |
| **Cost** | 寻路消耗（越高 AI 越绕开该区域） |

配合 NavMeshModifier 组件在 GameObject 上覆盖区域类型。

---

### NavMesh Surface（新版烘焙核心）

创建：`GameObject > AI > NavMesh Surface`

挂载在场景中的一个 GameObject 上，负责烘焙导航网格：

| 参数分组 | 参数 | 说明 |
|---------|------|------|
| **Agent Type** | Agent Type | 选用哪种代理类型的尺寸进行烘焙 |
| **Object Collection** | Collect Objects | All GameObjects / Volume（限定体积）/ Current Object Hierarchy / NavMeshModifier Component Only |
| | Include Layers | 按层过滤烘焙对象（默认 Everything） |
| | Use Geometry | Render Meshes（渲染网格）或 Physics Colliders（碰撞体）作为导航几何体 |
| **Advanced** | Default Area | 默认区域类型 |
| | Override Voxel Size | 手动体素大小（影响精度/速度） |
| | Override Tile Size | 手动瓦片大小（默认 256 体素） |

操作：
1. 选中 NavMeshSurface GameObject
2. 配置参数
3. 点 **Bake** 烘焙
4. 点 **Clear** 清除

---

### NavMeshModifier（导航网格修改器）

挂载到需要包含/排除/改区域的 GameObject 上：

| 参数 | 说明 |
|------|------|
| **Override Area** | 覆盖区域类型 |
| **Area** | 应用的区域（Walkable / Not Walkable 等） |
| **Ignore From Build** | 从烘焙中忽略此对象及其子对象 |
| **Apply to Children** | 设置应用到所有子对象 |

---

### NavMesh Agent（导航代理组件）

通过 `Component > Navigation > NavMesh Agent` 添加到角色：

| 分组 | 参数 | 说明 |
|------|------|------|
| **Agent Type** | Agent Type | 选用代理类型 |
| **Base Offset** | Base Offset | 碰撞体相对轴心的垂直偏移 |
| **Steering** | Speed | 最大移动速度 |
| | Angular Speed | 最大旋转速度（度/秒） |
| | Acceleration | 最大加速度 |
| | Stopping Distance | 距目标多远停止 |
| | Auto Braking | 到达时自动减速 |
| **Obstacle Avoidance** | Radius | 避障碰撞体半径 |
| | Height | 避障碰撞体高度 |
| | Quality | 避障质量 |
| | Priority | 优先级（0-99，越低越优先） |
| **Path Finding** | Auto Traverse Off Mesh Link | 自动通过 Off-Mesh 连接 |
| | Auto Repath | 路径失效时自动重寻路 |
| | Area Mask | 允许行走的区域（按位掩码） |

---

### 新版导航三步法

```
1. Package Manager → 安装 AI Navigation
2. GameObject > AI > NavMesh Surface → 配置参数 → 点 Bake
3. 角色上添加 NavMesh Agent → 代码 SetDestination()
```

排除物体：加 NavMeshModifier → 勾 Ignore From Build
