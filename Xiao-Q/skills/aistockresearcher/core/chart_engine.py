#!/usr/bin/env python3
"""Chart engine - matplotlib optional, ASCII fallback"""
import math, os

def _has_mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        return True
    except: return False

def _zh_font():
    for f in ["SimHei", "Microsoft YaHei", "STSong", "KaiTi"]:
        try:
            from matplotlib import font_manager
            if f in {x.name for x in font_manager.fontManager.ttflist}: return f
        except: pass
    return "SimHei"

class ChartEngine:
    def __init__(self): self._mpl = _has_mpl()

    def kline(self, data, title="K-line", save_path=None):
        if not data: return "no data"
        if self._mpl:
            try:
                import matplotlib.pyplot as plt
                plt.rcParams["font.sans-serif"] = [_zh_font()]
                plt.rcParams["axes.unicode_minus"] = False
                dates = [d.get("date", "") for d in data]
                prices = [d.get("close", 0) for d in data]
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.plot(dates, prices, "b-", linewidth=1.5)
                ax.set_title(title, fontsize=14)
                ax.grid(True, alpha=0.3)
                if save_path: plt.savefig(save_path, dpi=150, bbox_inches="tight")
                return f"saved: {save_path}" if save_path else "ok"
            except: pass
        prices = [d.get("close", 0) for d in data[-60:]]
        if not prices: return "no data"
        mn, mx = min(prices), max(prices)
        if mn == mx: mx = mn + 1
        h = 20
        lines = [f"\n{title} (ASCII)", "-" * 60]
        for i in range(h, 0, -1):
            th = mn + (mx - mn) * i / h
            bar = "".join("#" if p >= th else " " for p in prices[-60:])
            lines.append(f"{th:>8.1f} |{bar}")
        return "\n".join(lines)

    def returns_dist(self, returns):
        if not returns: return "no data"
        m = sum(returns) / len(returns)
        s = (sum((r - m) ** 2 for r in returns) / len(returns)) ** 0.5
        return f"mean={m:.2f}%, std={s:.2f}%, n={len(returns)}"
