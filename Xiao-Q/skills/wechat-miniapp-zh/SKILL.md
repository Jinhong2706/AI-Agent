---
name: wechat-miniapp-zh
displayName: 微信小程序开发助手
slug: wechat-miniapp-zh
version: 1.0.0
author: ikun
license: MIT
language: zh-CN
description: |
  微信小程序开发的全流程助手——从 appid 申请、原生 / Taro / uni-app 选型、云开发 / 自建后端选型，
  到登录鉴权、支付、订阅消息、审核避坑。区别于通用 Web 开发，专攻微信生态特殊性。
  覆盖：技术选型、架构设计、关键 API、审核驳回原因 5 大类、安全合规。
  触发：用户说 "微信小程序"、"小程序开发"、"Taro"、"uni-app"、"云开发"、"wx.login"、"小程序支付"、"订阅消息"、"审核驳回"。
keywords: ["微信小程序", "小程序开发", "Taro", "uni-app", "云开发", "wx.login", "微信支付", "订阅消息", "小程序审核", "appid", "WXML", "WXSS"]
---

# 微信小程序开发助手

## 这个 skill 解决什么

微信小程序和 Web 开发完全是两个物种：
- 没有 DOM、没有 window、没有 localStorage（有自己的 `wx.setStorage`）
- 路由不是 react-router / vue-router（是 `wx.navigateTo` 那一套）
- 没有第三方 npm 包用（90% 的 npm 包都跑不起来）
- 登录、支付、消息全是微信家的 API
- 审核被驳回不告诉你具体哪行错（只给一句"违反 X.X 条款"）

这个 skill 帮你：
1. **选型决策**：原生 / Taro / uni-app 选哪个
2. **关键 API 速查**：登录、支付、订阅消息、wx 全家桶
3. **审核避坑**：5 大类驳回原因 + 修复策略
4. **架构设计**：云开发 vs 自建后端怎么选

**不做的事**：不替你写完整业务代码（场景太多）；不做 UI 设计；不做支付证书申请那种纯账号工作。

---

## 选型决策（一上来就要对）

### 3 种主流方案对比

| | 原生（WXML/WXSS/JS） | Taro（React 风格） | uni-app（Vue 风格） |
|---|---|---|---|
| 学习成本 | 低（看官方文档 1 周） | 中（要会 React） | 中（要会 Vue） |
| 开发效率 | 中 | 高（组件化） | 高（生态成熟） |
| 性能 | 最好（原生） | 好（编译后接近原生） | 好 |
| 多端编译 | 只能微信 | ✅ 微信 / 支付宝 / H5 / RN | ✅ 微信 / 支付宝 / 抖音 / H5 / App |
| 调试 | 最稳（官方工具） | 中（多一层编译） | 中（多一层编译） |
| 生态 | 官方组件 | React 生态 | Vue 生态 + DCloud 插件市场 |
| 适合 | 纯微信 / 性能要求高 | React 团队 / 多端 | Vue 团队 / 跨端跨平台 |

### 决策树

```
是不是只发布微信？
├─ 是 → 团队会 React 吗？
│       ├─ 会 → Taro（更现代）或 原生（更稳）
│       └─ 不会 → 原生（学习成本最低）
└─ 否（要发抖音 / 支付宝 / H5 / App）→
        ├─ 团队 React → Taro
        └─ 团队 Vue → uni-app（多端兼容性最好）
```

---

## 后端选型（云开发 vs 自建）

### 云开发（CloudBase）
- **适合**：MVP / 轻量应用 / 不会运维
- **优势**：免服务器、免域名备案、自带云函数 / 数据库 / 存储
- **劣势**：贵（DAU 上去 1 万 + 每月 2k+）、不能用复杂的 SQL、迁出难
- **成本**：免费版 1 万次调用 / 月，付费版按用量

### 自建后端（Node / Java / Python + 服务器）
- **适合**：业务复杂 / 长期产品 / 团队有后端
- **优势**：可控、便宜、能用任何技术栈
- **劣势**：需要服务器 + 域名 + 备案 + ICP（最少 1 个月）、要自己运维
- **成本**：阿里云 / 腾讯云轻量服务器 60 元 / 月起

### 决策建议
- **3 个月内 MVP** → 云开发
- **正式产品 / 长期** → 自建（早晚要迁，越早越好）

---

## 关键 API 速查

### 1. 登录与用户信息

```javascript
// 1. 拿临时登录凭证
wx.login({
  success: async (res) => {
    // res.code 5 分钟有效，要立即发给后端
    const { openid, session_key } = await fetch('/api/wx/login', {
      method: 'POST',
      body: JSON.stringify({ code: res.code })
    }).then(r => r.json())
    // 保存 openid 到本地
    wx.setStorageSync('openid', openid)
  }
})

// 2. 后端用 code 换 openid（必须服务端做，不能前端）
// GET https://api.weixin.qq.com/sns/jscode2session?
//   appid=xxx&secret=xxx&js_code=CODE&grant_type=authorization_code
```

**坑**：
- `wx.getUserInfo` **2021 年起已废弃**，必须用 `<button open-type="getUserProfile">` 主动触发
- 头像昵称从 2022 年起需要用 `<button open-type="chooseAvatar">` 单独获取
- 手机号必须用 `<button open-type="getPhoneNumber">` 用户主动授权 → 后端解密

### 2. 微信支付（最复杂 API）

```javascript
// 前端：调起支付
wx.requestPayment({
  timeStamp: '...',  // 来自后端
  nonceStr: '...',
  package: 'prepay_id=...',
  signType: 'MD5',
  paySign: '...',
  success: (res) => { /* 支付成功 */ },
  fail: (err) => { /* 支付失败/取消 */ }
})

// 后端流程：
// 1. 创建订单到自己数据库
// 2. 调微信统一下单 API（unifiedorder）
// 3. 拿到 prepay_id，组装支付参数 + sign 给前端
// 4. 监听微信回调（必须验签 + 幂等处理）
// 5. 更新订单状态
```

**坑**：
- 支付证书申请要 1 周（商户号 → 申请 API 证书 → 下载 → 上传服务器）
- 沙箱环境不可信，必须真实测试
- 退款需要再申请退款 API（默认不开通）
- 回调一定要做幂等（微信会重试）

### 3. 订阅消息（替代旧版模板消息）

```javascript
// 前端：用户点击触发，请求订阅
wx.requestSubscribeMessage({
  tmplIds: ['xxx', 'xxx'],  // 后台预先申请的模板 ID
  success: (res) => { /* res 里看每个模板是否同意 */ }
})

// 后端：用户操作后发送
POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send
{
  "touser": "用户 openid",
  "template_id": "xxx",
  "page": "pages/order/detail?id=123",
  "data": { "thing1": { "value": "您的订单已发货" } }
}
```

**坑**：
- 订阅消息是**一次订阅一次发送**（用户每次都要重新订阅）
- 模板必须按微信类目申请（涉及行业资质）
- 发送时机有严格限制（用户操作后 7 天 / 24 小时）

### 4. 数据存储

```javascript
// 同步（小数据量，<10KB 推荐）
wx.setStorageSync('key', value)
const value = wx.getStorageSync('key')

// 异步（推荐用法）
wx.setStorage({ key, data })

// 单 key 上限 1MB，整个小程序 10MB
```

---

## 审核驳回 5 大原因 + 修复

### 原因 1：未提供测试账号
- 现象："提供测试账号供审核员体验"
- 修复：在提交审核备注里写"测试账号 / 密码"或"游客可体验"

### 原因 2：涉及虚拟支付
- 现象：iOS 端禁止虚拟物品（课程、会员、币）支付，被驳回
- 修复：iOS 端必须**关闭支付入口**或转用苹果 IAP（个人小程序无法接 IAP）

### 原因 3：诱导分享 / 关注
- 现象："分享获奖励"、"关注公众号才能用"
- 修复：把"必须分享 / 关注"改成"建议分享 / 关注"，福利改成普惠

### 原因 4：未审核类目超范围
- 现象：申请了"工具" 类目，里面做了商城功能
- 修复：扩展类目（小程序后台 → 服务类目 → 添加），有的类目要资质证明

### 原因 5：用户协议 / 隐私协议缺失
- 现象：首次进入未弹出隐私协议、或协议内容不完整
- 修复：
  - 必须在 `app.json` 里配 `__usePrivacyCheck__: true`
  - 首次进入弹隐私协议（用 `wx.requirePrivacyAuthorize`）
  - 协议内容必须包含：收集什么信息 / 如何使用 / 如何保护 / 用户权利

---

## 安全合规（高频忽略点）

| 项 | 要求 |
|---|---|
| 隐私协议 | 必须 + 用户主动同意（2024 起强审） |
| 用户数据收集 | 必须最小化、必须告知 |
| 第三方 SDK | 必须在隐私协议中列出（如友盟、Bugly） |
| 个人小程序 | 不能做电商 / 金融 / 医疗 / 教育（必须企业资质） |
| 内容安全 | 用户输入文字 / 图片必须过 `security.msgSecCheck` 内容安全 API |
| ICP 备案 | 服务器域名必须备案（境内）+ ICP 证（电商类） |

---

## AI 执行流程

### 第一步：摸场景

1. 你是要做新小程序还是优化已有的？
2. 业务类型是什么？（电商 / 工具 / 内容 / 社交 / 政务）
3. 团队技术栈？（会 React / Vue / 还是从零学）
4. 是否要多端（除微信外的支付宝 / 抖音 / H5 / App）？
5. 预算情况（决定云开发 vs 自建）？
6. 有没有具体卡住的问题？（如审核驳回、支付集成、性能优化）

### 第二步：给方案

按问题类型给：
- **选型问题** → 输出选型决策表 + 推荐
- **API 问题** → 输出代码示例 + 坑提示
- **审核问题** → 输出驳回类型分析 + 修复步骤
- **架构问题** → 输出推荐架构图 + 选型理由

### 第三步：自检 checklist

- [ ] 涉及版本兼容性的 API 注明微信版本要求
- [ ] 涉及证书 / 备案的提示前置时间
- [ ] 涉及合规的提示《个保法》《互联网信息服务管理办法》
- [ ] 代码示例可直接运行（不是伪代码）
- [ ] 给了"下一步具体怎么做"的步骤

---

## 输出格式

```markdown
## 你的问题
（复述）

## 推荐方案
（选型 / 架构 / API / 修复）

## 代码示例
```javascript
// 注释清楚，不写废话
```

## 注意事项 / 坑
- 坑 1：XXX
- 坑 2：XXX

## 下一步行动
1. 先做 XXX
2. 然后 XXX
3. 最后 XXX

## 相关资料
- 官方文档：https://developers.weixin.qq.com/miniprogram/dev/...
- 社区帖子：xxx
```

---

## 终止条件

- 用户拿到了可执行的方案 / 代码 / 步骤
- 涉及合规 / 安全的关键点提示完整
- 用户没追问"为什么"

不主动写完整业务代码（场景太多）；不主动给完整 UI 实现。
