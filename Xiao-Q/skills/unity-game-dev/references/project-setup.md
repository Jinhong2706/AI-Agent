# Unity 项目搭建指南

## 1. 安装 Unity

1. 下载 **Unity Hub**：https://unity.com/cn/download
2. 在 Unity Hub 中安装 Unity Editor（推荐 LTS 版本，如 2022.3 LTS 或 6000.x LTS）
3. 安装时勾选需要的平台模块：
   - **Windows Build Support** - 打包 Windows 游戏
   - **Android Build Support** - 打包 Android 应用（需 Android SDK/NDK）
   - **iOS Build Support** - 打包 iOS 应用（需要 Mac）
   - **WebGL Build Support** - 打包网页游戏

## 2. 创建新项目

1. 打开 Unity Hub → 点击"新建项目"
2. 选择模板：
   - **2D** - 平面游戏（横版、俯视角等）
   - **3D** - 立体游戏（第三人称、FPS 等）
   - **2D (URP)** / **3D (URP)** - 带通用渲染管线，画质更好
3. 填写项目名称和保存路径 → 创建

## 3. Unity 编辑器界面说明

```
+------------------+---------------------------+------------------+
|   Hierarchy      |       Scene View          |    Inspector     |
| (场景对象树)      |     (场景编辑视图)         |  (选中对象属性)  |
+------------------+---------------------------+------------------+
|   Project        |       Game View           |   Console        |
| (项目文件)        |     (游戏运行视图)         |  (日志/报错)     |
+------------------+---------------------------+------------------+
```

- **Hierarchy**: 当前场景所有 GameObject 的树形列表
- **Scene View**: 可拖拽、摆放游戏对象的编辑区域
- **Inspector**: 显示选中对象的所有组件和属性
- **Project**: 项目文件管理（脚本、图片、音频等）
- **Game View**: 点击播放按钮后模拟游戏运行效果
- **Console**: 显示 Debug.Log 输出和报错信息

## 4. 第一个场景搭建步骤

### 2D 游戏基础场景

1. **设置相机**
   - 选中 `Main Camera`
   - Inspector 中设置 `Projection` = `Orthographic`（正交投影）
   - 调整 `Size` 控制视野大小

2. **创建地面**
   - Hierarchy → 右键 → `2D Object > Sprite > Square`
   - 重命名为 "Ground"
   - 调整 Scale 拉长为地面形状（如 X=20, Y=1）
   - 添加组件：`Add Component` → `Rigidbody 2D` → 设置 `Body Type` = `Static`
   - 添加组件：`Add Component` → `Box Collider 2D`

3. **创建玩家**
   - Hierarchy → 右键 → `2D Object > Sprite > Square`
   - 重命名为 "Player"
   - 调整 Scale 为玩家大小（如 X=1, Y=1）
   - 添加组件：`Rigidbody 2D`（默认 Dynamic 即可）
   - 添加组件：`Box Collider 2D`
   - 创建脚本：Project 窗口右键 → `Create > C# Script`，命名为 `PlayerController`
   - 双击脚本用 VS Code 打开编写，写完后拖拽到 Player 对象上

4. **运行测试**
   - 点击编辑器顶部的 **Play** 按钮（三角形图标）
   - 在 Game View 中查看效果

## 5. 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `W` | 移动工具（Scene View 中移动对象） |
| `E` | 旋转工具 |
| `R` | 缩放工具 |
| `Ctrl+D` | 复制选中对象 |
| `Ctrl+Z` | 撤销 |
| `F` | 聚焦到选中对象 |
| `Ctrl+P` | 进入/退出播放模式 |
| `Ctrl+S` | 保存场景 |

## 6. 项目文件夹结构（推荐）

```
Assets/
├── Scenes/          # 场景文件 (.unity)
├── Scripts/         # C# 脚本
│   ├── Player/
│   ├── Enemy/
│   └── UI/
├── Sprites/         # 图片资源
├── Audio/           # 音频文件
├── Prefabs/         # 预制体
├── Animations/      # 动画
└── Materials/       # 材质
```

## 7. 打包发布

1. 菜单 `File > Build Settings`
2. 选择目标平台（PC、Android、WebGL 等）
3. 点击 `Add Open Scenes` 添加当前场景
4. 点击 `Build`（打包到指定文件夹）或 `Build and Run`（打包并运行）

### Android 打包前置步骤：
1. `Edit > Preferences > External Tools` 中配置 JDK/SDK/NDK 路径
2. 或使用 Unity Hub 安装时自带的 OpenJDK
3. `Player Settings > Other Settings` 中设置 `Package Name`（如 com.yourname.gamename）
