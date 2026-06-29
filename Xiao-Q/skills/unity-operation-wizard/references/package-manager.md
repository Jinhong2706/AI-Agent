# Package Manager

**打开方式：** `Window > Package Manager`

管理项目依赖的 Unity 包（Package）。Unity 功能以包形式分发，可按需安装。

---

## 窗口布局

| 区域 | 说明 |
|------|------|
| **左侧包列表** | 按来源分组的已安装/可用包 |
| **右侧详情面板** | 选中包的版本信息、文档链接、依赖项、示例等 |

---

## 包来源（左上角下拉）

| 来源 | 说明 |
|------|------|
| **Unity Registry** | Unity 官方注册表——官方和验证的包 |
| **My Registries** | 自定义注册表（Scoped Registry，在 Project Settings 中配置） |
| **In Project** | 当前项目已安装的包 |
| **Built-in** | 内置包（不可移除，如 Unity UI） |
| **By Name** | 按名称安装（Git URL、本地路径等） |

---

## 包操作

### 安装
1. 选择来源（如 Unity Registry）
2. 找到需要的包
3. 点击 **Install** 按钮

### 更新
1. 切换到 **In Project** 视图
2. 有可用更新的包显示箭头图标
3. 点击包 → 在详情面板选择新版本 → **Update to [version]**

### 移除
1. 切换到 **In Project** 视图
2. 选中包
3. 点击 **Remove** 按钮

### 安装特定版本
1. 选中包
2. 点击版本号下拉菜单
3. 选择需要安装的版本号（semver 格式：major.minor.patch）

---

## 从其他来源安装

| 来源 | 格式/方法 |
|------|----------|
| Git URL | `https://github.com/user/repo.git` 或 `git@github.com:user/repo.git` |
| Git + 版本 | `https://github.com/user/repo.git#v1.0.0` |
| 本地文件夹 | `file:/绝对路径/或/相对路径` |
| 本地 tarball | `file:/path/to/package.tgz` |
| 按名称 | 直接输入包名如 `com.unity.textmeshpro` |

通过按名称安装：点击 **+** 按钮 → 选择 **Add package by name...** → 输入名称/URL

---

## 关键概念

| 概念 | 说明 |
|------|------|
| **manifest.json** | 项目 `Packages/manifest.json`，记录所有包依赖 |
| **package.json** | 每个包内部的元数据和依赖声明 |
| **Semantic Versioning** | 版本号格式：`主版本.次版本.补丁版本` |
| **Immutable 包** | Registry/Git/Built-in 包不可编辑 |
| **Embedded 包** | 放在 `Packages/` 文件夹内，可编辑 |
| **Local 包** | 通过 `file:` 引用的本地文件夹，可编辑 |

---

## 常用官方包速查

| 包名 | 功能 |
|------|------|
| com.unity.textmeshpro | TextMeshPro——高质量文字渲染 |
| com.unity.inputsystem | 新版输入系统 |
| com.unity.ai.navigation | 导航系统（2022.3+） |
| com.unity.timeline | Timeline 时间线 |
| com.unity.2d.sprite | 2D Sprite |
| com.unity.ugui | Unity UI 系统 |
| com.unity.render-pipelines.universal | URP 通用渲染管线 |
| com.unity.render-pipelines.high-definition | HDRP 高清渲染管线 |
| com.unity.cinemachine | Cinemachine 虚拟摄像机 |
| com.unity.postprocessing | 后处理特效栈 |
| com.unity.probuilder | ProBuilder 关卡编辑 |
| com.unity.addressables | Addressables 资源管理 |
| com.unity.visualeffectgraph | VFX Graph |
| com.unity.shadergraph | Shader Graph |
