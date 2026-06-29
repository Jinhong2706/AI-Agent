#!/usr/bin/env python3
import sqlite3
from datetime import datetime

DB = 'tournament.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY, name TEXT, tag TEXT UNIQUE,
                  clan TEXT, town_hall INTEGER, trophies INTEGER, reg_time TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✅ 数据库就绪")

def register(name, tag, clan=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO players (name, tag, clan, reg_time) VALUES (?,?,?,?)",
                  (name, tag, clan, datetime.now()))
        conn.commit()
        print(f"✅ {name} ({tag}) 注册成功")
    except sqlite3.IntegrityError:
        print(f"❌ {tag} 已存在")
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python register.py --name 名字 --tag #标签 [--clan 部落]")
    else:
        init_db()
        # 简化参数解析
        print("请使用完整命令: python register.py")
