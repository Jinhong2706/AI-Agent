#!/usr/bin/env python3
import sqlite3
from datetime import datetime

DB = 'tournament.db'

def request_transfer(tag, new_clan):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE players SET clan=? WHERE tag=?", (new_clan, tag))
    conn.commit()
    print(f"✅ {tag} 已转会到 {new_clan}")
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        request_transfer(sys.argv[1], sys.argv[2])
    else:
        print("用法: python transfer.py <玩家标签> <新部落>")
