# Timeline 窗口

**打开方式：** `Window > Sequencing > Timeline`

Timeline 是 Unity 的过场动画/序列编辑器，可以编排动画、音频、激活、信号等的时间线。

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **Playable Director** | Timeline 的播放器组件，必须挂载在 GameObject 上 |
| **Timeline Asset** | .playable 资源，保存整个时间线编排 |
| **Track（轨道）** | 每种控制类型对应一个轨道（Animation、Audio、Activation 等） |
| **Clip（片段）** | 轨道上的具体内容，有起始时间和长度 |
| **Bindings（绑定）** | 将轨道连接到场景中的实际对象 |

---

## 窗口布局

| 区域 | 说明 |
|------|------|
| **左侧轨道列表** | 所有 Track 的名称，可折叠展开 |
| **右侧时间轴** | 每个 Track 上的 Clip 时间排列 |
| **顶部时间标尺** | 时间刻度，可点击设定 Playhead 位置 |
| **预览控制** | Play/Pause/Stop/步进 按钮 |

---

## 创建 Timeline

1. 选中场景中一个 GameObject
2. `Window > Sequencing > Timeline`
3. 在 Timeline 窗口中点击 **Create** 按钮
4. 选择路径保存 .playable 资源
5. Unity 自动添加 Playable Director 组件到该 GameObject

---

## 常用轨道类型

| 轨道类型 | 功能 |
|---------|------|
| **Animation Track** | 播放 Animation Clip。绑定到 Animator 组件 |
| **Activation Track** | 控制 GameObject 的激活/失活时间 |
| **Audio Track** | 播放 Audio Clip |
| **Control Track** | 控制另一个 Timeline 或 Prefab 的时间 |
| **Signal Track** | 在特定时间点发射信号事件（可用脚本监听） |
| **Cinemachine Track** | 控制 Cinemachine 虚拟相机切换 |
| **Playable Track** | 自定义 Playable（高级用途，需编写脚本） |

---

### Animation Track

绑定一个 Animator → 其上拖入 Animation Clip → 在时间轴上剪辑切口/循环。
- 右键空白处 → **Add From Animation Clip** 或直接拖入 Clip
- 每个 Clip 可调整 Blend In/Out、Ease In/Out 曲线

### Activation Track

绑定一个 GameObject → 添加 Activation Clip：
- Clip 范围内物体激活
- Clip 范围外物体失活

### Audio Track

- 拖入 Audio Clip
- 可在 Clip 上调整音量曲线

### Signal Track

- 添加 Signal Emitter（信号发射器）
- 需要定义一个 Signal Asset（.signal 资源）
- 在脚本中用 SignalReceiver 或 `SignalManager` 响应信号

---

## Track 操作

| 操作 | 方法 |
|------|------|
| 添加轨道 | 右键轨道区域 → 选择轨道类型 |
| 锁定轨道 | 点击轨道名旁的锁图标（锁定后不可编辑） |
| 静音轨道 | 点击眼睛图标旁的 M 按钮 |
| 删除轨道 | 右键轨道 → Delete |
| 移动轨道顺序 | 拖拽轨道上下 |

---

## Clip 操作

| 操作 | 方法 |
|------|------|
| 添加 Clip | 右键轨道空白 → Add / 从 Project 窗口拖入 |
| 移动 Clip | 拖拽（可跨轨道） |
| 裁剪 Clip | 拖拽 Clip 左右边缘 |
| 切割 Clip | 将 Playhead 放在目标位置 → 右键 Clip → Split / 按 S |
| 删除 Clip | 选中 → Delete |
| 复制 Clip | Ctrl+D |

---

## 常见工作流

### 创建过场动画
1. 创建一个空 GameObject 命名 "Cutscene"
2. 打开 Timeline → Create → 保存
3. 添加 Animation Track → 绑定角色的 Animator
4. 拖入动画剪辑到轨道
5. 添加 Activation Track → 绑定 UI 提示文字
6. 添加 Audio Track → 放入背景音乐/音效
7. 运行预览 → 调整时间点

### 代码控制 Timeline 播放

```csharp
PlayableDirector director = GetComponent<PlayableDirector>();

director.Play();       // 播放
director.Pause();      // 暂停
director.Stop();       // 停止
director.time = 0;     // 跳转到指定秒数
director.Evaluate();   // 立即采样当前时间（用于手动更新）

// 绑定具体对象到轨道
TimelineAsset timeline = director.playableAsset as TimelineAsset;
foreach (var track in timeline.GetOutputTracks())
{
    if (track.name == "Player Animation")
        director.SetGenericBinding(track, playerAnimator);
}
```
