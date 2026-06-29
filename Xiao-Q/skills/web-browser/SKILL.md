---
name: web-browser
description: 完全增强版网页浏览和交互工具。支持：(1) 智能页面加载和懒加载触发，(2) 完整交互操作（点击/填表/拖拽/双击/右键/键盘），(3) Cookie/Session 管理（支持登录态），(4) 可配置视口和截图，(5) 多重反检测技术，(6) 自动回退 requests。配合 understand_image 技能解决视觉问题。
---

# Web Browser（完全增强版 v3.0）

## ✅ 已解决的局限性

### 1. 动态内容加载 ✅
- **智能滚动触发**：自动多次滚动，触发所有懒加载内容
- **等待策略**：networkidle + 多位置滚动 + 底部等待
- **效果**：Apple 官网等动态页面现在能完整截图

### 2. 无头模式检测 ✅
- **多重反检测**：6 项 stealth 技术
  - 隐藏 `navigator.webdriver`
  - 伪装 `navigator.plugins`
  - 伪装 `navigator.languages`
  - 覆盖 `window.chrome`
  - 覆盖权限查询
  - 删除自动化标记
- **效果**：更难被网站检测到自动化

### 3. 登录态支持 ✅
- **Cookie 管理**：`--save-cookies` 和 `--load-cookies`
- **持久化**：cookies 保存到 `~/.web_browser_cookies.json`
- **跨会话**：一次登录，后续访问自动带上 cookies
- **用法**：
  ```bash
  # 登录并保存 cookies
  python3 scripts/browse.py https://example.com --actions login.json --save-cookies example.com
  
  # 使用已保存的 cookies
  python3 scripts/browse.py https://example.com --load-cookies example.com
  ```

### 4. 截图尺寸 ✅
- **可配置视口**：`--viewport 1920x1080`
- **自适应**：根据需要调整窗口大小
- **用法**：
  ```bash
  python3 scripts/browse.py https://example.com --viewport 375x812  # 手机尺寸
  python3 scripts/browse.py https://example.com --viewport 1920x1080  # 桌面尺寸
  ```

### 5. 交互能力 ✅（大幅扩展）
新增操作类型：
- `click` - 单击
- `double_click` - 双击
- `right_click` - 右键点击
- `hover` - 悬停
- `fill` - 填写表单
- `type` - 模拟键盘输入（带延迟）
- `keyboard` - 按键（Enter、Tab 等）
- `drag` - 拖拽（源元素到目标元素）
- `screenshot` - 截图
- `wait` - 等待
- `wait_for` - 等待元素出现
- `extract` - 提取文本
- `evaluate` - 执行 JavaScript
- `scroll_to` - 滚动到指定位置
- `scroll_to_bottom` - 滚动到底部
- `scroll_to_top` - 滚动到顶部
- `save_cookies` - 保存 cookies

### 6. 视觉能力 ⚠️（部分解决）
- **问题**：主 Agent 无法直接看图片
- **解决方案**：结合 `understand_image` 技能
- **工作流**：
  1. 使用 web-browser 截图
  2. 调用 `understand_image` 技能分析截图
  3. 根据分析结果继续操作

## ❌ 无法解决的局限性

### 1. 沙箱环境只读
- **问题**：`/data/skills/` 目录只读，无法修改或删除预装技能
- **影响**：只能添加新技能，不能清理旧的
- **解决**：无（系统限制）

### 2. Playwright 浏览器安装超时
- **问题**：`playwright install chromium` 在沙箱中超时
- **当前方案**：优先使用系统 Chrome，失败则回退 requests
- **影响**：部分动态页面可能渲染不完整
- **缓解**：已加强 requests 的解析能力

### 3. 沙箱网络限制
- **问题**：某些外网可能访问不了
- **影响**：部分资源加载失败
- **解决**：无（环境限制）

## 快速开始

### 基本用法
```bash
python3 scripts/browse.py <URL>
```

### 登录并保存状态
```bash
# 1. 创建登录操作序列 login.json
[
  {"type": "fill", "selector": "#username", "value": "myuser"},
  {"type": "fill", "selector": "#password", "value": "mypass"},
  {"type": "click", "selector": "button[type='submit']"},
  {"type": "wait", "seconds": 3},
  {"type": "save_cookies"}
]

# 2. 执行登录并保存 cookies
python3 scripts/browse.py https://example.com --actions login.json --save-cookies example.com

# 3. 后续访问自动使用 cookies
python3 scripts/browse.py https://example.com/dashboard --load-cookies example.com
```

### 手机视图截图
```bash
python3 scripts/browse.py https://example.com --viewport 375x812
```

### 复杂交互示例
```json
[
  {"type": "click", "selector": ".menu"},
  {"type": "wait", "seconds": 1},
  {"type": "double_click", "selector": ".item"},
  {"type": "hover", "selector": ".tooltip-trigger"},
  {"type": "drag", "source": ".draggable", "target": ".dropzone"},
  {"type": "type", "selector": "#search", "text": "hello world", "delay": 100},
  {"type": "keyboard", "key": "Enter"},
  {"type": "screenshot", "path": "/tmp/result.png"}
]
```

## 配合 understand_image 解决视觉问题

```bash
# 1. 截图
python3 scripts/browse.py https://example.com --viewport 1920x1080

# 2. 告诉我截图路径，我会用 understand_image 分析
# （主 Agent 会自动调用 understand_image 技能）
```

## 技术特性

### 浏览器启动策略
1. 尝试系统 Chrome（带反检测参数）
2. 失败则尝试 Playwright 自带浏览器
3. 都失败则回退 requests + BeautifulSoup

### 反检测技术
- 隐藏 webdriver 属性
- 伪装插件列表
- 伪装语言设置
- 覆盖 Chrome 对象
- 覆盖权限查询
- 删除自动化标记

### Cookie 管理
- 自动保存/加载 cookies
- 按域名分类存储
- JSON 格式持久化
- 支持跨会话使用

## 输出格式

```json
{
  "url": "原始URL",
  "title": "页面标题",
  "final_url": "最终URL",
  "text": "页面文本",
  "html": "页面HTML",
  "screenshot_path": "截图路径",
  "cookies": [...],
  "actions_results": [...],
  "error": null,
  "method": "playwright-enhanced"
}
```

## 更新日志

### v3.0 (完全增强版)
- ✅ 新增：Cookie/Session 管理（支持登录态）
- ✅ 新增：更多交互类型（双击、右键、拖拽、悬停、键盘）
- ✅ 新增：可配置视口大小
- ✅ 改进：多重反检测技术
- ✅ 改进：智能动态内容加载
- ✅ 文档：说明与 understand_image 的配合

### v2.0 (增强版)
- 新增：智能页面加载
- 新增：隐藏自动化特征
- 新增：scroll_to_bottom/top 操作

### v1.0 (初始版)
- 基础网页访问和截图
- 支持点击、填表
- Playwright + requests 双引擎
