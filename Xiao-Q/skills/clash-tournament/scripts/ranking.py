#!/usr/bin/env python3
import sqlite3

DB = 'tournament.db'

def show_ranking():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, tag, clan, trophies FROM players ORDER BY trophies DESC")
    print("\n🏆 排行榜 🏆")
    for i, row in enumerate(c.fetchall(), 1):
        print(f"{i}. {row[0]} ({row[1]}) - {row[2] or '无部落'} - {row[3]}杯")
    conn.close()

if __name__ == "__main__":
    show_ranking()
