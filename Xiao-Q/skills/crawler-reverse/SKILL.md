---
name: crawler-reverse
description: 爬虫逆向工程助手。当用户需要逆向分析 JS 加密参数（如 a_bogus、X-Bogus、_signature 等）、突破反爬机制（瑞数/阿里系/acw_sc__v2 等 Cookie 反爬）、补环境、抠代码、分析调用栈时使用。覆盖平台包括抖音、小红书、快手等。用户提到"逆向""补环境""抠代码""签名参数""反爬""JS 逆向""cookie 加密"时触发。
---

# 爬虫逆向 Skill

此 Skill 将 AI 驱动的爬虫逆向工作流系统化，覆盖从信息收集到代码产出的完整链路。

## 核心方法论：AI 辅助逆向 4 阶段

```
信息收集 → 断点定位 → 日志分析 → 算法复现
```

---

## 阶段 1：信息收集

### 1.1 接口抓包
- 打开浏览器 DevTools → Network 面板
- 过滤目标接口（XHR/Fetch），刷新触发请求
- 复制 cURL，去 https://curlconverter.com/ 生成 Python 代码
- 逐个注释可疑参数，确认哪些参数必须携带

### 1.2 参数识别
在不同平台，加密参数特征不同：

| 平台 | 核心签名参数 | 长度 | 位置 |
|------|------------|------|------|
| 抖音 Web | a_bogus | 168/172 | Query String |
| 抖音 Web | msToken | ~120 | Cookie |
| 小红书 | a_bogus | 44 或其他 | Query String/Header |
| 瑞数系 | Cookie_T (60e...) | 动态 | Cookie |

### 1.3 判断加密类型
- `412` 状态码 + 两次请求 → **瑞数系**（4/5/6 代/VMP）
- `a_bogus` 参数 → **字节系**（抖音/头条/西瓜）
- `_signature` → **快手/其他**
- 无限 debugger → 打开 "永不在此处暂停"

---

## 阶段 2：断点定位

### 2.1 定位入口（按优先级）

**方法 A: XHR/Fetch 断点**（推荐首选）
```
Sources → XHR/fetch Breakpoints → 添加接口路径片段
刷新页面，断住后查看 Call Stack
```

**方法 B: 全局搜索**
```
搜索关键字如 a_bogus、_signature、encrypt
如果混淆后搜不到 → 换方法 A
```

**方法 C: Hook Cookie**（瑞数专用）
```javascript
// 注入 Hook 代码
(function() {
    var cookieTemp = "";
    Object.defineProperty(document, 'cookie', {
        set: function(val) {
            if (val.indexOf('Cookie_T') > -1) {
                debugger;  // 断住 cookie 设置点
            }
            cookieTemp = val;
            return val;
        },
        get: function() { return cookieTemp; }
    });
})();
```
注入时机：Script 断点 → 外链 js 首行暂停 → Console 执行 Hook → 放开断点

### 2.2 堆栈回溯
从请求发送点（Call Stack 底部）往**上**追溯，找到参数**首次出现**的位置：
- 在携带参数和未携带参数的堆栈之间，就是生成位置
- 标记该位置，记录调用链

---

## 阶段 3：日志分析（核心技巧）

### 3.1 日志插桩
在定位到的生成位置附近打日志断点：

```javascript
// 日志断点示例（不暂停，只打印）
"func:", s, "args:", u, "result:", l
```

### 3.2 批量日志收集（防卡死）
浏览器控制台直接输出大量日志会卡死，使用下载脚本：

```javascript
// 将对象转为字符串
get_obj_str = function(obj) {
    try {
        return JSON.stringify(obj, function(k, v) {
            if (v == window) return 'window';
            else if (typeof v == 'function') return `function ${v.name}`;
            else if (v && v[Symbol.toStringTag]) return `Symbol ${v[Symbol.toStringTag]}`;
            else return v;
        });
    } catch (e) { return String(obj); }
};

// 累加到 window.my_code 并分段下载
add_json_str = function(param_name, param) {
    var log_str = param_name + ": " + get_obj_str(param) + "\n";
    window.my_code = (window.my_code || "") + log_str;
    if (window.my_code.length > 500000) {
        var blob = new Blob([window.my_code], {type: 'text/plain'});
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'log_' + Date.now() + '.txt';
        a.click();
        window.my_code = "";
    }
};
```

### 3.3 条件断点
只在特定条件触发时暂停：
```javascript
// 条件断点示例：只断 a_bogus 生成为 168 位时
s.apply(b, u).length == 168
```

### 3.4 日志分析步骤
1. 收集多组（输入参数 → 输出签名）对照数据
2. 观察输入与输出的对应规律
3. 识别中间数组的转换规则（置换、编码等）
4. 标记不确定的部分，准备动态调试

---

## 阶段 4：算法复现

### 4.1 抠代码策略

**策略 A: 全量抠**（推荐初次尝试）
- 找到加密函数所在 JS 文件，整段复制到本地
- 在 Node.js 中运行，逐个修复报错

**策略 B: 最小抠**（熟练后使用）
- 只提取加密核心函数链
- 补全依赖的辅助函数

### 4.2 补环境

**核心原理**：让 Node.js 环境和浏览器环境执行同一段代码的输出一致。

**常用补环境项**：
```javascript
// 基础环境
window = global;
navigator = { userAgent: "...", platform: "...", webdriver: false };
document = { cookie: "", createElement: () => ({}), addEventListener: () => {} };
location = { href: "...", host: "...", protocol: "https:" };
screen = { width: 1920, height: 1080 };

// 瑞数特殊处理
delete global.__filename;
delete global.__dirname;
global.ActiveXObject = undefined;

// Proxy 调试环境（瑞数高级）
const env = new Proxy(window, {
    set(obj, prop, value) {
        console.log(`[Env] set ${prop} =`, value);
        return Reflect.set(obj, prop, value);
    },
    get(obj, prop) {
        console.log(`[Env] get ${prop}`);
        return Reflect.get(obj, prop);
    }
});
```

**补环境验证法**：
1. 在浏览器断点处保存一份 JS 代码快照
2. 本地 Node.js 执行同一份代码
3. 对比两边的执行流程和输出 → 直到一致

---

## 针对特定平台的速查

### 字节系（抖音 a_bogus）
- MS_TOKEN = Cookie 中的 msToken，7 天有效
- a_bogus 生成步骤：参数数组 → 组合大数组 → 乱码字符串 → Base64 编码
- screen_width/height → cookie 中 dy_swidth/dy_sheight
- verifyFp/fp → cookie 中 s_v_web_id

### 瑞数系（Cookie 反爬）
- 6 代 Cookie 首字母: `60e...`
- 流程: 首次 412 → 获取 HTML + JS → 执行生成 Cookie → 二次请求成功
- 关键: VM 入口函数、`$_ts` 变量、环境检测点

---

## 参考资料

详细技术文档见：
- `references/a_bogus.md` — 抖音 a_bogus 逆向细节
- `references/ruishu.md` — 瑞数各代逆向指南
- `references/env-patch.md` — 补环境完整手册
