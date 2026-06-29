# Linux 常用命令参考

## 系统信息

```bash
# 查看系统信息
uname -a                    # 内核版本
cat /etc/os-release         # 操作系统版本
hostname                    # 主机名
uptime                      # 运行时间
whoami                      # 当前用户
```

## 性能监控

```bash
# CPU
top                         # 实时进程监控
htop                        # 增强版 top
mpstat                      # CPU 统计
vmstat                      # 虚拟内存统计

# 内存
free -h                     # 内存使用
cat /proc/meminfo           # 详细内存信息

# 磁盘
df -h                       # 磁盘空间
du -sh *                    # 目录大小
iostat                      # I/O 统计

# 网络
netstat -tulpn              # 网络连接
ss -tulpn                   # 快速版 netstat
ip addr                     # IP 地址
ping -c 4 example.com       # 网络连通性
```

## 进程管理

```bash
# 查看进程
ps aux                      # 所有进程
ps -ef | grep nginx         # 搜索进程
pgrep nginx                 # 按名称搜索 PID

# 控制进程
kill <PID>                  # 终止进程
kill -9 <PID>               # 强制终止
killall nginx               # 按名称终止
pkill -f pattern            # 按模式终止

# 优先级
nice -n 10 command          # 设置优先级
renice 10 -p <PID>          # 修改已运行进程优先级
```

## 服务管理 (systemd)

```bash
# 服务状态
systemctl status nginx              # 查看状态
systemctl list-units --type=service # 列出服务

# 服务控制
systemctl start nginx               # 启动
systemctl stop nginx                # 停止
systemctl restart nginx             # 重启
systemctl reload nginx              # 重载配置
systemctl enable nginx              # 开机自启
systemctl disable nginx             # 禁用自启

# 日志
journalctl -u nginx                 # 服务日志
journalctl -u nginx -f              # 实时跟踪
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx -n 100          # 最近 100 行
```

## 文件操作

```bash
# 基本操作
ls -la                      # 详细列表
cp -r src/ dest/            # 复制
mv file1 file2              # 移动/重命名
rm -rf directory/           # 删除
mkdir -p path/to/dir        # 创建目录

# 查看文件
cat file                    # 显示内容
less file                   # 分页查看
tail -f file                # 实时跟踪
head -n 20 file             # 前 20 行

# 查找文件
find /path -name "*.log"    # 按名称查找
find /path -mtime -7        # 7 天内修改
locate filename             # 快速查找
```

## 权限管理

```bash
# 查看权限
ls -l                       # 详细权限
stat file                   # 详细状态

# 修改权限
chmod 755 file              # 数字方式
chmod u+x file              # 符号方式
chown user:group file       # 修改所有者
chgrp group file            # 修改组

# 特殊权限
chmod +s file               # SetUID/SetGID
chmod +t directory/         # Sticky bit
```

## 网络操作

```bash
# 连接测试
ping host                   # ICMP 测试
telnet host port            # TCP 测试
nc -zv host port            # 快速端口测试
curl -I https://example.com # HTTP 测试

# 下载上传
curl -O url                 # 下载
wget url                    # 下载
scp file user@host:path     # SSH 复制
rsync -av src/ dest/        # 同步

# 防火墙
iptables -L                 # 查看规则
ufw status                  # Ubuntu 防火墙
firewall-cmd --list-all     # CentOS 防火墙
```

## 日志分析

```bash
# 查看日志
tail -f /var/log/syslog             # 系统日志
tail -f /var/log/nginx/access.log   # Nginx 访问日志
tail -f /var/log/mysql/error.log    # MySQL 错误日志

# 日志分析
grep "ERROR" /var/log/syslog        # 搜索错误
grep -c "404" access.log            # 统计 404
awk '{print $1}' access.log | sort | uniq -c  # IP 统计
cat access.log | jq '.'             # JSON 格式化
```

## 压缩归档

```bash
# tar
tar -czvf archive.tar.gz dir/       # 压缩
tar -xzvf archive.tar.gz            # 解压
tar -tvf archive.tar.gz             # 查看内容

# zip
zip -r archive.zip dir/             # 压缩
unzip archive.zip                   # 解压
```

## 用户管理

```bash
# 用户操作
useradd username                    # 创建用户
userdel username                    # 删除用户
passwd username                     # 修改密码
usermod -aG group username          # 添加到组

# 查看用户
id username                         # 用户信息
who                                 # 登录用户
last                                # 登录历史
```

## 计划任务

```bash
# crontab
crontab -e                          # 编辑任务
crontab -l                          # 列出任务
crontab -r                          # 删除任务

# 示例
# 每天凌晨 2 点执行
0 2 * * * /path/to/script.sh

# 每 5 分钟执行
*/5 * * * * /path/to/script.sh

# 每周一 9 点执行
0 9 * * 1 /path/to/script.sh
```

## 性能调优

```bash
# 查看资源限制
ulimit -a                           # 所有限制
ulimit -n                           # 文件描述符

# 修改限制
ulimit -n 65535                     # 临时修改
# /etc/security/limits.conf        # 永久修改

# 内核参数
sysctl -a                           # 查看所有参数
sysctl -w net.ipv4.tcp_max_syn_backlog=65536
```

## 故障排查

```bash
# 磁盘满
df -h                               # 查看磁盘使用
du -sh /* | sort -hr | head         # 查找大目录
find / -type f -size +100M          # 查找大文件

# 内存泄漏
ps aux --sort=-%mem | head          # 内存占用进程
free -h                             # 内存使用

# CPU 高
top                                 # 实时查看
pidstat 1                           # 进程统计

# 网络问题
netstat -tulpn                      # 监听端口
ss -s                               # 连接统计
tcpdump -i eth0 port 80             # 抓包分析
```
