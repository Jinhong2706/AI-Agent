---
name: server-ops
description: 服务器运维操作。支持 SSH 连接远程服务器，执行启动、停止、重启、状态查询、日志查看等操作。
             使用场景：服务器日常管理、故障排查、服务维护、批量操作。
             认证方式：SSH Key、密码认证。
metadata:
  domain: server-management
  transport: SSH
  requires:
    bins: [ssh, scp, ssh-keygen]
---

# 服务器运维 Skill

## 快速开始

### 步骤 1：配置服务器连接

```bash
# 添加服务器到配置
ssh-copy-id user@192.168.1.100

# 测试连接
ssh user@192.168.1.100 "echo connected"
```

### 步骤 2：执行服务器操作

```bash
# 查看服务器状态
python scripts/server-ops.py status --host 192.168.1.100 --user admin

# 重启服务器
python scripts/server-ops.py restart --host 192.168.1.100 --user admin

# 查看日志
python scripts/server-ops.py logs --host 192.168.1.100 --user admin --lines 50
```

---

## 支持的操作

### 1. 状态查询 (status)

```bash
python scripts/server-ops.py status --host <host> --user <user>
```

返回：
```json
{
  "hostname": "server-01",
  "uptime": "15 days, 3:24:11",
  "load": [0.52, 0.48, 0.45],
  "memory": {
    "total": 16384,
    "used": 8192,
    "free": 8192,
    "percent": 50.0
  },
  "disk": [
    {
      "mount": "/",
      "total": 500,
      "used": 250,
      "free": 250,
      "percent": 50.0
    }
  ],
  "cpu": {
    "cores": 4,
    "percent": 25.5
  },
  "services": [
    {"name": "nginx", "status": "running"},
    {"name": "mysql", "status": "running"}
  ]
}
```

### 2. 启动服务 (start)

```bash
python scripts/server-ops.py start --host <host> --user <user> --service <service_name>
```

示例：
```bash
python scripts/server-ops.py start --host 192.168.1.100 --user admin --service nginx
```

### 3. 停止服务 (stop)

```bash
python scripts/server-ops.py stop --host <host> --user <user> --service <service_name>
```

示例：
```bash
python scripts/server-ops.py stop --host 192.168.1.100 --user admin --service nginx
```

### 4. 重启服务 (restart)

```bash
python scripts/server-ops.py restart --host <host> --user <user> --service <service_name>
```

示例：
```bash
python scripts/server-ops.py restart --host 192.168.1.100 --user admin --service nginx
```

### 5. 查看日志 (logs)

```bash
python scripts/server-ops.py logs --host <host> --user <user> --service <service_name> --lines <n>
```

参数：
- `--lines`: 返回行数（默认 50）
- `--follow`: 实时跟踪（类似 tail -f）
- `--since`: 起始时间（如 "2026-04-17 10:00:00"）

示例：
```bash
# 查看最近 100 行日志
python scripts/server-ops.py logs --host 192.168.1.100 --user admin --service nginx --lines 100

# 实时跟踪日志
python scripts/server-ops.py logs --host 192.168.1.100 --user admin --service nginx --follow
```

### 6. 执行命令 (exec)

```bash
python scripts/server-ops.py exec --host <host> --user <user> --command "<command>"
```

示例：
```bash
python scripts/server-ops.py exec --host 192.168.1.100 --user admin --command "df -h"
```

### 7. 文件上传 (upload)

```bash
python scripts/server-ops.py upload --host <host> --user <user> --local <path> --remote <path>
```

示例：
```bash
python scripts/server-ops.py upload --host 192.168.1.100 --user admin --local ./config/nginx.conf --remote /etc/nginx/nginx.conf
```

### 8. 文件下载 (download)

```bash
python scripts/server-ops.py download --host <host> --user <user> --remote <path> --local <path>
```

示例：
```bash
python scripts/server-ops.py download --host 192.168.1.100 --user admin --remote /var/log/nginx/access.log --local ./logs/
```

---

## 批量操作

### 多服务器并行执行

```bash
# 创建服务器列表文件 servers.txt
192.168.1.100,admin
192.168.1.101,admin
192.168.1.102,admin

# 批量查看状态
python scripts/server-ops.py batch status --servers servers.txt

# 批量重启服务
python scripts/server-ops.py batch restart --servers servers.txt --service nginx
```

---

## 配置参考

### SSH 配置文件 (~/.ssh/config)

```ssh
Host server-prod
    HostName 192.168.1.100
    User admin
    IdentityFile ~/.ssh/id_rsa_prod
    Port 22

Host server-dev
    HostName 192.168.1.200
    User developer
    IdentityFile ~/.ssh/id_rsa_dev
    Port 2222
```

使用配置：
```bash
python scripts/server-ops.py status --host server-prod
```

---

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Connection refused` | SSH 服务未启动或端口错误 | 检查 SSH 服务和端口 |
| `Permission denied` | 认证失败 | 检查 SSH Key 或密码 |
| `Command not found` | 远程服务器缺少命令 | 安装必要工具 |
| `Timeout` | 网络超时 | 检查网络连接和防火墙 |

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "ssh: connect to host 192.168.1.100 port 22: Connection refused"
  }
}
```

---

## 安全注意事项

1. **SSH Key 管理**：使用密钥认证，禁用密码登录
2. **最小权限**：使用专用的运维账号，限制 sudo 权限
3. **审计日志**：记录所有远程操作
4. **超时设置**：所有操作都应设置合理的超时时间
5. **跳板机**：生产环境建议通过跳板机访问

---

## 何时读取参考资料

- **命令参考**：读取 `references/linux-commands.md` 查看常用 Linux 命令
- **服务管理**：读取 `references/service-management.md` 了解 systemd 服务管理
- **日志位置**：读取 `references/log-locations.md` 查看常见服务日志路径
