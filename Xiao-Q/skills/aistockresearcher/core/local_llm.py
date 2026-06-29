#!/usr/bin/env python3
import json, time
from urllib import request, error

class LocalLLM:
    def __init__(self, base_url="http://localhost:11434", model="qwen2.5:7b", timeout=60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._available = None

    def is_available(self):
        if self._available is not None:
            return self._available
        try:
            url = self.base_url + "/api/tags"
            resp = request.urlopen(request.Request(url), timeout=5)
            self._available = resp.status == 200
        except:
            self._available = False
        return self._available

    def chat(self, prompt, system=""):
        if not self.is_available():
            return {"error": "Ollama not available", "content": ""}
        try:
            body = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 2048}
            }).encode()
            url = self.base_url + "/api/generate"
            resp = request.urlopen(request.Request(url, data=body,
                headers={"Content-Type": "application/json"}, method="POST"), timeout=self.timeout)
            return {"content": json.loads(resp.read().decode()).get("response", ""), "model": self.model}
        except Exception as e:
            return {"error": str(e), "content": ""}

    def analyze_stock(self, info):
        if not self.is_available():
            return {"error": "Ollama not available", "method": "rule_based"}
        name = info.get("name", "")
        code = info.get("code", "")
        price = info.get("price", "")
        chg = info.get("change_pct", "")
        pe = info.get("pe", "?")
        pb = info.get("pb", "?")
        roe = info.get("roe", "?")
        p = "Analyze: " + name + "(" + code + ") price=" + str(price) + " chg=" + str(chg) + "% PE=" + str(pe) + " PB=" + str(pb) + " ROE=" + str(roe) + "%. Give score and recommendation."
        return self.chat(p, "You are an A-share analyst. Reply in Chinese, concise.")
