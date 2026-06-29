# Input Manager（旧版输入系统）

**路径：** `Edit > Project Settings > Input Manager`

Unity 内置的旧版输入系统。Unity 推荐新项目使用 Input System Package（`com.unity.inputsystem`）。

---

## 核心概念

| 类型 | 说明 |
|------|------|
| **Key** | 物理键盘按键（W、Space、Escape 等） |
| **Button** | 控制器按钮（如手柄 X 按钮） |
| **Virtual Axis（虚拟轴）** | 映射到按键/按钮的抽象名称，返回值 [-1, 1] |

---

## 虚拟轴属性

| 属性 | 说明 |
|------|------|
| **Name** | 轴名称，代码中通过此名称访问 |
| **Descriptive Name** | 描述名（独立平台中显示给用户） |
| **Negative Button / Positive Button** | 负/正向绑定按键（如 `left`/`right` 或 `a`/`d`） |
| **Alt Negative / Alt Positive Button** | 备用按键（如手柄） |
| **Gravity** | 松键后轴值回 0 的速度（单位/秒） |
| **Dead** | 死区。模拟摇杆绝对值小于此值视为 0 |
| **Sensitivity** | 轴值向目标值移动的速度（对数字按键有效） |
| **Snap** | 按反向键时立即归零 |
| **Invert** | 反转轴值 |
| **Type** | 类型：Key or Mouse / Mouse Movement / Joystick Axis |
| **Axis** | 设备轴（X axis / Y axis / 3rd axis(滚轮) 等） |
| **Joy Num** | 手柄编号（指定特定手柄或 Get Motion from all Joysticks） |

---

## 按键命名规则

### 键盘（不区分大小写）
| 按键类型 | 命名格式 |
|---------|---------|
| 字母键 | `a` `b` `c` ... `z` |
| 数字键 | `0` `1` `2` ... `9` |
| 方向键 | `up` `down` `left` `right` |
| 小键盘 | `[1]` `[2]` ... `[+]` `[equals]` |
| 修饰键 | `left shift` `right shift` `left ctrl` `right ctrl` `left alt` `right alt` `left cmd` `right cmd` |
| 特殊键 | `backspace` `tab` `return` `escape` `space` `delete` `enter` `insert` `home` `end` `page up` `page down` |
| 功能键 | `f1` `f2` ... `f15` |

### 鼠标
`mouse 0`（左键）/ `mouse 1`（右键）/ `mouse 2`（中键）/ `mouse 3` / `mouse 4`...

### 手柄
| 命名 | 说明 |
|------|------|
| `joystick button 0` ~ `joystick button 19` | 任意手柄按钮 |
| `joystick 1 button 0` | 特定 1 号手柄按钮 |

---

## Unity 默认预定义轴

| 轴名称 | 正键（Positive） | 负键（Negative） | 类型 | 用途 |
|--------|-----------------|-----------------|------|------|
| **Horizontal** | right / d | left / a | Key or Mouse | 左右移动 |
| **Vertical** | up / w | down / s | Key or Mouse | 前后移动 |
| **Fire1** | left ctrl / mouse 0 | — | Key or Mouse | 主射击/交互 |
| **Fire2** | left alt / mouse 1 | — | Key or Mouse | 副射击 |
| **Fire3** | left shift / mouse 2 | — | Key or Mouse | 第三操作 |
| **Jump** | space | — | Key or Mouse | 跳跃 |
| **Mouse X** | — | — | Mouse Movement | 鼠标水平 |
| **Mouse Y** | — | — | Mouse Movement | 鼠标垂直 |
| **Mouse ScrollWheel** | — | — | Mouse Movement | 滚轮 |
| **Submit** | return / joystick button 0 | — | Key or Mouse | UI 提交 |
| **Cancel** | escape / joystick button 1 | — | Key or Mouse | UI 取消 |

---

## 代码 API

```csharp
// 轴输入 — 平滑值 [-1, 1]
float h = Input.GetAxis("Horizontal");
float v = Input.GetAxis("Vertical");
float raw = Input.GetAxisRaw("Horizontal");  // 原始 (-1, 0, 1)

// 鼠标增量
float mx = Input.GetAxis("Mouse X");
float my = Input.GetAxis("Mouse Y");
float scroll = Input.GetAxis("Mouse ScrollWheel");

// 虚拟按钮（Fire1/Jump 等需要在 Input Manager 中定义）
bool held = Input.GetButton("Jump");
bool down = Input.GetButtonDown("Fire1");
bool up = Input.GetButtonUp("Fire2");

// 直接按键
bool w = Input.GetKey(KeyCode.W);
bool space = Input.GetKeyDown(KeyCode.Space);
bool esc = Input.GetKeyUp(KeyCode.Escape);

// 鼠标
bool left = Input.GetMouseButtonDown(0);
bool right = Input.GetMouseButton(1);
Vector3 pos = Input.mousePosition;
```

---

## 添加自定义轴

1. `Edit > Project Settings > Input Manager`
2. 增加 **Size** 数值，列表底部新增一条
3. 展开新条目，设置 Name、Positive/Negative Button 等属性
4. 右键条目可 Duplicate 或 Delete
