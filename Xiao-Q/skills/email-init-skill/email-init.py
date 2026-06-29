import imaplib
import smtplib
import email
import re
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any
from datetime import datetime
from openclaw import skill, message

# ==============================================
# QClaw 平台大模型调用
# ==============================================
def llm_chat(prompt: str, system: str = "") -> str:
    try:
        from qclaw import llm
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = llm.chat(messages)
        return resp.choices[0].message.content.strip()
    except:
        return "模型调用异常，请稍后再试"

# ==============================================
# 邮箱服务商自动配置
# ==============================================
def get_email_server_config(email_account):
    domain = email_account.strip().lower().split('@')[-1] if '@' in email_account else ""
    config = {
        "imap_server": f"imap.{domain}",
        "smtp_server": f"smtp.{domain}",
        "smtp_port": 465,
        "imap_port": 993,
        "spam_folders": ["Junk", "Spam", "垃圾箱", "垃圾邮件"]
    }
    preset = {
        "qq.com": {"imap_server": "imap.qq.com", "smtp_server": "smtp.qq.com", "spam_folders": ["Junk", "Spam"]},
        "163.com": {"imap_server": "imap.163.com", "smtp_server": "smtp.163.com"},
        "126.com": {"imap_server": "imap.126.com", "smtp_server": "smtp.126.com"},
        "gmail.com": {"imap_server": "imap.gmail.com", "smtp_server": "smtp.gmail.com", "spam_folders": ["[Gmail]/Spam"]},
        "outlook.com": {"imap_server": "imap-mail.outlook.com", "smtp_server": "smtp-mail.outlook.com"},
        "hotmail.com": {"imap_server": "imap-mail.outlook.com", "smtp_server": "smtp-mail.outlook.com"},
    }
    if domain in preset:
        config.update(preset[domain])
    return config

# ==============================================
# 邮件客户端
# ==============================================
class EmailClient:
    def __init__(self, account: Dict):
        self.account = account
        self.email = account["email_account"]
        self.auth_code = account["email_auth_code"]
        server_cfg = get_email_server_config(self.email)
        self.imap_server = account.get("imap_server") or server_cfg["imap_server"]
        self.smtp_server = account.get("smtp_server") or server_cfg["smtp_server"]
        self.spam_folders = server_cfg["spam_folders"]
        self.imap = None
        self.smtp = None

    def connect_imap(self):
        if self.imap: return
        self.imap = imaplib.IMAP4_SSL(self.imap_server, 993)
        self.imap.login(self.email, self.auth_code)

    def connect_smtp(self):
        if self.smtp: return
        self.smtp = smtplib.SMTP_SSL(self.smtp_server, 465)
        self.smtp.login(self.email, self.auth_code)

    def decode_str(self, s):
        if not s: return ""
        v, c = decode_header(s)[0]
        try:
            return v.decode(c or "utf-8")
        except:
            return str(v)

    def parse_email(self, msg_id):
        _, data = self.imap.fetch(msg_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        return {
            "id": msg_id.decode(),
            "subject": self.decode_str(msg.get("Subject", "")),
            "sender": self.decode_str(msg.get("From", "")),
            "date": self.decode_str(msg.get("Date", "")),
            "body": self._get_body(msg)
        }

    def _get_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        body = part.get_payload(decode=True).decode("gbk", "ignore")
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = part.get_payload(decode=True).decode("gbk", "ignore")
        return re.sub(r"\s+", " ", body).strip()

    def get_unread(self, limit=8):
        self.connect_imap()
        self.imap.select("INBOX")
        _, ids = self.imap.search(None, "UNSEEN")
        ids = ids[0].split()[-limit:] if ids[0] else []
        return [self.parse_email(i) for i in ids]

    def mark_seen(self, msg_id):
        self.connect_imap()
        self.imap.select("INBOX")
        self.imap.store(msg_id, "+FLAGS", "\\Seen")

    def send_email(self, to_addr, subject, content):
        self.connect_smtp()
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain", "utf-8"))
        self.smtp.sendmail(self.email, to_addr, msg.as_string())

    # ==============================================
    # 垃圾邮件判断
    # ==============================================
    def is_spam(self, mail, spam_kws, white_list):
        sub = mail["subject"].lower()
        sender = mail["sender"].lower()
        body = mail["body"].lower()
        for w in white_list:
            if w.strip().lower() in sender:
                return False
        for kw in spam_kws:
            kw = kw.strip().lower()
            if kw and (kw in sub or kw in body):
                return True
        return False

    # ==============================================
    # 自动删除垃圾邮件
    # ==============================================
    def auto_delete_spam(self, config):
        if not config.get("auto_delete_spam", True):
            return 0
        spam_kws = config.get("spam_keywords", [])
        white_list = config.get("spam_white_list", [])
        deleted = 0
        self.connect_imap()

        # 清理收件箱内垃圾
        self.imap.select("INBOX", readonly=False)
        _, msg_ids = self.imap.search(None, "ALL")
        for mid in msg_ids[0].split():
            try:
                mail = self.parse_email(mid)
                if self.is_spam(mail, spam_kws, white_list):
                    self.imap.store(mid, "+FLAGS", "\\Deleted")
                    deleted += 1
            except:
                continue
        self.imap.expunge()

        # 清理系统垃圾箱
        for folder in self.spam_folders:
            try:
                self.imap.select(folder, readonly=False)
                _, ids = self.imap.search(None, "ALL")
                for mid in ids[0].split():
                    self.imap.store(mid, "+FLAGS", "\\Deleted")
                    deleted += 1
                self.imap.expunge()
            except:
                continue
        return deleted

    def close(self):
        try:
            if self.imap: self.imap.logout()
            if self.smtp: self.smtp.quit()
        except:
            pass

# ==============================================
# 多邮箱管理
# ==============================================
def get_accounts(config):
    return config.get("email_accounts", [])

def current_account(ctx):
    accounts = get_accounts(ctx.user.config)
    if not accounts: return None
    idx = ctx.user.state.get("acc_idx", 0)
    return accounts[max(0, min(idx, len(accounts)-1))]

# ==============================================
# 邮件过滤
# ==============================================
def filter_emails(emails, keywords, senders):
    res = []
    for e in emails:
        txt = (e["subject"] + e["body"]).lower()
        sender_ok = not senders or any(s.strip().lower() in e["sender"].lower() for s in senders)
        kw_ok = not keywords or any(kw.strip().lower() in txt for kw in keywords)
        if sender_ok and kw_ok:
            res.append(e)
    return res

# ==============================================
# 1. 查询未读 & 总结
# ==============================================
@skill.intent("查询未读邮件", "查看未读", "邮件总结", "工作邮件", "重要邮件")
def check(ctx):
    acc = current_account(ctx)
    if not acc:
        return ctx.reply("请先配置邮箱账号")
    client = EmailClient(acc)
    try:
        del_cnt = client.auto_delete_spam(ctx.user.config)
        emails = client.get_unread(8)
        filtered = filter_emails(emails,
                                ctx.user.config.get("filter_keywords", []),
                                ctx.user.config.get("filter_senders", []))
        for e in filtered:
            client.mark_seen(e["id"])
        if not filtered:
            return ctx.reply(f"📭 暂无重要未读邮件\n🗑️ 本次清理垃圾：{del_cnt} 封")
        prompt = "请简洁总结以下工作邮件，突出事项、待办、时间：\n\n"
        for i, e in enumerate(filtered, 1):
            prompt += f"{i}. {e['subject']}\n{e['body'][:400]}\n\n"
        summary = llm_chat(prompt)
        return ctx.reply(f"✅ {len(filtered)} 封重要邮件（已标记已读）\n🗑️ 清理垃圾：{del_cnt} 封\n\n{summary}")
    finally:
        client.close()

# ==============================================
# 2. 智能回复
# ==============================================
@skill.intent("智能回复", "帮我回邮件", "回复邮件")
def reply(ctx):
    acc = current_account(ctx)
    if not acc: return ctx.reply("请先配置邮箱")
    client = EmailClient(acc)
    try:
        emails = client.get_unread(3)
        if not emails: return ctx.reply("暂无未读邮件")
        target = emails[0]
        hist = [m.content for m in ctx.messages[-4:]]
        prompt = f"""
邮件主题：{target['subject']}
发件人：{target['sender']}
内容：{target['body']}
用户语气：{hist}
请生成可直接发送的专业礼貌回复正文。
"""
        reply_text = llm_chat(prompt, system="你是专业邮件助手")
        return ctx.reply(f"📝 回复建议：\n{reply_text}")
    finally:
        client.close()

# ==============================================
# 3. 发送邮件
# ==============================================
@skill.intent("发送邮件", "写邮件", "发邮件给")
def send(ctx):
    acc = current_account(ctx)
    if not acc: return ctx.reply("请先配置邮箱")
    parts = ctx.input.text.split("|", 2)
    if len(parts) < 3:
        return ctx.reply("格式：发送邮件 收件人|主题|内容")
    to, sub, content = parts
    client = EmailClient(acc)
    try:
        client.send_email(to.strip(), sub.strip(), content.strip())
        return ctx.reply(f"✅ 已发送至：{to}")
    except Exception as e:
        return ctx.reply(f"发送失败：{str(e)}")
    finally:
        client.close()

# ==============================================
# 4. 邮箱切换
# ==============================================
@skill.intent("切换邮箱", "换邮箱")
def switch(ctx):
    accounts = get_accounts(ctx.user.config)
    if len(accounts) < 2:
        return ctx.reply("仅配置了一个邮箱")
    new_idx = (ctx.user.state.get("acc_idx", 0) + 1) % len(accounts)
    ctx.user.state["acc_idx"] = new_idx
    return ctx.reply(f"✅ 已切换：{accounts[new_idx]['email_account']}")

@skill.intent("邮箱列表")
def list_acc(ctx):
    accounts = get_accounts(ctx.user.config)
    if not accounts: return ctx.reply("暂无配置邮箱")
    txt = "\n".join(f"{i+1}. {a['email_account']}" for i, a in enumerate(accounts))
    return ctx.reply(f"📧 已配置邮箱：\n{txt}")

# ==============================================
# 5. 手动清理垃圾
# ==============================================
@skill.intent("清理垃圾邮件", "删除垃圾邮件")
def clean_spam(ctx):
    acc = current_account(ctx)
    if not acc: return ctx.reply("请先配置邮箱")
    client = EmailClient(acc)
    try:
        cnt = client.auto_delete_spam(ctx.user.config)
        return ctx.reply(f"🗑️ 已清理垃圾邮件：{cnt} 封")
    finally:
        client.close()

# ==============================================
# 每日凌晨定时自动清理
# ==============================================
@skill.cron("0 0 * * *")
def cron_daily_cleanup(ctx):
    user_cfg = ctx.user.config
    if not user_cfg.get("auto_delete_spam", True):
        return
    accounts = get_accounts(user_cfg)
    total = 0
    for acc in accounts:
        try:
            client = EmailClient(acc)
            cnt = client.auto_delete_spam(user_cfg)
            total += cnt
            client.close()
        except:
            continue

# ==============================================
# 配置页面
# ==============================================
@skill.config
def config():
    return {
        "type": "object",
        "properties": {
            "email_accounts": {
                "type": "array",
                "title": "多邮箱配置",
                "items": {
                    "type": "object",
                    "properties": {
                        "email_account": {"title": "邮箱账号", "type": "string"},
                        "email_auth_code": {"title": "授权码", "type": "string"},
                        "imap_server": {"title": "IMAP(可选)", "type": "string"},
                        "smtp_server": {"title": "SMTP(可选)", "type": "string"}
                    },
                    "required": ["email_account", "email_auth_code"]
                }
            },
            "filter_keywords": {
                "type": "array",
                "title": "工作/重要关键词",
                "default": ["会议","通知","合同","项目","工作","重要","紧急","审批"]
            },
            "filter_senders": {
                "type": "array",
                "title": "发件人过滤（只看）",
                "default": []
            },
            "auto_delete_spam": {
                "type": "boolean",
                "title": "自动删除垃圾邮件",
                "default": True
            },
            "spam_keywords": {
                "type": "array",
                "title": "垃圾邮件关键词",
                "default": ["中奖","免费领","刷单","返利","赌博","色情","发票","贷款","办卡","广告"]
            },
            "spam_white_list": {
                "type": "array",
                "title": "发件人白名单（不删）",
                "default": ["qq.com","163.com","126.com","gmail.com","outlook.com"]
            }
        }
    }