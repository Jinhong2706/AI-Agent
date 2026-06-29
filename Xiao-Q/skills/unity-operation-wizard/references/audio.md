# Audio Mixer 窗口

**打开方式：** `Window > Audio > Audio Mixer`，快捷键 `Ctrl+8`

Audio Mixer 是一个用于混合、路由和控制音频的工具。

---

## 窗口面板

| 面板 | 说明 |
|------|------|
| **Hierarchy view（层级视图）** | AudioGroup 树形结构——定义混音信号链路 |
| **Mixer Views（视图）** | 缓存的可见性设置——仅显示部分 AudioGroup |
| **Snapshots 面板** | 记录所有 Mixer 参数状态的快照列表 |
| **AudioGroup Strip View（带状视图）** | 水平条状 VU 表、音量滑块、Mute/Solo/Bypass、DSP 效果链 |
| **Exposed Parameters（暴露参数）** | 暴露给脚本控制的参数列表 |

---

## AudioGroup（音频组）

信号链基本单元，每组合：音量衰减 + 音高校正 + 插入效果器。

| 操作 | 方法 |
|------|------|
| 创建子组 | 右键现有组 → Add child group |
| 创建同级组 | 右键现有组 → Add sibling group / 点击 + 按钮 |
| 重组 | 拖拽组到另一个组上改变父子关系 |
| 颜色标记 | 眼睛图标旁的颜色条 |
| 删除 | 选中 → 右键 → Remove Group |

**Master 组**始终存在，是根节点。

---

## AudioGroup Strip View（带状视图）

每个 AudioGroup 显示为水平条带：

| 控件 | 说明 |
|------|------|
| **VU Meter** | 音量电平表 |
| **Volume (dB)** | 音量滑块 |
| **Mute（M）** | 静音 |
| **Solo（S）** | 独奏——只监听此组 |
| **Bypass（B）** | 旁通效果器 |
| **Effect Slots** | DSP 效果器插槽（如 Lowpass、Reverb、Echo 等） |

---

## Snapshots（快照）

记录 Audio Mixer 所有参数的状态快照，用于切换不同音频场景。

| 属性/操作 | 说明 |
|----------|------|
| **Start Snapshot（星标）** | 场景启动时 Mixer 初始化的快照 |
| 创建 | 点击 Snapshot 面板 + 按钮 |
| 用途 | 不同场景音频配置（水面下/暂停菜单/战斗等） |

代码过渡：
```csharp
AudioMixerSnapshot snap1 = mixer.FindSnapshot("Normal");
AudioMixerSnapshot snap2 = mixer.FindSnapshot("Combat");
mixer.TransitionToSnapshots(
    new AudioMixerSnapshot[] { snap1, snap2 },
    new float[] { 0.3f, 0.7f },  // 权重
    2.0f  // 过渡时间（秒）
);
```

---

## Views（视图）

纯工作流优化，不影响运行时表现。

| 操作 | 说明 |
|------|------|
| 创建新 View | Views 面板 + 按钮 |
| 设置可见组 | Hierarchy 中的眼睛图标——显示/隐藏 |
| 切换 View | 在列表中点击 |

---

## Exposed Parameters（暴露参数）

将 Mixer 中的参数暴露给脚本：

1. 在 Inspector 中右键某个参数（如音量滑块）→ **Expose**
2. 参数出现在 Exposed Parameters 列表中
3. 右键参数可**重命名**（字符串即代码中引用名）

代码控制：
```csharp
mixer.SetFloat("MasterVolume", -10f);
mixer.SetFloat("SFXVolume", 0f);
mixer.GetFloat("MusicVolume", out float vol);
```

---

## Audio Source 关联 Audio Mixer

1. 选中场景中的 Audio Source 组件
2. **Output** 字段 → 点击小圆圈 → 浏览 Audio Mixer → 选择目标 AudioGroup
3. 该 Audio Source 的音频将经过该 Group 的信号链处理

多个 Audio Source 可输出到同一个 AudioGroup 统一控制音量。
