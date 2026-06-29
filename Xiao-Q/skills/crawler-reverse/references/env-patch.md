# 补环境完整手册

## 核心原则
**让 Node.js 执行同一份 JS 代码的输出与浏览器一致。**

## 标准环境模板

### 浏览器基础对象
```javascript
// window
window = global;
self = global;
top = window;
frames = window;
parent = window;

// navigator
global.navigator = {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    platform: "Win32",
    language: "zh-CN",
    webdriver: false,
    cookieEnabled: true,
    appVersion: "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    vendor: "Google Inc.",
    plugins: { length: 5 },
    mimeTypes: { length: 2 },
    hardwareConcurrency: 8,
    deviceMemory: 8,
};

// location
global.location = {
    href: "https://www.douyin.com/",
    host: "www.douyin.com",
    hostname: "www.douyin.com",
    protocol: "https:",
    origin: "https://www.douyin.com",
    port: "",
    pathname: "/",
    search: "",
    hash: "",
};

// document
global.document = {
    cookie: "",
    createElement: function(tag) {
        return {
            style: {},
            setAttribute: function() {},
            getAttribute: function() { return null; },
            appendChild: function() {},
            removeChild: function() {},
            innerHTML: "",
        };
    },
    addEventListener: function() {},
    removeEventListener: function() {},
    querySelector: function() { return null; },
    querySelectorAll: function() { return []; },
    getElementById: function() { return null; },
    getElementsByTagName: function() { return []; },
    createEvent: function() { return { initEvent: function() {} }; },
    documentElement: { style: {} },
    body: { appendChild: function() {} },
    head: { appendChild: function() {} },
};

// screen
global.screen = {
    width: 1920,
    height: 1080,
    availWidth: 1920,
    availHeight: 1040,
    colorDepth: 24,
    pixelDepth: 24,
};

// localStorage / sessionStorage
global.localStorage = {
    _data: {},
    getItem: function(k) { return this._data[k] || null; },
    setItem: function(k, v) { this._data[k] = v; },
    removeItem: function(k) { delete this._data[k]; },
    clear: function() { this._data = {}; },
};
global.sessionStorage = JSON.parse(JSON.stringify(global.localStorage));

// indexedDB (慎补，容易暴露)
global.indexedDB = undefined;  // 先不补，报错再说
```

## 瑞数专项环境清理

```javascript
// === 必须最先执行 ===
delete global.__filename;
delete global.__dirname;
global.ActiveXObject = undefined;
delete global.exports;
delete global.require;
delete global.module;
```

## Proxy 调试法（通用）

当不确定某个属性被检测时，用 Proxy 拦截：

```javascript
function makeEnvProxy(target, label) {
    return new Proxy(target, {
        set(obj, prop, value) {
            console.log(`[${label}] SET ${String(prop)} =`, typeof value === 'function' ? 'function' : value);
            return Reflect.set(obj, prop, value);
        },
        get(obj, prop) {
            const val = Reflect.get(obj, prop);
            if (val === undefined) {
                console.log(`[${label}] GET ${String(prop)} → undefined ⚠️`);
            }
            return val;
        },
    });
}

window = makeEnvProxy(window, 'window');
document = makeEnvProxy(document, 'document');
navigator = makeEnvProxy(navigator, 'navigator');
```

未补的属性会打印 `⚠️`，逐个补上直到没有警告。

## 验证方法

### 分阶段验证
1. **导入阶段**：代码是否报语法错误
2. **初始化阶段**：环境检测是否通过
3. **执行阶段**：加密函数是否正常返回
4. **结果阶段**：输出是否与浏览器一致

### 对照基准
```
浏览器: 输入 → 加密函数 → 输出_A
Node:   输入 → 加密函数 → 输出_B
输出_A == 输出_B → 环境补完 ✅
```

## 常见检测与绕过

| 检测点 | 绕过方式 |
|--------|---------|
| `navigator.webdriver` | 设为 `false` |
| 无头浏览器检测 | 补 window 尺寸、chrome 属性 |
| `toString()` 检测 | 函数保持原生 toString |
| `Error.stack` 检测 | `Error.prepareStackTrace` 返回自定义 |
| `console` 检测 | 先设为 null 再恢复 |
| Canvas 指纹 | 不需高精度时跳过，需要时用 node-canvas |
