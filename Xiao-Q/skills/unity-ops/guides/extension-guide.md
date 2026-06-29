# 扩展命令开发指南

当用户请求的操作超出"可用命令"表格范围时，按以下流程处理。**禁止修改 Skill 目录中的任何 CS 源文件**（`CoreOperations.cs`、`UnityOpsListener.cs`）。

## 决策流程

```
用户请求超出可用命令
        │
        ▼
第一步：调用 CoreOperations.Manual 查询手册
        │
   ┌────┴────┐
   │ 手册中有 │──► 按手册说明生成参数，直接发送命令
   └────┬────┘
        │ 手册中没有
        ▼
第二步：在 Unity 工程的 Editor/UnityOps 目录下编写新 CS 文件
        │
        ▼
第三步：发送 RefreshAssets 等待编译，再调用新命令
```

## 第一步：查询 Manual 手册

在认定某个操作"不在可用命令中"之前，**必须先查询 Manual**：

```python
result = send_command(action="CoreOperations.Manual", full=True)
print(result["manual"])   # Markdown 格式的 API 文档
```

- 手册中**存在**对应命令 → 按手册说明构造 JSON 并发送
- 手册中**不存在**对应命令 → 进入第二步

## 第二步：编写新 CS 文件

**文件存放位置**：`$projectRoot/Assets/Editor/UnityOps/`

> ⛔ **禁止修改**：`CoreOperations.cs`、`UnityOpsListener.cs`（Skill 内置核心文件）。所有扩展代码必须：
> 1. 新建独立 CS 文件，或
> 2. 向用户自行创建的已有 CS 文件添加方法

### 选择或创建 CS 类

| 功能域 | 推荐类名 | 归属的操作类型 |
|--------|----------|----------------|
| Shader 相关 | `ShaderOperations` | shader 代码、变体、编译等 |
| 材质相关 | `MaterialOperations` | 颜色/贴图、Shader 更换、属性调整 |
| 网格/Mesh 相关 | `MeshOperations` | 模型合并、UV 修改、顶点编辑、变形 |
| 光照/渲染 | `LightingOperations` | 光源设置、烘焙、阴影配置 |
| 动画相关 | `AnimationOperations` | 动画剪辑、Animator、状态机 |
| 音频相关 | `AudioOperations` | 音频播放器、音效管理 |
| 物理/碰撞 | `PhysicsOperations` | 刚体/碰撞体、射线检测 |
| UI 相关 | `UIOperations` | Canvas/UI 元素创建、布局 |
| 输入/交互 | `InputOperations` | 输入轴、按键映射 |
| 通用/其他 | `CustomOperations` | 不属于以上分类的杂项 |

**选择规则**：
1. 优先复用已有的用户自定义类（`Editor/UnityOps/` 下除两个内置文件之外的 `.cs`）
2. 若无对应的类存在，新建 CS 文件
3. 所有自定义类均放在 `UnityOps` 命名空间下，声明为 `public static class`

### 命令方法规范

每个命令对应一个 **公开静态方法**：

```csharp
public static string CommandMethod(string paramJson)
```

- 返回值：JSON 字符串（`{"status":"success",...}` 或 `{"status":"error","message":"..."}`）
- 参数类必须包含 `public string action;` 字段
- 必须添加 `[OpsMarkdown]` 属性

### CS 文件模板

```csharp
using System;
using UnityEditor;
using UnityEngine;

namespace UnityOps
{
    [OpsMarkdown("自定义操作模块", "用于扩展 UnityOps 的自定义命令。")]
    public static class CustomOperations
    {
        [Serializable]
        public class MyCommandParam
        {
            public string action;   // 必须包含
            public string targetName;
            public float value;
        }

        [OpsMarkdown(
            "MyCommand/自定义命令",
            "**功能**: 描述这个命令做什么。\n\n" +
            "**参数** JSON:\n" +
            "| 字段 | 类型 | 必填 | 说明 |\n" +
            "|------|------|------|------|\n" +
            "| `targetName` | string | **是** | 目标对象名称 |\n" +
            "| `value` | float | 否 | 数值参数，默认 0 |\n\n" +
            "**返回值**: JSON `{status, message}`")]
        public static string MyCommand(string paramJson)
        {
            var param = JsonUtility.FromJson<MyCommandParam>(paramJson ?? "{}");
            
            if (string.IsNullOrEmpty(param.targetName))
                return "{\"status\":\"error\",\"message\":\"targetName is required\"}";

            return $"{{\"status\":\"success\",\"message\":\"done\"}}";
        }
    }
}
```

### `[OpsMarkdown]` 属性说明

| 参数 | 类型 | 说明 |
|------|------|------|
| title (第一参数) | string | 格式 `"英文名/中文名"`，Manual 手册章节标题 |
| description (第二参数) | string | Markdown 格式详细描述 |

## 第三步：触发编译并调用新命令

```python
# 触发资产刷新 & 脚本重编译
result = send_command(action="CoreOperations.RefreshAssets")
# 等待 Unity 编译完成（通常 5~15 秒）

# 调用新命令（action = "类名.方法名"）
result = send_command(action="CustomOperations.MyCommand",
                      targetName="SomeObject",
                      value=1.5)
print(result)
```

> 编译状态检测：发送 `RefreshAssets` 后建议等待 10 秒，若返回 `"unknown action"` 错误，说明编译未完成。

> 📢 **编写新 CS 文件后必须告知用户文件路径**，例如：
> - "新 CS 文件已创建至：`$projectRoot/Assets/Editor/UnityOps/LightingOperations.cs`"
> - 或 "已向现有文件 `$projectRoot/Assets/Editor/UnityOps/CustomOperations.cs` 添加了新方法 `AdjustLighting`"

## 注意事项

1. **命名空间**：必须在 `namespace UnityOps { }` 内
2. **静态类**：方法和类均为 `static`
3. **主线程安全**：可直接使用 Unity API（由主线程 Update 循环调用）
4. **JSON 转义**：特殊字符需转义（`Replace("\"", "\\\"").Replace("\n", "\\n")`）
5. **参数字段**：必须是 `public`，且为简单类型或 `[Serializable]` 嵌套类
