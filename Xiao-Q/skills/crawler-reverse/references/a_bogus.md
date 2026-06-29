# 抖音 a_bogus 逆向详解

## 概述
a_bogus 是字节系（抖音/头条/西瓜）核心反爬签名参数，长度 168 或 172 字符，位于 Query String。

## 关联参数
| 参数 | 位置 | 说明 |
|------|------|------|
| msToken | Cookie | 7天有效期 |
| X-Bogus | Header | 旧版签名，已过渡到 a_bogus |
| _signature | Query | 部分接口使用 |
| verifyFp | Query | 对应 cookie 中 s_v_web_id |

## 环境参数依赖
```
screen_width  → cookie.dy_swidth
screen_height → cookie.dy_sheight  
cpu_core_num  → cookie.device_web_cpu_core
device_memory → cookie.device_web_memory_size
verifyFp      → cookie.s_v_web_id
webid         → document.user_unique_id
```

## 生成流程 (4 步)

### Step 1: 参数收集
根据请求的 params、data、userAgent 以及环境参数生成 4 个数组

### Step 2: 数组组合
通过特定规则将 4 个数组组合成一个大数组

### Step 3: 乱码生成
- 通过随机数生成乱码字符串 1
- 根据大数组生成乱码字符串 2
- 拼接两个乱码字符串，再次处理得到最终乱码字符串

### Step 4: Base64 编码
根据最终乱码字符串生成 a_bogus → 魔改 Base64 编码

## 定位技巧
1. XHR 断点 → 接口路径 `/aweme/v1/web/` 
2. 堆栈回溯 → 找到 `s.apply(b, u)` 调用点
3. 条件断点 → `s.apply(b, u).length == 168`
4. 日志断点 → 输出 s, b, u, 返回值

## 还原验证
- 用相同输入参数调用生成函数
- 对比生成的 a_bogus 与浏览器抓包值
- 如果一致 → 纯算还原成功
