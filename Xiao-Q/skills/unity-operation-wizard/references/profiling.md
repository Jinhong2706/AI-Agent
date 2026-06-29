# Profiler + Frame Debugger

---

## Profiler（性能分析器）

**打开方式：** `Window > Analysis > Profiler`，快捷键 `Ctrl+7`

---

### 窗口结构

| 区域 | 说明 |
|------|------|
| **顶部控制栏** | Record / Deep Profile / 帧选择 / Clear / Save/Load |
| **模块选择区** | 勾选要显示的模块（CPU、GPU、Memory、Rendering...） |
| **中间帧时间图** | 绿≈16ms（60fps）/ 黄≈20-33ms / 红>33ms |
| **底部详细面板** | 选中帧后显示函数耗时层级与排序 |

---

### 控制栏

| 控制 | 功能 |
|------|------|
| **Record（⏺）** | 开始/停止数据采集 |
| **Deep Profile** | 深度剖析所有 C# 方法（慢但详细，开销大） |
| **Call Stacks** | 录制 GC.Alloc 等内存分配的完整调用栈 |
| **Clear on Play** | 每次 Play 自动清空旧数据 |
| **Target Selection** | 选择分析目标（Play Mode / Editor / 远程设备） |
| **Save（💾）** | 保存 Profiler 数据为 .data 文件 |
| **Load** | 加载已保存的 Profiler 数据 |
| **Frame Selection** | 下拉选择特定帧查看 |

---

### 核心模块

#### CPU Usage
始终激活，最常用。关注重点：
- **PlayerLoop** — 引擎主循环
- **BehaviourUpdate** — 你的脚本 Update 耗时
- **GC Alloc** — 内存分配（会触发 GC 导致卡顿）
- **RenderThread** — 渲染准备的 CPU 耗时
- **Physics.Processing** — 物理运算
- **UI Canvas** — UI 重建

> 常见优化：Update 过高→减少每帧计算 / GC Alloc 过高→避免字符串拼接、LINQ、装箱 / UI 过高→减少 Canvas 重建

#### GPU Usage
- 默认不激活（开销较高）
- 当 CPU 不忙但帧率低时，确认 GPU 是否瓶颈
- 分析 Camera.Render、Shadows、PostProcessing 等 GPU 耗时

#### Rendering
三个核心指标：
| 指标 | 含义 | 优化方向 |
|------|------|---------|
| **Draw Calls** | 绘制调用次数 | Static Batching / SRP Batcher / GPU Instancing |
| **Tris / Vertices** | 三角面/顶点数 | 减少模型面数、LOD |
| **SetPass Calls** | Shader 切换次数 | 减少材质球数量 |

#### Memory
| 指标 | 说明 |
|------|------|
| Total Allocated | 总内存占用 |
| Texture / Mesh / Animation / Audio | 各类资源内存分布 |
| GC Allocated | GC 堆内存 |

> 内存持续上涨不回落 = 内存泄漏。常见原因：资源加载未卸载、事件未注销、缓存列表无限增长

---

### 标准分析流程

```
1. 打开 Profiler → 确保 Record 开启
2. 运行游戏 → 找到红色掉帧区域 → 点击该帧
3. CPU Usage 面板查看最高耗时调用
4. 定位到自己的脚本或渲染问题
5. 查看 GC Alloc → 消除临时分配
6. 查看 Draw Call / SetPass → 优化合批
7. 必要时切换 GPU 模块确认 GPU 瓶颈
```

---

## Frame Debugger（帧调试器）

**打开方式：** `Window > Analysis > Frame Debugger`

逐 Draw Call 查看每一帧的渲染过程。

### 使用步骤
1. 打开 Frame Debugger
2. 点击 **Enable** 按钮
3. 帧调试器捕获当前帧的所有 Draw Call 序列
4. 在列表中逐条点击——Game 视图实时显示到该 Draw Call 为止的画面
5. 可以看到每个 Draw Call 的 Shader、材质、网格、Render Target 等详情

### 用途
- 排查 Draw Call 为什么不能合批
- 检查渲染顺序是否正确
- 确认透明物体/后处理的渲染时机
- 发现意外的额外渲染（如隐藏物体仍被绘制）
