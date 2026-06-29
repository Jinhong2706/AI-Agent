# Unity 开发最佳实践

## 性能优化基础

### 1. 对象池（Object Pooling）
频繁 Instantiate/Destroy 会导致卡顿（GC 压力）。对于子弹、特效、敌人等大量重复生成的对象，使用对象池。

```csharp
using System.Collections.Generic;
using UnityEngine;

public class ObjectPool : MonoBehaviour
{
    public static ObjectPool Instance;

    [SerializeField] private GameObject prefab;
    [SerializeField] private int poolSize = 20;

    private Queue<GameObject> pool = new Queue<GameObject>();

    private void Awake()
    {
        Instance = this;
        for (int i = 0; i < poolSize; i++)
        {
            var obj = Instantiate(prefab);
            obj.SetActive(false);
            pool.Enqueue(obj);
        }
    }

    public GameObject Get(Vector3 position, Quaternion rotation)
    {
        if (pool.Count == 0)
        {
            var newObj = Instantiate(prefab);
            return Activate(newObj, position, rotation);
        }
        var obj = pool.Dequeue();
        return Activate(obj, position, rotation);
    }

    public void Return(GameObject obj)
    {
        obj.SetActive(false);
        pool.Enqueue(obj);
    }

    private GameObject Activate(GameObject obj, Vector3 pos, Quaternion rot)
    {
        obj.transform.SetPositionAndRotation(pos, rot);
        obj.SetActive(true);
        return obj;
    }
}
```

### 2. 缓存组件引用
不要在 Update() 中调用 GetComponent<>()，在 Awake/Start 中缓存。

```csharp
// 错误写法（每帧调用）
void Update() {
    GetComponent<Rigidbody2D>().AddForce(Vector2.up); // 性能差！
}

// 正确写法
Rigidbody2D rb;
void Awake() { rb = GetComponent<Rigidbody2D>(); }
void Update() { rb.AddForce(Vector2.up); }
```

### 3. 减少 Find 调用
`GameObject.Find()` 和 `FindObjectOfType()` 很慢，尽量避免在运行时频繁调用，改用单例模式或事件系统。

---

## 代码架构建议

### 单例管理器模式
用于 GameManager、AudioManager、UIManager 等全局系统：

```csharp
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject); // 切换场景不销毁
        }
        else
        {
            Destroy(gameObject);
        }
    }
}
```

### ScriptableObject 数据配置
用于存储游戏配置数据（武器属性、关卡参数等），避免硬编码：

```csharp
[CreateAssetMenu(fileName = "WeaponData", menuName = "Game/Weapon Data")]
public class WeaponData : ScriptableObject
{
    public string weaponName;
    public float damage;
    public float fireRate;
    public GameObject bulletPrefab;
}
```
使用：右键 Project 窗口 → `Create > Game > Weapon Data` 创建配置文件。

### 事件系统（解耦通信）
用 C# 事件或 UnityEvent 替代组件间直接引用：

```csharp
// 定义事件
public static class GameEvents
{
    public static System.Action<int> OnScoreChanged;
    public static System.Action OnPlayerDied;
}

// 触发事件
GameEvents.OnScoreChanged?.Invoke(100);

// 监听事件
void OnEnable()  { GameEvents.OnScoreChanged += UpdateUI; }
void OnDisable() { GameEvents.OnScoreChanged -= UpdateUI; } // 必须取消订阅！
void UpdateUI(int newScore) { ... }
```

---

## 常见性能问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 游戏帧率低 | Update() 中有繁重计算 | 用协程分帧处理，或降低调用频率 |
| 物体穿透 | 高速移动的碰撞体 | 使用连续碰撞检测 (Collision Detection = Continuous) |
| 内存泄漏 | 事件未取消订阅 | OnDisable 中取消所有事件订阅 |
| 动画卡顿 | Sprite 图集未压缩 | 使用 Sprite Atlas 打图集，设置合适的压缩格式 |
| 材质 Draw Call 多 | 每个物体用不同材质 | 合并图集，使用 GPU Instancing |

---

## 移动端优化建议

1. **降低物理精度** - `Edit > Project Settings > Physics 2D` 降低 Velocity Iterations（8→4）
2. **控制活跃对象数量** - 超出屏幕范围的对象使用对象池
3. **音频压缩** - 长音乐用 Vorbis 压缩，短音效用 PCM 或 ADPCM
4. **纹理压缩** - Android 用 ETC2，iOS 用 ASTC
5. **降低阴影质量** - `Quality Settings` 中降低 Shadow Distance 或关闭阴影

---

## Debug 技巧

```csharp
// 在 Scene View 画调试线（不出现在游戏中）
Debug.DrawLine(startPos, endPos, Color.red);
Debug.DrawRay(transform.position, Vector3.up * 2, Color.blue);

// 在 Scene View 画 Gizmos（通过继承或 OnDrawGizmos 方法）
void OnDrawGizmos()
{
    Gizmos.color = Color.yellow;
    Gizmos.DrawWireSphere(transform.position, detectionRange);
}

// 带条件的日志（可批量开关）
[System.Diagnostics.Conditional("UNITY_EDITOR")]
void DebugLog(string msg) => Debug.Log($"[{gameObject.name}] {msg}");
```

---

## 输入系统选择

### 传统 Input System（简单项目推荐）
```csharp
float h = Input.GetAxis("Horizontal");          // -1 到 1，有平滑
float h = Input.GetAxisRaw("Horizontal");       // 只有 -1, 0, 1，无平滑
bool jump = Input.GetButtonDown("Jump");         // 单次触发
bool fire = Input.GetMouseButtonDown(0);         // 鼠标左键
```

### 新版 Input System（复杂项目 / 多平台）
需要 Package Manager 安装 `Input System`，然后：
```csharp
using UnityEngine.InputSystem;
// 使用 Input Actions Asset 配置按键映射
// 代码中通过 PlayerInput 组件或直接读取 Action 值
```
