#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tts_server.py  v3  -- 稳定版
Edge TTS 本地代理服务器 - 微软 Azure Neural 语音
每个请求在新事件循环中运行，避免状态污染。
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json, hashlib, time, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import edge_tts

SKILL_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SKILL_SCRIPTS, '.tts_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

PORT = 8766
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural",        "name": "晓晓 (女声-标准)",     "lang": "zh-CN", "gender": "Female"},
    {"id": "zh-CN-XiaoyiNeural",          "name": "晓伊 (女声-柔和)",     "lang": "zh-CN", "gender": "Female"},
    {"id": "zh-CN-YunxiNeural",           "name": "云希 (男声-情感)",     "lang": "zh-CN", "gender": "Male"},
    {"id": "zh-CN-YunjianNeural",         "name": "云健 (男声-清晰)",     "lang": "zh-CN", "gender": "Male"},
    {"id": "zh-CN-YunxiaNeural",          "name": "云夏 (男声)",          "lang": "zh-CN", "gender": "Male"},
    {"id": "zh-CN-YunyangNeural",         "name": "云扬 (男声)",          "lang": "zh-CN", "gender": "Male"},
    {"id": "zh-HK-HiuGaaiNeural",          "name": "香港-晓积 (女声)",    "lang": "zh-HK",  "gender": "Female"},
    {"id": "zh-TW-HsiaoChenNeural",        "name": "台湾-晓臻 (女声)",    "lang": "zh-TW",  "gender": "Female"},
    {"id": "zh-TW-YunJheNeural",           "name": "台湾-云哲 (男声)",    "lang": "zh-TW",  "gender": "Male"},
    {"id": "zh-CN-shaanxi-XiaoniNeural",  "name": "陕西话-小妮 (女声)",  "lang": "zh-CN",  "gender": "Female"},
    {"id": "zh-CN-liaoning-XiaobeiNeural", "name": "东北话-小北 (女声)",  "lang": "zh-CN",  "gender": "Female"},
]

def cache_path(text, voice, rate, volume):
    key = hashlib.md5(f"{text}|{voice}|{rate}|{volume}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, key + ".mp3")

def sync_synth(text, voice, rate, volume):
    """在新事件循环中运行异步合成"""
    cp = cache_path(text, voice, rate, volume)
    if os.path.exists(cp):
        return cp
    rate_str = f"{int((rate - 1)*100):+d}%"
    vol_str  = f"{int((volume - 1)*100):+d}%"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(edge_tts.Communicate(text, voice, rate=rate_str, volume=vol_str).save(cp))
    finally:
        loop.close()
    return cp

class TTSHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/voices':
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({
                "voices": VOICES,
                "default": DEFAULT_VOICE,
                "cache_count": len([f for f in os.listdir(CACHE_DIR) if f.endswith('.mp3')])
            }, ensure_ascii=False).encode())
            return

        if parsed.path == '/tts' or parsed.path.startswith('/tts?'):
            params = parse_qs(parsed.query)
            text  = ' '.join(params.get('text',  ['']))
            voice = params.get('voice', [DEFAULT_VOICE])[0]
            rate  = float(params.get('rate',  ['1.0'])[0])
            volume= float(params.get('volume',['1.0'])[0])
            if not text:
                self.send_error(400, "text parameter required")
                return
            try:
                cp = sync_synth(text[:500], voice, rate, volume)
                size = os.path.getsize(cp)
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(size))
                self.send_header("Accept-Ranges", "none")
                self.send_cors()
                self.end_headers()
                with open(cp, 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                import traceback; traceback.print_exc()
                self.send_error(500, str(e))
            return

        if parsed.path == '/health':
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_cors()
            self.end_headers()
            self.wfile.write(b"OK")
            return

        self.send_error(404)

    def do_POST(self):
        if self.path != '/tts':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            text   = data.get('text', '')
            voice  = data.get('voice', DEFAULT_VOICE)
            rate   = float(data.get('rate', 1.0))
            volume = float(data.get('volume', 1.0))
            if not text:
                self.send_error(400, "text is required")
                return
            cp = sync_synth(text[:500], voice, rate, volume)
            size = os.path.getsize(cp)
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(size))
            self.send_cors()
            self.end_headers()
            with open(cp, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            import traceback; traceback.print_exc()
            self.send_error(500, str(e))

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), TTSHandler)
    print(f"[TTS Server] Edge TTS Proxy running on http://127.0.0.1:{PORT}")
    print(f"[TTS Server] Cache dir: {CACHE_DIR}")
    print(f"[TTS Server] {len(VOICES)} voices available")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
