#!/usr/bin/env python3
"""
服务器运维脚本
封装 SSH 操作，提供标准化的服务器管理接口
"""

import subprocess
import json
import sys
import argparse
import paramiko
import scp
from typing import Any, Dict, List, Optional
from datetime import datetime


class ServerOps:
    """服务器操作类"""
    
    def __init__(self, host: str, user: str, port: int = 22, 
                 key_file: Optional[str] = None, password: Optional[str] = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_file = key_file
        self.password = password
        self.client = None
    
    def connect(self, timeout: int = 10) -> bool:
        """建立 SSH 连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_file:
                self.client.connect(
                    self.host, self.port, self.user,
                    key_filename=self.key_file,
                    timeout=timeout
                )
            elif self.password:
                self.client.connect(
                    self.host, self.port, self.user,
                    password=self.password,
                    timeout=timeout
                )
            else:
                # 使用系统 SSH 配置
                self.client.connect(
                    self.host, self.port, self.user,
                    timeout=timeout
                )
            return True
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def exec_command(self, command: str, timeout: int = 30) -> Dict:
        """执行远程命令"""
        try:
            if not self.client:
                self.connect()
            
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            result = {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout.read().decode('utf-8'),
                "stderr": stderr.read().decode('utf-8'),
                "command": command
            }
            
            if not result["success"]:
                result["error"] = result["stderr"]
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取服务器状态"""
        status = {}
        
        # 主机名
        result = self.exec_command("hostname")
        status["hostname"] = result.get("stdout", "").strip()
        
        # 运行时间
        result = self.exec_command("uptime -p")
        status["uptime"] = result.get("stdout", "").strip()
        
        # 负载
        result = self.exec_command("cat /proc/loadavg")
        load = result.get("stdout", "").split()[:3]
        status["load"] = [float(x) for x in load] if load else []
        
        # 内存
        result = self.exec_command("free -m")
        if result["success"]:
            lines = result["stdout"].strip().split('\n')
            mem_line = lines[1].split()
            status["memory"] = {
                "total": int(mem_line[1]),
                "used": int(mem_line[2]),
                "free": int(mem_line[3]),
                "percent": round(int(mem_line[2]) / int(mem_line[1]) * 100, 1)
            }
        
        # 磁盘
        result = self.exec_command("df -h --output=target,size,used,avail,pcent | grep -v tmpfs")
        if result["success"]:
            disks = []
            for line in result["stdout"].strip().split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    disks.append({
                        "mount": parts[0],
                        "total": parts[1],
                        "used": parts[2],
                        "free": parts[3],
                        "percent": float(parts[4].replace('%', ''))
                    })
            status["disk"] = disks
        
        # CPU
        result = self.exec_command("nproc")
        status["cpu"] = {
            "cores": int(result.get("stdout", "0").strip())
        }
        
        # 服务状态
        result = self.exec_command("systemctl list-units --type=service --state=running --no-legend")
        if result["success"]:
            services = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    services.append({
                        "name": line.split()[0],
                        "status": "running"
                    })
            status["services"] = services[:20]  # 限制返回数量
        
        return status
    
    def service_control(self, action: str, service_name: str) -> Dict:
        """服务控制（start/stop/restart）"""
        command = f"sudo systemctl {action} {service_name}"
        return self.exec_command(command)
    
    def get_logs(self, service_name: str, lines: int = 50, 
                 follow: bool = False, since: Optional[str] = None) -> Dict:
        """获取服务日志"""
        command = f"sudo journalctl -u {service_name} -n {lines} --no-pager"
        if since:
            command += f" --since '{since}'"
        return self.exec_command(command)
    
    def upload_file(self, local_path: str, remote_path: str) -> Dict:
        """上传文件"""
        try:
            if not self.client:
                self.connect()
            
            with scp.SCPClient(self.client.get_transport()) as scp_client:
                scp_client.put(local_path, remote_path)
            
            return {"success": True, "message": f"Uploaded {local_path} to {remote_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_file(self, remote_path: str, local_path: str) -> Dict:
        """下载文件"""
        try:
            if not self.client:
                self.connect()
            
            with scp.SCPClient(self.client.get_transport()) as scp_client:
                scp_client.get(remote_path, local_path)
            
            return {"success": True, "message": f"Downloaded {remote_path} to {local_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()


def main():
    parser = argparse.ArgumentParser(description="服务器运维工具")
    subparsers = parser.add_subparsers(dest="action", help="操作类型")
    
    # 通用参数
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--host", required=True, help="服务器地址")
    parent_parser.add_argument("--user", required=True, help="用户名")
    parent_parser.add_argument("--port", type=int, default=22, help="SSH 端口")
    parent_parser.add_argument("--key", help="SSH 密钥文件")
    parent_parser.add_argument("--password", help="SSH 密码")
    parent_parser.add_argument("--timeout", type=int, default=30, help="超时时间")
    
    # status
    status_parser = subparsers.add_parser("status", parents=[parent_parser])
    status_parser.add_argument("--output", default="json", help="输出格式")
    
    # start/stop/restart
    for action in ["start", "stop", "restart"]:
        action_parser = subparsers.add_parser(action, parents=[parent_parser])
        action_parser.add_argument("--service", required=True, help="服务名称")
    
    # logs
    logs_parser = subparsers.add_parser("logs", parents=[parent_parser])
    logs_parser.add_argument("--service", required=True, help="服务名称")
    logs_parser.add_argument("--lines", type=int, default=50, help="行数")
    logs_parser.add_argument("--follow", action="store_true", help="实时跟踪")
    logs_parser.add_argument("--since", help="起始时间")
    
    # exec
    exec_parser = subparsers.add_parser("exec", parents=[parent_parser])
    exec_parser.add_argument("--command", required=True, help="执行的命令")
    
    # upload
    upload_parser = subparsers.add_parser("upload", parents=[parent_parser])
    upload_parser.add_argument("--local", required=True, help="本地文件路径")
    upload_parser.add_argument("--remote", required=True, help="远程文件路径")
    
    # download
    download_parser = subparsers.add_parser("download", parents=[parent_parser])
    download_parser.add_argument("--remote", required=True, help="远程文件路径")
    download_parser.add_argument("--local", required=True, help="本地文件路径")
    
    args = parser.parse_args()
    
    # 创建操作实例
    server = ServerOps(
        host=args.host,
        user=args.user,
        port=args.port,
        key_file=args.key,
        password=args.password
    )
    
    try:
        # 连接服务器
        connect_result = server.connect(timeout=args.timeout)
        if isinstance(connect_result, dict) and not connect_result.get("success", True):
            print(json.dumps(connect_result, indent=2))
            sys.exit(1)
        
        # 执行操作
        if args.action == "status":
            result = server.get_status()
        elif args.action in ["start", "stop", "restart"]:
            result = server.service_control(args.action, args.service)
        elif args.action == "logs":
            result = server.get_logs(args.service, args.lines, args.follow, args.since)
        elif args.action == "exec":
            result = server.exec_command(args.command, timeout=args.timeout)
        elif args.action == "upload":
            result = server.upload_file(args.local, args.remote)
        elif args.action == "download":
            result = server.download_file(args.remote, args.local)
        else:
            parser.print_help()
            sys.exit(1)
        
        # 输出结果
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("success", True) else 1)
        
    finally:
        server.close()


if __name__ == "__main__":
    main()
