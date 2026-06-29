#!/usr/bin/env python3
"""
QQ群管理 CLI 工具
基于腾讯云IM REST API 和 QQ机器人开放平台 API

用法:
  qq-group-cli schema <domain>.<action>          # 查看参数定义
  qq-group-cli manage <action> [flags]            # 群组管理
  qq-group-cli member <action> [flags]            # 成员管理
  qq-group-cli login --json                       # 登录/检查状态
  qq-group-cli version                            # 版本信息
"""

import argparse
import json
import os
import sys
import time
import hashlib
import random
import hmac
import base64
import urllib.parse
import urllib.request
import urllib.error
import configparser
from pathlib import Path

VERSION = "1.0.0"

# ── 配置路径 ──
CONFIG_DIR = Path.home() / ".qqgroup-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ── API 域名 ──
IM_API_HOST = "console.tim.qq.com"
QQBOT_API_HOST = "https://api.sgroup.qq.com"
QQBOT_SANDBOX_HOST = "https://sandbox.api.sgroup.qq.com"

# ── Schema 定义 ──
SCHEMAS = {
    # ── 群组管理 ──
    "manage.create-group": {
        "flags": [
            {"name": "type", "type": "str", "required": True, "enum": ["Public", "Private", "ChatRoom", "AVChatRoom", "Community"], "desc": "群组类型: Public(陌生人社交群), Private(好友工作群), ChatRoom(会议群), AVChatRoom(直播群), Community(社群)"},
            {"name": "name", "type": "str", "required": True, "desc": "群名称，最长100字节(UTF-8)"},
            {"name": "owner-account", "type": "str", "required": False, "desc": "群主ID"},
            {"name": "group-id", "type": "str", "required": False, "desc": "自定义群组ID"},
            {"name": "introduction", "type": "str", "required": False, "desc": "群简介，最长400字节"},
            {"name": "notification", "type": "str", "required": False, "desc": "群公告，最长400字节"},
            {"name": "face-url", "type": "str", "required": False, "desc": "群头像URL"},
            {"name": "max-member-num", "type": "int", "required": False, "desc": "最大群成员数量"},
            {"name": "apply-join-option", "type": "str", "required": False, "enum": ["FreeAccess", "NeedPermission", "DisableApply"], "desc": "申请加群方式: FreeAccess(自由加入), NeedPermission(需要验证), DisableApply(禁止加群)"},
            {"name": "member-list", "type": "json", "required": False, "desc": "初始群成员列表(JSON数组), 例: [{\"Member_Account\":\"user1\",\"Role\":\"Admin\"}]"},
        ],
        "example": 'qq-group-cli manage create-group --type Public --name "我的群" --introduction "群简介"'
    },
    "manage.get-group-info": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
        ],
        "example": 'qq-group-cli manage get-group-info --group-id "@TGS#xxx"'
    },
    "manage.get-group-list": {
        "flags": [
            {"name": "limit", "type": "int", "required": False, "default": 10000, "desc": "一次最多获取的群组数量"},
            {"name": "group-type", "type": "str", "required": False, "enum": ["Public", "Private", "ChatRoom", "AVChatRoom", "Community"], "desc": "按群组类型过滤"},
            {"name": "next", "type": "str", "required": False, "desc": "分页签，从上次返回的 Next 值开始获取"},
        ],
        "example": "qq-group-cli manage get-group-list --limit 50"
    },
    "manage.modify-group-base-info": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "name", "type": "str", "required": False, "desc": "群名称"},
            {"name": "introduction", "type": "str", "required": False, "desc": "群简介"},
            {"name": "notification", "type": "str", "required": False, "desc": "群公告"},
            {"name": "face-url", "type": "str", "required": False, "desc": "群头像URL"},
            {"name": "max-member-num", "type": "int", "required": False, "desc": "最大群成员数量"},
            {"name": "apply-join-option", "type": "str", "required": False, "enum": ["FreeAccess", "NeedPermission", "DisableApply"], "desc": "申请加群方式"},
            {"name": "mute-all-member", "type": "str", "required": False, "enum": ["On", "Off"], "desc": "全员禁言: On(开启), Off(关闭)"},
        ],
        "example": 'qq-group-cli manage modify-group-base-info --group-id "@TGS#xxx" --name "新群名" --notification "新公告"'
    },
    "manage.search-group": {
        "flags": [
            {"name": "keyword", "type": "str", "required": True, "desc": "搜索关键字"},
            {"name": "group-type", "type": "str", "required": False, "enum": ["Public", "Private", "ChatRoom", "AVChatRoom", "Community"], "desc": "按群组类型过滤"},
            {"name": "limit", "type": "int", "required": False, "default": 20, "desc": "返回数量"},
        ],
        "example": 'qq-group-cli manage search-group --keyword "技术交流"'
    },
    "manage.join-group": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "申请加入的用户ID"},
            {"name": "reason", "type": "str", "required": False, "desc": "申请理由"},
        ],
        "example": 'qq-group-cli manage join-group --group-id "@TGS#xxx" --account user1 --reason "想加入群聊"'
    },
    "manage.quit-group": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "退出群组的用户ID"},
        ],
        "example": 'qq-group-cli manage quit-group --group-id "@TGS#xxx" --account user1'
    },
    "manage.dismiss-group": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
        ],
        "example": 'qq-group-cli manage dismiss-group --group-id "@TGS#xxx"'
    },
    "manage.get-join-application": {
        "flags": [
            {"name": "group-id", "type": "str", "required": False, "desc": "群组ID, 不填则获取所有加群申请"},
        ],
        "example": 'qq-group-cli manage get-join-application --group-id "@TGS#xxx"'
    },
    # ── 成员管理 ──
    "member.get-member-list": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "limit", "type": "int", "required": False, "default": 6000, "desc": "一次最多获取的成员数量"},
            {"name": "offset", "type": "int", "required": False, "default": 0, "desc": "偏移量"},
            {"name": "role-filter", "type": "str", "required": False, "enum": ["Owner", "Admin", "Member"], "desc": "按角色过滤"},
        ],
        "example": 'qq-group-cli member get-member-list --group-id "@TGS#xxx" --limit 100'
    },
    "member.get-member-info": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "要查询的用户ID(多个用逗号分隔)"},
        ],
        "example": 'qq-group-cli member get-member-info --group-id "@TGS#xxx" --account user1,user2'
    },
    "member.mute-member": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "要禁言的用户ID(多个用逗号分隔,最多500)"},
            {"name": "duration", "type": "int", "required": False, "default": 1800, "desc": "禁言时长(秒), 0为取消禁言"},
        ],
        "example": 'qq-group-cli member mute-member --group-id "@TGS#xxx" --account user1 --duration 3600'
    },
    "member.mute-all": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "mute-all-member", "type": "str", "required": True, "enum": ["On", "Off"], "desc": "On=开启全员禁言, Off=关闭全员禁言"},
        ],
        "example": 'qq-group-cli member mute-all --group-id "@TGS#xxx" --mute-all-member On'
    },
    "member.kick-member": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "要踢出的用户ID(多个用逗号分隔)"},
            {"name": "reason", "type": "str", "required": False, "desc": "踢出原因"},
        ],
        "example": 'qq-group-cli member kick-member --group-id "@TGS#xxx" --account user1 --reason "违规"'
    },
    "member.set-member-role": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "用户ID"},
            {"name": "role", "type": "str", "required": True, "enum": ["Admin", "Member"], "desc": "目标角色: Admin(管理员), Member(普通成员)"},
        ],
        "example": 'qq-group-cli member set-member-role --group-id "@TGS#xxx" --account user1 --role Admin'
    },
    "member.modify-member-info": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "用户ID"},
            {"name": "name-card", "type": "str", "required": False, "desc": "群名片"},
            {"name": "custom-data", "type": "json", "required": False, "desc": "自定义字段(JSON数组), 例: [{\"Key\":\"key1\",\"Value\":\"val1\"}]"},
        ],
        "example": 'qq-group-cli member modify-member-info --group-id "@TGS#xxx" --account user1 --name-card "新名片"'
    },
    "member.invite-member": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "要邀请的用户ID(多个用逗号分隔)"},
        ],
        "example": 'qq-group-cli member invite-member --group-id "@TGS#xxx" --account user1,user2'
    },
    "member.transfer-owner": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
            {"name": "account", "type": "str", "required": True, "desc": "新群主ID"},
        ],
        "example": 'qq-group-cli member transfer-owner --group-id "@TGS#xxx" --account newowner'
    },
    "member.get-online-count": {
        "flags": [
            {"name": "group-id", "type": "str", "required": True, "desc": "群组ID"},
        ],
        "example": 'qq-group-cli member get-online-count --group-id "@TGS#xxx"'
    },
}


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    """保存配置文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def gen_usersig(sdk_app_id, key, identifier, expire=86400*180):
    """
    生成 UserSig (HMAC-SHA256 签方案)
    基于 Tencent Cloud IM 的签名算法
    """
    curr_time = int(time.time())
    doc = {
        "TLS.identifier": identifier,
        "TLS.sdkappid": sdk_app_id,
        "TLS.expire": expire,
        "TLS.time": curr_time,
    }
    content_to_sign = "".join([
        f"TLS.identifier:{identifier}",
        f"TLS.sdkappid:{sdk_app_id}",
        f"TLS.expire:{expire}",
        f"TLS.time:{curr_time}",
    ])
    sig = hmac.new(key.encode("utf-8"), content_to_sign.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.b64encode(sig).decode("utf-8")
    doc["TLS.sig"] = sig_b64
    doc_json = json.dumps(doc, separators=(",", ":"))
    # URL-safe base64
    encoded = base64.b64encode(doc_json.encode("utf-8")).decode("utf-8")
    return encoded.replace("+", "!").replace("/", "*").replace("=", "_")


def get_im_api_url(service, command):
    """构建腾讯云IM REST API URL"""
    cfg = load_config()
    sdk_app_id = cfg.get("sdk_app_id", "")
    identifier = cfg.get("identifier", "administrator")
    user_sig = cfg.get("user_sig", "")

    # 如果没有缓存的 user_sig，尝试自动生成
    if not user_sig and cfg.get("secret_key"):
        user_sig = gen_usersig(
            int(sdk_app_id),
            cfg["secret_key"],
            identifier
        )
        cfg["user_sig"] = user_sig
        cfg["user_sig_time"] = int(time.time())
        save_config(cfg)

    random_val = random.randint(0, 4294967295)
    url = (
        f"https://{IM_API_HOST}/v4/{service}/{command}"
        f"?sdkappid={sdk_app_id}"
        f"&identifier={identifier}"
        f"&usersig={user_sig}"
        f"&random={random_val}"
        f"&contenttype=json"
    )
    return url


def get_qqbot_token():
    """获取QQ机器人AccessToken"""
    cfg = load_config()
    app_id = cfg.get("qqbot_app_id", "")
    app_secret = cfg.get("qqbot_app_secret", "")
    token = cfg.get("qqbot_access_token", "")
    token_expire = cfg.get("qqbot_token_expire", 0)

    if token and int(time.time()) < token_expire:
        return token

    if not app_id or not app_secret:
        return None

    url = "https://bots.qq.com/app/getAppAccessToken"
    data = json.dumps({
        "appId": app_id,
        "clientSecret": app_secret,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        token = result.get("access_token", "")
        expires_in = int(result.get("expires_in", 7200))
        cfg["qqbot_access_token"] = token
        cfg["qqbot_token_expire"] = int(time.time()) + expires_in - 60
        save_config(cfg)
        return token
    except Exception as e:
        print(json.dumps({"error": f"获取AccessToken失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        return None


def im_api_call(service, command, body, method="POST"):
    """调用腾讯云IM REST API"""
    url = get_im_api_url(service, command)
    data = json.dumps(body).encode("utf-8") if body else b""
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return {"ActionStatus": "FAIL", "ErrorCode": e.code, "ErrorInfo": body_text}
    except Exception as e:
        return {"ActionStatus": "FAIL", "ErrorCode": -1, "ErrorInfo": str(e)}


def qqbot_api_call(path, body=None, method="GET"):
    """调用QQ机器人开放平台API"""
    cfg = load_config()
    sandbox = cfg.get("qqbot_sandbox", False)
    base = QQBOT_SANDBOX_HOST if sandbox else QQBOT_API_HOST
    url = f"{base}{path}"
    token = get_qqbot_token()
    if not token:
        return {"error": "未配置QQ机器人凭证，请先执行 qq-group-cli login"}

    headers = {
        "Authorization": f"QQBot {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}", "detail": body_text}
    except Exception as e:
        return {"error": str(e)}


# ── 群组管理操作 ──
def manage_create_group(args):
    body = {"Type": args.type, "Name": args.name}
    if args.owner_account:
        body["Owner_Account"] = args.owner_account
    if args.group_id:
        body["GroupId"] = args.group_id
    if args.introduction:
        body["Introduction"] = args.introduction
    if args.notification:
        body["Notification"] = args.notification
    if args.face_url:
        body["FaceUrl"] = args.face_url
    if args.max_member_num:
        body["MaxMemberNum"] = args.max_member_num
    if args.apply_join_option:
        body["ApplyJoinOption"] = args.apply_join_option
    if args.member_list:
        body["MemberList"] = json.loads(args.member_list)
    return im_api_call("group_open_http_svc", "create_group", body)


def manage_get_group_info(args):
    body = {"GroupIdList": [args.group_id]}
    return im_api_call("group_open_http_svc", "get_group_info", body)


def manage_get_group_list(args):
    body = {"Limit": args.limit}
    if args.group_type:
        body["GroupType"] = args.group_type
    if args.next:
        body["Next"] = args.next
    return im_api_call("group_open_http_svc", "get_appid_group_list", body)


def manage_modify_group_base_info(args):
    body = {"GroupId": args.group_id}
    if args.name:
        body["Name"] = args.name
    if args.introduction:
        body["Introduction"] = args.introduction
    if args.notification:
        body["Notification"] = args.notification
    if args.face_url:
        body["FaceUrl"] = args.face_url
    if args.max_member_num:
        body["MaxMemberNum"] = args.max_member_num
    if args.apply_join_option:
        body["ApplyJoinOption"] = args.apply_join_option
    if args.mute_all_member:
        body["MuteAllMember"] = args.mute_all_member
    return im_api_call("group_open_http_svc", "modify_group_base_info", body)


def manage_search_group(args):
    body = {
        "Keyword": args.keyword,
    }
    if args.group_type:
        body["GroupType"] = args.group_type
    return im_api_call("group_open_http_svc", "search_group", body)


def manage_join_group(args):
    body = {
        "GroupId": args.group_id,
        "ApplyToJoin": {
            "ApplyReason": args.reason or "",
        }
    }
    # 通过 QQ Bot API 申请加群
    return qqbot_api_call(f"/v2/groups/{args.group_id}/members", body, method="POST")


def manage_quit_group(args):
    body = {"GroupId": args.group_id}
    return im_api_call("group_open_http_svc", "quit_group", body)


def manage_dismiss_group(args):
    body = {"GroupId": args.group_id}
    return im_api_call("group_open_http_svc", "destroy_group", body)


def manage_get_join_application(args):
    body = {}
    if args.group_id:
        body["GroupId"] = args.group_id
    return im_api_call("group_open_http_svc", "get_group_application", body)


# ── 成员管理操作 ──
def member_get_member_list(args):
    body = {"GroupId": args.group_id, "Limit": args.limit, "Offset": args.offset}
    if args.role_filter:
        body["RoleFilter"] = args.role_filter
    return im_api_call("group_open_http_svc", "get_group_member_info", body)


def member_get_member_info(args):
    accounts = [a.strip() for a in args.account.split(",")]
    body = {
        "GroupId": args.group_id,
        "MemberList": [{"Member_Account": a} for a in accounts],
    }
    return im_api_call("group_open_http_svc", "get_group_member_info", body)


def member_mute_member(args):
    accounts = [a.strip() for a in args.account.split(",")]
    body = {
        "GroupId": args.group_id,
        "Members_Account": accounts,
        "MuteTime": args.duration,
    }
    return im_api_call("group_open_http_svc", "forbid_send_msg", body)


def member_mute_all(args):
    body = {
        "GroupId": args.group_id,
        "MuteAllMember": args.mute_all_member,
    }
    return im_api_call("group_open_http_svc", "modify_group_base_info", body)


def member_kick_member(args):
    accounts = [a.strip() for a in args.account.split(",")]
    body = {
        "GroupId": args.group_id,
        "MemberToDel_Account": accounts,
    }
    if args.reason:
        body["Reason"] = args.reason
    return im_api_call("group_open_http_svc", "delete_group_member", body)


def member_set_member_role(args):
    body = {
        "GroupId": args.group_id,
        "Member_Account": args.account,
        "Role": args.role,
    }
    return im_api_call("group_open_http_svc", "modify_group_member_info", body)


def member_modify_member_info(args):
    body = {"GroupId": args.group_id, "Member_Account": args.account}
    if args.name_card:
        body["NameCard"] = args.name_card
    if args.custom_data:
        body["AppMemberDefinedData"] = json.loads(args.custom_data)
    return im_api_call("group_open_http_svc", "modify_group_member_info", body)


def member_invite_member(args):
    accounts = [a.strip() for a in args.account.split(",")]
    body = {
        "GroupId": args.group_id,
        "InvitedAccountList": [{"Member_Account": a} for a in accounts],
    }
    return im_api_call("group_open_http_svc", "add_group_member", body)


def member_transfer_owner(args):
    body = {
        "GroupId": args.group_id,
        "NewOwner_Account": args.account,
    }
    return im_api_call("group_open_http_svc", "change_group_owner", body)


def member_get_online_count(args):
    body = {"GroupId": args.group_id}
    return im_api_call("group_open_http_svc", "get_group_online_member_num", body)


# ── 命令路由表 ──
MANAGE_ACTIONS = {
    "create-group": (manage_create_group, [
        ("--type", {"required": True}),
        ("--name", {"required": True}),
        ("--owner-account", {}),
        ("--group-id", {}),
        ("--introduction", {}),
        ("--notification", {}),
        ("--face-url", {}),
        ("--max-member-num", {"type": int}),
        ("--apply-join-option", {}),
        ("--member-list", {}),
    ]),
    "get-group-info": (manage_get_group_info, [
        ("--group-id", {"required": True}),
    ]),
    "get-group-list": (manage_get_group_list, [
        ("--limit", {"type": int, "default": 10000}),
        ("--group-type", {}),
        ("--next", {}),
    ]),
    "modify-group-base-info": (manage_modify_group_base_info, [
        ("--group-id", {"required": True}),
        ("--name", {}),
        ("--introduction", {}),
        ("--notification", {}),
        ("--face-url", {}),
        ("--max-member-num", {"type": int}),
        ("--apply-join-option", {}),
        ("--mute-all-member", {}),
    ]),
    "search-group": (manage_search_group, [
        ("--keyword", {"required": True}),
        ("--group-type", {}),
        ("--limit", {"type": int, "default": 20}),
    ]),
    "join-group": (manage_join_group, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
        ("--reason", {}),
    ]),
    "quit-group": (manage_quit_group, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
    ]),
    "dismiss-group": (manage_dismiss_group, [
        ("--group-id", {"required": True}),
    ]),
    "get-join-application": (manage_get_join_application, [
        ("--group-id", {}),
    ]),
}

MEMBER_ACTIONS = {
    "get-member-list": (member_get_member_list, [
        ("--group-id", {"required": True}),
        ("--limit", {"type": int, "default": 6000}),
        ("--offset", {"type": int, "default": 0}),
        ("--role-filter", {}),
    ]),
    "get-member-info": (member_get_member_info, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
    ]),
    "mute-member": (member_mute_member, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
        ("--duration", {"type": int, "default": 1800}),
    ]),
    "mute-all": (member_mute_all, [
        ("--group-id", {"required": True}),
        ("--mute-all-member", {"required": True}),
    ]),
    "kick-member": (member_kick_member, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
        ("--reason", {}),
    ]),
    "set-member-role": (member_set_member_role, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
        ("--role", {"required": True}),
    ]),
    "modify-member-info": (member_modify_member_info, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
        ("--name-card", {}),
        ("--custom-data", {}),
    ]),
    "invite-member": (member_invite_member, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
    ]),
    "transfer-owner": (member_transfer_owner, [
        ("--group-id", {"required": True}),
        ("--account", {"required": True}),
    ]),
    "get-online-count": (member_get_online_count, [
        ("--group-id", {"required": True}),
    ]),
}


def cmd_schema(args):
    key = args.action
    if key not in SCHEMAS:
        print(json.dumps({"error": f"未找到 schema: {key}", "available": list(SCHEMAS.keys())}, ensure_ascii=False, indent=2))
        sys.exit(1)
    print(json.dumps(SCHEMAS[key], ensure_ascii=False, indent=2))


def cmd_login(args):
    """登录配置"""
    cfg = load_config()

    if args.json:
        print(json.dumps(cfg.get("status", {}), ensure_ascii=False, indent=2))
        return

    # 交互式配置
    print("=== QQ群管理 CLI 登录配置 ===")
    print()
    print("请选择认证方式:")
    print("1. 腾讯云IM (SDKAppID + SecretKey)")
    print("2. QQ机器人开放平台 (AppID + AppSecret)")

    choice = input("请输入选项 (1/2): ").strip()

    if choice == "1":
        sdk_app_id = input("SDKAppID: ").strip()
        secret_key = input("SecretKey: ").strip()
        identifier = input("管理员账号 (默认 administrator): ").strip() or "administrator"

        cfg["sdk_app_id"] = sdk_app_id
        cfg["secret_key"] = secret_key
        cfg["identifier"] = identifier
        cfg["auth_mode"] = "im"

        # 生成 UserSig
        user_sig = gen_usersig(int(sdk_app_id), secret_key, identifier)
        cfg["user_sig"] = user_sig
        cfg["user_sig_time"] = int(time.time())

    elif choice == "2":
        app_id = input("AppID: ").strip()
        app_secret = input("AppSecret: ").strip()
        sandbox = input("是否使用沙箱环境? (y/N): ").strip().lower() == "y"

        cfg["qqbot_app_id"] = app_id
        cfg["qqbot_app_secret"] = app_secret
        cfg["qqbot_sandbox"] = sandbox
        cfg["auth_mode"] = "qqbot"

        # 获取 AccessToken
        token = get_qqbot_token()
        if token:
            print("AccessToken 获取成功!")
        else:
            print("AccessToken 获取失败，请检查凭证")

    else:
        print("无效选项")
        sys.exit(1)

    cfg["status"] = {"logged_in": True, "auth_mode": cfg.get("auth_mode"), "login_time": int(time.time())}
    save_config(cfg)
    print("\n配置已保存!")


def cmd_login_status(args):
    """检查登录状态"""
    cfg = load_config()
    status = cfg.get("status", {})
    if status.get("logged_in"):
        print(json.dumps({"status": "logged_in", "auth_mode": status.get("auth_mode"), "login_time": status.get("login_time")}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": "not_logged_in"}, ensure_ascii=False, indent=2))


def cmd_version(args):
    print(f"qq-group-cli v{VERSION}")


def build_action_parser(subparsers, domain, actions):
    """为某个域构建子命令解析器"""
    domain_parser = subparsers.add_parser(domain, help=f"{domain} 操作")
    action_sub = domain_parser.add_subparsers(dest="action", required=True)

    for action_name, (handler, flags) in actions.items():
        p = action_sub.add_parser(action_name, help=f"{action_name}")
        for flag_name, flag_kwargs in flags:
            p.add_argument(flag_name, **flag_kwargs)
        p.set_defaults(handler=handler)


def main():
    parser = argparse.ArgumentParser(
        prog="qq-group-cli",
        description="QQ群管理 CLI 工具",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # schema
    schema_parser = subparsers.add_parser("schema", help="查看参数定义")
    schema_parser.add_argument("action", help="domain.action, 如 manage.create-group")
    schema_parser.set_defaults(handler=cmd_schema)

    # manage
    build_action_parser(subparsers, "manage", MANAGE_ACTIONS)

    # member
    build_action_parser(subparsers, "member", MEMBER_ACTIONS)

    # login
    login_parser = subparsers.add_parser("login", help="登录配置")
    login_parser.add_argument("--json", action="store_true", help="以JSON格式输出当前状态")
    login_parser.add_argument("--status", action="store_true", help="检查登录状态")
    login_parser.set_defaults(handler=cmd_login)

    # version
    version_parser = subparsers.add_parser("version", help="版本信息")
    version_parser.set_defaults(handler=cmd_version)

    args = parser.parse_args()

    if args.command == "login" and getattr(args, "status", False):
        cmd_login_status(args)
        return

    if hasattr(args, "handler"):
        result = args.handler(args)
        if isinstance(result, dict):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result is not None:
            print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
