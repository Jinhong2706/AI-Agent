# Game 视图

**打开方式：** `Window > General > Game`

Game 视图是从场景中摄像机渲染的游戏画面预览窗口。运行时无法编辑场景，但可以查看最终效果。顶部控制栏各控件如下：

---

## 控制栏详解

### Display（显示屏）
- 场景中挂载多个 Camera 时，从此下拉菜单选择不同摄像机的视角
- 默认 Display 1

### Aspect（宽高比）
- 选择不同宽高比来测试不同显示器效果
- 默认 **Free Aspect**（自由比例）
- 常用选项：16:9、16:10、4:3、21:9 等
- 点击 **+** 可添加自定义分辨率

### Low Resolution Aspect Ratios（低分辨率宽高比）
- 勾选后模拟旧显示器的像素密度
- 选择宽高比时会降低 Game 视图分辨率
- 非 Retina 显示器上始终启用

### Scale（缩放滑块）
- 向右拖动放大检查画面细节
- 向左拖动缩小查看完整画面
- **也可用鼠标滚轮**缩放

### Maximize on Play（运行时最大化）
- 启用后进入 Play 模式时，Game 视图最大化占满编辑器窗口

### Mute Audio（静音）
- 启用后在 Play 模式下静音所有游戏内音频

### VSync（Game view only）
- 启用后优先处理 Game 视图渲染，添加垂直同步
- **录制视频时特别有用**

### Stats（统计信息）
- 点击切换 **Statistics（统计面板）**
- 显示渲染性能数据：**帧率 FPS、Draw Calls、三角面数、顶点数、SetPass Calls、内存使用**等
- 用于监控和优化性能

### Gizmos
- 点击在 Game 视图里开关 Gizmos 显示
- 旁边下拉箭头可选择性显示/隐藏特定 Gizmo：灯光图标、声音图标、相机图标、碰撞体线框等
- 也包含 3D Gizmos 选项和图标大小滑块

---

## Statistics 面板各指标含义

| 指标 | 含义 | 参考值 |
|------|------|--------|
| **FPS** | 每秒帧数 | 目标 30/60 FPS |
| **CPU** | 主线程耗时 | <16ms（60FPS） |
| **Render thread** | 渲染线程耗时 | <16ms |
| **Batches / Draw Calls** | 绘制调用次数 | 越少越好。PC 建议 < 500 |
| **Saved by batching** | 合批节省的 Draw Call | 越大说明合批越有效 |
| **Tris** | 三角面数 | 视场景复杂度 |
| **Verts** | 顶点数 | 视场景复杂度 |
| **SetPass Calls** | Shader 切换次数 | 越少越好。与 Shader 种类数相关 |

---

## 播放控制

位于编辑器顶部工具栏（或 Game 视图上方）：

| 按钮 | 快捷键 | 功能 |
|------|--------|------|
| ▶ Play | Ctrl+P | 进入 Play 模式 |
| ❚❚ Pause | Ctrl+Shift+P | 暂停播放（可在 Inspector 中修改值观察运行时效果） |
| ▶❚ Step | Ctrl+Alt+P | 逐帧播放（暂停状态下每按一次前进一帧） |
