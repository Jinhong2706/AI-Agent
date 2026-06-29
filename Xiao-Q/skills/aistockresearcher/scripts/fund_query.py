#!/usr/bin/env python3
"""基金查询"""
import sys, os, argparse, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.data_providers.fund_provider import FundProvider

def main():
    p = argparse.ArgumentParser(description="基金查询")
    p.add_argument("--code", default="000001")
    p.add_argument("--search", type=str)
    p.add_argument("--type", choices=["realtime","detail","holdings","all"], default="all")
    p.add_argument("--holdings", action="store_true")
    args = p.parse_args()
    fp = FundProvider()
    if args.search:
        r = fp.search(args.search)
    elif args.holdings:
        r = {"holdings": fp.holdings(args.code)}
    else:
        r = {}
        if args.type in ("realtime", "all"):
            r["realtime"] = fp.realtime(args.code)
        if args.type in ("detail", "all"):
            r["detail"] = fp.detail(args.code)
        if args.type in ("holdings", "all"):
            r["holdings"] = fp.holdings(args.code)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
