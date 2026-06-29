# Windows 11 系统优化与性能提升

## 启动项管理

### 1. 使用任务管理器禁用启动项
`Ctrl + Shift + Esc` → 启动应用
- 禁用不需要的开机启动程序
- 启动影响：高/中/低
- 右键程序 → 禁用

### 2. 使用设置应用管理
设置 → 应用 → 启动
- 开关控制启动状态
- 显示启动影响评估
- 更直观的管理界面

### 3. 使用 System Internals Autoruns（高级）
```powershell
# 下载并运行（微软官方工具）
# https://docs.microsoft.com/en-us/sysinternals/downloads/autoruns
```
- 管理所有启动项目（注册表、服务、计划任务等）
- 微软官方免费工具

## 系统服务优化

### 1. 安全禁用不必要的服务
`Win + R` → `services.msc`
- **Connected User Experiences and Telemetry**：遥测服务（可禁用）
- **SysMain（原SuperFetch）**：预加载程序（SSD上可禁用）
- **Windows Search**：索引服务（禁用会影响搜索速度）
- **Print Spooler**：打印服务（不打印可禁用）
- **Xbox Accessory Management**：Xbox 配件服务（无 Xbox 可禁用）

### 2. 服务启动类型建议
- **自动（延迟启动）**：非关键驱动服务
- **手动**：按需启动的服务
- **禁用**：确认不用的服务

⚠️ **警告**：不确定用途的服务不要禁用！

## 存储空间清理

### 1. 存储感知自动清理
设置 → 系统 → 存储 → 存储感知
- 自动删除临时文件
- 自动清空回收站（1/14/30/60天）
- 自动删除已同步到云的内容

### 2. 手动清理方法
```powershell
# 清理临时文件
cleanmgr

# 或使用命令
cleanmgr /d C:
```
选择要删除的内容：
- Windows 更新清理
- 临时 Windows 安装文件
- 系统错误内存转储文件
- 已下载的程序文件

### 3. 大文件查找
设置 → 系统 → 存储 → 显示更多类别
- 应用和游戏
- 文档、图片、视频、音乐
- 邮件、地图、OneDrive

### 4. 卸载预装应用
```powershell
# 卸载 Xbox 应用
Get-AppxPackage *xbox* | Remove-AppxPackage

# 卸载邮件和日历
Get-AppxPackage *windowscommunicationsapps* | Remove-AppxPackage

# 卸载人脉
Get-AppxPackage *people* | Remove-AppxPackage
```

## 游戏性能优化

### 1. 开启游戏模式
设置 → 游戏 → 游戏模式
- 优化系统资源分配给游戏
- 暂停后台 Windows 更新
- 提升游戏帧率和稳定性

### 2. GPU 性能偏好
设置 → 系统 → 显示 → 图形
- 为具体应用设置 GPU 偏好
- 选择节能（集成显卡）或高性能（独立显卡）
- 对游戏和创作应用特别有效

### 3. 禁用 Xbox Game Bar（可选）
设置 → 游戏 → Xbox Game Bar
- 如果不需要录屏和截图，可关闭
- 释放系统资源

### 4. 关闭硬件加速 GPU 计划
设置 → 系统 → 显示 → 图形 → 更改默认图形设置
- 开启/关闭硬件加速 GPU 计划
- 部分老显卡开启后可能更稳定

### 5. 游戏DVR优化
```reg
[HKEY_CURRENT_USER\System\GameConfigStore]
"GameDVR_Enabled"=dword:00000000
"GameDVR_FSEBehavior"=dword:00000002
```

## 内存优化

### 1. 虚拟内存设置
设置 → 系统 → 关于 → 高级系统设置
→ 性能设置 → 高级 → 虚拟内存
- 推荐：自动管理所有驱动器的分页文件大小
- 或手动设置：初始大小 = RAM 的 1.5 倍，最大值 = RAM 的 3 倍

### 2. 内存压缩（默认开启）
Windows 11 自动压缩不活跃内存页面
- 可在任务管理器 → 性能 → 内存中查看
- 通常不需要手动调整

### 3. 禁用不需要的内核
```msconfig
# Win + R → msconfig → 引导 → 高级选项
# 取消勾选"处理器数"和"最大内存"
```

## 硬盘优化（SSD/HDD）

### 1. SSD 优化设置
- **开启 TRIM**：默认已开启
```powershell
# 检查 TRIM 状态
fsutil behavior query disabledeletenotify
# 0 = TRIM 已启用
```

- **禁用磁盘碎片整理**：SSD 不需要，Windows 会自动禁用
- **禁用 SuperFetch/SysMain**：SSD 上可禁用，提升响应速度

### 2. HDD 优化
设置 → 系统 → 存储 → 高级存储设置
→ 驱动器优化
- 定期碎片整理（每周一次）
- 自动优化已启用

### 3. 禁用系统还原（可选）
设置 → 系统 → 关于 → 系统保护
- 可节省磁盘空间
- 但会失去系统还原点功能

## 网络优化

### 1. 关闭传递优化
设置 → Windows 更新 → 高级选项 → 传递优化
- 关闭"允许从其他电脑下载"
- 节省带宽，提升更新速度

### 2. DNS 优化
设置 → 网络和 Internet → 以太网/WiFi
→ 硬件属性 → DNS 服务器分配 → 编辑
- 推荐 DNS：
  - Google: 8.8.8.8, 8.8.4.4
  - Cloudflare: 1.1.1.1, 1.0.0.1
  - 阿里: 223.5.5.5, 223.6.6.6

### 3. 关闭后台应用
设置 → 隐私和安全性 → 后台应用
- 关闭不需要的后台应用
- 节省网络和电池资源

## 电源计划优化

### 1. 选择高性能计划
设置 → 系统 → 电源和电池
- 电源模式：最佳性能
- 屏幕和睡眠：根据需要调整

### 2. 高级电源设置
`Win + R` → `powercfg.cpl`
→ 更改计划设置 → 更改高级电源设置
- 处理器电源管理：最小/最大状态 5%/100%
- 硬盘：关闭硬盘时间 → 20 分钟
- USB 设置：禁用选择性暂停

### 3. 终极性能计划（隐藏）
```powershell
# 启用终极性能计划
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
```

## 视觉效果优化

### 1. 性能选项设置
设置 → 系统 → 关于 → 高级系统设置
→ 性能设置
- **最佳性能**：关闭所有效果（老旧电脑）
- **自定义**：选择性关闭
  - 关闭：动画控件和元素、淡入淡出等
  - 保留：平滑屏幕字体边缘、缩略图

### 2. 关闭透明效果
设置 → 个性化 → 颜色 → 透明效果
- 关闭后界面更流畅（低端显卡）

## 注册表优化

### 1. 加速开始菜单
```reg
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced]
"Start_ShowClassicList"=dword:00000001
```

### 2. 关闭动画效果
```reg
[HKEY_CURRENT_USER\Control Panel\Desktop]
"UserPreferencesMask"=hex:90,12,01,80,10,00,00,00
```

### 3. 加速任务栏缩略图
```reg
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced]
"ExtendedUIHoverTime"=dword:00000100
```

## 命令快速优化

### 一键优化脚本
```powershell
# 清理系统垃圾
cleanmgr /d C:

# 系统文件检查
sfc /scannow

# 磁盘检查
chkdsk C: /f

# 更新清理
Dism.exe /Online /Cleanup-Image /StartComponentCleanup

# 关闭休眠（节省空间，等于 RAM 大小）
powercfg -h off
```

## 监控与维护

### 1. 任务管理器监控
`Ctrl + Shift + Esc`
- 进程：查看 CPU/内存/磁盘/网络占用
- 性能：实时图表监控
- 启动：管理启动项
- 用户：查看登录用户

### 2. 资源监视器（高级）
`Win + R` → `resmon`
- 更详细的资源监控
- CPU/内存/磁盘/网络深度分析

### 3. 可靠性监视器
`Win + R` → `perfmon /rel`
- 查看系统稳定性历史
- 故障和错误报告

### 4. 事件查看器
`Win + R` → `eventvwr.msc`
- 查看系统和应用日志
- 诊断系统问题

## 提示

⚡ **优化原则：**
- 不要同时应用所有优化
- 一次优化一项，观察效果
- 备份注册表前再进行修改

🔧 **适用场景：**
- 新电脑：适度优化，保持原样
- 老电脑：重点优化视觉和启动项
- 游戏电脑：重点优化 GPU 和电源
- 办公电脑：重点优化启动和后台

📊 **性能基准测试：**
优化前后使用工具测试：
- **CrystalDiskMark**：硬盘速度
- **CPU-Z**：CPU 性能
- **3DMark**：游戏性能
- **PCMark**：综合性能
