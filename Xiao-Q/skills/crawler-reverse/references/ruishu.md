# 瑞数反爬逆向指南

## 版本识别

| 代际 | Cookie_T 首字符 | 特征 |
|------|----------------|------|
| 瑞数 3 | `31...` | 简单动态 JS |
| 瑞数 4 | `41...` | 双层动态 JS |
| 瑞数 5 | `51...` | 多层嵌套 |
| 瑞数 6 | `60e...` | VM 虚拟机执行 |
| 瑞数 VMP | 类似 6 代 | 自研虚拟指令集 |

## 通用流程

### 1. 请求特征
- 首次请求返回 `412` 状态码
- HTML 中包含加密 JS 和 `content` 字段
- Cookie 中返回 `Cookie_T` 初始值
- 浏览器执行 JS 后，二次请求成功（200）

### 2. Hook Cookie
```javascript
(function() {
    var cookieTemp = "";
    Object.defineProperty(document, 'cookie', {
        set: function(val) {
            if (val.indexOf('Cookie_T') > -1) {
                debugger;
            }
            cookieTemp = val;
            return val;
        },
        get: function() { return cookieTemp; }
    });
})();
```

### 3. 定位 Cookie_T 生成位置
- Script 断点 → 外链 js 首行暂停
- Console 注入 Hook 代码
- 放开断点继续执行
- Hook 触发时查看 Call Stack
- 找到 Cookie 值首次出现的堆栈位置

## 瑞数 6 代专项

### VM 入口定位
- HTML 中外链 JS 即 VM 入口
- `$_ts` 变量承载加密数据
- `content` 字段是 VM 执行的字节码

### 关键检测点
- `__filename` / `__dirname` 存在检测
- `ActiveXObject` 可用性
- `navigator.webdriver` 检测
- Canvas/WebGL 指纹
- `toString()` 对函数原型的检测

### 补环境策略
```javascript
// 必须在任何其他代码执行前
delete global.__filename;
delete global.__dirname;
global.ActiveXObject = undefined;
global.navigator = { webdriver: false };
```

### 调试技巧
- 用 `vm2` 模块隔离执行环境
- Proxy 拦截所有属性读写
- 对比浏览器和 Node 两端输出差异
- 逐属性补全，逐个消除差异

## 常见坑
1. 无限 debugger → 注入反 debugger 脚本或 "永不在此处暂停"
2. 内存爆增 → 瑞数检测到环境不对时故意死循环
3. 浏览器卡死 → 补 `top.location` / `location.href`
4. Cookie 生成后仍 412 → 检查是否有第二层环境检测
