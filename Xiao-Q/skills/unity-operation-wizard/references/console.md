# Console 窗口

**打开方式：** `Window > General > Console`，快捷键 `Ctrl+Shift+C`（Windows）/ `Cmd+Shift+C`（macOS）

---

## 窗口布局（4 个区域）

| 区域 | 功能 |
|------|------|
| **工具栏（A）** | 消息过滤、搜索、播放时行为按钮 |
| **窗口菜单（B）** | 打开日志文件、设置最大行数、堆栈跟踪选项 |
| **消息列表（C）** | 每条日志消息的列表显示 |
| **详细信息区（D）** | 选中消息的完整文本，包含可点击的堆栈跟踪链接 |

---

## 工具栏选项

| 选项 | 功能 |
|------|------|
| **Clear** | 清除控制台（编译器错误保留） |
| **Clear on Play** | 进入 Play 模式时自动清除 |
| **Clear on Build** | 构建时自动清除 |
| **Clear on Recompile** | 脚本重新编译时自动清除 |
| **Collapse** | 合并重复消息（每帧报同一错误时只显示第一条实例） |
| **Error Pause** | 调用 `Debug.LogError` 时自动暂停播放 |
| **Editor** | 下拉选择连接的目标：编辑器 / 远程设备 Player |

---

## 消息类型与过滤

| 类型 | API | 颜色 | 图标按钮 |
|------|-----|------|---------|
| **Log（普通日志）** | `Debug.Log()` | 白色 | 文档图标 📄 |
| **Warning（警告）** | `Debug.LogWarning()` | 黄色 | ⚠️ |
| **Error（错误）** | `Debug.LogError()` | 红色 | ❌ |

工具栏的 📄 / ⚠️ / ❌ 按钮可分别开关对应类型的显示。

---

## 带上下文的日志

传递 GameObject 作为第二个参数，点击日志即可在 Hierarchy 中定位到对应物体：

```csharp
Debug.LogWarning("警告信息", this.gameObject);
```

---

## 堆栈跟踪设置

### 三种模式
| 模式 | 行为 |
|------|------|
| **None** | 不输出堆栈跟踪 |
| **ScriptOnly**（默认） | 仅输出 C# 脚本的堆栈（不含引擎内部） |
| **Full** | 输出完整堆栈（含引擎 C++ 层和原生插件） |

### 配置方式
1. 点击 Console 窗口菜单按钮（⋮）
2. 选择 **Stack Trace Logging →**
3. 选择 **All** 统一设置，或分别设置 **Error / Warning / Log / Exception / Assert**

> Full 模式开销很大，仅调试时使用，不要带到发布版本。

---

## 日志文件

Console 中的所有内容也会写入日志文件：

**打开方式：** Console 窗口菜单（⋮）→ **Open Editor Log** 或 **Open Player Log**

| 平台 | Editor 日志路径 |
|------|----------------|
| Windows | `%LOCALAPPDATA%\Unity\Editor\Editor.log` |
| macOS | `~/Library/Logs/Unity/Editor.log` |
| Linux | `~/.config/unity3d/Editor.log` |

| 平台 | Player 日志路径 |
|------|----------------|
| Windows | `%USERPROFILE%\AppData\LocalLow\[公司名]\[产品名]\Player.log` |
| macOS | `~/Library/Logs/[公司名]/[产品名]/Player.log` |

---

## Debug.Log 日志格式化

```csharp
// 富文本（支持 HTML 标签）
Debug.Log("<color=green>成功！</color>");
Debug.Log("<b>粗体</b> <i>斜体</i> <size=20>大号文字</size>");

// 格式化日志
Debug.LogFormat("玩家血量：{0}", health);
```

---

## Debug 类常用方法速查

| 方法 | 说明 |
|------|------|
| `Debug.Log(object)` | 输出普通日志 |
| `Debug.LogFormat(string, params)` | 格式化日志 |
| `Debug.LogWarning(object)` | 输出警告（黄色） |
| `Debug.LogWarningFormat(string, params)` | 格式化警告 |
| `Debug.LogError(object)` | 输出错误（红色） |
| `Debug.LogErrorFormat(string, params)` | 格式化错误 |
| `Debug.LogException(Exception)` | 输出异常（带堆栈） |
| `Debug.Assert(bool)` | 条件为 false 时输出错误 |
| `Debug.Break()` | 暂停编辑器（等价于断点） |
