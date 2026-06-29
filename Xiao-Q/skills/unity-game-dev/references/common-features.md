# Unity 常用游戏功能代码模板

---

## movement-2d：2D 角色移动与跳跃

```csharp
using UnityEngine;

public class PlayerController2D : MonoBehaviour
{
    [Header("移动参数")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float jumpForce = 12f;

    [Header("地面检测")]
    [SerializeField] private Transform groundCheck;
    [SerializeField] private float groundCheckRadius = 0.2f;
    [SerializeField] private LayerMask groundLayer;

    private Rigidbody2D rb;
    private bool isGrounded;
    private float horizontalInput;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        // 获取水平输入（-1 到 1）
        horizontalInput = Input.GetAxisRaw("Horizontal");

        // 地面检测
        isGrounded = Physics2D.OverlapCircle(groundCheck.position, groundCheckRadius, groundLayer);

        // 跳跃
        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
        }

        // 翻转角色朝向
        if (horizontalInput > 0)
            transform.localScale = new Vector3(1, 1, 1);
        else if (horizontalInput < 0)
            transform.localScale = new Vector3(-1, 1, 1);
    }

    private void FixedUpdate()
    {
        // 物理移动
        rb.linearVelocity = new Vector2(horizontalInput * moveSpeed, rb.linearVelocity.y);
    }

    // 在 Scene View 中显示地面检测范围（调试用）
    private void OnDrawGizmosSelected()
    {
        if (groundCheck != null)
        {
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(groundCheck.position, groundCheckRadius);
        }
    }
}
```

**挂载说明：**
1. 脚本挂到 Player GameObject
2. 在 Player 子节点创建空对象 "GroundCheck"，放在角色脚下
3. 将 GroundCheck 拖入 Inspector 中的 Ground Check 槽
4. 地面 GameObject 设置 Layer 为 "Ground"，Inspector 的 Ground Layer 选择 "Ground"

---

## movement-3d：3D 角色移动（第三人称）

```csharp
using UnityEngine;

public class PlayerController3D : MonoBehaviour
{
    [Header("移动参数")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float rotationSpeed = 10f;
    [SerializeField] private float jumpForce = 8f;
    [SerializeField] private float gravity = -9.81f;

    private CharacterController controller;
    private Vector3 velocity;
    private bool isGrounded;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
    }

    private void Update()
    {
        // 地面检测
        isGrounded = controller.isGrounded;
        if (isGrounded && velocity.y < 0)
            velocity.y = -2f;

        // 获取输入
        float h = Input.GetAxisRaw("Horizontal");
        float v = Input.GetAxisRaw("Vertical");
        Vector3 direction = new Vector3(h, 0, v).normalized;

        // 移动
        if (direction.magnitude >= 0.1f)
        {
            // 朝移动方向旋转
            float targetAngle = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg;
            float angle = Mathf.LerpAngle(transform.eulerAngles.y, targetAngle, rotationSpeed * Time.deltaTime);
            transform.rotation = Quaternion.Euler(0, angle, 0);

            controller.Move(direction * moveSpeed * Time.deltaTime);
        }

        // 跳跃
        if (Input.GetButtonDown("Jump") && isGrounded)
            velocity.y = Mathf.Sqrt(jumpForce * -2f * gravity);

        // 重力
        velocity.y += gravity * Time.deltaTime;
        controller.Move(velocity * Time.deltaTime);
    }
}
```

**挂载说明：** 脚本 + CharacterController 组件挂到 Player，调整 CharacterController 的 Center/Height/Radius

---

## camera：相机跟随（2D/3D 通用）

```csharp
using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    [SerializeField] private Transform target;          // 跟随目标（玩家）
    [SerializeField] private float smoothSpeed = 5f;   // 跟随平滑度
    [SerializeField] private Vector3 offset = new Vector3(0, 2, -10); // 相机偏移

    [Header("边界限制（可选）")]
    [SerializeField] private bool useBounds = false;
    [SerializeField] private float minX, maxX, minY, maxY;

    private void LateUpdate()
    {
        if (target == null) return;

        Vector3 desiredPos = target.position + offset;

        // 边界限制
        if (useBounds)
        {
            desiredPos.x = Mathf.Clamp(desiredPos.x, minX, maxX);
            desiredPos.y = Mathf.Clamp(desiredPos.y, minY, maxY);
        }

        // 平滑跟随
        transform.position = Vector3.Lerp(transform.position, desiredPos, smoothSpeed * Time.deltaTime);
    }
}
```

---

## collision：碰撞检测与触发器

```csharp
using UnityEngine;

public class CollisionExample : MonoBehaviour
{
    // 物理碰撞（需要 Rigidbody + Collider，且 Is Trigger = false）
    private void OnCollisionEnter2D(Collision2D other)
    {
        if (other.gameObject.CompareTag("Enemy"))
        {
            Debug.Log("碰到敌人！");
        }
    }

    // 触发器（需要其中一方 Collider 的 Is Trigger = true）
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.gameObject.CompareTag("Coin"))
        {
            Debug.Log("拾取金币！");
            Destroy(other.gameObject); // 销毁金币
        }
    }
}
```

---

## health：血量系统

```csharp
using UnityEngine;
using UnityEngine.Events;

public class HealthSystem : MonoBehaviour
{
    [SerializeField] private float maxHealth = 100f;
    public float CurrentHealth { get; private set; }

    public UnityEvent<float> onHealthChanged;  // 参数：当前血量百分比 0~1
    public UnityEvent onDeath;

    private void Awake()
    {
        CurrentHealth = maxHealth;
    }

    public void TakeDamage(float damage)
    {
        CurrentHealth = Mathf.Clamp(CurrentHealth - damage, 0, maxHealth);
        onHealthChanged?.Invoke(CurrentHealth / maxHealth);

        if (CurrentHealth <= 0)
            onDeath?.Invoke();
    }

    public void Heal(float amount)
    {
        CurrentHealth = Mathf.Clamp(CurrentHealth + amount, 0, maxHealth);
        onHealthChanged?.Invoke(CurrentHealth / maxHealth);
    }
}
```

---

## inventory：背包/物品系统（简单版）

```csharp
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class Item
{
    public string itemName;
    public int quantity;
    public Sprite icon;
}

public class Inventory : MonoBehaviour
{
    public static Inventory Instance { get; private set; }

    [SerializeField] private int maxSlots = 20;
    private List<Item> items = new List<Item>();

    private void Awake()
    {
        // 单例模式
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    public bool AddItem(Item newItem)
    {
        // 先尝试堆叠
        Item existing = items.Find(i => i.itemName == newItem.itemName);
        if (existing != null)
        {
            existing.quantity += newItem.quantity;
            Debug.Log($"叠加物品: {newItem.itemName} x{existing.quantity}");
            return true;
        }

        // 添加新格子
        if (items.Count < maxSlots)
        {
            items.Add(newItem);
            Debug.Log($"获得物品: {newItem.itemName}");
            return true;
        }

        Debug.Log("背包已满！");
        return false;
    }

    public bool RemoveItem(string itemName, int count = 1)
    {
        Item item = items.Find(i => i.itemName == itemName);
        if (item == null || item.quantity < count) return false;

        item.quantity -= count;
        if (item.quantity <= 0) items.Remove(item);
        return true;
    }

    public List<Item> GetItems() => items;
}
```

---

## enemy-ai-basic：敌人 AI（有限状态机 + 巡逻 + 追踪 + 攻击）

```csharp
using UnityEngine;

public class EnemyAI : MonoBehaviour
{
    public enum State { Patrol, Chase, Attack, Stunned, Dead }

    [Header("移动参数")]
    [SerializeField] private float patrolSpeed = 2f;
    [SerializeField] private float chaseSpeed = 4f;

    [Header("感知范围")]
    [SerializeField] private float detectionRange = 8f;
    [SerializeField] private float attackRange = 1.5f;
    [SerializeField] private float attackDamage = 10f;
    [SerializeField] private float attackCooldown = 1f;

    [Header("巡逻点")]
    [SerializeField] private Transform[] patrolPoints;
    [SerializeField] private float waitAtWaypoint = 1f; // 巡逻点等待时间

    private Transform player;
    private State currentState = State.Patrol;
    private int patrolIndex = 0;
    private float lastAttackTime;
    private float waitTimer;
    private Animator anim;

    private void Start()
    {
        player = GameObject.FindGameObjectWithTag("Player").transform;
        anim = GetComponent<Animator>();
    }

    private void Update()
    {
        float distToPlayer = Vector2.Distance(transform.position, player.position);

        // 状态切换（优先级：死亡 > 眩晕 > 攻击 > 追击 > 巡逻）
        if (currentState == State.Dead) return;

        if (distToPlayer <= attackRange)
            ChangeState(State.Attack);
        else if (distToPlayer <= detectionRange)
            ChangeState(State.Chase);
        else if (currentState != State.Patrol)
            ChangeState(State.Patrol);

        // 状态行为
        switch (currentState)
        {
            case State.Patrol:  DoPatrol(); break;
            case State.Chase:   DoChase();  break;
            case State.Attack:  DoAttack(); break;
            case State.Stunned: break; // 眩晕什么都不做
        }

        // 翻转朝向
        FlipTowardsTarget();
    }

    private void ChangeState(State newState)
    {
        if (currentState == newState) return;
        currentState = newState;
        // 状态切换时可以触发动画变化
    }

    private void DoPatrol()
    {
        if (patrolPoints.Length == 0)
        {
            // 无巡逻点时原地待机
            return;
        }

        Transform target = patrolPoints[patrolIndex];
        float dist = Vector2.Distance(transform.position, target.position);

        if (dist < 0.1f)
        {
            waitTimer += Time.deltaTime;
            if (waitTimer >= waitAtWaypoint)
            {
                waitTimer = 0;
                patrolIndex = (patrolIndex + 1) % patrolPoints.Length;
            }
            return;
        }

        transform.position = Vector2.MoveTowards(transform.position, target.position, patrolSpeed * Time.deltaTime);
    }

    private void DoChase()
    {
        transform.position = Vector2.MoveTowards(transform.position, player.position, chaseSpeed * Time.deltaTime);
    }

    private void DoAttack()
    {
        if (Time.time - lastAttackTime >= attackCooldown)
        {
            lastAttackTime = Time.time;
            anim?.SetTrigger("Attack");
            player.GetComponent<HealthSystem>()?.TakeDamage(attackDamage);
        }
    }

    private void FlipTowardsTarget()
    {
        Vector3 target = (currentState == State.Patrol && patrolPoints.Length > 0)
            ? patrolPoints[patrolIndex].position
            : player.position;
        float dir = target.x - transform.position.x;
        if (Mathf.Abs(dir) > 0.01f)
            transform.localScale = new Vector3(Mathf.Sign(dir) * Mathf.Abs(transform.localScale.x), transform.localScale.y, 1);
    }
}
```

**扩展建议：**
- 添加 `TakeDamage/Stun/Die` 方法可在外部调用
- 使用 ScriptableObject 存储敌人数据（血量、速度等）

---

## enemy-ai-navmesh：NavMesh 寻路（3D 游戏推荐）

> **适用场景：** 3D 游戏中有复杂地形（楼梯、坡道、障碍物），需要敌人智能绕过障碍追踪玩家。

```csharp
using UnityEngine;
using UnityEngine.AI;

public class EnemyNavMesh : MonoBehaviour
{
    public enum State { Idle, Patrol, Chase, Attack }

    [Header("寻路参数")]
    [SerializeField] private float patrolRadius = 10f;
    [SerializeField] private float chaseSpeed = 5f;
    [SerializeField] private float detectionRange = 15f;
    [SerializeField] private float attackRange = 2f;

    [Header("攻击参数")]
    [SerializeField] private float attackDamage = 15f;
    [SerializeField] private float attackCooldown = 1.5f;

    private NavMeshAgent agent;
    private Transform player;
    private State currentState;
    private float lastAttackTime;
    private Vector3 patrolCenter; // 巡逻起始点

    private void Start()
    {
        agent = GetComponent<NavMeshAgent>();
        player = GameObject.FindGameObjectWithTag("Player").transform;
        patrolCenter = transform.position;
        SetNewPatrolDestination();
    }

    private void Update()
    {
        float distToPlayer = Vector3.Distance(transform.position, player.position);

        // 状态判定
        if (distToPlayer <= attackRange)
            ChangeState(State.Attack);
        else if (distToPlayer <= detectionRange)
            ChangeState(State.Chase);
        else
            ChangeState(State.Patrol);

        // 执行状态
        switch (currentState)
        {
            case State.Patrol:
                if (!agent.pathPending && agent.remainingDistance < 0.5f)
                    SetNewPatrolDestination();
                break;
            case State.Chase:
                agent.speed = chaseSpeed;
                agent.SetDestination(player.position);
                break;
            case State.Attack:
                agent.SetDestination(transform.position); // 停下
                AttackPlayer();
                break;
        }
    }

    private void ChangeState(State newState)
    {
        if (currentState == newState) return;
        currentState = newState;
    }

    private void SetNewPatrolDestination()
    {
        agent.speed = 3f;
        // 在巡逻中心随机找一个点
        Vector3 randomDir = Random.insideUnitSphere * patrolRadius;
        randomDir += patrolCenter;
        NavMeshHit hit;
        if (NavMesh.SamplePosition(randomDir, out hit, patrolRadius, NavMesh.AllAreas))
            agent.SetDestination(hit.position);
    }

    private void AttackPlayer()
    {
        if (Time.time - lastAttackTime >= attackCooldown)
        {
            lastAttackTime = Time.time;
            player.GetComponent<HealthSystem>()?.TakeDamage(attackDamage);
        }
    }
}
```

**搭建步骤：**
1. 将地面和障碍物设为 `Navigation Static`
2. `Window > AI > Navigation` → Bake 导航网格
3. 给敌人挂 NavMeshAgent 组件 + 此脚本

---

## enemy-ai-fov：视野检测（FOV + 射线）

> **常见需求：** 敌人只在"看到"玩家时才追击，而非进入圆形范围就发现。

```csharp
using UnityEngine;

public class EnemyFOV : MonoBehaviour
{
    [Header("视野参数")]
    [SerializeField] private float viewRadius = 10f;
    [SerializeField] [Range(0, 360)] private float viewAngle = 90f; // 视野角度
    [SerializeField] private LayerMask obstacleMask;  // 障碍物层
    [SerializeField] private LayerMask targetMask;    // 玩家层

    public bool CanSeePlayer { get; private set; }
    public Vector3 LastKnownPosition { get; private set; }

    private Transform player;

    private void Start()
    {
        player = GameObject.FindGameObjectWithTag("Player").transform;
        // 每 0.2 秒检测一次，不用每帧检测（性能优化）
        InvokeRepeating(nameof(FindVisibleTargets), 0f, 0.2f);
    }

    private void FindVisibleTargets()
    {
        CanSeePlayer = false;

        // 检查距离
        Vector3 dirToTarget = (player.position - transform.position);
        float distToTarget = dirToTarget.magnitude;
        if (distToTarget > viewRadius) return;

        // 检查角度（玩家是否在视野锥形内）
        float angleToTarget = Vector3.Angle(transform.right, dirToTarget.normalized);
        if (angleToTarget > viewAngle / 2) return;

        // 检查射线遮挡（中间是否有墙）
        if (Physics.Raycast(transform.position, dirToTarget.normalized, distToTarget, obstacleMask))
            return;

        CanSeePlayer = true;
        LastKnownPosition = player.position;
    }

    // 在 Scene 视图中绘制视野范围（调试用）
    private void OnDrawGizmos()
    {
        Gizmos.color = CanSeePlayer ? Color.red : Color.yellow;
        Vector3 viewAngleA = DirFromAngle(-viewAngle / 2, false);
        Vector3 viewAngleB = DirFromAngle(viewAngle / 2, false);
        Gizmos.DrawLine(transform.position, transform.position + viewAngleA * viewRadius);
        Gizmos.DrawLine(transform.position, transform.position + viewAngleB * viewRadius);
    }

    private Vector3 DirFromAngle(float angleInDegrees, bool isGlobal)
    {
        if (!isGlobal) angleInDegrees += transform.eulerAngles.z;
        return new Vector3(Mathf.Cos(angleInDegrees * Mathf.Deg2Rad), Mathf.Sin(angleInDegrees * Mathf.Deg2Rad), 0);
    }
}
```

**用法：** 将此脚本挂在敌人上，EnemyAI 中通过 `GetComponent<EnemyFOV>().CanSeePlayer` 替代距离检测触发追击。

---

## enemy-ai-behaviortree：行为树模式概览

当敌人行为超过 5 种状态时，建议从有限状态机（FSM）升级到行为树（Behavior Tree）。
行为树的核心节点类型：

| 节点 | 作用 | 示例 |
|------|------|------|
| **Sequence（顺序）** | 依次执行子节点，某一个失败则整体失败 | 检测玩家 → 移动到玩家 → 攻击 |
| **Selector（选择）** | 依次尝试子节点，某一个成功则整体成功 | 先尝试攻击，否则追击，否则巡逻 |
| **Condition（条件）** | 判断条件是否满足 | 玩家在攻击范围内？血量低于30%？ |
| **Action（动作）** | 执行具体行为 | 播放攻击动画、造成伤害、播放音效 |
| **Decorator（装饰）** | 修饰子节点 | 重复执行、冷却时间、反转结果 |

**简单行为树示例（伪代码）：**
```
Root (Repeat Forever)
└── Selector（优先级从左到右）
    ├── Sequence「战斗」
    │   ├── Condition: 玩家在视野内？
    │   └── Selector
    │       ├── Sequence「攻击」
    │       │   ├── Condition: 玩家在攻击范围？
    │       │   └── Action: 执行攻击
    │       └── Action「追击」: 移动到玩家
    └── Sequence「巡逻」
        ├── Action: 移动到巡逻点
        └── Action: 等待 2 秒
```

Unity 中可使用开源行为树插件（如 Behavior Designer）或自行实现。

---

## animation：Animator 动画控制

```csharp
using UnityEngine;

public class AnimationController : MonoBehaviour
{
    private Animator anim;
    private Rigidbody2D rb;

    private void Awake()
    {
        anim = GetComponent<Animator>();
        rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        // 根据速度切换跑步/站立动画
        float speed = Mathf.Abs(rb.linearVelocity.x);
        anim.SetFloat("Speed", speed);

        // 根据是否在空中切换跳跃动画
        bool isGrounded = Mathf.Abs(rb.linearVelocity.y) < 0.1f;
        anim.SetBool("IsGrounded", isGrounded);
    }

    // 触发一次性动画（如攻击）
    public void PlayAttack()
    {
        anim.SetTrigger("Attack");
    }
}
```

**Animator 配置说明：**
- 创建 Animator Controller，添加参数：`Speed`(Float), `IsGrounded`(Bool), `Attack`(Trigger)
- 创建动画状态机：Idle -> Run (Speed > 0.1), Run -> Idle (Speed < 0.1)

---

## ui-basic：UI 基础（血条 + 分数 + 按钮事件）

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class GameUI : MonoBehaviour
{
    [Header("血条")]
    [SerializeField] private Slider healthBar;

    [Header("分数")]
    [SerializeField] private TextMeshProUGUI scoreText;
    private int score = 0;

    // 更新血条（0~1）
    public void UpdateHealthBar(float fillAmount)
    {
        healthBar.value = fillAmount;
    }

    // 增加分数（带动画效果）
    public void AddScore(int amount)
    {
        score += amount;
        scoreText.text = $"分数: {score}";
    }
}
```

**搭建步骤：**
1. Hierarchy 右键 → `UI > Canvas`
2. 在 Canvas 下添加 `UI > Slider` 作为血条
3. 在 Canvas 下添加 `UI > Text - TextMeshPro` 作为分数显示
4. 将 GameUI 脚本挂到 Canvas，关联对应 UI 元素

---

## ui-main-menu：主菜单（开始 / 设置 / 退出）

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class MainMenu : MonoBehaviour
{
    [Header("按钮")]
    [SerializeField] private Button startButton;
    [SerializeField] private Button settingsButton;
    [SerializeField] private Button quitButton;

    [Header("面板")]
    [SerializeField] private GameObject mainPanel;
    [SerializeField] private GameObject settingsPanel;

    private void Start()
    {
        // 绑定按钮事件（推荐用代码绑定，而不是 Inspector 拖拽）
        startButton.onClick.AddListener(OnStartGame);
        settingsButton.onClick.AddListener(OnOpenSettings);
        quitButton.onClick.AddListener(OnQuitGame);

        // 初始状态：显示主面板，隐藏设置
        settingsPanel.SetActive(false);
    }

    private void OnStartGame()
    {
        SceneManager.LoadScene("GameScene"); // 替换为实际场景名
    }

    private void OnOpenSettings()
    {
        mainPanel.SetActive(false);
        settingsPanel.SetActive(true);
    }

    public void OnCloseSettings()
    {
        mainPanel.SetActive(true);
        settingsPanel.SetActive(false);
    }

    private void OnQuitGame()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}
```

**UI 搭建步骤：**
1. Canvas 下创建 Panel → 命名 "MainPanel"
2. 在 MainPanel 下放三个 Button（开始游戏、设置、退出）
3. Canvas 下再创建 Panel → 命名 "SettingsPanel"
4. 挂 MainMenu 脚本到 Canvas，拖拽所有引用

---

## ui-pause：暂停菜单（暂停 / 恢复 / 返回主菜单）

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;

public class PauseMenu : MonoBehaviour
{
    [SerializeField] private GameObject pausePanel;

    private bool isPaused = false;

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (isPaused) ResumeGame();
            else PauseGame();
        }
    }

    public void PauseGame()
    {
        pausePanel.SetActive(true);
        Time.timeScale = 0f; // 冻结游戏逻辑
        isPaused = true;
    }

    public void ResumeGame()
    {
        pausePanel.SetActive(false);
        Time.timeScale = 1f;
        isPaused = false;
    }

    public void ReturnToMainMenu()
    {
        Time.timeScale = 1f; // 恢复时间，否则主菜单也会冻结
        SceneManager.LoadScene("MainMenu");
    }
}
```

**注意：** `Time.timeScale = 0` 会暂停所有依赖 Time.deltaTime 的逻辑，包括动画（Animator 的 Update Mode 需设为 Unscaled Time 才能继续播放暂停动画）。

---

## ui-settings：设置面板（音量控制 + 分辨率）

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SettingsPanel : MonoBehaviour
{
    [Header("音量")]
    [SerializeField] private Slider masterVolumeSlider;
    [SerializeField] private Slider bgmVolumeSlider;
    [SerializeField] private Slider sfxVolumeSlider;

    [Header("分辨率")]
    [SerializeField] private TMP_Dropdown resolutionDropdown;
    [SerializeField] private Toggle fullscreenToggle;

    private Resolution[] resolutions;

    private void Start()
    {
        // === 音量 ===
        // 从 PlayerPrefs 读取上次设置，默认 0.8
        masterVolumeSlider.value = PlayerPrefs.GetFloat("MasterVolume", 0.8f);
        bgmVolumeSlider.value = PlayerPrefs.GetFloat("BGMVolume", 0.8f);
        sfxVolumeSlider.value = PlayerPrefs.GetFloat("SFXVolume", 0.8f);

        masterVolumeSlider.onValueChanged.AddListener(OnMasterVolumeChanged);
        bgmVolumeSlider.onValueChanged.AddListener(OnBGMVolumeChanged);
        sfxVolumeSlider.onValueChanged.AddListener(OnSFXVolumeChanged);

        // === 分辨率 ===
        resolutions = Screen.resolutions;
        resolutionDropdown.ClearOptions();
        int currentIndex = 0;
        var options = new System.Collections.Generic.List<string>();
        for (int i = 0; i < resolutions.Length; i++)
        {
            string option = $"{resolutions[i].width} x {resolutions[i].height}";
            options.Add(option);
            if (resolutions[i].width == Screen.currentResolution.width &&
                resolutions[i].height == Screen.currentResolution.height)
                currentIndex = i;
        }
        resolutionDropdown.AddOptions(options);
        resolutionDropdown.value = currentIndex;
        resolutionDropdown.RefreshShownValue();

        resolutionDropdown.onValueChanged.AddListener(OnResolutionChanged);
        fullscreenToggle.isOn = Screen.fullScreen;
        fullscreenToggle.onValueChanged.AddListener(OnFullscreenChanged);
    }

    private void OnMasterVolumeChanged(float value)
    {
        AudioListener.volume = value;
        PlayerPrefs.SetFloat("MasterVolume", value);
    }
    private void OnBGMVolumeChanged(float value)
    {
        PlayerPrefs.SetFloat("BGMVolume", value);
        // 通过 AudioManager 应用：AudioManager.Instance.SetBGMVolume(value);
    }
    private void OnSFXVolumeChanged(float value)
    {
        PlayerPrefs.SetFloat("SFXVolume", value);
        PlayerPrefs.Save();
    }
    private void OnResolutionChanged(int index)
    {
        Resolution res = resolutions[index];
        Screen.SetResolution(res.width, res.height, Screen.fullScreen);
    }
    private void OnFullscreenChanged(bool isFullscreen)
    {
        Screen.fullScreen = isFullscreen;
    }
}
```

---

## ui-inventory：背包 UI（网格布局 + 物品槽）

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

// 单个物品槽
public class ItemSlot : MonoBehaviour
{
    [SerializeField] private Image iconImage;
    [SerializeField] private TextMeshProUGUI quantityText;
    [SerializeField] private Button slotButton;

    public Item CurrentItem { get; private set; }
    public int Quantity { get; private set; }

    public void SetItem(Item item, int qty)
    {
        CurrentItem = item;
        Quantity = qty;
        iconImage.sprite = item.icon;
        iconImage.enabled = true;
        quantityText.text = qty > 1 ? $"x{qty}" : "";
    }

    public void ClearSlot()
    {
        CurrentItem = null;
        Quantity = 0;
        iconImage.sprite = null;
        iconImage.enabled = false;
        quantityText.text = "";
    }
}

// 背包面板
public class InventoryUI : MonoBehaviour
{
    [SerializeField] private GameObject inventoryPanel;
    [SerializeField] private Transform slotContainer; // 挂 GridLayoutGroup 的父节点
    [SerializeField] private ItemSlot slotPrefab;     // 物品槽预制体
    [SerializeField] private int slotCount = 20;

    private ItemSlot[] slots;
    private bool isOpen = false;

    private void Start()
    {
        // 生成物品槽
        slots = new ItemSlot[slotCount];
        for (int i = 0; i < slotCount; i++)
        {
            slots[i] = Instantiate(slotPrefab, slotContainer);
            slots[i].ClearSlot();
        }
        inventoryPanel.SetActive(false);
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.I))
        {
            ToggleInventory();
        }
    }

    public void ToggleInventory()
    {
        isOpen = !isOpen;
        inventoryPanel.SetActive(isOpen);
        if (isOpen) RefreshUI();
    }

    public void RefreshUI()
    {
        var items = Inventory.Instance.GetItems();
        // 先清空所有槽
        for (int i = 0; i < slots.Length; i++)
            slots[i].ClearSlot();
        // 填入物品
        for (int i = 0; i < items.Count && i < slots.Length; i++)
            slots[i].SetItem(items[i], items[i].quantity);
    }
}
```

**搭建步骤：**
1. Canvas 下创建 Panel → 命名 "InventoryPanel"，加半透明背景 Image
2. 在 Panel 下创建空物体 → 添加 `GridLayoutGroup` 组件（设置 Cell Size + Spacing）
3. 创建 Slot 预制体：一个 Button，子节点放 Icon(Image) + Quantity(TMP)
4. 将 InventoryUI 挂到 Canvas，关联 SlotContainer 和 SlotPrefab

---

## ui-dialog：对话框/叙事系统

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

public class DialogSystem : MonoBehaviour
{
    [Header("UI 引用")]
    [SerializeField] private GameObject dialogPanel;
    [SerializeField] private TextMeshProUGUI dialogText;
    [SerializeField] private TextMeshProUGUI speakerNameText;
    [SerializeField] private float textSpeed = 0.05f; // 逐字显示速度

    private string[] currentLines;
    private int currentIndex;
    private bool isTyping;
    private Coroutine typingCoroutine;

    private void Update()
    {
        if (!dialogPanel.activeSelf) return;

        // 点击继续/跳过
        if (Input.GetMouseButtonDown(0) || Input.GetKeyDown(KeyCode.Space))
        {
            if (isTyping)
            {
                // 正在打字 → 立刻显示全部
                SkipTyping();
            }
            else
            {
                // 显示下一句
                ShowNextLine();
            }
        }
    }

    // 外部调用：开始一段对话
    public void StartDialog(string speaker, string[] lines)
    {
        dialogPanel.SetActive(true);
        currentLines = lines;
        currentIndex = 0;
        speakerNameText.text = speaker;
        ShowLine(currentLines[0]);
    }

    private void ShowLine(string line)
    {
        if (typingCoroutine != null) StopCoroutine(typingCoroutine);
        typingCoroutine = StartCoroutine(TypeText(line));
    }

    private IEnumerator TypeText(string line)
    {
        isTyping = true;
        dialogText.text = "";
        foreach (char c in line)
        {
            dialogText.text += c;
            yield return new WaitForSeconds(textSpeed);
        }
        isTyping = false;
    }

    private void SkipTyping()
    {
        if (typingCoroutine != null) StopCoroutine(typingCoroutine);
        dialogText.text = currentLines[currentIndex];
        isTyping = false;
    }

    private void ShowNextLine()
    {
        currentIndex++;
        if (currentIndex < currentLines.Length)
        {
            ShowLine(currentLines[currentIndex]);
        }
        else
        {
            EndDialog();
        }
    }

    private void EndDialog()
    {
        dialogPanel.SetActive(false);
        // 可触发后续事件：OnDialogEnd?.Invoke();
    }
}
```

**调用示例：**
```csharp
dialogSystem.StartDialog("村长", new string[] {
    "勇者，你终于来了！",
    "村子东边的洞穴里有怪物出没。",
    "请帮我们消灭它们吧！"
});
```

---

## ui-transition：场景过渡效果（淡入淡出）

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using UnityEngine.SceneManagement;

public class SceneTransition : MonoBehaviour
{
    public static SceneTransition Instance { get; private set; }

    [SerializeField] private Image fadeImage;
    [SerializeField] private float fadeDuration = 1f;

    private void Awake()
    {
        if (Instance == null) { Instance = this; DontDestroyOnLoad(gameObject); }
        else Destroy(gameObject);
    }

    private void Start()
    {
        // 场景开始时淡入
        StartCoroutine(FadeIn());
    }

    // 加载场景并带过渡
    public void LoadScene(string sceneName)
    {
        StartCoroutine(TransitionToScene(sceneName));
    }

    private IEnumerator TransitionToScene(string sceneName)
    {
        // 先淡出到黑屏
        yield return StartCoroutine(FadeOut());
        // 加载场景
        yield return SceneManager.LoadSceneAsync(sceneName);
        // 淡入
        yield return StartCoroutine(FadeIn());
    }

    private IEnumerator FadeIn()
    {
        float elapsed = 0;
        Color color = fadeImage.color;
        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            color.a = 1 - Mathf.Clamp01(elapsed / fadeDuration);
            fadeImage.color = color;
            yield return null;
        }
        color.a = 0;
        fadeImage.color = color;
    }

    private IEnumerator FadeOut()
    {
        float elapsed = 0;
        Color color = fadeImage.color;
        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            color.a = Mathf.Clamp01(elapsed / fadeDuration);
            fadeImage.color = color;
            yield return null;
        }
        color.a = 1;
        fadeImage.color = color;
    }
}
```

**搭建步骤：**
1. 创建 Canvas（Sort Order 设最高，如 999）
2. 在 Canvas 下创建纯黑 Image，铺满全屏
3. 将此脚本挂到 Canvas，关联 fadeImage
4. 外部通过 `SceneTransition.Instance.LoadScene("SceneName")` 切换场景

---

## save：存档系统（PlayerPrefs 简单版）

```csharp
using UnityEngine;

public class SaveSystem : MonoBehaviour
{
    // 保存数据
    public static void SaveGame(int score, float health, Vector3 position)
    {
        PlayerPrefs.SetInt("Score", score);
        PlayerPrefs.SetFloat("Health", health);
        PlayerPrefs.SetFloat("PosX", position.x);
        PlayerPrefs.SetFloat("PosY", position.y);
        PlayerPrefs.SetFloat("PosZ", position.z);
        PlayerPrefs.Save();
        Debug.Log("游戏已保存");
    }

    // 读取数据
    public static (int score, float health, Vector3 position) LoadGame()
    {
        int score = PlayerPrefs.GetInt("Score", 0);
        float health = PlayerPrefs.GetFloat("Health", 100f);
        Vector3 pos = new Vector3(
            PlayerPrefs.GetFloat("PosX", 0),
            PlayerPrefs.GetFloat("PosY", 0),
            PlayerPrefs.GetFloat("PosZ", 0)
        );
        return (score, health, pos);
    }

    // 检查是否有存档
    public static bool HasSave() => PlayerPrefs.HasKey("Score");

    // 删除存档
    public static void DeleteSave() => PlayerPrefs.DeleteAll();
}
```

---

## audio：音效与背景音乐

```csharp
using UnityEngine;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance;

    [Header("背景音乐")]
    [SerializeField] private AudioSource bgmSource;

    [Header("音效")]
    [SerializeField] private AudioSource sfxSource;
    [SerializeField] private AudioClip jumpSound;
    [SerializeField] private AudioClip coinSound;
    [SerializeField] private AudioClip hurtSound;

    private void Awake()
    {
        if (Instance == null) { Instance = this; DontDestroyOnLoad(gameObject); }
        else Destroy(gameObject);
    }

    public void PlayJump()   => sfxSource.PlayOneShot(jumpSound);
    public void PlayCoin()   => sfxSource.PlayOneShot(coinSound);
    public void PlayHurt()   => sfxSource.PlayOneShot(hurtSound);

    public void SetBGMVolume(float volume) => bgmSource.volume = volume;
    public void PauseBGM()  => bgmSource.Pause();
    public void ResumeBGM() => bgmSource.UnPause();
}
```

---

## scene：场景管理

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneController : MonoBehaviour
{
    // 加载场景（按名称）
    public void LoadScene(string sceneName)
    {
        SceneManager.LoadScene(sceneName);
    }

    // 重新加载当前场景（重开游戏）
    public void ReloadCurrentScene()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }

    // 加载下一个场景
    public void LoadNextScene()
    {
        int nextIndex = SceneManager.GetActiveScene().buildIndex + 1;
        if (nextIndex < SceneManager.sceneCountInBuildSettings)
            SceneManager.LoadScene(nextIndex);
        else
            Debug.Log("已是最后一个场景");
    }

    // 退出游戏
    public void QuitGame()
    {
        Application.Quit();
        // 编辑器内测试时用：
        // UnityEditor.EditorApplication.isPlaying = false;
    }
}
```

**注意：** 场景必须在 `File > Build Settings` 中添加才能通过 buildIndex 加载。

---

## singleton-base：单例基类

> **适用场景：** GameManager、AudioManager、UIManager 等全局唯一管理器。用基类避免每个管理器重复写单例逻辑。

```csharp
using UnityEngine;

public class Singleton<T> : MonoBehaviour where T : MonoBehaviour
{
    private static T _instance;
    public static T Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<T>();
                if (_instance == null)
                    Debug.LogError($"[Singleton] 未找到 {typeof(T).Name} 的实例！");
            }
            return _instance;
        }
    }

    protected virtual void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }
        _instance = this;
    }
}
```

**用法：** 任何管理器只需继承即可：
```csharp
public class GameManager : Singleton<GameManager>
{
    protected override void Awake()
    {
        base.Awake();
        DontDestroyOnLoad(gameObject); // 需要跨场景保留时加这行
        Debug.Log("GameManager 初始化完成");
    }

    public int Score { get; private set; }
    public void AddScore(int amount) => Score += amount;
}
```

---

## event-system：事件系统（观察者模式）

> **适用场景：** UI、玩家、敌人、道具之间需要通信，但不希望互相直接引用（解耦）。

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

// 通用事件系统（支持任意参数类型的事件）
public static class EventManager
{
    private static Dictionary<string, Delegate> eventTable = new Dictionary<string, Delegate>();

    // 注册监听
    public static void Register<T>(string eventName, Action<T> handler)
    {
        if (eventTable.TryGetValue(eventName, out var existing))
        {
            eventTable[eventName] = Delegate.Combine(existing, handler);
        }
        else
        {
            eventTable[eventName] = handler;
        }
    }

    // 取消监听
    public static void Unregister<T>(string eventName, Action<T> handler)
    {
        if (eventTable.TryGetValue(eventName, out var existing))
        {
            var result = Delegate.Remove(existing, handler);
            if (result == null) eventTable.Remove(eventName);
            else eventTable[eventName] = result;
        }
    }

    // 触发事件
    public static void Trigger<T>(string eventName, T data)
    {
        if (eventTable.TryGetValue(eventName, out var handler))
        {
            (handler as Action<T>)?.Invoke(data);
        }
    }

    // 无参数版本
    public static void Register(string eventName, Action handler)
    {
        if (eventTable.TryGetValue(eventName, out var existing))
            eventTable[eventName] = Delegate.Combine(existing, handler);
        else
            eventTable[eventName] = handler;
    }

    public static void Unregister(string eventName, Action handler)
    {
        if (eventTable.TryGetValue(eventName, out var existing))
        {
            var result = Delegate.Remove(existing, handler);
            if (result == null) eventTable.Remove(eventName);
            else eventTable[eventName] = result;
        }
    }

    public static void Trigger(string eventName)
    {
        if (eventTable.TryGetValue(eventName, out var handler))
            (handler as Action)?.Invoke();
    }
}
```

**使用示例：**
```csharp
// 定义事件名称常量（建议统一放一个静态类中）
public static class GameEvents
{
    public const string ON_SCORE_CHANGED = "OnScoreChanged";
    public const string ON_PLAYER_DIED = "OnPlayerDied";
    public const string ON_ENEMY_KILLED = "OnEnemyKilled";
}

// 监听者（如 UI）
void OnEnable()
{
    EventManager.Register<int>(GameEvents.ON_SCORE_CHANGED, UpdateScoreUI);
    EventManager.Register(GameEvents.ON_PLAYER_DIED, ShowGameOver);
}
void OnDisable()
{
    EventManager.Unregister<int>(GameEvents.ON_SCORE_CHANGED, UpdateScoreUI);
    EventManager.Unregister(GameEvents.ON_PLAYER_DIED, ShowGameOver);
}
void UpdateScoreUI(int newScore) { /* 更新 UI */ }
void ShowGameOver() { /* 显示游戏结束 */ }

// 触发者（如敌人死亡时）
EventManager.Trigger(GameEvents.ON_ENEMY_KILLED);
EventManager.Trigger<int>(GameEvents.ON_SCORE_CHANGED, 100);
```

---

## object-pool：对象池

> **适用场景：** 子弹、粒子特效、敌人等频繁生成/销毁的对象。用对象池避免 GC 卡顿。

```csharp
using System.Collections.Generic;
using UnityEngine;

public class ObjectPool : MonoBehaviour
{
    public static ObjectPool Instance { get; private set; }

    [System.Serializable]
    public class PoolConfig
    {
        public string name;
        public GameObject prefab;
        public int initialSize = 10;
    }

    [SerializeField] private PoolConfig[] poolConfigs;
    private Dictionary<string, Queue<GameObject>> pools = new Dictionary<string, Queue<GameObject>>();
    private Dictionary<string, GameObject> prefabs = new Dictionary<string, GameObject>();

    private void Awake()
    {
        Instance = this;

        foreach (var config in poolConfigs)
        {
            var queue = new Queue<GameObject>();
            prefabs[config.name] = config.prefab;

            for (int i = 0; i < config.initialSize; i++)
            {
                var obj = Instantiate(config.prefab, transform);
                obj.SetActive(false);
                queue.Enqueue(obj);
            }
            pools[config.name] = queue;
        }
    }

    // 从池中获取对象
    public GameObject Get(string poolName, Vector3 position, Quaternion rotation)
    {
        if (!pools.ContainsKey(poolName))
        {
            Debug.LogError($"[ObjectPool] 未找到名为 '{poolName}' 的对象池");
            return null;
        }

        if (pools[poolName].Count == 0)
        {
            var newObj = Instantiate(prefabs[poolName], transform);
            newObj.SetActive(false);
            return Activate(newObj, position, rotation);
        }

        var obj = pools[poolName].Dequeue();
        return Activate(obj, position, rotation);
    }

    // 归还对象到池中
    public void Return(string poolName, GameObject obj)
    {
        obj.SetActive(false);
        obj.transform.SetParent(transform);
        if (pools.ContainsKey(poolName))
            pools[poolName].Enqueue(obj);
        else
            Destroy(obj);
    }

    private GameObject Activate(GameObject obj, Vector3 pos, Quaternion rot)
    {
        obj.transform.SetPositionAndRotation(pos, rot);
        obj.SetActive(true);
        return obj;
    }
}
```

**使用示例（子弹发射）：**
```csharp
public class Gun : MonoBehaviour
{
    [SerializeField] private float fireRate = 0.2f;
    [SerializeField] private Transform firePoint;
    private float lastFireTime;

    private void Update()
    {
        if (Input.GetMouseButton(0) && Time.time - lastFireTime >= fireRate)
        {
            lastFireTime = Time.time;
            Fire();
        }
    }

    private void Fire()
    {
        var bullet = ObjectPool.Instance.Get("Bullet", firePoint.position, firePoint.rotation);
        // 子弹脚本在飞出屏幕或碰撞后调用：
        // ObjectPool.Instance.Return("Bullet", gameObject);
    }
}
```

**Inspector 配置：** 在 ObjectPool 组件中添加 PoolConfig 条目，设置名称（如 "Bullet"）和预制体引用。

---

## scriptable-object：ScriptableObject 数据配置

> **适用场景：** 武器属性、敌人数据、关卡配置等。避免硬编码，策划可在 Inspector 中直接调整数据。

```csharp
using UnityEngine;

// 定义可创建的配置资产类型
[CreateAssetMenu(fileName = "WeaponData", menuName = "Game Config/Weapon Data")]
public class WeaponData : ScriptableObject
{
    [Header("基础属性")]
    public string weaponName;
    public float damage = 10f;
    public float fireRate = 0.5f;
    public float bulletSpeed = 20f;

    [Header("资源")]
    public GameObject bulletPrefab;
    public AudioClip shootSound;
    public Sprite weaponIcon;

    [Header("弹药")]
    public int maxAmmo = 30;
    public float reloadTime = 1.5f;
}

// 多武器管理器
public class WeaponManager : MonoBehaviour
{
    [SerializeField] private WeaponData[] weapons;
    private int currentIndex = 0;

    public WeaponData CurrentWeapon => weapons[currentIndex];

    private void Update()
    {
        // 滚轮或数字键切换武器
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        if (scroll > 0) SwitchWeapon(1);
        else if (scroll < 0) SwitchWeapon(-1);

        for (int i = 0; i < weapons.Length; i++)
        {
            if (Input.GetKeyDown(KeyCode.Alpha1 + i))
                SwitchWeaponTo(i);
        }
    }

    private void SwitchWeapon(int direction)
    {
        currentIndex = (currentIndex + direction + weapons.Length) % weapons.Length;
        Debug.Log($"切换到武器: {CurrentWeapon.weaponName}");
    }

    private void SwitchWeaponTo(int index)
    {
        if (index >= 0 && index < weapons.Length)
        {
            currentIndex = index;
            Debug.Log($"切换到武器: {CurrentWeapon.weaponName}");
        }
    }
}
```

**创建步骤：** 在 Project 窗口右键 → `Create > Game Config > Weapon Data`，创建多个武器配置文件，拖拽到 WeaponManager 的数组中。

---

## shooting：射击系统

> **适用场景：** 2D/3D 射击游戏中的子弹发射、弹道控制。

```csharp
using UnityEngine;

public class Bullet : MonoBehaviour
{
    [Header("子弹属性")]
    [SerializeField] private float speed = 15f;
    [SerializeField] private float damage = 10f;
    [SerializeField] private float lifetime = 3f; // 自动销毁时间

    [Header("射击方向（2D）")]
    [SerializeField] private Vector2 direction = Vector2.right;

    private Rigidbody2D rb;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void Start()
    {
        // 发射子弹
        if (rb != null)
            rb.linearVelocity = direction * speed;
        else
            Debug.LogWarning("Bullet 需要 Rigidbody2D 组件");

        // 自动销毁（防止飞出屏幕后永久存在）
        Destroy(gameObject, lifetime);
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Enemy"))
        {
            other.GetComponent<HealthSystem>()?.TakeDamage(damage);
            // 如果使用对象池: ObjectPool.Instance.Return("Bullet", gameObject);
            // 否则直接销毁:
            Destroy(gameObject);
        }

        if (other.CompareTag("Ground") || other.CompareTag("Wall"))
        {
            // 碰到墙壁销毁
            Destroy(gameObject);
        }
    }

    // 外部设置子弹方向（射击时调用）
    public void SetDirection(Vector2 dir)
    {
        direction = dir.normalized;
        // 翻转子弹朝向
        if (dir.x < 0)
            transform.localScale = new Vector3(-1, 1, 1);
    }
}

// 射击发射器
public class Shooter : MonoBehaviour
{
    [Header("射击设置")]
    [SerializeField] private GameObject bulletPrefab;
    [SerializeField] private Transform firePoint;
    [SerializeField] private float fireRate = 0.3f;

    [Header("方向控制")]
    [SerializeField] private bool aimAtMouse = true; // 朝鼠标方向射击

    private float lastFireTime;
    private Camera cam;

    private void Awake()
    {
        cam = Camera.main;
    }

    private void Update()
    {
        if (Input.GetMouseButton(0) && Time.time - lastFireTime >= fireRate)
        {
            lastFireTime = Time.time;
            Shoot();
        }
    }

    private void Shoot()
    {
        Vector2 direction;
        if (aimAtMouse && cam != null)
        {
            Vector3 mouseWorld = cam.ScreenToWorldPoint(Input.mousePosition);
            direction = (mouseWorld - firePoint.position).normalized;
        }
        else
        {
            // 朝角色面朝方向射击
            direction = transform.localScale.x > 0 ? Vector2.right : Vector2.left;
        }

        var bullet = Instantiate(bulletPrefab, firePoint.position, Quaternion.identity);
        bullet.GetComponent<Bullet>()?.SetDirection(direction);
    }
}
```

**挂载说明：**
1. 创建子弹预制体：Sprite + Rigidbody2D（Gravity Scale=0）+ Collider2D（Is Trigger=true）+ Bullet 脚本，Tag 设为 "Bullet"
2. Shooter 脚本挂到玩家，设置 FirePoint（子弹发射位置，通常是枪口）

---

## advanced-movement：高级移动（二段跳 + 墙跳）

> **适用场景：** 平台跳跃游戏（Platformer），需要更丰富的操控手感。

```csharp
using UnityEngine;

public class AdvancedMovement : MonoBehaviour
{
    [Header("基础移动")]
    [SerializeField] private float moveSpeed = 6f;
    [SerializeField] private float jumpForce = 12f;
    [SerializeField] private int maxJumps = 2;       // 最大跳跃次数（含地面跳）
    [SerializeField] private float coyoteTime = 0.15f; // 离开地面后的容错时间
    [SerializeField] private float jumpBuffer = 0.1f; // 提前按跳的容错时间

    [Header("墙跳")]
    [SerializeField] private float wallJumpForceX = 8f;
    [SerializeField] private float wallJumpForceY = 10f;
    [SerializeField] private float wallSlideSpeed = 2f;  // 贴墙下滑速度
    [SerializeField] private LayerMask wallLayer;

    [Header("地面检测")]
    [SerializeField] private Transform groundCheck;
    [SerializeField] private float groundCheckRadius = 0.15f;
    [SerializeField] private LayerMask groundLayer;

    private Rigidbody2D rb;
    private bool isGrounded;
    private int jumpCount;
    private float coyoteTimer;
    private float jumpBufferTimer;
    private float horizontalInput;
    private bool isWallSliding;
    private bool isOnWall;
    private int wallDir;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        horizontalInput = Input.GetAxisRaw("Horizontal");

        // 地面检测
        bool wasGrounded = isGrounded;
        isGrounded = Physics2D.OverlapCircle(groundCheck.position, groundCheckRadius, groundLayer);

        // 土狼时间（离开平台后短暂仍可跳）
        if (isGrounded)
        {
            jumpCount = 0;
            coyoteTimer = coyoteTime;
        }
        else
        {
            coyoteTimer -= Time.deltaTime;
        }

        // 跳跃缓冲（落地前提前按跳也能跳）
        if (Input.GetButtonDown("Jump"))
            jumpBufferTimer = jumpBuffer;
        else
            jumpBufferTimer -= Time.deltaTime;

        // 执行跳跃
        if (jumpBufferTimer > 0f)
        {
            if (isOnWall && !isGrounded)
                WallJump();
            else if (jumpCount < maxJumps && coyoteTimer > 0f)
                Jump();

            if (Input.GetButtonDown("Jump")) // 重置缓冲
                jumpBufferTimer = 0f;
        }

        // 贴墙检测
        isOnWall = false;
        wallDir = 0;
        RaycastHit2D wallHit = Physics2D.Raycast(transform.position, Vector2.right * Mathf.Sign(horizontalInput), 0.6f, wallLayer);
        if (wallHit.collider != null && !isGrounded && Mathf.Abs(horizontalInput) > 0.1f)
        {
            isOnWall = true;
            wallDir = Mathf.Sign(horizontalInput);
        }

        // 翻转朝向（贴墙时不翻转）
        if (!isWallSliding && horizontalInput != 0)
            transform.localScale = new Vector3(Mathf.Sign(horizontalInput), 1, 1);
    }

    private void FixedUpdate()
    {
        // 贴墙滑行
        if (isOnWall && rb.linearVelocity.y < 0)
        {
            isWallSliding = true;
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, -wallSlideSpeed);
        }
        else
        {
            isWallSliding = false;
        }

        // 水平移动（贴墙时减速）
        float targetSpeed = isWallSliding ? horizontalInput * moveSpeed * 0.3f : horizontalInput * moveSpeed;
        rb.linearVelocity = new Vector2(targetSpeed, rb.linearVelocity.y);
    }

    private void Jump()
    {
        rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
        jumpCount++;
        coyoteTimer = 0f;
    }

    private void WallJump()
    {
        rb.linearVelocity = new Vector2(-wallDir * wallJumpForceX, wallJumpForceY);
        jumpCount = 0;
        // 翻转朝向（跳离墙壁）
        transform.localScale = new Vector3(-wallDir, 1, 1);
    }
}
```

**挂载说明：**
1. 玩家需要 Rigidbody2D + Collider2D + GroundCheck 子对象
2. 墙壁需要有 Collider2D，设置 Layer 为 "Wall"
3. Inspector 中 Wall Layer 选择 "Wall" 层

---

## particle-effects：粒子特效控制

> **适用场景：** 爆炸、灰尘、火焰、血液等视觉特效的动态控制。

```csharp
using UnityEngine;

public class ParticleEffectController : MonoBehaviour
{
    [Header("粒子预设")]
    [SerializeField] private ParticleSystem explosionEffect;
    [SerializeField] private ParticleSystem dustEffect;
    [SerializeField] private ParticleSystem muzzleFlashEffect;

    // 在指定位置播放特效并自动销毁
    public void PlayExplosion(Vector3 position)
    {
        if (explosionEffect == null) return;
        var ps = Instantiate(explosionEffect, position, Quaternion.identity);
        // 播放完毕后自动销毁
        var duration = ps.main.duration + ps.main.startLifetimeMultiplier;
        Destroy(ps.gameObject, duration);
    }

    // 角色落地灰尘
    public void PlayDust(Vector3 position)
    {
        if (dustEffect == null) return;
        var ps = Instantiate(dustEffect, position, Quaternion.identity);
        Destroy(ps.gameObject, ps.main.duration);
    }

    // 枪口火焰（需要跟随枪口）
    public ParticleSystem PlayMuzzleFlash(Transform firePoint)
    {
        if (muzzleFlashEffect == null) return null;
        var ps = Instantiate(muzzleFlashEffect, firePoint.position, firePoint.rotation, firePoint);
        return ps;
    }
}

// 脚本内播放特效的常用写法：
// public ParticleEffectController fx;
// fx.PlayExplosion(hitPoint);
```

**Unity 编辑器设置：**
1. Hierarchy 右键 → `Effects > Particle System` 创建粒子系统
2. 调整参数：Duration、Start Speed、Start Size、Start Color、Gravity Modifier
3. 添加子粒子（如爆炸的火花和烟雾）
4. 将粒子系统拖入 Inspector 的对应槽位

---

## mobile-input：移动端触控输入

> **适用场景：** 发布到 Android/iOS 的游戏，需要虚拟摇杆和触控按钮。

```csharp
using UnityEngine;
using UnityEngine.Events;

// 虚拟摇杆
public class VirtualJoystick : MonoBehaviour, IDragHandler, IEndDragHandler
{
    [SerializeField] private Transform handle;      // 摇杆手柄
    [SerializeField] private float maxRadius = 80f;   // 最大拖拽半径

    public Vector2 Direction { get; private set; }
    public UnityEvent<Vector2> onJoystickInput;

    public void OnDrag(UnityEngine.EventSystems.PointerEventData eventData)
    {
        Vector2 inputDir = (eventData.position - (Vector2)transform.position).normalized;
        float distance = Vector2.Distance(eventData.position, transform.position);
        float clampedDist = Mathf.Min(distance, maxRadius);

        // 移动手柄
        handle.localPosition = inputDir * clampedDist;
        Direction = inputDir;
        onJoystickInput?.Invoke(inputDir);
    }

    public void OnEndDrag(UnityEngine.EventSystems.PointerEventData eventData)
    {
        handle.localPosition = Vector2.zero;
        Direction = Vector2.zero;
        onJoystickInput?.Invoke(Vector2.zero);
    }
}

// 触控按钮（跳跃、攻击等）
public class TouchButton : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
{
    public UnityEvent onPressed;
    public UnityEvent onReleased;
    public bool IsPressed { get; private set; }

    public void OnPointerDown(UnityEngine.EventSystems.PointerEventData eventData)
    {
        IsPressed = true;
        onPressed?.Invoke();
    }

    public void OnPointerUp(UnityEngine.EventSystems.PointerEventData eventData)
    {
        IsPressed = false;
        onReleased?.Invoke();
    }
}

// 使用触控输入的角色控制器（替代键盘输入版）
public class MobilePlayerController : MonoBehaviour
{
    [SerializeField] private VirtualJoystick joystick;
    [SerializeField] private TouchButton jumpButton;

    [Header("移动参数")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float jumpForce = 12f;

    private Rigidbody2D rb;
    private bool isGrounded;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        jumpButton.onPressed.AddListener(Jump);
    }

    private void FixedUpdate()
    {
        rb.linearVelocity = new Vector2(joystick.Direction.x * moveSpeed, rb.linearVelocity.y);
    }

    private void Jump()
    {
        if (isGrounded)
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
    }
}
```

**UI 搭建步骤：**
1. Canvas 设为 `Screen Space - Overlay`，添加 CanvasScaler（Scale With Screen Size）
2. 左下角创建虚拟摇杆 UI：Background（圆形 Image）+ Handle（小圆形 Image，Pivot=Center）
3. 右下角创建跳跃按钮：大圆形 Button + TouchButton 脚本
4. 确保 Canvas 有 `EventSystem`（会自动添加）

---

## boss-fight：Boss 战模式

> **适用场景：** 关卡 Boss 战，多阶段血量、特殊攻击模式、过场演出。

```csharp
using UnityEngine;
using UnityEngine.Events;

public class BossController : MonoBehaviour
{
    public enum BossPhase { Phase1, Phase2, Phase3, Dead }

    [Header("Boss 属性")]
    [SerializeField] private float maxHealth = 500f;
    [SerializeField] private float currentHealth;

    [Header("阶段阈值（百分比）")]
    [SerializeField] private float phase2Threshold = 0.6f;
    [SerializeField] private float phase3Threshold = 0.3f;

    [Header("攻击参数")]
    [SerializeField] private float phase1AttackInterval = 2f;
    [SerializeField] private float phase2AttackInterval = 1.2f;
    [SerializeField] private float phase3AttackInterval = 0.8f;

    [Header("事件")]
    public UnityEvent<BossPhase> onPhaseChanged;
    public UnityEvent onBossDefeated;

    private BossPhase currentPhase = BossPhase.Phase1;
    private float attackTimer;
    private Animator anim;
    private HealthSystem healthSystem;

    private void Awake()
    {
        currentHealth = maxHealth;
        anim = GetComponent<Animator>();
        healthSystem = GetComponent<HealthSystem>();
    }

    private void Start()
    {
        healthSystem.onHealthChanged.AddListener(OnHealthChanged);
        healthSystem.onDeath.AddListener(OnDefeated);
    }

    private void Update()
    {
        if (currentPhase == BossPhase.Dead) return;

        attackTimer -= Time.deltaTime;
        if (attackTimer <= 0f)
        {
            ExecuteAttack();
            ResetAttackTimer();
        }
    }

    private void OnHealthChanged(float healthPercent)
    {
        float hpRatio = currentHealth / maxHealth;

        if (hpRatio <= phase3Threshold && currentPhase < BossPhase.Phase3)
        {
            currentPhase = BossPhase.Phase3;
            onPhaseChanged?.Invoke(currentPhase);
            anim?.SetTrigger("Phase3");
            Phase3Enrage();
        }
        else if (hpRatio <= phase2Threshold && currentPhase < BossPhase.Phase2)
        {
            currentPhase = BossPhase.Phase2;
            onPhaseChanged?.Invoke(currentPhase);
            anim?.SetTrigger("Phase2");
            Phase2Enhance();
        }
    }

    private void ExecuteAttack()
    {
        switch (currentPhase)
        {
            case BossPhase.Phase1:
                PerformBasicAttack();
                break;
            case BossPhase.Phase2:
                if (Random.value < 0.4f) PerformBasicAttack();
                else PerformSpecialAttack();
                break;
            case BossPhase.Phase3:
                if (Random.value < 0.3f) PerformBasicAttack();
                else if (Random.value < 0.6f) PerformSpecialAttack();
                else PerformUltimateAttack();
                break;
        }
    }

    private void ResetAttackTimer()
    {
        switch (currentPhase)
        {
            case BossPhase.Phase1: attackTimer = phase1AttackInterval; break;
            case BossPhase.Phase2: attackTimer = phase2AttackInterval; break;
            case BossPhase.Phase3: attackTimer = phase3AttackInterval; break;
        }
    }

    // 各阶段攻击实现（根据具体游戏设计填充）
    private void PerformBasicAttack()
    {
        anim?.SetTrigger("BasicAttack");
        // 发射弹幕 / 挥击 / 冲刺等
    }

    private void PerformSpecialAttack()
    {
        anim?.SetTrigger("SpecialAttack");
        // 范围攻击 / 召唤小怪 / 护盾等
    }

    private void PerformUltimateAttack()
    {
        anim?.SetTrigger("UltimateAttack");
        // 全屏弹幕 / 大范围 AOE 等
    }

    private void Phase2Enhance()
    {
        // Phase 2 开始时的增强效果（如增加移动速度、添加新攻击）
        Debug.Log("Boss 进入 Phase 2！");
    }

    private void Phase3Enrage()
    {
        // Phase 3 狂暴模式（如更快的攻击频率、全屏特效）
        Debug.Log("Boss 进入 Phase 3 狂暴模式！");
    }

    private void OnDefeated()
    {
        currentPhase = BossPhase.Dead;
        anim?.SetTrigger("Death");
        onBossDefeated?.Invoke();
        Debug.Log("Boss 已被击败！");
    }
}
```

**扩展建议：**
- 结合 Animator 制作各阶段的过场动画
- Phase 切换时添加屏幕震动（Camera Shake）
- Phase3 可添加无敌帧的快速弹幕躲避机制

---

## procedural-generation：随机地图生成（地牢）

> **适用场景：** Roguelike、地牢探险等需要随机生成关卡的游戏。

```csharp
using UnityEngine;
using System.Collections.Generic;

public class DungeonGenerator : MonoBehaviour
{
    [Header("地图参数")]
    [SerializeField] private int dungeonWidth = 40;
    [SerializeField] private int dungeonHeight = 40;
    [SerializeField] private int roomMaxSize = 8;
    [SerializeField] private int roomMinSize = 4;
    [SerializeField] private int maxRooms = 15;
    [SerializeField] private int roomPlacementAttempts = 100;

    [Header("资源")]
    [SerializeField] private GameObject floorTile;
    [SerializeField] private GameObject wallTile;
    [SerializeField] private GameObject playerPrefab;
    [SerializeField] private GameObject exitPrefab;

    private bool[,] grid;
    private List<Room> rooms = new List<Room>();

    [System.Serializable]
    public class Room
    {
        public int x, y, width, height;
        public Vector2Int center => new Vector2Int(x + width / 2, y + height / 2);

        public Room(int x, int y, int width, int height)
        {
            this.x = x; this.y = y;
            this.width = width; this.height = height;
        }

        public bool Overlaps(Room other, int padding = 1)
        {
            return !(x + width + padding <= other.x || other.x + other.width + padding <= x ||
                     y + height + padding <= other.y || other.y + other.height + padding <= y);
        }
    }

    private void Start()
    {
        GenerateDungeon();
    }

    private void GenerateDungeon()
    {
        grid = new bool[dungeonWidth, dungeonHeight];

        // 生成房间
        for (int i = 0; i < roomPlacementAttempts && rooms.Count < maxRooms; i++)
        {
            int w = Random.Range(roomMinSize, roomMaxSize + 1);
            int h = Random.Range(roomMinSize, roomMaxSize + 1);
            int x = Random.Range(1, dungeonWidth - w - 1);
            int y = Random.Range(1, dungeonHeight - h - 1);

            var newRoom = new Room(x, y, w, h);

            bool overlaps = false;
            foreach (var existingRoom in rooms)
            {
                if (newRoom.Overlaps(existingRoom))
                {
                    overlaps = true;
                    break;
                }
            }

            if (!overlaps)
            {
                CarveRoom(newRoom);
                rooms.Add(newRoom);
            }
        }

        // 连接房间（走廊）
        for (int i = 1; i < rooms.Count; i++)
        {
            CarveCorridor(rooms[i - 1].center, rooms[i].center);
        }

        // 渲染地图
        RenderDungeon();

        // 放置玩家和出口
        if (rooms.Count > 0)
        {
            Instantiate(playerPrefab, (Vector2)rooms[0].center, Quaternion.identity);
            Instantiate(exitPrefab, (Vector2)rooms[rooms.Count - 1].center, Quaternion.identity);
        }
    }

    private void CarveRoom(Room room)
    {
        for (int x = room.x; x < room.x + room.width; x++)
        {
            for (int y = room.y; y < room.y + room.height; y++)
            {
                if (x >= 0 && x < dungeonWidth && y >= 0 && y < dungeonHeight)
                    grid[x, y] = true;
            }
        }
    }

    private void CarveCorridor(Vector2Int from, Vector2Int to)
    {
        int x = from.x;
        int y = from.y;

        // L 形走廊：先横后纵（或随机先纵后横）
        while (x != to.x)
        {
            if (x >= 0 && x < dungeonWidth && y >= 0 && y < dungeonHeight)
                grid[x, y] = true;
            x += x < to.x ? 1 : -1;
        }

        while (y != to.y)
        {
            if (x >= 0 && x < dungeonWidth && y >= 0 && y < dungeonHeight)
                grid[x, y] = true;
            y += y < to.y ? 1 : -1;
        }
    }

    private void RenderDungeon()
    {
        for (int x = 0; x < dungeonWidth; x++)
        {
            for (int y = 0; y < dungeonHeight; y++)
            {
                Vector3 pos = new Vector3(x, y, 0);

                if (grid[x, y])
                {
                    Instantiate(floorTile, pos, Quaternion.identity, transform);
                }
                else
                {
                    // 只在地板相邻处生成墙壁（减少墙壁数量）
                    if (HasAdjacentFloor(x, y))
                        Instantiate(wallTile, pos, Quaternion.identity, transform);
                }
            }
        }
    }

    private bool HasAdjacentFloor(int x, int y)
    {
        int[] dx = { -1, 1, 0, 0 };
        int[] dy = { 0, 0, -1, 1 };
        for (int i = 0; i < 4; i++)
        {
            int nx = x + dx[i], ny = y + dy[i];
            if (nx >= 0 && nx < dungeonWidth && ny >= 0 && ny < dungeonHeight && grid[nx, ny])
                return true;
        }
        return false;
    }
}
```

**挂载说明：**
1. 创建 floorTile 和 wallTile 的预制体（简单的 Sprite 即可）
2. 脚本挂到空 GameObject，点击运行即可生成随机地牢
3. Camera 需要足够大或动态调整 Orthographic Size 以显示整个地牢
