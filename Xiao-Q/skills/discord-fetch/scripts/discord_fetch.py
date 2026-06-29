#!/usr/bin/env python3
"""Discord channel message fetcher (skill engine).

Requires Python >= 3.9.

Fetches chat messages from a Discord channel via the Discord REST API (v10)
and prints clean, structured JSON to stdout — ready to feed into a Feishu
(Lark) Bitable write step.

AUTH (in priority order):
  1. --token CLI argument
  2. DISCORD_BOT_TOKEN environment variable (recommended)

USAGE EXAMPLES:
  python discord_fetch.py --channel 1234567890123456789 --max 200
  python discord_fetch.py --channel 123... --after 1300000000000000000
  python discord_fetch.py --channel 123... --after-date 2026-01-01 --before-date 2026-02-01
  python discord_fetch.py --channel 123... --max 500 --format csv > messages.csv
  python discord_fetch.py --channel 123... --check
  python discord_fetch.py --channel 123... --info
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib import error, parse, request

DISCORD_API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (discord-fetch-skill/1.0.0)"
PAGE_SIZE = 100
HARD_MESSAGE_CAP = 5000
REQUEST_TIMEOUT = 30
MAX_429_RETRIES = 5
DISCORD_EPOCH_MS = 1420070400000


# --------------------------------------------------------------------------- #
# Snowflake helpers
# --------------------------------------------------------------------------- #

def datetime_to_snowflake(dt: datetime) -> str:
    ms = int(dt.timestamp() * 1000)
    return str((ms - DISCORD_EPOCH_MS) << 22)


def parse_date_arg(s: str, end_of_day: bool = False) -> str:
    try:
        dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        die(f"Invalid date '{s}'. Use YYYY-MM-DD format (e.g. 2026-01-01).")
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return datetime_to_snowflake(dt)


# --------------------------------------------------------------------------- #
# Token handling
# --------------------------------------------------------------------------- #

def resolve_token(cli_token: Optional[str]) -> str:
    token = (cli_token or os.environ.get("DISCORD_BOT_TOKEN") or "").strip()
    if not token:
        die(
            "No bot token found. Provide one via --token, or set the "
            "DISCORD_BOT_TOKEN environment variable (recommended)."
        )
    return token


def mask_token(token: str) -> str:
    t = token.strip()
    return "***" if len(t) <= 8 else f"{t[:4]}...{t[-4:]}"


def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def log(msg: str) -> None:
    """Progress info goes to stderr so stdout JSON/CSV stays clean."""
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def discord_get(path: str, token: str, params: Optional[dict[str, Any]] = None) -> Any:
    url = f"{DISCORD_API_BASE}{path}"
    if params:
        url = f"{url}?{parse.urlencode(params)}"
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_429_RETRIES + 1):
        req = request.Request(url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            if e.code == 429 and attempt < MAX_429_RETRIES:
                retry_after = 1.0
                try:
                    body = json.loads(e.read().decode("utf-8"))
                    retry_after = float(body.get("retry_after", 1.0))
                except Exception:
                    pass
                log(f"[rate-limit] retry after {retry_after:.1f}s (attempt {attempt+1}/{MAX_429_RETRIES})")
                time.sleep(min(retry_after, 10.0) + 0.1)
                continue
            raise
    raise RuntimeError("Exhausted 429 retries")


def explain_http_error(e: error.HTTPError, token: str) -> str:
    hints = {
        401: "Unauthorized (401): bot token is missing or invalid. Reset it in the Developer Portal.",
        403: "Forbidden (403): bot lacks access. Invite the bot and grant 'View Channel' + 'Read Message History'.",
        404: "Not found (404): wrong channel_id, or the bot cannot see this channel.",
        429: "Rate limited (429): the script auto-retries; if persistent, fetch fewer messages at a time.",
    }
    detail = ""
    try:
        body = json.loads(e.read().decode("utf-8"))
        if isinstance(body, dict) and body.get("message"):
            detail = f" Discord said: {body['message']}."
    except Exception:
        pass
    base = hints.get(e.code, f"Discord API returned HTTP {e.code}.")
    return f"{base}{detail} (token {mask_token(token)})"


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #

def run_check(channel_id: str, token: str) -> None:
    results: list[tuple[str, bool, str]] = []

    t = token.strip()
    token_ok = len(t) > 20 and "." in t
    results.append(("Token format", token_ok,
                    "looks valid" if token_ok else "token seems malformed"))

    try:
        info = discord_get(f"/channels/{channel_id}", token)
        results.append(("Channel access", True,
                        f"#{info.get('name', '?')} in guild {info.get('guild_id', '?')}"))
        if info.get("nsfw"):
            results.append(("NSFW flag", False, "channel is NSFW — confirm you intend to fetch it"))
    except error.HTTPError as e:
        results.append(("Channel access", False, explain_http_error(e, token)))

    try:
        msgs = discord_get(f"/channels/{channel_id}/messages", token, {"limit": 1})
        if msgs:
            content = msgs[0].get("content", None)
            intent_ok = content is not None and content != ""
            results.append(("Message Content Intent", intent_ok,
                            "content visible" if intent_ok else
                            "content is empty — enable 'Message Content Intent' in the Developer Portal"))
        else:
            results.append(("Message Content Intent", True, "channel is empty, cannot verify"))
    except error.HTTPError as e:
        results.append(("Message Content Intent", False, explain_http_error(e, token)))

    log("\n=== discord-fetch self-check ===")
    all_pass = True
    for name, ok, detail in results:
        icon = "OK" if ok else "FAIL"
        log(f"  [{icon}] {name}: {detail}")
        if not ok:
            all_pass = False
    log("================================")
    if all_pass:
        log("All checks passed. Ready to fetch.")
    else:
        log("One or more checks failed. Fix the issues above before fetching.")
        sys.exit(1)


# --------------------------------------------------------------------------- #
# Message shaping
# --------------------------------------------------------------------------- #

def simplify_message(msg: dict[str, Any]) -> dict[str, Any]:
    author = msg.get("author") or {}
    attachments = [
        {
            "filename": a.get("filename"),
            "url": a.get("url"),
            "size": a.get("size"),
            "content_type": a.get("content_type"),
        }
        for a in (msg.get("attachments") or [])
    ]
    embeds = [
        {
            "title": e.get("title"),
            "description": e.get("description"),
            "url": e.get("url"),
            "type": e.get("type"),
        }
        for e in (msg.get("embeds") or [])
    ]
    referenced = msg.get("referenced_message") or {}
    return {
        "message_id": msg.get("id"),
        "channel_id": msg.get("channel_id"),
        "author_id": author.get("id"),
        "author_username": author.get("username"),
        "author_global_name": author.get("global_name"),
        "is_bot": bool(author.get("bot", False)),
        "content": msg.get("content", ""),
        "timestamp": msg.get("timestamp"),
        "edited_timestamp": msg.get("edited_timestamp"),
        "reply_to_message_id": referenced.get("id"),
        "attachment_count": len(attachments),
        "attachments": attachments,
        "embed_count": len(embeds),
        "embeds": embeds,
    }


# --------------------------------------------------------------------------- #
# Fetch
# --------------------------------------------------------------------------- #

def fetch_history(
    channel_id: str,
    token: str,
    max_messages: int,
    after: Optional[str],
    before: Optional[str],
) -> dict[str, Any]:
    collected: dict[str, dict[str, Any]] = {}
    reached_end = False
    base = f"/channels/{channel_id}/messages"

    if after:
        cursor = after
        while len(collected) < max_messages:
            page = min(PAGE_SIZE, max_messages - len(collected))
            params: dict[str, Any] = {"limit": page, "after": cursor}
            if before:
                params["before"] = before
            raw = discord_get(base, token, params)
            if not raw:
                reached_end = True
                break
            for m in raw:
                collected[m["id"]] = simplify_message(m)
            log(f"[fetch] {len(collected)} messages collected...")
            cursor = str(max(int(m["id"]) for m in raw))
            if len(raw) < page:
                reached_end = True
                break
    else:
        cursor = before or None
        while len(collected) < max_messages:
            page = min(PAGE_SIZE, max_messages - len(collected))
            params = {"limit": page}
            if cursor:
                params["before"] = cursor
            raw = discord_get(base, token, params)
            if not raw:
                reached_end = True
                break
            for m in raw:
                collected[m["id"]] = simplify_message(m)
            log(f"[fetch] {len(collected)} messages collected...")
            cursor = str(min(int(m["id"]) for m in raw))
            if len(raw) < page:
                reached_end = True
                break

    messages = list(collected.values())
    messages.sort(key=lambda m: int(m["message_id"]))
    ids = [int(m["message_id"]) for m in messages]
    return {
        "channel_id": channel_id,
        "count": len(messages),
        "newest_message_id": str(max(ids)) if ids else None,
        "oldest_message_id": str(min(ids)) if ids else None,
        "reached_end": reached_end,
        "messages": messages,
    }


def get_channel_info(channel_id: str, token: str) -> dict[str, Any]:
    raw = discord_get(f"/channels/{channel_id}", token)
    return {
        "channel_id": raw.get("id"),
        "name": raw.get("name"),
        "type": raw.get("type"),
        "topic": raw.get("topic"),
        "guild_id": raw.get("guild_id"),
        "nsfw": raw.get("nsfw", False),
        "parent_id": raw.get("parent_id"),
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

CSV_FIELDS = [
    "message_id", "channel_id", "author_id", "author_username",
    "author_global_name", "is_bot", "content", "timestamp",
    "edited_timestamp", "reply_to_message_id",
    "attachment_count", "attachment_urls", "embed_count", "embed_titles",
]


def to_csv(result: dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for m in result["messages"]:
        row = dict(m)
        row["attachment_urls"] = "; ".join(
            a["url"] for a in m["attachments"] if a.get("url"))
        row["embed_titles"] = "; ".join(
            e["title"] for e in m["embeds"] if e.get("title"))
        writer.writerow(row)
    return buf.getvalue()


def to_markdown(result: dict[str, Any]) -> str:
    msgs = result["messages"]
    if not msgs:
        return f"No messages found in channel {result['channel_id']}."
    lines = [
        f"# {result['count']} message(s) from channel {result['channel_id']}",
        f"_newest_message_id: {result['newest_message_id']}_",
        "",
    ]
    for m in msgs:
        name = m["author_global_name"] or m["author_username"] or m["author_id"]
        bot = " [BOT]" if m["is_bot"] else ""
        lines.append(f"**{name}{bot}** · {m['timestamp']} · `{m['message_id']}`")
        lines.append(m["content"] or "_(no text content)_")
        for a in m["attachments"]:
            lines.append(f"  Attachment: {a['filename']}: {a['url']}")
        for e in m["embeds"]:
            if e.get("title"):
                lines.append(f"  Embed: {e['title']}: {e.get('url', '')}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Fetch Discord channel messages as structured JSON/CSV.")
    p.add_argument("--channel", required=True, help="Target channel ID (snowflake).")
    p.add_argument("--token", default=None,
                   help="Bot token. Prefer DISCORD_BOT_TOKEN env var instead.")
    p.add_argument("--max", type=int, default=200, dest="max_messages",
                   help=f"Max messages to collect (1-{HARD_MESSAGE_CAP}). Default 200.")
    p.add_argument("--after", default=None,
                   help="Only fetch messages NEWER than this message ID.")
    p.add_argument("--before", default=None,
                   help="Only fetch messages OLDER than this message ID.")
    p.add_argument("--after-date", default=None, metavar="YYYY-MM-DD",
                   help="Only fetch messages on or after this date (UTC).")
    p.add_argument("--before-date", default=None, metavar="YYYY-MM-DD",
                   help="Only fetch messages on or before this date (UTC).")
    p.add_argument("--format", choices=["json", "csv", "markdown"], default="json",
                   help="Output format.")
    p.add_argument("--info", action="store_true",
                   help="Print channel metadata and exit.")
    p.add_argument("--check", action="store_true",
                   help="Run full environment self-check (token, permissions, intent).")
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not args.channel.isdigit() or not (5 <= len(args.channel) <= 25):
        die("--channel must be a numeric Discord ID (snowflake).")
    if not (1 <= args.max_messages <= HARD_MESSAGE_CAP):
        die(f"--max must be between 1 and {HARD_MESSAGE_CAP}.")
    if args.after and not (args.after.isdigit() and 5 <= len(args.after) <= 25):
        die("--after must be a numeric Discord message ID (snowflake).")
    if args.before and not (args.before.isdigit() and 5 <= len(args.before) <= 25):
        die("--before must be a numeric Discord message ID (snowflake).")

    after = args.after
    before = args.before
    if args.after_date:
        after = parse_date_arg(args.after_date, end_of_day=False)
    if args.before_date:
        before = parse_date_arg(args.before_date, end_of_day=True)

    token = resolve_token(args.token)

    try:
        if args.check:
            run_check(args.channel, token)
            return
        if args.info:
            print(json.dumps(get_channel_info(args.channel, token),
                             ensure_ascii=False, indent=2))
            return
        result = fetch_history(args.channel, token, args.max_messages, after, before)
    except error.HTTPError as e:
        die(explain_http_error(e, token))
    except error.URLError as e:
        die(f"Network error: {e.reason}. Check connectivity (token {mask_token(token)}).")
    except Exception as e:
        die(f"Unexpected error: {type(e).__name__}: {e} (token {mask_token(token)}).")

    log(f"[done] fetched {result['count']} messages.")

    if args.format == "markdown":
        print(to_markdown(result))
    elif args.format == "csv":
        print(to_csv(result), end="")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
