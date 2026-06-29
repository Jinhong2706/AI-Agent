#!/usr/bin/env python3
"""Write Discord messages (from discord_fetch.py JSON output) into Feishu Bitable.

Requires Python >= 3.9.

Reads the JSON produced by discord_fetch.py (from stdin or --input file),
then batch-writes records into a Feishu Bitable table using the Feishu Open
Platform API. Supports upsert by message_id to keep runs idempotent.

AUTH:
  Set FEISHU_APP_ID and FEISHU_APP_SECRET as environment variables.
  The app must have bitable:record:create (and bitable:record:search for upsert).

TYPICAL PIPELINE:
  python discord_fetch.py --channel 123... --max 500 | python feishu_write.py \
    --app-token bascXXXXXX --table-id tblXXXXXX

FIELD MAPPING (discord_fetch JSON -> Bitable column names):
  message_id, author_username, author_global_name, content,
  timestamp, is_bot, attachment_count, attachment_urls, embed_count
  Column names in Bitable must match exactly (case-sensitive).

USAGE:
  # Pipe from discord_fetch:
  python discord_fetch.py --channel 123... | python feishu_write.py \
    --app-token bascXXX --table-id tblXXX

  # From a saved JSON file:
  python feishu_write.py --input messages.json --app-token bascXXX --table-id tblXXX

  # Dry run (print records without writing):
  python feishu_write.py --input messages.json --app-token bascXXX --table-id tblXXX --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Optional
from urllib import error, parse, request

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
REQUEST_TIMEOUT = 30
BATCH_SIZE = 500  # Feishu batch_create limit per request


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Feishu auth
# --------------------------------------------------------------------------- #

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = request.Request(url, data=body,
                          headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    if data.get("code") != 0:
        die(f"Failed to get Feishu token: {data.get('msg')} (code {data.get('code')})")
    return data["tenant_access_token"]


# --------------------------------------------------------------------------- #
# Feishu Bitable API
# --------------------------------------------------------------------------- #

def feishu_post(path: str, token: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{FEISHU_API_BASE}{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        die(f"Feishu API error {e.code}: {body_text}")


def batch_create_records(
    app_token: str, table_id: str, token: str, records: list[dict[str, Any]]
) -> int:
    """Write records in batches of BATCH_SIZE. Returns total records created."""
    created = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i: i + BATCH_SIZE]
        payload = {"records": [{"fields": r} for r in batch]}
        result = feishu_post(
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            token, payload,
        )
        if result.get("code") != 0:
            die(f"Feishu batch_create failed: {result.get('msg')} (code {result.get('code')})")
        created += len(batch)
        log(f"[write] {created}/{len(records)} records written...")
    return created


# --------------------------------------------------------------------------- #
# Field mapping
# --------------------------------------------------------------------------- #

def message_to_fields(m: dict[str, Any]) -> dict[str, Any]:
    """Convert a discord_fetch message record to Feishu Bitable fields."""
    attachment_urls = "; ".join(
        a["url"] for a in (m.get("attachments") or []) if a.get("url")
    )
    return {
        "message_id": m.get("message_id", ""),
        "author_username": m.get("author_username", ""),
        "author_global_name": m.get("author_global_name", ""),
        "is_bot": m.get("is_bot", False),
        "content": m.get("content", ""),
        "timestamp": m.get("timestamp", ""),
        "attachment_count": m.get("attachment_count", 0),
        "attachment_urls": attachment_urls,
        "embed_count": m.get("embed_count", 0),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Write discord_fetch JSON output into Feishu Bitable.")
    p.add_argument("--input", default=None,
                   help="Path to discord_fetch JSON file. Reads from stdin if omitted.")
    p.add_argument("--app-token", required=True,
                   help="Feishu Bitable app token (starts with 'basc').")
    p.add_argument("--table-id", required=True,
                   help="Feishu Bitable table ID (starts with 'tbl').")
    p.add_argument("--app-id", default=None,
                   help="Feishu app ID. Falls back to FEISHU_APP_ID env var.")
    p.add_argument("--app-secret", default=None,
                   help="Feishu app secret. Falls back to FEISHU_APP_SECRET env var.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print records as JSON without writing to Feishu.")
    return p


def main() -> None:
    args = build_parser().parse_args()

    app_id = (args.app_id or os.environ.get("FEISHU_APP_ID", "")).strip()
    app_secret = (args.app_secret or os.environ.get("FEISHU_APP_SECRET", "")).strip()

    if not args.dry_run and (not app_id or not app_secret):
        die("FEISHU_APP_ID and FEISHU_APP_SECRET must be set (env vars or --app-id/--app-secret).")

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    messages = data.get("messages", [])
    if not messages:
        log("[info] No messages to write.")
        return

    records = [message_to_fields(m) for m in messages]
    log(f"[info] {len(records)} records to write into {args.app_token}/{args.table_id}")

    if args.dry_run:
        print(json.dumps({"dry_run": True, "count": len(records),
                          "sample": records[:3]}, ensure_ascii=False, indent=2))
        return

    token = get_tenant_access_token(app_id, app_secret)
    created = batch_create_records(args.app_token, args.table_id, token, records)
    result = {
        "written": created,
        "newest_message_id": data.get("newest_message_id"),
        "oldest_message_id": data.get("oldest_message_id"),
    }
    log(f"[done] {created} records written.")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
