#!/usr/bin/env python3
import os, json, time, hashlib

class CacheManager:
    def __init__(self, cache_dir=None, default_ttl=300):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), "..", ".cache")
        self.default_ttl = default_ttl
        os.makedirs(self.cache_dir, exist_ok=True)

    def _key_path(self, key):
        return os.path.join(self.cache_dir, hashlib.md5(str(key).encode()).hexdigest() + ".json")

    def get(self, key):
        path = self._key_path(key)
        if not os.path.exists(path): return None
        try:
            with open(path, "r", encoding="utf-8") as f: data = json.load(f)
            if time.time() - data.get("_ts", 0) > data.get("_ttl", self.default_ttl):
                os.remove(path); return None
            return data.get("value")
        except: return None

    def set(self, key, value, ttl=None):
        try:
            with open(self._key_path(key), "w", encoding="utf-8") as f:
                json.dump({"_ts": time.time(), "_ttl": ttl or self.default_ttl, "value": value}, f, ensure_ascii=False)
        except: pass

    def clear(self):
        for f in os.listdir(self.cache_dir):
            if f.endswith(".json"):
                try: os.remove(os.path.join(self.cache_dir, f))
                except: pass
