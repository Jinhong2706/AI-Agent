import json
import os
import smtplib
import sys
import argparse
from email.mime.text import MIMEText
from datetime import datetime


def write_send_log(receiver: str, subject: str, content: str, status: str):
    log_path = os.path.join(os.path.dirname(__file__), "emailSend.log")
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_content = f"[{now_time}] 收件人: {receiver} | 主题: {subject} | 状态: {status} | 内容: {content}\n"
    

    try:
        with open(log_path, "a+", encoding="utf-8") as f:
            f.write(log_content)
    except Exception:
        pass

def load_config(config_path: str = os.path.join(os.path.dirname(__file__), "lib/config.json")) -> dict:
    if not os.path.exists(config_path):
        return "[OpenClaw] 错误：配置文件不存在！路径：" + config_path
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return "[OpenClaw] 错误：配置文件 JSON 语法错误！"
    except Exception as e:
        return f"[OpenClaw] 错误：配置加载失败：{str(e)}"


def send_email(receiver: str, subject: str, content: str):
    config = load_config()
    if isinstance(config, str):
        # 新增：配置加载失败，记录失败日志
        write_send_log(receiver, subject, content, "配置加载失败")
        return config

    base_cfg = config["BaseConfig"]
    sender_cfg = config["SenderConfig"]
    default_cfg = config["DefaultConfig"]

    smtp_host = base_cfg["QemailSMTPDress"]
    smtp_port = int(base_cfg["QemailSMTPort"])
    smtp_timeout = int(base_cfg["QEmailSMTPtimeout"])
    
    send_email_addr = sender_cfg["QemailSender"]
    send_email_pass = sender_cfg["QemailPass"]
    sender_alias = sender_cfg["AliasSenderName"]
    
    subject_prefix = default_cfg["DefaultSubjectPrefix"]
    reply_email = default_cfg["DefaultReplayEmailDress"]

    try:
        full_subject = f"{subject_prefix} | {subject}"
        msg = MIMEText(content, "plain", "utf-8")
        
        msg["Subject"] = full_subject
        msg["From"] = f"{sender_alias} <{send_email_addr}>"  
        msg["To"] = receiver
        msg["Reply-To"] = reply_email 

        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=smtp_timeout) as server:
            server.login(send_email_addr, send_email_pass)
            server.sendmail(send_email_addr, receiver, msg.as_string())

        write_send_log(receiver, subject, content, "发送成功")
        return "✅ 邮件发送成功！"

    except smtplib.SMTPAuthenticationError:
        write_send_log(receiver, subject, content, "授权码错误/失效")
        return "❌ 发送失败：QQ邮箱授权码错误/已失效"
    except smtplib.SMTPConnectError:
        write_send_log(receiver, subject, content, "SMTP服务器连接失败")
        write_send_log(receiver, subject, content, "发送失败")
        return "❌ 发送失败：SMTP服务器连接失败"
    except Exception as e:
        write_send_log(receiver, subject, content, f"发送失败({str(e)})")
        return f"❌ 发送失败：{str(e)}"


def interactive_mode():
    print("===== OpenClaw send-txmail 邮件技能（交互模式）=====")
    
    receiver = input("OpenClaw：请输入收件人邮箱 → ")
    if not receiver:
        print("OpenClaw：错误！收件人邮箱不能为空")
        return

    subject = input("OpenClaw：请输入邮件主题 → ")
    if not subject:
        print("OpenClaw：错误！邮件主题不能为空")
        return

    content = input("OpenClaw：请输入邮件内容 → ")
    if not content:
        print("OpenClaw：错误！邮件内容不能为空")
        return

    print("\nOpenClaw：正在发送邮件，请稍候...")
    result = send_email(receiver, subject, content)
    print(f"\n{result}")

def cli_mode(to, subject, content, debug=False):
    if debug:
        print("===== OpenClaw send-txmail 邮件技能（命令行模式，调试中）=====")
        print(f"收件人：{to}")
        print(f"主题：{subject}")
        print(f"内容：{content}")
    
    print("\n正在发送邮件，请稍候...")
    # 修复：去掉多余的debug参数
    result = send_email(to, subject, content)
    print(f"\n{result}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='OpenClaw 邮件发送技能')
    parser.add_argument('--to', help='收件人邮箱地址')
    parser.add_argument('--subject', help='邮件主题')
    parser.add_argument('--content', help='邮件正文内容')
    parser.add_argument('--interactive', '-i', action='store_true', help='使用交互式模式')
    parser.add_argument('--debug', '-d', action='store_true', help='调试模式，显示详细信息')
    
    args = parser.parse_args()
    
    if args.interactive or (not args.to and not args.subject and not args.content):
        interactive_mode()
    elif args.to and args.subject and args.content:
        cli_mode(args.to, args.subject, args.content, args.debug)
    else:
        print("❌ 使用方式错误！")
        print("\n使用方式：")
        print("  1. 交互模式：python3 send-txmail.py")
        print("  2. 交互模式（显式）：python3 send-txmail.py --interactive")
        print("  3. 命令行模式：python3 send-txmail.py --to '邮箱' --subject '主题' --content '内容'")
        print("  4. 命令行模式带调试：python3 send-txmail.py --to '邮箱' --subject '主题' --content '内容' --debug")
        print("\n示例：")
        print("  python3 send-txmail.py --to 'example@qq.com' --subject '测试' --content '这是一个测试邮件'")
        sys.exit(1)

if __name__ == "__main__":
    main()