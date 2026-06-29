---
name: unity-ops
description: 通过 TCP 网络连接操作 Unity 编辑器的专用技能。当用户需要控制 Unity 编辑器执行场景操作（新建/保存/加载场景）、模型操作（创建几何体/放置资产/删除对象）、截图（渲染场景快照）或刷新资产数据库时使用。触发场景：(1) 在 Unity 场景中创建、移动、删除 3D 对象，(2) 保存或切换 Unity 场景，(3) 截取 Unity 场景截图，(4) 从 Agent 发指令控制 Unity 编辑器，(5) 提到 UnityOps / Unity Editor 操作时，(6) 用户说"在 Unity 中"做任何操作时（如"在Unity中创建一个球"、"在Unity中新建场景"等）。
---

# UnityOps — 通过网络操控 Unity 编辑器

UnityOps 通过 TCP Socket 向 Unity 编辑器内运行的 `UnityOpsListener` 服务发送 JSON 指令，实现对 Unity 场景的远程控制。

> **⛔ 全局严格限制：任何情况下都不允许修改、编辑或覆盖 Skill 目录中的两个 CS 源文件（`UnityOpsListener.cs`、`CoreOperations.cs`）。** CS 文件只能从 Skill 单向复制到 Unity 工程，绝对不可反向操作。

---

## ⚡ 使用前必须执行的检查流程

**每次执行任何 Unity 操作之前**，必须按以下顺序完成全部检查，任何一步失败都要先处理后再继续。

### 第一步：检查 Unity 进程并自动同步 CS 脚本

**1a. 检查进程**

```powershell
Get-Process | Where-Object { $_.MainWindowTitle -like "*Unity*" -and $_.ProcessName -eq "Unity" } | Select-Object Id, MainWindowTitle
```

- **找到进程** → 从 `MainWindowTitle` 提取工程路径，记录为 `$projectRoot`，继续 1b。
- **未找到进程** → 需要工程路径（见下方"未打开时"流程），完成 1b 后执行第二步自动启动。

若无法从标题提取工程路径，检查最近打开的 Unity 工程记录：
```powershell
Get-Content "$env:APPDATA\Unity\Editor\EditorPrefs.plist" -ErrorAction SilentlyContinue | Select-String "recentlyUsedProjectPaths"
```
仍无法确定时，询问用户工程路径（`.sln` 所在目录或含 `Assets/` 的目录）。

**1b. 自动同步 CS 脚本**（获取到 `$projectRoot` 后立即执行，无需询问）

```powershell
$skillSrc  = "$env:USERPROFILE\.agent\skills\unity-ops\scripts\unity_editor"
$targetDir = "$projectRoot\Assets\Editor\UnityOps"
$files = @("UnityOpsListener.cs","CoreOperations.cs")
if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
$diffFiles = @()

foreach ($f in $files) {
    $src = Join-Path $skillSrc $f
    $dst = Join-Path $targetDir $f
    if (-not (Test-Path $dst)) {
        Copy-Item $src $dst -Force
        Write-Host "[已复制] $f"
    } else {
        $srcHash = (Get-FileHash $src -Algorithm MD5).Hash
        $dstHash = (Get-FileHash $dst -Algorithm MD5).Hash
        if ($srcHash -ne $dstHash) {
            Write-Host "[不同] $f  (Skill:$srcHash  Unity工程:$dstHash)"
            $diffFiles += $f
        } else {
            Write-Host "[一致] $f"
        }
    }
}
```

**差异文件（`[不同]`）处理规则**：两边文件内容不一致时，**必须询问用户**：
> "检测到以下文件存在差异：`[文件名]`。请问您希望使用哪个版本？
> - **A. 使用 Skill 中的版本**（将 Skill 中的文件复制到 Unity 工程）
> - **B. 使用 Unity 工程中的版本**（保留现有文件，不做修改）"
- 用户选 A → 复制覆盖；复制完成后，**必须强制调用一次 `RefreshAssets()` 以确保 Unity 重新加载脚本**（若 TCP 连接尚未建立，则在连接成功后第一时间发送此指令）；用户选 B → 跳过，直接继续。

若有文件被复制，Unity 会自动重新编译，等待编译完成后再继续。

### 第二步：检查端口并启动 Unity（如需）

**2a. 检查端口 8888**

```powershell
$conn = Get-NetTCPConnection -LocalPort 8888 -State Listen -ErrorAction SilentlyContinue
if ($conn) { Write-Host "端口 8888 已监听，PID: $($conn.OwningProcess)" }
else { Write-Host "端口 8888 未监听" }
```

**情况 A：端口已监听** → 使用 `CoreOperations.GetAssetPath` 命令更新 `$projectRoot`，然后进行业务操作：

```python
result = send_command(action="CoreOperations.GetAssetPath")
if result.get("status") == "success":
    $projectRoot = result["project_path"]  # 更新为 Unity 返回的实际项目路径
    print(f"项目路径已更新: $projectRoot")
else:
    print(f"⚠️ GetAssetPath 获取失败: {result.get('message')}, 继续使用现有 $projectRoot")
```

**情况 B：端口未监听，且 Unity 已打开** → 提示用户：
> "Unity 已打开但 UnityOps 服务未启动。请在 Unity 编辑器中打开菜单 **Tools → UnityOpsListener**，点击 **启动服务器** 按钮。"
> 等待用户操作完成后，重新检查端口确认监听成功。

若用户无法手动启动服务（例如菜单不存在、编译报错等），**追加询问**：
> "⚠️ 如果您无法手动启动服务，我可以强制关闭当前 Unity 进程并以自动启动方式重新打开它（**注意：未保存的场景数据将会丢失**）。是否继续？"
- 用户**同意** → 执行以下命令强制终止 Unity 进程，然后按**情况 C** 的完整流程重新启动：
  ```powershell
  # 强制终止 Unity 进程（请确认用户已同意）
  Stop-Process -Id <Unity进程PID> -Force
  Write-Host "Unity 进程已终止，准备重新启动..."
  ```
- 用户**拒绝** → 停止操作，告知用户需手动处理后再继续。

**情况 C：端口未监听，且 Unity 未打开** → 按以下完整步骤自动启动 Unity：

**C-1. 自动查找 Unity 可执行文件**

```powershell
# 优先在 Unity Hub 管理的目录中查找最新版本
$unityExe = Get-ChildItem "C:\Program Files\Unity\Hub\Editor" -Recurse -Filter "Unity.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName

# 备用：在 Unity 标准安装目录中查找
if (-not $unityExe) {
    $unityExe = Get-ChildItem "C:\Program Files\Unity" -Recurse -Filter "Unity.exe" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
}

Write-Host "找到 Unity: $unityExe"
```

若自动查找失败（`$unityExe` 为空），询问用户 Unity 可执行文件路径，然后继续。

**C-2. 启动 Unity 并附带命令行参数**

> ⚠️ `UnityOpsListener.cs` 的静态构造函数中已内置命令行参数支持：检测到 `-startServer` 参数时会在 `[InitializeOnLoad]` 阶段自动调用 `StartServer()`，无需手动点击菜单。`-port` 参数可指定监听端口（默认 8888）。

```powershell
# 使用 -startServer -port 参数启动，Unity 加载完成后会自动开启 TCP 服务
Start-Process "$unityExe" -ArgumentList "-projectPath `"$projectRoot`" -startServer -port 8888"
Write-Host "已启动 Unity，等待服务就绪..."
```

**C-3. 轮询等待端口就绪**

Unity 加载工程通常需要 30~90 秒，使用轮询方式检测，避免无效等待：

```powershell
$skillRoot = "$env:USERPROFILE\.agent\skills\unity-ops"
$result = & "$skillRoot\scripts\wait-for-port.ps1" -Port 8888 -MaxWaitSeconds 120 -IntervalSeconds 5
if ($result.connected) {
    Write-Host "服务已就绪，PID: $($result.pid)"
} else {
    Write-Host "⚠️ 等待超时"
}
```

> 脚本路径：`scripts/wait-for-port.ps1`，支持 `-Port`、`-MaxWaitSeconds`、`-IntervalSeconds` 参数。

**C-4. 超时处理**

若 120 秒后端口仍未监听，按以下顺序排查：
1. 确认 Unity 编辑器已完成加载（窗口标题不再显示"正在编译..."）
2. 查看 Unity Console 是否有编译错误导致脚本未执行
3. 手动在 Unity 中打开 **Tools → UnityOpsListener**，点击 **启动服务器** 按钮作为兜底方案

---

## 通信方式

通过 TCP Socket 发送 UTF-8 编码的 JSON，读取返回的 JSON 响应。

**Python 发送示例**：

```python
import socket, json

def send_command(host="127.0.0.1", port=8888, **kwargs):
    payload = json.dumps(kwargs)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(payload.encode("utf-8"))
        response = s.recv(65536).decode("utf-8")
    return json.loads(response)
```

**消息格式**：所有命令均为一个 JSON 对象，必须包含 `action` 字段，其他字段按命令而定。

```json
{ "action": "ClassName.MethodName", ...其他参数... }
```

---

## 可用命令

所有操作命令均位于 `CoreOperations` 类中，按功能分为场景操作、模型操作、截图三组。

### 场景操作

| action | 功能 | 关键参数 |
|--------|------|----------|
| `CoreOperations.SaveScene` | 保存当前场景 | `scene_name`（可选，未命名时自动生成） |
| `CoreOperations.NewScene` | 新建场景 | 无 |
| `CoreOperations.LoadScene` | 加载场景 | `scene_name`（场景名或 Assets 路径，**必填**） |

### 模型操作

| action | 功能 | 关键参数 |
|--------|------|----------|
| `CoreOperations.CreateModel` | 创建基本几何体 | `type`（**必填**）、`name`、`position`、`rotation`、`scale` |
| `CoreOperations.DeleteObject` | 删除场景中的对象 | `name`（**必填**）、`delete_children` |
| `CoreOperations.PlaceAsset` | 放置 FBX/Prefab 资产 | `asset_path`（**必填**）、`name`、`position`、`rotation`、`scale` |

**几何体类型（`type` 可选值）**：`Cube`、`Sphere`、`Cylinder`、`Capsule`、`Plane`

**位置/旋转/缩放格式**（Vector3Data）：
```json
{ "x": 0.0, "y": 1.0, "z": 0.0 }
```

### 截图

| action | 功能 | 关键参数 |
|--------|------|----------|
| `CoreOperations.CaptureScreenshot` | 渲染并保存场景截图 | `angle_preset`、`output_path`、`screenshot_width`、`screenshot_height`、`fov`、`camera_position`、`camera_target` |

**视角预设（`angle_preset`）**：`iso`（等距，默认）、`top`（俯视）、`front`（正视）

截图默认保存到 Unity 项目根目录下的 `Screenshots/` 文件夹，返回绝对路径。

### 其他

| action | 功能 | 关键参数 |
|--------|------|----------|
| `CoreOperations.RefreshAssets` | 刷新资产数据库（AssetDatabase.Refresh） | 无 |
| `CoreOperations.Manual` | 获取完整 API 手册（返回 Markdown 字符串），添加 `"full": true` 可获取含模块概览的完整版 | `full`（可选） |
| `CoreOperations.GetAssetPath` | 获取 Unity 项目路径信息 | 无 |

**`GetAssetPath` 返回值**：JSON `{status, asset_path, project_path}`
- `asset_path`: `Application.dataPath` 的绝对路径（Assets 目录）
- `project_path`: 项目根目录绝对路径

## 响应格式

所有命令返回 JSON，成功时 `status` 为 `"success"`，失败时为 `"error"` 并附带 `message`：

```json
{ "status": "success", "name": "Cube" }
{ "status": "error", "message": "找不到名为 'xxx' 的 GameObject" }
```

---

## 示例：在场景中心创建一个 Cube

```python
# 1. 创建 Cube
result = send_command(action="CoreOperations.CreateModel",
                      type="Cube", name="MyCube",
                      position={"x": 0, "y": 0.5, "z": 0})
print(result)  # {"status": "success", "name": "MyCube"}

# 2. 截图确认
result = send_command(action="CoreOperations.CaptureScreenshot",
                      angle_preset="iso")
print(result["path"])  # 截图绝对路径

# 3. 保存场景
result = send_command(action="CoreOperations.SaveScene",
                      scene_name="MyScene")
print(result)  # {"status": "success", "path": "Assets/Scenes/MyScene.unity"}
```

---

## 扩展命令：处理"可用命令"之外的请求

当用户请求的操作超出上方"可用命令"表格范围时，**请先阅读 `guides/extension-guide.md` 参考文档**获取完整的开发指南（含决策流程、CS 文件编写规范、模板代码等）。

> **⛔ 严格限制：禁止修改 Skill 目录中的任何 CS 源文件（`UnityOpsListener.cs`、`CoreOperations.cs`）。** 所有扩展代码必须在 Unity 工程的 `Assets/Editor/UnityOps/` 目录下新建独立 CS 文件。

**快速决策流程**：
1. 先调用 `CoreOperations.Manual(full=True)` 查询运行时手册
2. 手册有该命令 → 直接使用
3. 手册没有 → 按 `guides/extension-guide.md` 指南在 Unity 工程中编写新 CS 文件 → `RefreshAssets` → 调用新命令
