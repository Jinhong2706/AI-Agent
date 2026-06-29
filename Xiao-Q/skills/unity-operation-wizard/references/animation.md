# Animation 窗口 + Animator 窗口

---

## Animation 窗口

**打开方式：** `Window > Animation > Animation`，快捷键 `Ctrl+6`

用于创建和编辑 Animation Clip（动画剪辑）。首次给物体添加动画时，Unity 自动创建 Animator 组件和 Animator Controller。

### 窗口布局

| 区域 | 说明 |
|------|------|
| **左侧属性列表** | 列出正在动画化的属性（Position、Rotation、Scale、自定义属性等） |
| **右侧时间轴** | 显示关键帧（菱形标记）和时间线 |
| **底部按钮** | 播放/暂停/录制模式、Dope Sheet/Curves 模式切换 |

### 两种视图模式

| 模式 | 说明 |
|------|------|
| **Dope Sheet（关键帧表）** | 线性轨道视图，显示关键帧的**时间位置**（菱形标记） |
| **Curves（曲线编辑器）** | 图形视图，显示属性值**随时间变化的方式**（贝塞尔曲线） |

### Dope Sheet 操作

| 操作 | 方法 |
|------|------|
| 选中关键帧 | Shift+单击 / 框选 |
| 移动关键帧 | 拖拽选中区域 |
| 缩放关键帧间距 | 拖拽蓝色选择手柄（压缩/拉伸时间） |
| 添加关键帧 | 在属性行上右键 → Add Keyframe |

### Curves 曲线模式操作

| 操作 | 方法 |
|------|------|
| 框选全部 | F |
| 平移 | 中键拖拽 / Alt+左键拖拽 |
| 缩放（等比例） | 滚轮 |
| 水平缩放 | Ctrl/Cmd + 滚轮 |
| 垂直缩放 | Shift + 滚轮 |
| 添加关键帧 | 双击曲线 / 右键 Add Keyframe |
| 删除关键帧 | 选中 → Delete / 右键 Delete Keyframe |

### 切线类型（控制曲线平滑）

右键关键帧 → 选择切线类型：

| 类型 | 行为 |
|------|------|
| **Clamped Auto**（默认） | 自动平滑，不会超出目标值（推荐） |
| **Auto**（旧版） | 自动平滑，可能超出 |
| **Free Smooth** | 手动拖拽切线手柄（保持光滑连续） |
| **Flat** | 水平切线 |
| **Broken - Free** | 左右手柄独立（锐角变化） |
| **Broken - Linear** | 直线连接相邻关键帧 |
| **Broken - Constant** | 保持值不变直到下一个关键帧（阶梯形/Step） |

### 可动画化的属性类型

- Float、Integer
- Color
- Vector2、Vector3、Vector4
- Quaternion
- Boolean（0=false，非0=true）

> 不可动画化：数组、结构体、其他对象类型

---

## Animator 窗口

**打开方式：** `Window > Animation > Animator`

可视化的状态机编辑器。需要一个 Animator Controller 资源作为基础。

### 窗口布局

| 区域 | 说明 |
|------|------|
| **主网格区域** | 可视化状态机图（Base Layer） |
| **左侧面板** | 可在 Parameters（参数）和 Layers（层级）之间切换 |

### 导航操作
- 中键拖拽 / Alt+左键拖拽：平移
- 右键单击网格：创建状态

---

## Animator 核心概念

### 状态（States）

每个状态代表一个动画行为。状态类型：

| 类型 | 说明 |
|------|------|
| **普通状态** | 引用一个 Animation Clip 或 Blend Tree |
| **Entry** | 起始节点——状态机的入口 |
| **Any State** | 任意状态——从任意状态都可转换到此（用于全局过渡如受伤/死亡） |
| **Exit** | 退出节点——退出当前状态机 |
| **Sub-State Machine** | 子状态机——封装一组相关状态简化主图 |

创建：**右键网格 → Create State → Empty**（然后赋 Motion），或直接拖入 Animation Clip。

### 过渡（Transitions）

定义在什么条件下从一个状态切换到另一个状态。右键状态 → **Make Transition** → 连线到目标状态。

| 属性 | 说明 |
|------|------|
| **Has Exit Time** | 等待动画播放到特定归一化时间才过渡 |
| **Exit Time** | Has Exit Time 为 true 时的触发时间点 |
| **Transition Duration** | 两个状态之间的混合时长 |
| **Transition Offset** | 目标动画从哪个位置开始播放 |
| **Conditions** | 触发过渡的条件（一个或多个，全部满足才触发） |
| **Interruption Source** | 当前过渡是否可被其他过渡打断 |

### 参数（Parameters）

状态机的外部输入信号，脚本通过参数控制动画。

| 类型 | 用途 | 示例 |
|------|------|------|
| **Float** | 连续值 | Speed、Health |
| **Int** | 离散值 | AmmoCount、Level |
| **Bool** | 开关 | IsWalking、IsDead |
| **Trigger** | 一次性触发（自动重置） | Jump、Attack |

添加：左侧 Parameters 面板 → 点击 **+** 按钮 → 选择类型

代码控制：
```csharp
animator.SetFloat("Speed", speed);
animator.SetBool("IsWalking", true);
animator.SetTrigger("Jump");
animator.SetInteger("Ammo", 5);
```

### 层级（Layers）

允许多个状态机同时运行（如身体跑动 + 手臂投掷）。

| 属性 | 说明 |
|------|------|
| **Weight** | 该层对最终姿态的影响权重（0-1） |
| **Blending** | Override（覆盖下层）/ Additive（叠加） |
| **Mask** | Avatar Mask——指定该层控制哪些身体部位（如仅上半身） |
| **Sync** | 与另一层共享状态结构但使用不同动画剪辑 |

### Blend Tree（混合树）

在一个状态内根据参数平滑混合多个动画。

**创建：** 右键 → Create State → From New Blend Tree → 双击进入

**示例——1D 运动混合（参数：Speed）：**

| 动画 | Threshold |
|------|-----------|
| Idle（站立） | 0 |
| Walk（行走） | 0.5 |
| Run（奔跑） | 1.0 |

混合类型：**1D**（一个参数）/ **2D Simple Directional**（两个参数）/ **2D Freeform Directional** / **2D Freeform Cartesian** / **Direct**

> **Blend Tree vs Transition：** Transition 是在两个状态间随时间混合；Blend Tree 是在一个状态内同时混合多个动画。

---

## 创建动画工作流

1. 选中 GameObject → `Window > Animation > Animation`
2. 点击 **Create** 按钮 → 选择路径保存 Animation Clip
3. 点击红色**录制按钮**（Record）进入录制模式
4. 拖拽时间线 → 修改 Inspector 中的属性值 → 自动创建关键帧
5. 再次点击录制按钮结束
6. Unity 自动创建 Animator Controller，回到 Animator 窗口查看状态

### 导入的动画

在 Project 窗口选中导入的动画文件 → Inspector 中 **Animation** 标签页：
- 可添加 Curves 曲线（映射归一化时间 0-1 到自定义值）
- 可配置循环、Root Motion、事件等
