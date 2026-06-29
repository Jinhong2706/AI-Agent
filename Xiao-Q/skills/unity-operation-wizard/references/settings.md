# Preferences 与 Project Settings

---

## Preferences（偏好设置）

**路径：** `Edit > Preferences...`

用户级设置，对所有项目生效。

### General（通用）
| 设置 | 说明 |
|------|------|
| Load Previous Project on Startup | 启动时自动加载上次工程 |
| Compress Assets on Import | 导入时压缩资源 |
| Editor Analytics | 发送使用数据给 Unity |
| Show Asset Store search hits | 在 Project 窗口搜索时包含 Asset Store 结果 |
| Auto Refresh | 脚本更改后自动编译（建议开启） |
| Script Changes While Playing | 运行时脚本变更行为：Recompile And Continue Playing / Recompile After Finished Playing / Stop Playing |

### Colors（颜色）
可自定义各个编辑器元素的颜色：
| 可改元素 | 说明 |
|---------|------|
| Playmode tint | Play 模式下编辑器色调（默认淡灰色） |
| Scene 视图 Background | Scene 视图背景色 |
| Grid | 场景网格线颜色 |
| Selected Outline / Wireframe | 选中物体轮廓/线框颜色 |
| 各种组件 Gizmo 颜色 | 碰撞器、导航网格等 |

### Keys（按键/快捷键）
- 查看和修改所有快捷键绑定
- 每个命令可绑定多个快捷键（Primary / Alternative）
- 点击命令旁的输入框后按下键盘设置新快捷键

### External Tools（外部工具）
| 设置 | 说明 |
|------|------|
| External Script Editor | 选择 IDE（Visual Studio / VS Code / Rider 等） |
| External Script Editor Args | IDE 启动参数 |
| Image application | 图片编辑器 |
| Revision Control Diff/Merge | 版本控制差异/合并工具 |

### GI Cache（全局光照缓存）
- 清理 GI 缓存，设置缓存大小上限
- 缓存路径默认为 `%APPDATA%\..\LocalLow\Unity\Caches\GiCache`

### 2D
- Sprite 默认 pivot 位置
- Grid Slicing 默认格子大小

### Scene View
- 摄像机移动速度等默认设置

---

## Project Settings（项目设置）

**路径：** `Edit > Project Settings...`

项目级设置，随项目存储共享。

---

### Input Manager（旧版输入系统）

`Edit > Project Settings > Input Manager`

输入轴列表（Axes），默认定义了以下虚拟轴：

| 轴名称 | 正向键 | 负向键 | 功能 |
|--------|--------|--------|------|
| Horizontal | right / d | left / a | 左右移动 |
| Vertical | up / w | down / s | 前后移动 |
| Fire1 | left ctrl / mouse 0 | — | 主操作 |
| Fire2 | left alt / mouse 1 | — | 副操作 |
| Fire3 | left shift / mouse 2 | — | 第三操作 |
| Jump | space | — | 跳跃 |
| Mouse X | — | — | 鼠标水平移动 |
| Mouse Y | — | — | 鼠标垂直移动 |
| Mouse ScrollWheel | — | — | 鼠标滚轮 |

每个轴的属性：
| 属性 | 说明 |
|------|------|
| Name | 轴名称 |
| Negative / Positive Button | 绑定按键 |
| Alt Negative / Alt Positive | 备用按键 |
| Gravity | 松键后归零速度 |
| Dead | 死区（模拟摇杆小于此值视为 0） |
| Sensitivity | 灵敏度 |
| Snap | 按反向键时立即归零 |
| Type | Key or Mouse / Mouse Movement / Joystick Axis |
| Axis | 设备轴（X/Y/3rd 等） |

---

### Tags and Layers（标签和层级）
- **Tags：** 预定义字符串标签（如 Player、Enemy、Untagged）。GameObject 在 Inspector 中选择 Tag
- **Layers：** 最多 31 个用户层（Layer 0-7 为内置，8-31 为用户可用）。用于碰撞矩阵、渲染 Culling Mask、Raycast 层过滤

---

### Time（时间设置）
| 属性 | 说明 |
|------|------|
| Fixed Timestep | 物理更新间隔（默认 0.02s = 50Hz） |
| Maximum Allowed Timestep | 单帧物理最大耗时（防止物理爆炸导致死循环） |
| Time Scale | 时间缩放（1=正常，0.5=半速，0=暂停） |

---

### Physics（3D 物理）
| 属性 | 说明 |
|------|------|
| Gravity | 重力向量（X,Y,Z）。真实重力为负 Y，默认 (0, -9.81, 0) |
| Default Material | 默认物理材质（无指定 Collider 时使用） |
| Bounce Threshold | 低于此相对速度不反弹（减少抖动） |
| Sleep Threshold | 低于此能量阈值进入休眠 |
| Default Contact Offset | 碰撞检测容差（默认 0.01） |
| Default Solver Iterations | 解算器迭代次数 |
| Queries Hit Triggers | Raycast 等查询是否命中触发器 |
| **Layer Collision Matrix**（底部） | 勾选矩阵中哪些层之间可碰撞 |

### Physics 2D（2D 物理）
与 3D 物理类似，有独立的 Gravity 和 Layer Collision Matrix。

---

### Player（发布设置）
打包和发布的核心设置：
| 设置分组 | 说明 |
|---------|------|
| Company Name | 公司名称 |
| Product Name | 产品名称 |
| Version | 版本号 |
| Default Icon | 应用图标 |
| Resolution and Presentation | 分辨率、全屏、方向 |
| Splash Image | 启动画面（Unity Logo + 自定义） |
| Other Settings | 渲染 API、颜色空间、脚本后端（IL2CPP/Mono）、API 兼容级别、目标架构 |
| XR Settings | 需配合 XR Plug-in Management |

---

### Quality（画质设置）
| 属性 | 说明 |
|------|------|
| 画质等级列表 | 6 个等级（Very Low 到 Ultra），可增删 |
| 每级控制 | 像素光数量、纹理质量、抗锯齿、阴影质量、软粒子、LOD Bias、VSync Count 等 |
| 平台默认等级 | 每个平台设置默认使用哪个画质等级 |

---

### Graphics（图形设置）
| 设置 | 说明 |
|------|------|
| Scriptable Render Pipeline Settings | SRP 资源引用（URP/HDRP 在此设置） |
| Always Included Shaders | 始终包含在构建中的 Shader 列表 |
| Preloaded Shaders | 预加载的 Shader |
| Shader Stripping | Shader 变体剔除设置 |

---

### Editor（编辑器设置）
| 设置 | 说明 |
|------|------|
| Version Control Mode | 版本控制模式（Visible Meta Files + 隐藏的 .meta） |
| Asset Serialization Mode | Mixed / Force Text / Force Binary |
| Default Behavior Mode | 3D 或 2D 默认模式 |
| Sprite Packer | 启用/禁用模式 |

---

### Script Execution Order
- 控制脚本 Awake/OnEnable/Update 等方法的执行顺序
- 数字越小越先执行
- 可为特定脚本指定执行顺序号
