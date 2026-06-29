# LinkedIn CSS 选择器参考

本文档记录 LinkedIn 页面关键元素的 CSS 选择器，用于浏览器自动化数据采集。

---

## 一、个人主页选择器

### 1.1 基本信息

```css
/* 姓名 */
.pv-text-details__left-panel .text-heading-xlarge

/* 头衔/简介 */
.pv-text-details__left-panel .text-body-medium

/* 当前位置 */
.pv-text-details__left-panel span:first-child

/* 公司链接 */
.pv-text-details__left-panel a[href*="/company/"]

/* 地区 */
.pv-text-details__left-panel [aria-label*="location"]

/* 人脉数量 */
.pv-text-details__left-panel [aria-label*="connections"]
```

### 1.2 工作经历

```css
/* 工作经历列表 */
.pv-profile-section:nth-child(5) .pv-entity__position-group

/* 单个职位 */
.pv-entity__position-group-role-item

/* 职位名称 */
.pv-entity__summary-info h3

/* 公司名 */
.pv-entity__secondary-title

/* 任职时间 */
.pv-entity__date-range span:nth-child(2)

/* 职位描述 */
.pv-entity__description
```

### 1.3 教育背景

```css
/* 教育经历列表 */
.pv-profile-section:nth-child(6) .pv-entity__position-group

/* 学校名称 */
.pv-entity__school-name

/* 学位 */
.pv-entity__description
```

---

## 二、动态页面选择器

### 2.1 动态列表

```css
/* 动态容器 */
div[aria-label*="activity"]

/* 单个动态 */
.update-components-actor

/* 动态内容 */
.update-components-text

/* 动态时间 */
.update-components-actor time

/* 动态类型图标 */
.update-components-actor img
```

### 2.2 动态详情

```css
/* 点赞数 */
.social-counts__votes

/* 评论数 */
button[aria-label*="comment"]

/* 分享数 */
button[aria-label*="repost"]

/* 评论列表 */
.comments-comment-item

/* 单条评论 */
.comments-comment-item__content
```

---

## 三、公司页面选择器

### 3.1 公司信息

```css
/* 公司名 */
.org-top-card__primary-content h1

/* 行业 */
.org-top-card__secondary-details dd:nth-child(2)

/* 公司规模 */
.org-top-card__secondary-details dd:nth-child(4)

/* 总部位置 */
.org-top-card__secondary-details dd:nth-child(6)

/* 公司简介 */
.org-top-card__about-about .break-words
```

### 3.2 公司动态

```css
/* 动态列表 */
.org-module--updates

/* 单个动态 */
.feed-shared-update-v2

/* 动态内容 */
.update-components-text

/* 发布时间 */
.update-components-actor__sub-description
```

---

## 四、搜索结果选择器

### 4.1 人员搜索

```css
/* 搜索结果列表 */
.search-results-container

/* 单个结果 */
.search-result

/* 姓名 */
.search-result__title-link

/* 职位 */
.search-result__sub-title

/* 公司 */
.search-result__sub-description
```

### 4.2 公司搜索

```css
/* 公司结果 */
.search-result--company

/* 公司名 */
.search-result__result-link

/* 行业/规模 */
.search-result__description
```

---

## 五、消息页面选择器

### 5.1 消息列表

```css
/* 消息容器 */
.msg-conversations-container

/* 单个会话 */
.msg-conversation-card

/* 联系人姓名 */
.msg-conversation-card__actor-name

/* 最后一条消息 */
.msg-conversation-card__message-text
```

### 5.2 消息发送

```css
/* 消息输入框 */
.msg-form__input

/* 发送按钮 */
.msg-form__send-button
```

---

## 六、登录页面选择器

### 6.1 登录表单

```css
/* 邮箱输入 */
#username

/* 密码输入 */
#password

/* 登录按钮 */
button[type="submit"]

/* 错误提示 */
.alert[role="alert"]

/* 验证码输入 */
#challenge-field
```

---

## 七、注意事项

### 7.1 选择器稳定性

LinkedIn 经常更新页面结构，选择器可能失效。建议：

1. **使用 aria-label**: 比 CSS 类更稳定
   ```css
   [aria-label*="member profile"]
   [aria-label*="activity"]
   ```

2. **使用数据属性**: LinkedIn 有时使用 data-属性
   ```css
   [data-control-name*="profile"]
   [data-tracking-info*="member_profile"]
   ```

3. **多层级验证**: 不要依赖单一选择器
   ```python
   # 先找父容器，再找子元素
   parent = page.query_selector('.pv-profile-section')
   name = parent.query_selector('.text-heading-xlarge') if parent else None
   ```

### 7.2 反爬虫检测

LinkedIn 有严格的反爬虫机制：

1. **请求频率**: 单次检查间隔 ≥ 5 秒
2. **用户代理**: 使用真实浏览器 UA
3. **登录状态**: 保持登录会话，避免频繁登录
4. **验证码处理**: 检测到验证码时暂停并通知用户

### 7.3 页面加载等待

```python
# 等待网络空闲
page.goto(url, wait_until='networkidle')

# 等待特定元素
page.wait_for_selector('.pv-text-details__left-panel', timeout=10000)

# 等待导航完成
page.wait_for_load_state('domcontentloaded')
```

---

## 八、调试技巧

### 8.1 浏览器开发者工具

1. 打开 LinkedIn 页面
2. F12 打开开发者工具
3. 使用元素选择器 (Ctrl+Shift+C)
4. 右键元素 → Copy → Copy selector

### 8.2 Playwright 调试

```python
# 开启调试模式
browser = playwright.chromium.launch(headless=False, devtools=True)

# 截图调试
page.screenshot(path='debug.png')

# 打印页面 HTML
print(page.content())
```

### 8.3 选择器测试

```python
# 测试选择器是否有效
element = page.query_selector('.your-selector')
if element:
    print(f"✓ 选择器有效：{element.inner_text()}")
else:
    print("✗ 选择器无效")
```

---

## 九、更新日志

| 日期 | 更新内容 | 版本 |
|------|----------|------|
| 2026-03-31 | 初始版本 | v1.0 |

---

**维护说明**: 
- 每次 LinkedIn 页面更新后验证选择器
- 记录失效的选择器并寻找替代方案
- 优先使用 aria-label 等稳定属性
