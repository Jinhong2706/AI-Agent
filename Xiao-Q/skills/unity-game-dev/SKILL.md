---
name: unity-game-dev
version: 1.2.0
description: "Unity 游戏开发助手，专为新手打造。帮助用户从零创建 2D/3D 游戏和应用。覆盖项目搭建、角色移动、物理碰撞、相机跟随、血量系统、背包系统、敌人 AI（FSM+NavMesh+FOV+行为树）、动画控制、完整 UI（主菜单、暂停、设置、背包、对话、场景过渡）、存档系统、音效、场景切换、粒子特效、射击系统、移动端触控、对象池、事件系统、ScriptableObject 配置、二段跳/墙跳、Boss 战、随机地图生成等 30+ 常用功能，每个功能提供完整可用的 C# 脚本和详细操作指引。包含新手常见误区提醒和报错排查方案。"
agent_created: true
---

# Unity 游戏开发助手

## 概述

本技能帮助用户在 Unity 引擎中从零开始创建游戏、应用或交互式程序。
面向 Unity 新手，提供逐步引导、可运行的 C# 脚本、最佳实践建议和常见问题解决方案。
涵盖 **30+ 个完整代码模板**，覆盖从基础到中级的游戏开发需求。

---

## 什么时候该用这个技能

**直接用以下话术开场，帮助用户快速判断：**

> "我看到你提到 Unity / 游戏开发相关的内容。需要我帮你用 Unity 实现吗？我可以直接生成 C# 脚本和操作步骤。"

### 触发关键词（出现这些词就主动介入）

| 中文触发词 | 英文触发词 | 场景 |
|-----------|-----------|------|
| Unity 游戏 / Unity 脚本 / Unity 报错 | Unity game / Unity script / Unity error | 所有 Unity 场景 |
| 帮我做个游戏 / 做个 app / 做个程序 | make a game / create an app | 新项目 |
| 角色移动 / 跳跃 / 碰撞 / 相机跟随 | player movement / jump / collision | 功能实现 |
| 敌人 AI / 巡逻 / 追踪 / Boss | enemy AI / patrol / chase / boss | AI 系统 |
| 背包 / 物品 / 道具 / 拾取 | inventory / item / pickup | 物品系统 |
| 血条 / 血量 / 伤害 / 死亡 | health / damage / death | 战斗系统 |
| 主菜单 / 暂停 / 设置 / UI | main menu / pause / settings / UI | UI 系统 |
| 存档 / 保存进度 / 读取 | save / load game | 数据持久化 |
| 音效 / BGM / 背景音乐 | sound / BGM / audio | 音频系统 |
| 手机游戏 / 移动端 / 触屏 / 虚拟摇杆 | mobile / touch / joystick | 移动端开发 |
| 打包 / 发布 / 出包 / APK | build / publish / APK | 发布部署 |
| "NullReferenceException" / "报错" / "不工作" | NullReference / error / not working | 调试排错 |

### 不应触发的场景

- 用户在讨论其他引擎（Godot、Unreal、Cocos），除非明确问到 Unity 对比
- 用户问的是 C# 语言基础语法（非 Unity 上下文）
- 用户在做非游戏类的 Unity 项目（如工业仿真），除非功能通用

### 适用场景

- 用户想创建 Unity 项目（2D/3D 游戏、手机游戏、PC 游戏、教学工具等）
- 用户需要实现具体游戏功能（角色移动、跳跃、AI、背包、存档等）
- 用户遇到 Unity C# 脚本报错或行为异常 → **直接帮排查，不要让用户自己翻文档**
- 用户想了解 Unity 某个系统的原理或用法
- 用户需要打包发布到 PC/手机/WebGL 等平台

---

## 核心工作流程

### 第一步：理解用户需求

在回应前，先判断用户属于哪个场景：

1. **全新项目** - 需要项目搭建指引 → 参考 `references/project-setup.md`
2. **实现某个功能** - 需要具体代码和步骤 → 参考 `references/common-features.md`
3. **调试/修复 Bug** - 需要分析错误并给出修复方案
4. **学习/理解概念** - 需要清晰的概念解释 + 示例代码

如果需求不明确，先用一句话确认："你是想从零建项目，还是在已有项目里添加某个功能？"

### 第二步：给出可落地的解决方案

回应时始终遵循以下结构（按需调整）：

1. **前置条件** - 用户需要预先准备什么（Unity 版本、资源、组件设置）
2. **代码实现** - 完整可运行的 C# 脚本，包含必要注释
3. **挂载说明** - 明确告诉用户把脚本挂到哪个 GameObject 上
4. **参数说明** - Inspector 中各公开变量的含义和推荐值
5. **测试方法** - 如何验证功能正常工作
6. **扩展建议** - （可选）如何在此基础上进一步扩展

### 第三步：代码规范

生成 C# 脚本时，遵循以下规范：

```csharp
// 文件开头：必须包含必要的 using 语句
using UnityEngine;
// 如需 UI: using UnityEngine.UI;
// 如需新版 Input: using UnityEngine.InputSystem;

// 类名与文件名保持一致
public class PlayerController : MonoBehaviour
{
    // 公开变量加 [SerializeField] 或 public，便于在 Inspector 调整
    [Header("移动参数")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float jumpForce = 10f;

    // 私有变量
    private Rigidbody2D rb;
    private bool isGrounded;

    // Awake: 初始化组件引用
    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    // Start: 初始化逻辑（仅运行时需要的）
    private void Start() { }

    // Update: 处理输入和非物理逻辑
    private void Update() { }

    // FixedUpdate: 处理物理逻辑
    private void FixedUpdate() { }
}
```

---

## 快速上手（3 分钟体验）

> 如果你是 Unity 新手，照着以下步骤就能做出一个能跑的小游戏。

### 1. 新建项目
1. 打开 Unity Hub → 新建项目 → 选择 **2D** 或 **3D** 模板
2. 项目名称随便取（如 "MyFirstGame"），点击创建
3. 等待编辑器打开（首次可能需要 1-3 分钟）

### 2. 做一个能移动的角色
1. Hierarchy 右键 → `2D Object > Sprite` → 重命名为 "Player"
2. 给 Player 添加组件：`Add Component` → 搜索 `Rigidbody2D` → 添加
3. 在 Rigidbody2D 中设置：Gravity Scale = 3，Constraints → Freeze Rotation Z ✓
4. 在 Player 下创建空子物体 → 重命名为 "GroundCheck"，拖到角色脚下
5. 创建地面：Hierarchy 右键 → `2D Object > Sprite` → 拉宽作为地面
6. 地面添加 `Box Collider 2D`，添加 Layer → 创建新 Layer "Ground"，地面设为 Ground
7. 创建 PlayerController2D 脚本（参考 `common-features.md#movement-2d`），挂到 Player
8. 在 Inspector 中：Ground Check 拖入 GroundCheck 子物体，Ground Layer 选 Ground
9. 点击 Play ▶️ → 用 A/D 或 ←/→ 移动，空格跳跃

### 3. 加一个能捡的金币
1. 创建圆形 Sprite → 命名 "Coin" → Tag 设为 "Coin"，添加 `Circle Collider 2D`（Is Trigger ✓）
2. 给 Player 添加 `CollisionExample` 脚本（参考 `common-features.md#collision`）
3. 点击 Play ▶️ → 碰到金币即销毁

### 4. 常见问题马上解决

| 问题 | 解决方案 |
|------|---------|
| 角色穿过了地面 | 地面和角色都需要 Collider2D，地面 Is Trigger = false |
| 跳不了 | GroundCheck 位置要刚好在角色脚下，Ground Layer 要选对 |
| 角色飞起来了 | Rigidbody2D 的 Gravity Scale 设为 1~5 之间 |
| 脚本报红字 | 复制完整报错信息发给 AI，直接帮你修复 |

> 更详细的故障排查，参考 `references/faq-troubleshooting.md`

---

## 常见功能速查表

直接加载 `references/common-features.md` 获取详细代码模板。

### 基础系统

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 角色移动 (2D) | 跑动、左右移动、跳跃 | common-features#movement-2d |
| 角色移动 (3D) | 3D移动、第三人称 | common-features#movement-3d |
| 相机跟随 | 摄像机、跟随玩家 | common-features#camera |
| 碰撞检测 | 碰到敌人、拾取道具 | common-features#collision |
| 血量系统 | 生命值、受伤、死亡 | common-features#health |

### 高级移动

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 二段跳/墙跳 | 二段跳、蹬墙跳、空中控制 | common-features#advanced-movement |
| 移动端触控 | 手机触屏、虚拟摇杆、触控操作 | common-features#mobile-input |

### AI 系统

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 敌人 AI（基础） | 巡逻、追踪、FSM | common-features#enemy-ai-basic |
| 敌人 AI（NavMesh） | 3D 寻路、绕过障碍 | common-features#enemy-ai-navmesh |
| 敌人 AI（视野检测） | FOV、看到玩家才追 | common-features#enemy-ai-fov |
| 敌人 AI（行为树） | 复杂 AI 设计模式 | common-features#enemy-ai-behaviortree |
| Boss 战模式 | Boss 血量、多阶段、特殊攻击 | common-features#boss-fight |

### 动画与视觉

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 动画控制 | Animator、播放动画 | common-features#animation |
| 粒子特效 | 爆炸、灰尘、火焰效果 | common-features#particle-effects |

### UI 系统

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| UI 基础 | 血条、分数 | common-features#ui-basic |
| 主菜单 | 开始/设置/退出 | common-features#ui-main-menu |
| 暂停菜单 | 暂停/恢复/返回 | common-features#ui-pause |
| 设置面板 | 音量、分辨率 | common-features#ui-settings |
| 背包 UI | 网格物品槽 | common-features#ui-inventory |
| 对话框系统 | NPC 对话、逐字显示 | common-features#ui-dialog |
| 场景过渡 | 淡入淡出 | common-features#ui-transition |

### 系统/数据

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 背包/物品 | 道具、拾取、背包 | common-features#inventory |
| 存档系统 | 保存、读取进度 | common-features#save |
| 音效/音乐 | AudioSource、BGM | common-features#audio |
| 场景管理 | 切换场景、加载 | common-features#scene |

### 架构与工具

| 功能 | 关键词 | 参考章节 |
|------|--------|----------|
| 单例基类 | GameManager、全局管理 | common-features#singleton-base |
| 事件系统 | 解耦通信、观察者模式 | common-features#event-system |
| 对象池 | 子弹、特效、减少 GC | common-features#object-pool |
| ScriptableObject | 数据配置、武器属性 | common-features#scriptable-object |
| 射击系统 | 子弹发射、弹道 | common-features#shooting |
| 随机地图生成 | 程序化生成、地牢 | common-features#procedural-generation |

---

## 新手常见误区（主动提醒）

在回答时，如果用户的做法触及以下误区，主动给出提醒：

1. **在 Update() 里用 transform.position 做物理移动** → 应改用 Rigidbody/CharacterController
2. **Find/GetComponent 放在 Update() 里每帧调用** → 应在 Awake/Start 里缓存
3. **忘记设置 Rigidbody2D 的 Gravity Scale / Freeze Rotation** → 导致角色倒地
4. **Layer 和 Tag 混用** → 碰撞检测逻辑混乱
5. **协程用 while(true) 不加 yield** → 导致无限循环卡死
6. **场景没有 EventSystem** → UI 点击无响应
7. **忘记取消事件订阅** → 切换场景后报 MissingReferenceException
8. **UI Canvas 的 Render Mode 未根据场景调整** → 屏幕适配异常

---

## 运行时保护机制（生成的代码必须包含）

生成的所有脚本必须包含以下防护模式，避免运行时崩溃：

### 1. 组件引用安全检查（防止 NullReferenceException）
```csharp
private void Awake()
{
    rb = GetComponent<Rigidbody2D>();
    if (rb == null)
    {
        Debug.LogError($"[PlayerController] 缺少 Rigidbody2D 组件！", this);
        enabled = false; // 禁用脚本，防止后续 Update 报错
        return;
    }
}
```

### 2. 单例安全访问模式
```csharp
public static GameManager Instance { get; private set; }

private void Awake()
{
    if (Instance != null && Instance != this)
    {
        Destroy(gameObject);
        return;
    }
    Instance = this;
    DontDestroyOnLoad(gameObject);
}
```

### 3. 对象销毁前安全判断
```csharp
// 销毁或禁用的对象必须先判断是否为 null
if (target != null && target.gameObject.activeSelf)
{
    target.TakeDamage(damage);
}

// 或者用 Unity 的 null 检查（比 C# 默认 null 检查更准确）
if (healthSystem != null)
    healthSystem.TakeDamage(damage);
```

### 4. 协程超时保护
```csharp
private IEnumerator WaitForSomething(float maxWait = 5f)
{
    float elapsed = 0f;
    while (!condition)
    {
        elapsed += Time.deltaTime;
        if (elapsed > maxWait)
        {
            Debug.LogWarning("等待超时，执行兜底逻辑");
            FallbackAction();
            yield break;
        }
        yield return null;
    }
    SuccessAction();
}
```

### 5. Try-Catch 包裹关键操作
```csharp
private void LoadGameData()
{
    try
    {
        string json = PlayerPrefs.GetString("SaveData");
        if (string.IsNullOrEmpty(json)) return;
        var data = JsonUtility.FromJson<GameData>(json);
        ApplyData(data);
    }
    catch (System.Exception e)
    {
        Debug.LogError($"[SaveSystem] 读取存档失败: {e.Message}");
        // 使用默认数据兜底
        ApplyDefaultData();
    }
}
```

---

## 调试辅助

当用户报告报错时，引导以下步骤：

1. 读取完整报错信息（行号 + 错误类型）
2. 确认脚本是否已挂载到 GameObject
3. 确认 Inspector 中的引用是否为空（NullReferenceException）
4. 建议在关键位置加 `Debug.Log()` 打印中间值

常见错误快速定位：

- `NullReferenceException` → 组件/变量未赋值，检查 Inspector 或 GetComponent
- `MissingReferenceException` → 引用的对象已被销毁（Destroy 后仍访问）
- `CS0246 type not found` → 缺少 using 语句或组件未安装（如 InputSystem）
- `Animator has not been initialized` → Animator 组件未挂载或未赋值

---

## 参考文件说明

- `references/project-setup.md` - Unity 项目搭建完整流程（从安装到第一个场景）
- `references/common-features.md` - 常用游戏功能代码模板（30+ 个系统，含完整 UI 与高级 AI）
- `references/faq-troubleshooting.md` - **常见问题快速解答**（按问题场景分类，不用翻全文）
- `references/unity-best-practices.md` - Unity 开发最佳实践与性能优化建议

按需读取对应参考文件以获取详细内容。**遇到用户报错时，优先查阅 `faq-troubleshooting.md`。**
