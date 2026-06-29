# 安全检查规则库

## 一、注入类 (Injection)

### 搜索模式 (Grep)
```
SQL注入: "SELECT" +, "INSERT INTO" +, cursor.execute( 无参数化
OS命令: exec(, system(, popen(, subprocess.call(, Runtime.exec(, os.system(
模板注入: Jinja2 env.from_string, EJS <%-, Pug != (未转义)
日志注入: 用户输入直接拼接含 \n
```

### 检查点
- 参数化查询 / ORM 安全方法
- 用户输入是否验证和转义后才拼入命令
- 模板引擎是否开启自动转义

## 二、失效访问控制

### 搜索模式
- 路由定义缺少中间件（Express 未加 authMiddleware）
- API 路径含可预测资源 ID（`/api/user/123/invoice`）未作归属校验
- CORS 配置 `Access-Control-Allow-Origin: *` 且 `Allow-Credentials: true`

### 检查点
- 敏感操作是否校验权限
- JWT/Session 验证是否在受保护路由前统一执行
- 是否存在 IDOR 风险

## 三、加密失效

### 搜索模式
```
弱哈希: MD5(, SHA1(, digest('sha1')
硬编码密钥: password =, secret_key =, API_KEY =, -----BEGIN RSA PRIVATE KEY-----
不安全随机数: Math.random() 用于安全令牌
ECB模式: AES.MODE_ECB
```

### 检查点
- 密钥管理是否用环境变量或 KMS
- 密码哈希是否用 bcrypt/scrypt/Argon2
- TLS 版本

## 四、不安全设计

### 检查点
- 速率限制缺失
- 密码重置令牌可猜测（时间戳）
- 错误消息泄露内部信息（堆栈 trace、数据库类型）
- 批量分配漏洞（`req.body` 直接赋值模型）

## 五、安全配置错误

### 搜索模式
```
文件权限: chmod 777, mode: "0777"
调试模式: DEBUG=True, NODE_ENV=development
不必要 HTTP 方法暴露
默认凭据: admin/admin
```

### 检查点
- 生产环境是否关闭调试
- 是否移除默认账号
- 安全头：CSP, HSTS, X-Content-Type-Options

## 六、过时组件

- 解析 package.json, requirements.txt, Gemfile 等
- 若允许 Bash：运行 `npm audit --json` 或 `pip-audit`
- 否则列出依赖和版本，结合 WebSearch 查 CVE

## 七、敏感信息泄露

### 搜索模式（不区分大小写）
```
通用密钥: (?i)(secret|password|key|token|auth).{0,20}['":=](?!.*(example|test|dummy|your_)).{8,}
AWS密钥: AKIA[0-9A-Z]{16}
GitHub Token: ghp_[0-9a-zA-Z]{36}
私钥: -----BEGIN (RSA|EC|DSA) PRIVATE KEY-----
```

检出真实凭证时仅显示掩码（如 `AKIA****`），立即警告用户轮换。

## 八、SSRF

### 模式
用户可控制的 URL 传入 `requests.get()`, `urllib.urlopen()`, `axios.get()`

### 检查点
- 是否校验目标 IP 非内网
- 是否禁用跳转
- 是否仅允许白名单域名

## 九、框架/语言专项

### JavaScript/Node.js
- 原型污染：`_.merge({}, userInput)`
- XSS：`innerHTML` 赋值、`dangerouslySetInnerHTML`
- 正则 ReDoS：`/(a+)+b/`

### Python
- 反序列化：`pickle.loads(untrusted)`, `yaml.load`（应用 `safe_load`）
- 路径遍历：`open(user_path)` 未过滤 `..`

### Java
- XXE：`DocumentBuilderFactory` 未禁用外部实体
- 反序列化：`ObjectInputStream` 读不可信数据

### Go
- 模板注入：`template.HTML(userInput)` 未过滤

### Docker/K8s
- 容器 root 运行：`USER root`
- 特权容器：`privileged: true`
- 挂载 Docker socket：`/var/run/docker.sock`
- K8s：`runAsNonRoot: false`, `allowPrivilegeEscalation: true`
