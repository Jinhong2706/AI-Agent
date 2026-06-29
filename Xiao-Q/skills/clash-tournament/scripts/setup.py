#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def init_database():
    conn = sqlite3.connect('tournament.db')
    c = conn.cursor()
    print("📦 初始化数据库...")
    
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, tag TEXT UNIQUE NOT NULL,
                  clan TEXT, town_hall INTEGER, trophies INTEGER, wins INTEGER DEFAULT 0,
                  losses INTEGER DEFAULT 0, registration_time TIMESTAMP, status TEXT DEFAULT 'pending')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS clans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, clan_name TEXT UNIQUE NOT NULL,
                  clan_tag TEXT UNIQUE, leader TEXT, member_count INTEGER DEFAULT 0,
                  registration_time TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transfers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, player_tag TEXT NOT NULL,
                  from_clan TEXT, to_clan TEXT, request_time TIMESTAMP,
                  status TEXT DEFAULT 'pending')''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

if __name__ == "__main__":
    init_database()
