# Unity 2022.3 菜单栏完整结构

---

## File（文件）菜单

| 菜单项 | 快捷键 | 说明 |
|--------|--------|------|
| New Scene | Ctrl+N | 新建场景 |
| Open Scene | Ctrl+O | 打开已有场景 |
| Save | Ctrl+S | 保存当前场景 |
| Save As... | Ctrl+Shift+S | 场景另存为 |
| New Project... | — | 新建工程 |
| Open Project... | — | 打开已有工程 |
| Save Project | — | 保存工程 |
| Build Settings... | Ctrl+Shift+B | 构建设置 |
| Build And Run | Ctrl+B | 构建并运行 |
| Exit | — | 退出 Unity |

---

## Edit（编辑）菜单

| 菜单项 | 快捷键 | 说明 |
|--------|--------|------|
| Undo | Ctrl+Z | 撤销 |
| Redo | Ctrl+Y | 重做 |
| Cut | Ctrl+X | 剪切 |
| Copy | Ctrl+C | 复制 |
| Paste | Ctrl+V | 粘贴 |
| Duplicate | Ctrl+D | 原地复制 |
| Delete | Shift+Del | 删除 |
| Frame Selected | F | 视图居中选中物体 |
| Lock View to Selected | Shift+F | 锁定视角跟随选中物体 |
| Find | Ctrl+F | 在资源区按名称查找 |
| Select All | Ctrl+A | 全选 |
| Play | Ctrl+P | 播放/运行 |
| Pause | Ctrl+Shift+P | 暂停 |
| Step | Ctrl+Alt+P | 逐帧 |
| Preferences... | — | 编辑器偏好设置 |
| Project Settings ▶ | — | 项目设置（见下方子菜单） |
| Graphics Emulation ▶ | — | 图形仿真 |
| Network Emulation ▶ | — | 网络仿真 |
| Snap Settings... | — | 吸附/对齐设置 |
| Selection | — | 选中物体相关操作 |
| Sign in... | — | 登录 Unity 账号 |

### Project Settings 子菜单

| 子项 | 说明 |
|------|------|
| Input Manager | 旧版输入系统配置 |
| Tags and Layers | 标签和层级管理 |
| Audio | 全局音频设置 |
| Time | 时间尺度（Time.timeScale 默认值等） |
| Player | 发布设置（应用名、图标、分辨率、Splash 等） |
| Physics | 3D 物理参数（重力、碰撞矩阵等） |
| Physics 2D | 2D 物理参数 |
| Quality | 画质等级设置 |
| Graphics | 渲染管线/Shader 相关设置 |
| Editor | 编辑器行为设置 |
| Script Execution Order | 脚本执行顺序 |
| Preset Manager | 预设管理器 |

---

## Assets（资源）菜单

| 菜单项 | 快捷键 | 说明 |
|--------|--------|------|
| Create ▶ | — | 创建资源（Folder / C# Script / Shader / Prefab / Material / Animation / Scene 等） |
| Show in Explorer | — | 在文件管理器中显示 |
| Open | — | 打开选中资源 |
| Delete | — | 删除选中资源 |
| Rename | F2 | 重命名 |
| Open Scene Additive | — | 叠加方式打开场景（不关闭当前场景） |
| Import New Asset... | — | 导入新资源 |
| Import Package ▶ | — | 导入资源包（Custom Package / 内置如 Characters、Effects 等） |
| Export Package... | — | 导出选中资源为 .unitypackage |
| Find References in Scene | — | 在场景中查找对该资源的引用 |
| Select Dependencies | — | 选中所有依赖资源 |
| Refresh | Ctrl+R | 刷新资源数据库 |
| Reimport | — | 重新导入选中资源 |
| Reimport All | — | 全部重新导入 |
| Extract From Prefab | — | 从预制体中提取 |
| Run API Updater... | — | 运行 API 升级器 |
| Open C# Project | — | 在 IDE 中打开 C# 工程 |

---

## GameObject（游戏对象）菜单

| 菜单项 | 说明 |
|--------|------|
| Create Empty | 创建空对象 |
| Create Empty Child（Alt+Shift+N） | 创建子空对象 |
| 3D Object ▶ | Cube / Sphere / Capsule / Cylinder / Plane / Quad / Ragdoll / Terrain / Tree / Wind Zone / 3D Text |
| 2D Object ▶ | Sprite（多种形状）/ Tilemap / 其他 2D 对象 |
| Effects ▶ | Particle System / Trail / Line |
| Light ▶ | Directional / Point / Spot / Area / Reflection Probe / Light Probe Group |
| Audio ▶ | Audio Source / Audio Reverb Zone |
| Video ▶ | Video Player |
| UI ▶ | Canvas / Panel / Button / Text / TextMeshPro / Image / Raw Image / Slider / Scrollbar / Toggle / Input Field / Scroll View / Dropdown / Event System |
| Camera | 创建摄像机 |
| Center On Children | 父物体移到子物体中心 |
| Make Parent | 将选中设为一个父物体 |
| Clear Parent | 解除父子关系 |
| Apply Changes To Prefab | 应用预制体变更 |
| Break Prefab Instance | 断开预制体关联 |
| Set as First/Last Sibling | 设为兄弟节点第一个/最后一个 |
| Move To View（Ctrl+Alt+F） | 将选中物体移到 Scene 视图中心 |
| Align With View（Ctrl+Shift+F） | 物体对齐到当前 Scene 视角 |
| Align View to Selected | 视角与选中物体对齐 |
| Toggle Active State（Alt+Shift+A） | 切换激活状态 |

---

## Component（组件）菜单

| 菜单项 | 说明 |
|--------|------|
| Mesh ▶ | Mesh Filter / Mesh Renderer / Text Mesh |
| Effects ▶ | Particle System / Trail Renderer / Line Renderer / Visual Effect |
| Physics ▶ | Rigidbody / Character Controller / Box Collider / Sphere Collider / Capsule Collider / Mesh Collider / Wheel Collider / Terrain Collider / Joint（多种）/ Constant Force |
| Physics 2D ▶ | Rigidbody 2D / Collider 2D（多种）/ Joint 2D（多种）/ Effector 2D（多种） |
| Navigation ▶ | NavMesh Agent / NavMesh Obstacle / Off Mesh Link |
| Audio ▶ | Audio Listener / Audio Source / Audio Reverb Zone 等 |
| Rendering ▶ | Camera / Light（多种）/ Skybox / Lens Flare / Sprite Renderer / Sorting Group 等 |
| Layout ▶ | 布局相关组件 |
| Miscellaneous ▶ | Animation / Animator / Network View 等 |
| Event ▶ | Event System / Event Trigger / Standalone Input Module 等 |
| UI ▶ | Canvas / Canvas Scaler / Graphic Raycaster / Image / Text / Button / Raw Image 等 |
| Tilemap ▶ | Tilemap / Tilemap Renderer / Tilemap Collider 2D 等 |
| Scripts ▶ | 项目中自定义的脚本 |

---

## Window（窗口）菜单

| 菜单项 | 快捷键 | 说明 |
|--------|--------|------|
| Next Window | Ctrl+Tab | 下一个窗口 |
| Previous Window | Ctrl+Shift+Tab | 上一个窗口 |
| Layouts ▶ | — | 窗口布局管理（Default / 2 by 3 / 4 Split / Tall / Wide / Save Layout / Delete Layout / Revert Factory Settings） |
| Panels ▶ | — | 面板子菜单 |
| Services | — | Unity Services 面板 |
| General ▶ | — | 通用窗口子菜单 |
| Rendering ▶ | — | 渲染相关窗口（Lighting、Occlusion Culling、Frame Debugger 等） |
| Animation ▶ | — | Animation 窗口 + Animator 窗口 |
| Audio ▶ | — | Audio Mixer 窗口 |
| UI Toolkit ▶ | — | UI Toolkit 调试/开发工具 |
| TextMeshPro ▶ | — | TextMeshPro 相关窗口 |
| Analysis ▶ | — | Profiler 等分析工具 |
| Asset Management ▶ | — | 资源管理相关 |
| Package Manager | — | 包管理器 |

### General 子菜单
Scene / Game / Inspector / Hierarchy / Project / Console（Ctrl+Shift+C）

### Rendering 子菜单
Lighting / Occlusion Culling / Frame Debugger

### Animation 子菜单
Animation（Ctrl+6）/ Animator

### Audio 子菜单
Audio Mixer（Ctrl+8）

### Analysis 子菜单
Profiler（Ctrl+7）

---

## Help（帮助）菜单

| 菜单项 | 说明 |
|--------|------|
| About Unity... | 版本信息 |
| Manage License... | 管理许可证 |
| Unity Manual | 打开官方手册 |
| Scripting Reference | 打开脚本 API 文档 |
| Unity Forum | 官方论坛 |
| Unity Answers | 问答社区 |
| Unity Feedback | 提交反馈 |
| Check for Updates | 检查更新 |
| Release Notes | 更新日志 |
| Report a Bug... | 报告 Bug |
| Welcome Screen | 欢迎页 |
