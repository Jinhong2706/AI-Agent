#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
Cloud-Sea Report Generator v5
从 report_config_{date}.json 读取数据，填充 report-template.html

用法:
    python report_gen.py <date> [output.html]
    python report_gen.py 2026-04-25
    python report_gen.py 2026-04-25 /tmp/out.html

数据流:
    report_config_{date}.json → report_gen.py → output.html
                                ↓
                          report-template.html（9个占位符）
"""
import json, sys, pathlib, datetime

# 确保 cloud_sea_shared 在路径中
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from cloud_sea_shared import (
    FOG_MECHANISM_MAP, FOG_BEST_TIME_MAP, FOG_ICONS,
    estimate_transparency
)

# 路径配置
SCRIPT_DIR  = pathlib.Path(__file__).parent
TEMPLATE    = SCRIPT_DIR.parent / "assets" / "report-template.html"

# 工作目录优先查找 weather_data_{date}.json
WORKSPACE   = pathlib.Path(r"C:\Users\86139\.qclaw\workspace")

# ═══════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()


def _v(d, *keys, default=0):
    """安全获取嵌套字典值，依次查找多个key直到找到非None值。"""
    for k in keys:
        if isinstance(d, dict):
            val = d.get(k, None)
            if val is not None:
                return val
    return default


def _cls_prob(p):
    if p >= 65: return "prob-high"
    if p >= 45: return "prob-medium"
    if p >= 25: return "prob-low"
    return "prob-very-low"


def _cls_diff(d):
    if d == "——": return "diff-negative"
    if d >= 200: return "diff-positive"
    if d >= 50:  return "diff-edge"
    return "diff-negative"


def _diff_str(d):
    if d == "——": return "——"
    if d > 0:   return f"&#8593;+{d}m"
    elif d < 0: return f"&#8595;{abs(d)}m"
    return "&#8212;0m"




# fog_badge() 已删除 (2026-04-27 self-improving) — 定义后从未调用，_FOG_BADGE_STYLE 未定义，存在 NameError 风险


# ═══════════════════════════════════════════════════════════════════════
# 构建函数
# ═══════════════════════════════════════════════════════════════════════


def visual_effect(diff, fog_type=""):
    # fog_type 可能是 string 或 list (从JSON反序列化), 统一处理
    ft_str = ""
    if isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2:
        ft_str = str(fog_type[1])  # 取雾型中文名
    else:
        ft_str = str(fog_type) if fog_type else ""
    # 无雾时无论diff多少都不存在云海
    if any(k in ft_str for k in ('none', '无雾', '无云', '晴空雾')):
        return "无雾，无云海"
    # 修复：diff=山顶海拔-雾顶MSL，diff越大表示山顶越高于雾顶，云海效果越好
    # diff > 0: 山顶在雾顶之上，可以看到云海
    # diff < 0: 山顶在雾中，看不到云海
    if diff is None or diff == "——":
        diff = 0
    if diff <= 0 and diff > -200:
        return "雾中（山顶不可见）"
    elif diff <= -200:
        return "深雾中（完全不可见）"
    elif diff >= 800:
        return "脚下云海，壮丽穿云"
    elif diff >= 500:
        return "云海在脚下，视野极佳"
    elif diff >= 200:
        return "清晰云海，视觉良好"
    elif diff >= 50:
        return "云海可见，稍模糊"
    else:
        return "边缘云海，效果一般"

def build_top3_cards(config):
    """TOP3 卡片 — 使用 top3 字段或从 ranked 推导。"""
    top3 = config.get("top3", [])
    if not top3:
        top3 = config.get("ranked", [])[:3]

    medals = ["&#127941;", "&#127942;", "&#127943;"]   # 🥇🥈🥉
    rows = []
    for i, p in enumerate(top3[:3]):
        name     = p.get("name", "-")
        prob     = int(_v(p, "score", "prob", default=0))
        elev     = int(_v(p, "summit_elev", "elevation", "elev", default=0))
        lcl      = int(_v(p, "lcl", default=0))
        rh       = int(_v(p, "rh", default=0))
        wind     = _v(p, "wind", default=0)
        fog_type = p.get("fog_type", "-")
        stars    = p.get("sunrise_stars", "&#9733;")
        # FIX: fog_type may be tuple/list — extract Chinese name (index 1)
        if isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2:
            fog_type_display = fog_type[1]
        elif isinstance(fog_type, (list, tuple)) and len(fog_type) == 1:
            fog_type_display = str(fog_type[0])
        else:
            fog_type_display = str(fog_type)
        # FIX: fog_type_key for FOG_BEST_TIME_MAP lookup — keys are Chinese names
        if isinstance(fog_type, (list, tuple)) and len(fog_type) >= 2:
            fog_type_key = fog_type[1]  # Chinese name
        elif isinstance(fog_type, (list, tuple)) and len(fog_type) > 0:
            fog_type_key = fog_type[0]
        else:
            fog_type_key = str(fog_type)
        best     = FOG_BEST_TIME_MAP.get(fog_type_key, "待定")
        travel   = config.get("travel_map", {}).get(name, ["", 0, 0])
        addr     = travel[0] if travel else ""
        km       = travel[1] if len(travel) > 1 else 0
        t_h      = travel[2] if len(travel) > 2 else 0
        diff     = int(_v(p, "diff", "summit_diff_m", default=0))
        diff_cls = _cls_diff(diff)
        diff_s   = _diff_str(diff)
        rank_cls = f"rank-{i+1}"
        visual   = visual_effect(diff, fog_type_key)

        rows.append(f"""<div class="top3-card {rank_cls}">
  <div class="rank-badge">{medals[i]}</div>
  <div class="prob-block">
    <span class="prob-num">{prob}</span><span class="prob-pct">%</span>
  </div>
  <div class="peak-name">{name}</div>
  <div class="top3-metrics-grid">
    <div class="top3-metric-row">
      <div class="top3-metric wide">
        <span class="top3-metric-label">海拔</span>
        <span class="top3-metric-val">{elev}m</span>
      </div>
      <div class="top3-metric wide">
        <span class="top3-metric-label">险差</span>
        <span class="top3-metric-val {diff_cls}">{diff_s}</span>
      </div>
    </div>
    <div class="top3-metric-row">
      <div class="top3-metric wide">
        <span class="top3-metric-label">湿度</span>
        <span class="top3-metric-val">{rh}%</span>
      </div>
      <div class="top3-metric wide">
        <span class="top3-metric-label">风速</span>
        <span class="top3-metric-val">{wind:.1f}km/h</span>
      </div>
    </div>
    <div class="top3-metric-row">
      <div class="top3-metric wide">
        <span class="top3-metric-label">最佳时间</span>
        <span class="top3-metric-val">{best}</span>
      </div>
      <div class="top3-metric wide">
        <span class="top3-metric-label">日出评级</span>
        <span class="top3-metric-val top3-stars">{stars}</span>
      </div>
    </div>
  </div>
</div>""")

    return '<div class="top3-section">\n' + "\n".join(rows) + "\n</div>"


def build_ranking_rows(config):
    """16峰排名表 — 使用 ranked 字段，含概率/险差颜色标记。"""
    peaks = config.get("ranked", [])
    html  = ""
    for i, p in enumerate(peaks, 1):
        name     = p.get("name", "-")
        elev     = int(_v(p, "summit_elev", "elevation", default=0))
        prob     = int(_v(p, "score", "prob", default=0))
        lcl      = int(_v(p, "lcl", default=0))
        fog_top  = int(_v(p, "fog_top", "cloud_base", default=0))
        diff     = int(_v(p, "diff", "summit_diff_m", default=0))
        wind     = _v(p, "wind", default=0)
        fog_type = p.get("fog_type", "-")
        fog_type_raw = p.get("fog_type_raw", fog_type)  # raw tuple/list from calc_fog_type
        stars    = p.get("sunrise_stars", "&#9733;")
        # B-2 FIX: 提取数值 score，estimate_transparency 需要 0-10 分制数值
        trans_raw = config.get("transparency", {}).get("score", 6.0)
        if isinstance(trans_raw, dict):
            trans_score = trans_raw.get("score", 6.0)
        else:
            trans_score = float(trans_raw)
        trans_result = estimate_transparency(trans_score, rh=p.get("rh", 50))
        # FIX: estimate_transparency returns dict, extract display string
        if isinstance(trans_result, dict):
            trans_display = trans_result.get("score", {}).get("level", str(trans_result))
        else:
            trans_display = str(trans_result)
        # FIX: fog_type extraction — prefer fog_type_raw (list/tuple), fallback to fog_type (may be str repr)
        _ft = fog_type_raw if isinstance(fog_type_raw, (list, tuple)) else None
        if _ft is None and isinstance(fog_type, (list, tuple)):
            _ft = fog_type
        if _ft is not None and len(_ft) >= 2:
            fog_type_display = _ft[1]  # Chinese name like '混合雾'
        elif _ft is not None and len(_ft) == 1:
            fog_type_display = str(_ft[0])
        else:
            fog_type_display = str(fog_type)
        # 无雾时雾顶和险差显示为"——"
        _is_no_fog = any(kw in str(fog_type_display).lower() for kw in ['none', '无雾', '无云', '晴空雾'])
        if _is_no_fog:
            fog_top = "——"
            diff = "——"
        visual = visual_effect(diff, fog_type)
        # FIX: fog_type_key for FOG_BEST_TIME_MAP lookup — keys are Chinese names
        if _ft is not None and len(_ft) >= 2:
            fog_type_key = _ft[1]  # Chinese name like '混合雾'
        elif _ft is not None and len(_ft) > 0:
            fog_type_key = _ft[0]
        else:
            fog_type_key = str(fog_type)
        best_t   = FOG_BEST_TIME_MAP.get(fog_type_key, "待定")

        prob_cls = _cls_prob(prob)
        diff_cls = _cls_diff(diff)
        diff_s   = _diff_str(diff)

        # 前3行高亮
        row_cls = ""
        if i == 1: row_cls = "row-top1"
        elif i == 2: row_cls = "row-top2"
        elif i == 3: row_cls = "row-top3"

        html += f"""<tr class="{row_cls}">
  <td>{i}</td>
  <td class="td-name"><strong>{name}</strong></td>
  <td>{elev}m</td>
  <td class="{prob_cls}">{prob}%</td>
  <td>{lcl}m</td>
  <td>{'——' if fog_top == '——' else f'{fog_top}m'}</td>
  <td class="{diff_cls}">{'——' if diff == '——' else diff_s}</td>
  <td>{int(wind)}</td>
  <td>{trans_display}</td>
  <td class="star-cell">{stars}</td>
  <td>{fog_type_display}</td>
  <td>{visual}</td>
  <td>{best_t}</td>
</tr>"""
    return html


def build_fog_summary(config):
    """雾型综合判断摘要。"""
    ranked = config.get("ranked", [])
    # 整体概率取排名第一的山峰得分
    top_prob = int(_v(ranked[0], "score", "prob", default=0)) if ranked else 0
    top_peak = ranked[0].get("name", "") if ranked else ""
    fog_forecast = config.get("fog_forecast", "待分析")
    return f"雾型综合判断：{fog_forecast}"


def build_mechanism_cards(config):
    """雾型机制卡片 — 从 fog_types 字段读取。"""
    fog_types = config.get("fog_types", [])
    if not fog_types:
        # 从 ranked peaks 反推
        ranked    = config.get("ranked", [])
        seen      = {}
        for p in ranked:
            ft = p.get("fog_type", "-")
            # FIX: fog_type may be tuple
            if isinstance(ft, (list, tuple)):
                ft_key = ft[0] if len(ft) > 0 else str(ft)
            else:
                ft_key = ft
            sc = int(_v(p, "score", "prob", default=0))
            if ft_key not in seen or sc > seen[ft_key]:
                seen[ft_key] = sc
        fog_types = [{"name": k, "prob": v, "active": True} for k, v in seen.items()]

    cards = []
    for ft in fog_types:
        name   = ft.get("name", "Unknown")
        prob   = ft.get("prob", 0)
        active = " mech-active" if ft.get("active", False) else ""
        icon   = FOG_ICONS.get(name, "&#127787;")
        desc   = FOG_MECHANISM_MAP.get(name, "待分析")
        cards.append(f"""<div class="mech-card{active}">
  <div class="mech-icon">{icon}</div>
  <div class="mech-body">
    <div class="mech-name">{name}</div>
    <div class="mech-desc">{desc}</div>
  </div>
</div>""")
    return "\n".join(cards)


def build_travel_suggestions(config):
    """出行建议卡片 — 从 ranked + travel_map 动态生成。"""
    ranked    = config.get("ranked", [])
    travel_map = config.get("travel_map", {})
    rows = []
    labels  = [("强烈推荐", "sugg-recommend"), ("推荐", "sugg-alternative"), ("可考虑", "sugg-optional")]
    classes = ["prob-high", "prob-medium", "prob-low"]

    for i, p in enumerate(ranked[:3]):
        if i >= 3:
            break
        name     = p.get("name", "-")
        prob     = int(_v(p, "score", "prob", default=0))
        prob_cls = classes[i]
        fog_type = p.get("fog_type", "-")
        lcl      = int(_v(p, "lcl", default=0))
        fog_top  = int(_v(p, "fog_top", default=0))
        diff     = int(_v(p, "diff", default=0))
        rh       = int(_v(p, "rh", default=0))
        travel   = travel_map.get(name, ["", 0, 0])
        addr     = travel[0] if travel else ""
        km       = travel[1] if len(travel) > 1 else 0
        t_h      = travel[2] if len(travel) > 2 else 0
        label, cls_suffix = labels[i]

        rows.append(f"""<div class="sugg-card {cls_suffix}">
  <div class="sugg-header">
    <span class="sugg-icon">&#127957;</span>
    <span class="sugg-label">{label}</span>
  </div>
  <div class="sugg-peak">{name}</div>
  <div class="sugg-prob">{prob}%</div>
  <ul class="sugg-points">
    <li>地址：{addr}（{km}km / {t_h}h）</li>
    <li>雾型：{fog_type}，险差 {diff}m</li>
    <li>LCL {lcl}m，湿度 {rh}%</li>
  </ul>
</div>""")

    # 警告框
    warn = config.get("warn", "")
    warn_detail = config.get("warn_detail", "")
    warn_html = ""
    if warn or warn_detail:
        warn_html = f"""<div class="warn-box" style="margin-top:12px;">
  <span class="warn-icon">&#9888;</span>
  <div>
    <div class="warn-title">{warn}</div>
    <ul class="warn-items"><li>{warn_detail}</li></ul>
  </div>
</div>"""

    return '<div class="suggest-row">\n' + "\n".join(rows) + "\n</div>\n" + warn_html


def build_hourly_tables(config):
    """逐小时数据表 — 使用 sunrise_rows（完整字段），回退到 probs/temps flat 数组。"""
    sunrise_rows = config.get("sunrise_rows", [])
    if not sunrise_rows:
        # Flat fallback: hours + probs + temps
        hours = config.get("hours", [])
        probs = config.get("probs", [])
        temps = config.get("temps", [])
        if hours:
            rows = []
            for i, hr in enumerate(hours):
                p = probs[i] if i < len(probs) else 0
                t = temps[i] if i < len(temps) else 0
                cls = "cloud-yes" if p >= 75 else "cloud-maybe" if p >= 40 else "cloud-no"
                rows.append(f"<tr><td class='time-col'>{hr}</td><td>{t}°C</td><td class='{cls}'>{p}%</td><td>&#8212;</td></tr>")
            return f"""<div class="hourly-block">
  <div class="hourly-title">逐小时云海概率</div>
  <table class="hourly-tbl">
    <thead><tr><th>时间</th><th>气温</th><th>概率</th><th>备注</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""
        return '<div class="hourly-block"><div class="hourly-title">暂无逐小时数据</div></div>'

    
    top_name = config.get('ranked', [{}])[0].get('name', '目标峰')  # AUDIT-014 FIX: 更有意义的回退文本

    # AUDIT-007 FIX: 检测整体是否无雾，控制逐小时云海判断
    overall_fog_type = config.get('ranked', [{}])[0].get('fog_type', '')
    if isinstance(overall_fog_type, (list, tuple)):
        overall_fog_type = overall_fog_type[1] if len(overall_fog_type) > 1 else str(overall_fog_type)
    overall_no_fog = any(kw in str(overall_fog_type).lower() for kw in ['none', '无雾', '无云', '晴空雾'])

# 完整 sunrise_rows
    rows = []
    for row in sunrise_rows:
        hr     = row.get("hour", row.get("time", ""))
        if "T" in str(hr):
            hr = str(hr).split("T")[-1][:5]
        T      = row.get("T", 0)
        Td     = row.get("Td", 0)
        rh     = int(row.get("RH", 0))
        wind   = row.get("wind", 0)
        lcl    = int(row.get("lcl", 0))
        diff   = int(row.get("diff", 0))
        cc     = int(row.get("cc", 0))
        prob   = int(row.get("prob", 0))
        status = row.get("status", "")
        rain   = int(row.get("rain", 0))

        cls_map = {"above": "cloud-yes", "edge": "cloud-maybe", "below": "cloud-no", "": "cloud-maybe"}
        cls = cls_map.get(status, "cloud-maybe")
        diff_s = _diff_str(diff)
        diff_cls = _cls_diff(diff)

        # 云量显示
        cc_cls = "cloud-yes" if cc < 30 else "cloud-maybe" if cc < 70 else "cloud-no"

        # 雾顶计算（从 sunrise_rows 的 fog_top 字段获取，由 analyzer.py 生成）
        # 2026-05-06 FIX: 不再用 lcl+555 硬编码，直接读 sunrise_rows.fog_top
        fog_top = int(row.get("fog_top", lcl + 555))  # fallback: lcl+555 仅在无fog_top时
        
        # 无雾时雾顶和山顶差显示为"——"
        if overall_no_fog:
            fog_top = "——"
            diff = "——"
            diff_s = "——"
            diff_color = "#888888"
        else:
            # 山顶差颜色
            diff_cls = _cls_diff(diff)
            diff_color = "#00e87a" if diff > 0 else "#ff3355"  # 绿色正差/红色负差
        
        # AUDIT-007 FIX: 通透度从 config.transparency.detail 获取实际数据
        # 优先使用城区能见度和PM2.5等实测指标，而非简化公式
        trans_base = config.get("transparency", {}).get("score", 6.0)
        if isinstance(trans_base, dict):
            trans_base = trans_base.get("score", 6.0)
        trans_detail = config.get("transparency", {}).get("detail", {})
        # 尝试从 detail 中获取逐小时能见度/PM2.5
        vis_avg = trans_detail.get("visibility_avg_km", None)
        pm25_avg = trans_detail.get("pm25_avg", None)
        # 综合评分：基础分 + 小时级微调
        trans_adj = trans_base
        # 云量高时轻微下调（遮挡=不通透）
        if cc > 80:
            trans_adj -= 1.5
        elif cc > 60:
            trans_adj -= 0.5
        # 低湿度+低云量=干燥空气，通透度略降
        if rh < 40 and cc < 30:
            trans_adj -= 0.3
        trans_score = max(1, min(10, round(trans_adj, 1)))
        trans_str = f"{trans_score}/10"
        
        # 云海判断
        # 修复: 如果整体无雾，所有小时都显示"无雾，无云海"
        if overall_no_fog:
            cloud_judge = "无雾，无云海"
            judge_cls = "judge-none"
        elif diff > 200:
            cloud_judge = f"&#127775; 最佳云海"
            judge_cls = "judge-best"
        elif diff > 50:
            cloud_judge = f"&#9888; 接近雾缘"
            judge_cls = "judge-good"
        elif diff >= 0:
            cloud_judge = f"&#128161; 边缘可见"
            judge_cls = "judge-edge"
        else:
            cloud_judge = f"&#10060; 在雾中"
            judge_cls = "judge-bad"

        rows.append(f"""<tr>
  <td class="time-col">{hr}</td>
  <td class="temp-col">{T}</td>
  <td class="rh-col">{rh}</td>
  <td class="wind-col">{int(wind)}</td>
  <td class="lcl-col">{lcl}</td>
  <td class="cc-col {cc_cls}">{cc}</td>
  <td class="fogtop-col">{fog_top}</td>
  <td class="diff-col" style="color:{diff_color}">{diff_s}</td>
  <td class="trans-col">{trans_str}</td>
  <td class="judge-col {judge_cls}">{cloud_judge}</td>
</tr>""")

    return f"""<div class="hourly-block">
  <div class="hourly-title">&#127750; 逐小时数据（{top_name}）</div>
  <table class="hourly-tbl">
    <thead>
      <tr>
        <th style="width:70px;">时间</th>
        <th style="width:80px;">温度(°C)</th>
        <th style="width:70px;">湿度(%)</th>
        <th style="width:100px;">风速(km/h)</th>
        <th style="width:70px;">LCL(m)</th>
        <th style="width:70px;">云量(%)</th>
        <th style="width:90px;">雾顶(m)</th>
        <th style="width:110px;">山顶差(m)</th>
        <th style="width:80px;">通透度</th>
        <th style="width:180px;">云海判断</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>"""


def build_equip_grid(config):
    """装备清单。"""
    items = [
        ("&#128268;", "头灯", "必备·山顶无光源"),
        ("&#129532;", "保暖", "抓绒/羽绒服·山顶冷"),
        ("&#129533;", "防风", "硬壳冲锋衣"),
        ("&#127991;", "登山杖", "下山碎石路用"),
        ("&#129703;", "热水", "保暖瓶·山顶必备"),
        ("&#128247;", "相机", "高感相机·手机也行"),
        ("&#128267;", "三脚架", "长曝光·星空/云海"),
        ("&#128171;", "充电宝", "低温耗电快"),
        ("&#127912;", "ND/GND镜", "压光比·云海日出"),
        ("&#129504;", "镜头布", "湿气·雾气会弄湿镜头"),
        ("&#128567;", "口罩", "KN95·山路扬尘"),
        ("&#127869;", "补给", "干粮/巧克力/能量棒"),
    ]
    cols = []
    for icon, name, note in items:
        cols.append(f"""<div class="equip-item">
  <span class="equip-icon">{icon}</span>
  <div class="equip-text">
    <span class="equip-name">{name}</span>
    <span class="equip-note">{note}</span>
  </div>
</div>""")
    return "\n".join(cols)


# ═══════════════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════════════

def generate(config_path, output_path):
    """读取配置 + 模板，填充所有占位符，输出 HTML。"""
    config  = load_json(config_path)
    template = load_template()

    # 组件
    top3      = build_top3_cards(config)
    ranking   = build_ranking_rows(config)
    fog_sum   = build_fog_summary(config)
    mech_cds  = build_mechanism_cards(config)
    travel    = build_travel_suggestions(config)
    hourly    = build_hourly_tables(config)
    equip     = build_equip_grid(config)

    # 占位符映射（字典驱动，便于维护）
    placeholders = {
        "TITLE":             config.get("title", "云海预测报告"),
        "SUBTITLE":         config.get("subtitle", ""),
        "UPDATE_TIME":      datetime.datetime.now().strftime("更新 %Y-%m-%d %H:%M:%S GMT+8"),
        "TOP3_CARDS":       top3,
        "RANKING_ROWS":     ranking,
        "FOG_SUMMARY":      fog_sum,
        "MECHANISM_CARDS":  mech_cds,
        "TRAVEL_SUGGESTIONS": travel,
        "HOURLY_TABLES":    hourly,
        "EQUIP_GRID":       equip,
        "FOOTER_NOTE":      config.get("footer_note", "数据来源：Open-Meteo API · Cloud-Sea Skill"),
    }

    # 统一填充
    for key, val in placeholders.items():
        template = template.replace(f"{{{{{key}}}}}", str(val))

    # 写文件
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    size_kb = pathlib.Path(output_path).stat().st_size // 1024
    print(f"OK: {output_path}  ({size_kb} KB)")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法: python report_gen.py <date> [output.html]")
        print("示例: python report_gen.py 2026-04-25")
        sys.exit(1)

    date = sys.argv[1].strip()

    # 查找配置文件
    config_paths = [
        SCRIPT_DIR.parent / "data" / f"report_config_{date}.json",
        SCRIPT_DIR.parent / "data" / f"report_config_{date}.json",
    ]
    config_path = None
    for p in config_paths:
        if p.exists():
            config_path = p
            break

    if not config_path:
        print(f"ERROR: 找不到配置 {date} 的 report_config JSON")
        print("查找路径:")
        for p in config_paths:
            print(f"  {p}  {'[OK]' if p.exists() else '[MISSING]'}")
        sys.exit(1)

    # 输出路径
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = str(SCRIPT_DIR.parent / "output" / f"cloud-sea-{date}.html")

    # Check if config is stale (prevent using old data)
    check_stale_config(config_path, date)
    
    print(f"配置: {config_path}")
    print(f"模板: {TEMPLATE}")
    generate(str(config_path), output_path)



# ==================================================================
# 过期检查（2026-05-27 新增）
# ==================================================================
def check_stale_config(config_path, date):
    """检查 report_config 是否比 weather_data 旧（过期）"""
    import datetime
    
    # 推导 weather_data 路径（与 analyzer.py 逻辑一致）
    data_dir = config_path.parent.parent / "data"
    weather_data_paths = [
        data_dir / f"weather_data_{date}.json",
        data_dir / "weather_data.json",
        config_path.parent / f"weather_data_{date}.json",
        config_path.parent / "weather_data.json",
    ]
    weather_data_path = None
    for p in weather_data_paths:
        if p.exists():
            weather_data_path = p
            break
    
    if not weather_data_path:
        print("WARN: Cannot find weather_data.json, skip staleness check")
        return
    
    config_mtime = config_path.stat().st_mtime
    data_mtime = weather_data_path.stat().st_mtime
    
    if config_mtime < data_mtime:
        config_time = datetime.datetime.fromtimestamp(config_mtime).strftime('%Y-%m-%d %H:%M:%S')
        data_time = datetime.datetime.fromtimestamp(data_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ERROR: report_config.json is stale!")
        print(f"  config mtime: {config_time}")
        print(f"  data mtime:   {data_time}")
        print(f"  Please re-run: python analyzer.py --date {date} --config")
        import sys
        sys.exit(1)
    else:
        print(f"OK: Config is fresh (mtime: {datetime.datetime.fromtimestamp(config_mtime).strftime('%Y-%m-%d %H:%M:%S')})")



# ==================================================================
# Staleness check (added 2026-05-27)
# ==================================================================
def check_stale_config(config_path, date):
    """Check if report_config is older than weather_data"""
    import datetime
    
    # Find weather_data path (same logic as analyzer.py)
    data_dir = config_path.parent.parent / "data"
    weather_data_paths = [
        data_dir / f"weather_data_{date}.json",
        data_dir / "weather_data.json",
        config_path.parent / f"weather_data_{date}.json",
        config_path.parent / "weather_data.json",
    ]
    weather_data_path = None
    for p in weather_data_paths:
        if p.exists():
            weather_data_path = p
            break
    
    if not weather_data_path:
        print("WARN: Cannot find weather_data.json, skip staleness check")
        return
    
    config_mtime = config_path.stat().st_mtime
    data_mtime = weather_data_path.stat().st_mtime
    
    if config_mtime < data_mtime:
        config_time = datetime.datetime.fromtimestamp(config_mtime).strftime('%Y-%m-%d %H:%M:%S')
        data_time = datetime.datetime.fromtimestamp(data_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ERROR: report_config.json is stale!")
        print(f"  config mtime: {config_time}")
        print(f"  data mtime:   {data_time}")
        print(f"  Please re-run: python analyzer.py --date {date} --config")
        import sys
        sys.exit(1)
    else:
        print(f"OK: Config is fresh (mtime: {datetime.datetime.fromtimestamp(config_mtime).strftime('%Y-%m-%d %H:%M:%S')})")



if __name__ == "__main__":
    main()

