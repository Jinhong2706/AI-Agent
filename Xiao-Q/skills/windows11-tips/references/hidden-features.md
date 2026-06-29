# Windows 11 隐藏功能与秘密技巧

## 隐藏的系统工具

### 1. 上帝模式（God Mode）
访问所有控制面板设置在一个文件夹中：
```powershell
# 创建方法：
# 1. 新建文件夹
# 2. 重命名为：GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}
```
包含数百个系统设置选项，一站式管理！

### 2. 隐藏的壁纸文件夹
Windows 11 原装壁纸位置：
```
C:\Windows\Web\Wallpaper\    # 系统壁纸
C:\Windows\Web\4K\Wallpaper\Windows\  # 4K壁纸
```

### 3. 新的表情符号面板
- 快捷键：`Win + .` 或 `Win + ;`
- 包含：表情符号、符号、颜文字（¯\_(ツ)_/¯）
- 可搜索："开心"、"动物"等

### 4. 剪贴板历史
- 开启：`Win + V` 后点击"启用"
- 功能：保存最近复制的 25 项内容
- 同步：登录微软账号可跨设备同步

## 注册表隐藏技巧

### 1. 恢复经典右键菜单
```reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32]
@=""
```
使用后在任务管理器中重启"Windows 资源管理器"

### 2. 增加任务栏透明效果
```reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize]
"EnableTranslucentEffect"=dword:00000001
```

### 3. 禁用开始菜单推荐项目
```reg
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced]
"Start_IrisRecommendations"=dword:00000000
```

### 4. 加速任务栏缩略图显示
```reg
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced]
"ExtendedUIHoverTime"=dword:00000100
```
数值单位为毫秒，默认 400

## 实验性功能（Vivetool）

### 安装 ViVeTool
```powershell
winget install ViVeTool
```

### 启用隐藏功能
```powershell
# 查看功能列表
vivetool /query

# 启用特定功能（需要功能ID）
vivetool /enable /id:xxxxxxxx

# 禁用功能
vivetool /disable /id:xxxxxxxx
```

### 热门可启用功能
- **任务栏标签**：显示打开窗口的标签
- **新版文件资源管理器**：新设计的文件管理器
- **Mica 效果增强**：更漂亮的窗口效果
- **新版开始菜单**：实验性的开始菜单布局

## 不为人知的小技巧

### 1. 动态刷新率
设置 → 系统 → 屏幕 → 高级显示 → 显示器刷新率
- 选择"动态"模式，根据内容自动调整刷新率以省电

### 2. 专注助手自动规则
设置 → 系统 → 专注助手
- 可设置在全屏使用应用时、玩游戏时自动开启
- 可设置优先级列表，仅允许特定联系人通知

### 3. 存储感知自动清理
设置 → 系统 → 存储 → 存储感知
- 自动删除临时文件
- 自动清空回收站（1天/14天/30天/60天）
- 自动将文件移至 OneDrive（未访问超过X天）

### 4. 应用音量单独控制
设置 → 系统 → 声音 → 音量混合器
- 可单独调整每个应用的音量
- 可单独设置默认输出设备

### 5. 鼠标指针轨迹加速
设置 → 蓝牙和其他设备 → 鼠标 → 其他鼠标选项
→ 指针选项 → 显示指针轨迹
- 可调整轨迹长度，提升定位精度

## 隐藏的命令行工具

### 1. 系统文件检查器
```cmd
sfc /scannow
```
扫描并修复系统文件

### 2. 磁盘检查与修复
```cmd
chkdsk C: /f /r
```
检查磁盘错误并恢复可读信息

### 3. 系统映像修复
```cmd
DISM /Online /Cleanup-Image /RestoreHealth
```
修复 Windows 映像

### 4. 网络重置
```cmd
netsh winsock reset
```
重置网络适配器设置

### 5. 电源计划管理
```cmd
# 查看所有电源计划
powercfg /list

# 激活高性能模式
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
```

## 文件资源管理器隐藏技巧

### 1. 隐藏的文件扩展名
查看 → 显示 → 文件扩展名
- 显示完整文件名，避免伪装病毒文件

### 2. 快速访问工具栏
- 将常用功能（删除、属性、撤销）添加到工具栏
- 可用 `Alt + 数字键` 快速调用

### 3. 标签页功能
- `Ctrl + T` 新建标签页
- `Ctrl + W` 关闭标签页
- 拖拽标签页可创建新窗口

### 4. 压缩文件右键菜单
- 右键文件 → 显示更多选项 → 发送到 → 压缩(zipped)文件夹
- 或使用 7-Zip、WinRAR 等第三方工具

## 启动与关机技巧

### 1. 快速启动（进阶）
```powershell
# 禁用快速启动（解决某些关机问题）
powercfg /h off
```

### 2. 创建自定义重启快捷方式
```cmd
shutdown /r /t 0
```

### 3. 休眠快捷键
```cmd
rundll32.exe powrprof.dll,SetSuspendState 0,1,0
```
创建快捷方式并设快捷键

## 开发者隐藏功能

### 1. Windows Terminal 配色方案
设置 → 配色方案 → 可导入自定义方案
- 推荐网站：windowsterminalthemes.dev

### 2. WSL 图形界面
```bash
# 在 WSL2 中运行图形应用
export DISPLAY=:0
# 需要安装 X Server（如 VcXsrv）
```

### 3. 虚拟内存优化
设置 → 系统 → 关于 → 高级系统设置
→ 性能设置 → 高级 → 虚拟内存
- 可手动设置页面文件大小，提升性能

## 隐藏的游戏功能

### 1. Xbox Game Bar 小组件
`Win + G` 打开后：
- 性能监控（CPU/GPU/RAM）
- 音频控制
- 窗口固定（游戏模式）

### 2. 游戏模式
设置 → 游戏 → 游戏模式
- 优化系统资源分配给游戏
- 禁用后台应用更新

### 3. HDR 游戏优化
设置 → 系统 → 屏幕 → HDR
- 自动 HDR（将 SDR 游戏转为 HDR）
- 可变刷新率（减少画面撕裂）

## 安全隐藏功能

### 1. BitLocker 设备加密
设置 → 隐私和安全性 → 设备加密
- 自动加密设备（需硬件支持）
- 保护数据不被未授权访问

### 2. Windows Hello 增强
- 动态锁：离开电脑自动锁定
- 需要蓝牙连接手机，离开范围自动锁屏

### 3. 应用和浏览器控制
Windows 安全中心 → 应用和浏览器控制
- 检查应用和文件
- SmartScreen 筛选器
- 隔离模式（防止 ransomware）

## 提示

⚠️ **修改注册表前务必备份！**
```cmd
reg export "HKCU\Software" C:\backup\software_backup.reg
```

🔍 **想发现更多隐藏功能？**
- 使用 `Win + R` 运行 `shell:appsfolder` 查看所有应用
- 探索 `C:\Users\你的用户名\AppData\` 下的隐藏文件夹
- 关注 Windows 11 更新日志，新功能持续加入！
