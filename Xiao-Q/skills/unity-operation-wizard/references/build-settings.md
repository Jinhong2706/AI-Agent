# Build Settings 窗口

**打开方式：** `File > Build Settings`，快捷键 `Ctrl+Shift+B`

---

## 平台列表（Platform）

显示当前编辑器可以构建的所有目标平台。当前激活的平台有 Unity 图标标记。

| 平台 | 说明 |
|------|------|
| PC, Mac & Linux Standalone | 桌面独立应用 |
| Android | 安卓设备 |
| iOS | iPhone/iPad |
| Universal Windows Platform（UWP） | Windows 桌面/Xbox/HoloLens |
| WebGL | 网页浏览器（HTML5） |
| tvOS | Apple TV |
| PS4 / PS5 / Xbox / Switch | 游戏主机（需对应开发资格和模块） |

### 切换平台
1. 选中目标平台
2. 点击 **Switch Platform** 按钮
3. Unity 会重新导入适配目标平台的资源（耗时）

> 添加新平台模块：通过 **Unity Hub** → 选择编辑器版本 → 三点菜单 → Add Module

---

## Scenes in Build（场景列表）

列出构建中包含的场景。场景按列表顺序加载（第一个为启动场景）。

| 操作 | 如何做 |
|------|--------|
| 添加场景 | 拖拽场景从 Project 窗口到列表，或点击 **Add Open Scenes** |
| 排除场景 | 取消场景前面的复选框（保留在列表但不参与构建） |
| 删除场景 | 选中后按 Delete |
| 调整顺序 | 拖拽场景上下移动 |

---

## Build Options（构建选项）

| 选项 | 说明 |
|------|------|
| **Development Build** | 开发版——包含 Debug 符号和 Profiler 支持，设置 `DEVELOPMENT_BUILD` 宏 |
| **Autoconnect Profiler** | 自动连接 Profiler（需启用 Development Build） |
| **Deep Profiling Support** | 深度剖析每个函数调用（需 Development Build，性能开销大） |
| **Script Debugging** | 允许调试脚本代码（需 Development Build） |
| **Scripts Only Build** | 仅重编译脚本，复用上次数据文件（需 Development Build） |
| **Compression Method** | Default / LZ4（快）/ LZ4HC（高压缩但慢） |

---

## 按钮

| 按钮 | 说明 |
|------|------|
| **Build** | 开始构建，选择输出路径 |
| **Build And Run** | 构建完成后自动运行（快捷键 Ctrl+B） |
| **Player Settings...** | 打开 `Edit > Project Settings > Player` |

---

## Player Settings 关键项

构建时最常配置的内容：

| 设置 | 说明 |
|------|------|
| **Company Name** | 公司名称，决定 Application.dataPath 的一部分 |
| **Product Name** | 产品名——应用窗口标题和可执行文件名 |
| **Version** | 版本号 |
| **Default Icon** | 应用图标 |
| **Resolution** | 默认分辨率、全屏模式 |
| **Splash Image** | 启动画面配置 |
| **Rendering API** | 渲染 API（DirectX / Vulkan / Metal / OpenGL） |
| **Color Space** | Gamma / Linear 色彩空间 |
| **Scripting Backend** | Mono / IL2CPP |
| **API Compatibility Level** | .NET Standard 2.1 / .NET Framework |
| **Target Architectures** | x86 / x86_64 / ARM |

每个平台（PC、Android、iOS 等）有独立的 **Player Settings** 覆盖项，点击平台标签进入。

---

## 常见构建配置速查

### Windows Standalone
- Target Platform: Windows
- Architecture: Intel 64-bit（x86_64）
- Copy PDB files: 勾选（调试需要）

### Android
- 需要安装 Android Build Support 模块 + JDK/NDK/SDK
- Package Name（com.company.product 格式）必填
- Minimum API Level、Target API Level

### WebGL
- Compression Format: Gzip / Brotli / Disabled
- Code Optimization: Size / Speed
- 需要本地服务器测试（不能直接打开 .html）
