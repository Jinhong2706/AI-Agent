# Windows 11 内置工具与实用应用

## PowerToys 工具集

### 安装 PowerToys
```powershell
winget install Microsoft.PowerToys
```

### 核心工具

#### 1. FancyZones（窗口布局管理器）
- 自定义窗口布局区域
- 快速将窗口吸附到预设区域
- 支持多显示器布局
- 快捷键：`Win + ~` 快速启动

#### 2. PowerRename（批量重命名）
- 支持正则表达式
- 实时预览重命名结果
- 批量替换、删除、插入文本
- 使用方法：选中文件 → 右键 → PowerRename

#### 3. File Explorer Preview Pane（文件预览增强）
- 预览 Markdown、SVG、PDF 等
- 支持更多文件格式
- 在文件资源管理器中开启预览窗格使用

#### 4. Keyboard Manager（键盘重映射）
- 重映射单个键
- 创建自定义快捷键
- 导入/导出配置
- 应用级快捷键（仅在特定应用中生效）

#### 5. Color Picker（取色器）
- 快捷键：`Win + Shift + C`
- 从屏幕任何位置取色
- 支持多种格式（HEX、RGB、HSL等）
- 颜色历史记录

#### 6. Image Resizer（图片批量调整）
- 右键菜单快速调整图片大小
- 预设尺寸：小/中/大/手机/自定义
- 批量处理多张图片
- 保持纵横比或自定义裁剪

#### 7. Mouse Utilities（鼠标工具）
- 查找我的鼠标：抖动鼠标高亮指针
- 鼠标跳跃：快速移动到另一显示器
- 鼠标荧光笔：点击时显示视觉反馈

#### 8. Awake（系统保持唤醒）
- 临时或永久保持系统唤醒
- 防止屏幕关闭和睡眠
- 系统托盘控制

## 系统自带实用工具

### 1. 截图工具（Snipping Tool）
`Win + Shift + S` 快速启动
- 矩形截图
- 自由形状截图
- 窗口截图
- 全屏截图
- 支持延时截图（3秒/5秒/10秒）
- 截图后可直接标注、保存或分享

### 2. 记事本（Notepad）
全新 Windows 11 风格：
- Tab 多标签页支持
- 自动保存会话
- 深色模式支持
- 更现代的界面

### 3. 画图（Paint）
- 基础绘图工具
- 支持图层（Paint 3D 已弃用）
- 简单图像编辑
- 支持触控笔输入

### 4. 计算器（Calculator）
`Win + R` → `calc`
- 标准模式
- 科学模式
- 程序员模式（进制转换）
- 日期计算
- 货币转换
- 单位转换

### 5. 录音机（Voice Recorder）
- 简单录音
- 标记重要片段
- 音频修剪
- 导出为 MP3

### 6. 步骤记录器（PSR）
`psr` 命令启动
- 自动记录操作步骤
- 生成 HTML 报告
- 适合制作教程和故障排除
- 可添加注释和截图

## 系统管理工具

### 1. 任务管理器（Task Manager）
`Ctrl + Shift + Esc`
- 进程管理：结束任务、设置优先级
- 性能监控：CPU、内存、磁盘、网络、GPU
- 启动管理：禁用/启用启动项
- 用户管理：查看登录用户
- 服务管理：启动/停止系统服务

### 2. 资源监视器（Resource Monitor）
`Win + R` → `resmon`
- 更详细的资源使用分析
- CPU：进程、服务、关联句柄
- 内存：进程占用详情
- 磁盘：读写活动、存储活动
- 网络：网络连接、监听端口

### 3. 事件查看器（Event Viewer）
`Win + R` → `eventvwr.msc`
- 查看系统日志
- 应用程序错误诊断
- 安全审计
- 自定义视图筛选

### 4. 性能监视器（Performance Monitor）
`Win + R` → `perfmon`
- 实时性能数据
- 自定义数据收集器
- 生成性能报告
- 设置性能警报

### 5. 系统配置（MSConfig）
`Win + R` → `msconfig`
- 启动选项（安全模式、调试模式）
- 服务管理（隐藏 Microsoft 服务）
- 启动项管理
- 工具快捷方式

## 命令行工具

### 1. Windows Terminal
`Win + X` → 选择 Terminal
- 多标签页支持
- 多配置文件（PowerShell、CMD、WSL）
- 自定义配色方案和背景
- 支持亚克力效果
- 自定义字体和字号

### 2. PowerShell
- 更强大的命令行工具
- 面向对象管道
- 远程管理功能
- 与 .NET 集成
- 常用命令：
  ```powershell
  Get-Help          # 查看帮助
  Get-Command       # 列出所有命令
  Get-Process       # 查看进程
  Stop-Process      # 结束进程
  Get-Service       # 查看服务
  Start-Service     # 启动服务
  ```

### 3. 命令提示符（CMD）
传统命令行工具：
- `ipconfig` - 查看网络配置
- `ping` - 测试网络连通性
- `tracert` - 追踪路由
- `netstat` - 查看网络连接
- `systeminfo` - 查看系统信息
- `driverquery` - 查看驱动程序列表

### 4. Windows Package Manager (Winget)
```powershell
# 搜索应用
winget search <应用名>

# 安装应用
winget install <应用ID>

# 升级应用
winget upgrade <应用ID>
winget upgrade --all

# 卸载应用
winget uninstall <应用ID>

# 列出已安装应用
winget list
```

热门应用 ID：
- `Microsoft.Edge` - Microsoft Edge
- `7zip.7zip` - 7-Zip
- `VideoLAN.VLC` - VLC 播放器
- `Notepad++.Notepad++` - Notepad++
- `Microsoft.VisualStudioCode` - VS Code

## 开发者工具

### 1. WSL（Windows Subsystem for Linux）
```powershell
# 安装 WSL
wsl --install

# 查看可用发行版
wsl --list --online

# 安装特定发行版
wsl --install -d Ubuntu

# 设置默认版本为 WSL2
wsl --set-default-version 2
```

### 2. Hyper-V（虚拟机）
`Win + R` → `optionalfeatures`
- 启用 Hyper-V 功能
- 创建和管理虚拟机
- 适合测试不同系统环境

### 3. 远程桌面（Remote Desktop）
设置 → 系统 → 远程桌面
- 启用远程连接
- 设置允许的用户
- 使用 Microsoft Remote Desktop 客户端连接

### 4. Windows Subsystem for Android
- 运行 Android 应用
- 需要安装 Amazon Appstore 或侧载 APK
- 适合测试移动应用

## 网络工具

### 1. 网络诊断
设置 → 系统 → 疑难解答 → 其他疑难解答
- Internet 连接
- 传入连接
- 网络适配器
- 共享文件夹

### 2. IP 配置工具
```cmd
# 查看 IP 配置
ipconfig /all

# 释放 IP 地址
ipconfig /release

# 更新 IP 地址
ipconfig /renew

# 刷新 DNS 缓存
ipconfig /flushdns
```

### 3. 网络映射
```cmd
# 显示网络路径
tracert www.google.com

# 持续 ping
ping -t www.google.com

# 查看 ARP 表
arp -a
```

## 辅助功能工具

### 1. 放大镜（Magnifier）
`Win + +` 启动
- 全屏放大
- 镜头模式
- 停靠模式
- 快捷键：`Win + Esc` 关闭

### 2. 讲述人（Narrator）
`Win + Ctrl + Enter` 启动
- 屏幕阅读器
- 导航和阅读文本
- 支持触摸和键盘

### 3. 屏幕键盘（On-Screen Keyboard）
`Win + R` → `osk`
- 虚拟键盘
- 支持鼠标或触控操作
- 可固定到任务栏

### 4. 高对比度模式
`Left Alt + Left Shift + Print Screen` 切换
- 高对比度主题
- 提升可读性
- 可自定义颜色方案

## 系统信息工具

### 1. 系统信息（System Information）
`Win + R` → `msinfo32`
- 查看硬件资源
- 组件信息
- 软件环境
- 导出系统报告

### 2. DirectX 诊断工具（DXDiag）
`Win + R` → `dxdiag`
- DirectX 版本信息
- 显示设备信息
- 声音设备信息
- 输入设备信息

### 3. 可靠性和性能监视器
`perfmon /rel`
- 系统稳定性图表
- 关键事件时间线
- 可靠性详细信息

## 提示

🛠️ **快速访问工具：**
- `Win + R` 打开运行对话框
- 输入工具名称（如 `calc`、`notepad`）
- 快速启动任意系统工具

📦 **安装更多工具：**
- Microsoft Store：官方应用商店
- Winget：命令行包管理器
- Chocolatey：第三方包管理器（需安装）

🔧 **建议保留的工具：**
- 任务管理器（必备）
- 截图工具（必备）
- 计算器（必备）
- PowerToys（推荐安装）
- Windows Terminal（推荐）
