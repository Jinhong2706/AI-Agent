# Unity 常见问题快速解答（FAQ）

> **用法：** 遇到用户报错或问题时，先搜索关键词定位到对应条目，直接给出解决方案。不用从头翻。

---

## 目录

- [报错类](#报错类)
- [物理/移动类](#物理移动类)
- [UI 类](#ui-类)
- [动画类](#动画类)
- [场景/加载类](#场景加载类)
- [音频类](#音频类)
- [构建发布类](#构建发布类)
- [AI/脚本类](#ai脚本类)

---

## 报错类

### NullReferenceException: Object reference not set to an instance of an object

**最常见报错，90% 的新手都会遇到。**

**原因：** 你在代码里用了一个为 null（没有赋值）的变量或组件。

**排查步骤：**
1. 看报错信息里的行号，定位到具体代码行
2. 找出那一行里哪个变量可能是 null
3. 常见情况：
   - `GetComponent<T>()` 没找到 → 该 GameObject 上没挂这个组件
   - Inspector 里的拖拽槽没填 → `[SerializeField]` 的变量没有赋值
   - `GameObject.Find()` 没找到 → 对象名字不对或不在当前场景
   - `player` 变量为 null → Tag 没设为 "Player" 或 `FindGameObjectWithTag` 拼写错

**快速修复：** 在代码中加空值保护：
```csharp
if (rb != null)
    rb.linearVelocity = new Vector2(speed, rb.linearVelocity.y);
else
    Debug.LogError("Rigidbody2D 未找到！", this);
```

---

### MissingReferenceException: The object of type 'XXX' has been destroyed

**原因：** 代码引用的对象已经被 `Destroy()` 销毁了，但代码还在访问它。

**解决方案：**
```csharp
// 在访问前检查对象是否还存在
if (targetEnemy != null)
    targetEnemy.TakeDamage(damage);

// 或者用 Unity 内置的 null 检查（推荐，比 C# null 更准确）
if (healthSystem)
    healthSystem.TakeDamage(damage);
```

---

### CS0246: The type or namespace name 'XXX' could not be found

**原因：** 缺少 using 语句，或者没安装对应的包。

**解决方案：**
1. 检查是否需要添加 `using`：
   - `TextMeshPro` → `using TMPro;`
   - `InputSystem` → `using UnityEngine.InputSystem;`
   - `SceneManagement` → `using UnityEngine.SceneManagement;`
2. 如果是新输入系统，需要在 Package Manager 里安装 `com.unity.inputsystem`

---

### ArgumentException: Input Axis XXX is not setup

**原因：** 使用了旧版 Input Manager 中不存在的轴名称。

**解决方案：**
1. `Edit > Project Settings > Input Manager`
2. 找到或添加对应轴（如 "Horizontal"、"Jump"、"Vertical"）
3. 检查拼写是否一致（区分大小写）

---

## 物理移动类

### 角色穿过地面掉下去了

1. 角色和地面都需要 **Collider2D** 组件
2. 角色需要 **Rigidbody2D** 组件（且不是 Kinematic）
3. 地面的 Collider2D 的 **Is Trigger 不能勾选**
4. 确保 Collision Detection 不是 Discrete（高速物体选 Continuous）

### 角色不能跳跃

1. GroundCheck 子物体的位置是否在角色脚下
2. `groundCheckRadius` 是否足够大（建议 0.15~0.3）
3. 地面的 Layer 是否正确设置
4. `groundLayer` 在 Inspector 中是否选了地面所在的 Layer
5. `Input.GetButtonDown("Jump")` 中的 "Jump" 轴是否在 Input Manager 中配置了（默认绑空格键）

### 角色移到一半卡在墙里

1. 给角色添加合适的 **Collider2D**（不要太小）
2. Rigidbody2D 的 **Collision Detection** 改为 **Continuous**
3. 移动速度不要太高（超过 collider 大小会导致穿透）

### 跳跃手感差（跳不高 / 飘着下不来）

- 跳不高 → 增大 `jumpForce`（推荐 10~15）
- 下落太慢 → 检查 Rigidbody2D 的 Gravity Scale（默认 1，可调到 2~3）
- 要更真实的手感 → 参考高级移动模板中的"土狼时间"和"跳跃缓冲"

---

## UI 类

### 点击按钮没反应

1. Canvas 下必须有 **EventSystem**（会自动创建，如果删除了需手动添加）
2. Button 的 **OnClick** 事件是否绑定了方法
3. Button 上方是否有其他 UI 元素遮挡（用 Raycast Target 调试）
4. Canvas 的 Render Mode 是否正确：
   - Overlay → 全屏 UI
   - Camera → 需要 Event Camera 引用
   - World Space → 需要 Canvas 的 BoxCollider 或 PhysicsRaycaster

### UI 拖出屏幕 / 位置不对

1. Canvas 的 **Canvas Scaler** → UI Scale Mode 设为 **Scale With Screen Size**
2. Reference Resolution 设为 1920×1080（常用分辨率）
3. 检查 UI 元素的 Anchors 是否设对了（通常选 Middle-Center）

### TMP 字体显示为方块 / 不显示

1. 需要先导入 TMP Essentials：`Window > TextMeshPro > Import TMP Essentials`
2. 或者改用普通的 `Text` 组件（Legacy UI）
3. 确认 Font Asset 赋值正确

---

## 动画类

### 动画不播放

1. Animator 组件是否挂载
2. Animator Controller 是否赋值
3. 动画片段是否在 Animator Controller 中创建了状态
4. 参数名是否和代码中一致（区分大小写）
5. `anim.SetFloat("Speed", speed)` 中的 "Speed" 要和 Animator 参数名完全匹配

### 动画卡住 / 不过渡

1. 状态之间的 Transition 是否连接
2. Transition 的 **Conditions** 是否设置正确
3. 检查 **Has Exit Time**：如果勾选了，动画会播完才切换
4. Transition Duration 太长 → 缩短过渡时间

---

## 场景加载类

### SceneManager.LoadScene 找不到场景

1. 场景必须在 `File > Build Settings` 中手动添加
2. 场景名称拼写要完全一致（区分大小写）
3. 确认 buildIndex 正确

### 切换场景后数据丢失

1. 需要跨场景保留的对象 → 加 `DontDestroyOnLoad(gameObject)`
2. 或使用静态变量 / ScriptableObject / PlayerPrefs 存储数据
3. 切换场景时事件订阅未取消 → 在 `OnDestroy()` 中取消订阅

---

## 音频类

### 没有声音

1. AudioSource 组件是否挂载
2. AudioClip 是否赋值（Inspector 中拖入音频文件）
3. AudioSource 的 **Volume** 是否为 0
4. **Play On Awake** 是否勾选（不需要自动播放就取消）
5. 检查 `AudioListener` 是否存在（每个场景至少一个，通常在 Camera 上）

### 声音重叠 / 播放过快

- 使用 `PlayOneShot()` 而不是 `Play()` 来播放叠加音效
- 加冷却时间控制播放频率

---

## 构建发布类

### 打包失败 / 报错

1. 检查 `File > Build Settings` 中是否有错误图标
2. 常见原因：
   - 场景未添加到 Build Settings
   - Script Compilation Error（代码编译错误，先修代码）
   -缺少平台模块（如 Android Build Support 未安装）
3. 查看完整的构建日志：`Console` 窗口点击 `Clear` 后重新 Build

### Android 打包后安装失败

1. 包名（Bundle Identifier）格式要正确（如 `com.company.game`）
2. API Level 设置要合适（推荐 Minimum API Level 21+）
3. 如果是 ARM 设备，确保 Target Architectures 包含 ARMv7/ARM64

---

## AI/脚本类

### 敌人不追玩家

1. 玩家的 Tag 是否设为 "Player"
2. `FindGameObjectWithTag("Player")` 拼写是否正确
3. 检查 `detectionRange` 是否足够大
4. 确认敌人有自己的移动组件（Rigidbody2D + Collider）

### 敌人穿过墙壁追过来

1. 2D 游戏：用 `Vector2.MoveTowards` 不会穿墙，但如果直接设 `transform.position` 可能会
2. 3D 游戏：使用 NavMeshAgent 自动绕过障碍（参考 `common-features.md#enemy-ai-navmesh`）
3. 如果用 NavMesh：地面需要设为 Navigation Static 并 Bake

### 协程不执行 / 无限循环

```csharp
// 错误：没有 yield，会卡死
IEnumerator DoSomething()
{
    while (true) { /* 做事 */ }
}

// 正确：必须有 yield return
IEnumerator DoSomething()
{
    while (true)
    {
        yield return new WaitForSeconds(1f);
    }
}
```
