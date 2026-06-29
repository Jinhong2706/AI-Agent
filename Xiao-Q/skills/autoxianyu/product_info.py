"""
product_info.py - 商品信息解析
核心原则：任何输入都能发布，字典没有的随机兜底
"""
import re
import random

# 品牌 → 热门型号（随机选）
BRAND_MODELS = {
    "苹果":      ["iPhone 15", "iPhone 15 Pro", "iPhone 14", "iPhone 14 Pro", "iPhone 13"],
    "小米":      ["小米14", "小米14 Pro", "小米13", "小米15"],
    "红米":      ["Redmi K70", "Redmi K70 Pro", "Redmi Note 13"],
    "华为":      ["Mate 60", "Mate 60 Pro", "P70", "P70 Pro"],
    "荣耀":      ["荣耀Magic 6", "荣耀Magic 6 Pro", "荣耀X50"],
    "OPPO":      ["Find X8", "Find X8 Pro", "Reno 12"],
    "vivo":      ["X200", "X100", "X100 Pro", "X200 Pro"],
    "iQOO":      ["iQOO 13", "iQOO Neo 10"],
    "一加":      ["OnePlus 12", "OnePlus Ace 4"],
    "真我":      ["realme GT5", "realme 13 Pro"],
    "三星":      ["Galaxy S25", "Galaxy S25 Ultra", "Galaxy Z Fold6"],
    "索尼":      ["Xperia 1 VI", "Xperia 5 V"],
    "努比亚":    ["Nubia Z60 Ultra", "Nubia Flip"],
    "中兴":      ["Axon 60", "Axon 60 Lite"],
    "联想":      ["拯救者Y70", "拯救者Y90"],
    "摩托罗拉":  ["moto X50", "moto edge 50"],
    "传音":      ["Tecno Camon 30", "Infinix Note 40"],
    "海信":      ["Hi 战神", "Hi 阅读"],
    "酷派":      ["酷派 COOL 30", "锋行 Y75"],
    "MacBook":   ["MacBook Pro 14", "MacBook Air 13", "MacBook Pro 16"],
    "iPad":      ["iPad Pro 11", "iPad Air 11", "iPad 10"],
    "小米平板":  ["小米平板7 Pro", "小米平板7", "小米平板6"],
    "华为平板":  ["MatePad Pro 13", "MatePad Air 11"],
    "荣耀平板":  ["荣耀平板 V8 Pro", "荣耀平板 9"],
    "OPPO平板":  ["OPPO Pad 3", "OPPO Pad Air2"],
    "vivo平板":  ["vivo Pad 3", "vivo Pad Air"],
    "三星平板":  ["Galaxy Tab S10 Ultra", "Galaxy Tab S9"],
    "联想平板":  ["小新Pad Pro 12", "小新Pad Plus"],
    "ThinkPad":  ["ThinkPad X1 Carbon", "ThinkPad T14", "ThinkPad P1"],
    "华为电脑":  ["MateBook 14", "MateBook X Pro"],
    "戴尔":      ["XPS 15", "XPS 13", "Inspiron 15"],
    "惠普":      ["Spectre x360", "Pavilion 15", "战66"],
    "联想电脑":  ["ThinkBook 14", "Yoga 14", "小新Pro 14"],
    "华硕":      ["灵耀14", "天选5", "ROG 幻16"],
    "宏碁":      ["Swift 5", "Predator 掠夺者"],
    "微星":      ["Stealth 16", "Titan 18"],
    "机械革命":  ["极光 Pro", "旷世 G16"],
}

# 具体型号 → 参考价（key 统一小写+去空格，用于匹配）
# 型号参考价字典（key 统一英文全小写）
MODEL_PRICE = {
    # Apple
    "iphone15promax": 9999, "iphone15pro": 8999,
    "iphone15": 5999, "iphone14promax": 8999,
    "iphone14pro": 7999, "iphone14": 5299,
    "iphone13": 4299, "iphone16promax": 10999,
    "macbookpro14": 14999, "macbookpro16": 19999,
    "macbookair13": 8999, "macbookair15": 10499,
    "ipadpro12.9": 9299, "ipadpro11": 7299,
    "ipadair11": 4799, "ipad10": 3999,
    # Xiaomi
    "xiaomi15": 4499, "xiaomi14ultra": 5999,
    "xiaomi14pro": 4999, "xiaomi14": 3999,
    "xiaomi13pro": 3699, "xiaomi13": 3299,
    # Redmi
    "redmik70pro": 2699, "redmik70": 2099,
    "redminote13": 1099,
    # Samsung
    "galaxys25ultra": 8999, "galaxys25": 6499,
    "galaxyzfold6": 9999, "galaxyzflip6": 5999,
    # Huawei
    "mate70pro": 6999, "mate60": 4999,
    "p70pro": 6999, "p70": 5999,
    # Honor
    "honormagic6pro": 4999, "honormagic6": 3999,
    # vivo
    "x200pro": 4999, "x200": 3999,
    "x100pro": 3999, "x100": 2999,
    # iQOO
    "iqoo13": 3999, "iqooneo10": 3299,
    # OnePlus
    "oneplus12": 3999, "oneplusace4": 3299,
    # OPPO
    "findx8pro": 4999, "findx8": 3999,
    "reno13": 2499, "reno12": 2299,
    # realme
    "realmegt5": 2299, "realmepro": 1999,
    "realme13pro": 1699,
    # Sony
    "xperia1vi": 8999, "xperia5v": 6999,
    # Nubia
    "nubiaz60ultra": 4999,
    # ZTE
    "axon60": 1999,
    # Motorola
    "motoedge50": 2499, "motox50": 3999,
    # ThinkPad
    "thinkpadx1carbon": 9999, "thinkpadt14": 6999,
    # 小米平板
    "xiaomipad7pro": 2999, "xiaomipad7": 2499,
}

# 参考价兜底（未知型号时用品牌均价区间估算）
DEFAULT_PRICE = {"手机": 2999, "平板": 2999, "电脑": 6999, "耳机": 699, "手表": 1299}

# 品牌价格区间（未知型号时的兜底，单位：元）
# 结构: brand -> (低端均价, 高端均价)  用于根据型号关键词档位估算
BRAND_PRICE_RANGE = {
    "苹果":   (3000, 12000),
    "小米":   (1500, 6000),
    "红米":   (800, 3000),
    "华为":   (3000, 8000),
    "荣耀":   (2000, 6000),
    "OPPO":   (1500, 5000),
    "vivo":   (1500, 5000),
    "iQOO":   (2500, 5000),
    "一加":   (2500, 5000),
    "真我":   (1000, 2500),
    "三星":   (3000, 10000),
    "索尼":   (4000, 10000),
    "努比亚": (3000, 6000),
    "中兴":   (1000, 2500),
    "联想":   (2000, 8000),
    "摩托罗拉": (1500, 4000),
    "传音":   (500, 2000),
    "海信":   (1000, 3000),
    "酷派":   (300, 1000),
    "MacBook": (8000, 20000),
    "iPad":   (3000, 10000),
    "小米平板": (1500, 3500),
    "华为平板": (2500, 6000),
    "荣耀平板": (1500, 4000),
    "OPPO平板": (1500, 3500),
    "vivo平板": (1500, 3500),
    "三星平板": (3000, 9000),
    "联想平板": (1200, 3500),
    "ThinkPad": (5000, 15000),
    "华为电脑": (4000, 12000),
    "戴尔":   (4000, 15000),
    "惠普":   (4000, 15000),
    "联想电脑": (4000, 12000),
    "华硕":   (4000, 15000),
    "宏碁":   (3500, 12000),
    "微星":   (8000, 20000),
    "机械革命": (5000, 15000),
}

# 型号档位关键词（用于在未知型号时判断是高端还是低端）
MODEL_TIER_KEYWORDS = {
    "high": ["ultra", "promax", "max", "pro", "plus", "ultra", "折叠", "折叠屏",
             "16寸", "16\"", "15寸", "15\"", "14寸", "14\"", "13寸", "13\"",
             "max", "致臻版", "非凡版", "旗舰", "至尊", "顶配", "皇帝版"],
    "low":  ["se", "lite", "青春", "标准版", "基础版", "note", "x", "c", "i", "a"],
}

# 颜色库
COLORS = {
    "手机": ["黑色", "白色", "蓝色", "紫色", "金色", "银色", "绿色"],
    "平板": ["深空灰", "银色", "蓝色", "紫色"],
    "电脑": ["深空灰", "银色", "星光色"],
    "耳机": ["白色", "黑色"],
    "手表": ["黑色", "银色", "金色"],
}

# 成色
COND_FACTOR = {"全新": 0.95, "99新": 0.88, "98新": 0.82, "95新": 0.72, "9成新": 0.70, "85新": 0.55, "8成新": 0.40}
DEFAULT_COND = "95新"


def _norm(s: str) -> str:
    """只保留中文、字母、数字（去空格/符号），用于型号匹配"""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", s.lower())


def detect_brand(text: str):
    """识别品牌，返回 BRAND_MODEMS 里的标准品牌名"""
    t = text.lower().replace(" ", "")
    aliases = [
        ("苹果电脑", "MacBook"), ("苹果手机", "苹果"),
        ("airpods", "苹果"), ("airpod", "苹果"),
        ("苹果", "苹果"), ("apple", "苹果"), ("iphone", "苹果"),
        ("小米", "小米"), ("xiaomi", "小米"), ("mipad", "小米"),
        ("红米", "红米"), ("redmi", "红米"),
        ("华为", "华为"), ("huawei", "华为"), ("hwpad", "华为"),
        ("荣耀", "荣耀"), ("honor", "荣耀"),
        ("OPPO", "OPPO"), ("oppo", "OPPO"), ("find", "OPPO"),
        ("vivo", "vivo"),
        ("iQOO", "iQOO"), ("iqoo", "iQOO"), ("neo", "iQOO"),
        ("一加", "一加"), ("oneplus", "一加"),
        ("真我", "真我"), ("realme", "真我"),
        ("三星", "三星"), ("samsung", "三星"), ("galaxy", "三星"),
        ("索尼", "索尼"), ("sony", "索尼"), ("xperia", "索尼"),
        ("努比亚", "努比亚"), ("nubia", "努比亚"),
        ("中兴", "中兴"), ("zte", "中兴"), ("axon", "中兴"),
        ("联想", "联想"), ("lenovo", "联想"),
        ("摩托罗拉", "摩托罗拉"), ("moto", "摩托罗拉"),
        ("传音", "传音"), ("tecno", "传音"), ("infinix", "传音"),
        ("海信", "海信"), ("hisense", "海信"),
        ("酷派", "酷派"), ("coolpad", "酷派"),
        ("MacBook", "MacBook"), ("macbook", "MacBook"),
        ("iPad", "iPad"), ("ipad", "iPad"),
        ("小米平板", "小米平板"),
        ("华为平板", "华为平板"),
        ("ThinkPad", "ThinkPad"), ("thinkpad", "ThinkPad"),
        ("戴尔", "戴尔"), ("dell", "戴尔"),
        ("惠普", "惠普"), ("hp", "惠普"),
        ("华硕", "华硕"), ("asus", "华硕"),
        ("宏碁", "宏碁"), ("acer", "宏碁"),
        ("微星", "微星"), ("msi", "微星"),
        ("机械革命", "机械革命"),
    ]
    for alias, brand in sorted(aliases, key=lambda x: -len(x[0])):
        if alias in t:
            return brand
    return None


def detect_category(text: str, brand: str = None):
    # 品牌强映射：MacBook/iPad/ThinkPad 等直接定品类
    if brand:
        brand_computer = {"MacBook", "ThinkPad", "华为电脑", "戴尔", "惠普", "联想电脑",
                          "华硕", "宏碁", "微星", "机械革命"}
        brand_pad = {"iPad", "小米平板", "华为平板", "荣耀平板", "OPPO平板", "vivo平板",
                     "三星平板", "联想平板"}
        brand_phone = {"苹果", "小米", "红米", "华为", "荣耀", "OPPO", "vivo",
                       "iQOO", "一加", "真我", "三星", "索尼", "努比亚",
                       "中兴", "联想", "摩托罗拉", "传音", "海信", "酷派"}
        if brand in brand_computer:
            return "电脑"
        if brand in brand_pad:
            return "平板"
        if brand in brand_phone:
            return "手机"
    # 兜底：靠关键词
    t = text.lower()
    t_en = _norm(text)
    for cat, kws in [
        ("电脑", ["macbook", "thinkpad", "notebook", "laptop"]),
        ("平板", ["ipad", "pad"]),
        ("耳机", ["airpod", "earphone"]),
        ("手表", ["watch", "band"]),
    ]:
        for kw in kws:
            if kw in t_en:
                return cat
    for cat, kws in [
        ("电脑", ["电脑", "笔记本", "游戏本", "轻薄本", "商务本"]),
        ("平板", ["平板"]),
        ("耳机", ["耳机", "蓝牙耳机"]),
        ("手表", ["手表", "智能手表", "手环"]),
    ]:
        for kw in kws:
            if kw in t:
                return cat
    return "手机"


def detect_condition(text: str):
    for c in COND_FACTOR:
        if c in text:
            return c
    return DEFAULT_COND


def detect_price(text: str) -> int | None:
    nums = re.findall(r"\d{4,}", text)
    for n in nums:
        v = int(n)
        if 300 <= v <= 99999:
            return v
    return None


def parse(raw: str) -> dict:
    brand = detect_brand(raw)
    category = detect_category(raw, brand)
    condition = detect_condition(raw)
    user_price = detect_price(raw)

    # ── 型号：MODEL_PRICE 归一化匹配（最长优先）──
    # MODEL_PRICE key = 英文品牌名+型号归一化（如 "苹果15pro" → "iphone15pro"）
    # 所以需要把中文品牌名替换成英文，再归一化
    raw_c = _norm(raw)
    if brand:
        # 中文品牌 → 英文（用于在 MODEL_PRICE key 中匹配）
        brand_en = {
            "苹果": "iphone", "小米": "xiaomi", "红米": "redmi",
            "华为": "huawei", "荣耀": "honor",
            "OPPO": "oppo", "vivo": "vivo", "iQOO": "iqoo",
            "三星": "galaxy", "索尼": "sony", "中兴": "axon",
            "努比亚": "nubia", "一加": "oneplus",
        }.get(brand)
        if brand_en:
            # 把 raw_c 里的中文品牌名替换成英文（如 "苹果15pro" → "iphone15pro"）
            cn_brand_norm = _norm(brand)
            raw_c = raw_c.replace(cn_brand_norm, brand_en)

    model = None
    market_price = None
    best_len = 0
    for m_key, p in sorted(MODEL_PRICE.items(), key=lambda x: -len(x[0])):
        if m_key in raw_c and len(m_key) > best_len:
            model = _restore_model_name(m_key)
            market_price = p
            best_len = len(m_key)

    # ── 字典没有 → 品牌随机选 + 品牌价格区间估算 ──
    if not model:
        if brand and brand in BRAND_MODELS:
            model = random.choice(BRAND_MODELS[brand])
        else:
            # 品牌也识别不了 → 从输入提取第一段作为品牌名
            parts = re.split(r"[\s,，、/]+", raw.strip())
            brand = parts[0] if parts else "苹果"
            model = raw.strip()  # 用原始输入作为型号显示
        # 用品牌价格区间估算：根据型号关键词判断档位
        brand_price_range = BRAND_PRICE_RANGE.get(brand, DEFAULT_PRICE.get(category, 2999))
        if isinstance(brand_price_range, tuple):
            low, high = brand_price_range
            raw_lower = raw.lower()
            # 高端关键词 → 取高价，低端关键词 → 取低价，都没命 → 取中间
            if any(kw in raw_lower for kw in MODEL_TIER_KEYWORDS["high"]):
                market_price = high
            elif any(kw in raw_lower for kw in MODEL_TIER_KEYWORDS["low"]):
                market_price = low
            else:
                market_price = (low + high) // 2
        else:
            market_price = brand_price_range

    # ── 品牌未知 → 从型号反推 ──
    if not brand:
        for b, models in BRAND_MODELS.items():
            for m in models:
                if _norm(m) in raw_c or raw_c in _norm(m):
                    brand = b
                    break
            if brand:
                break
        brand = brand or "苹果"

    # ── 定价 ──
    color = random.choice(COLORS.get(category, COLORS["手机"]))
    factor = COND_FACTOR.get(condition, 0.72)
    recycle = (int(market_price * factor) // 50) * 50
    sell_price = user_price if user_price else recycle

    return {
        "brand": brand,
        "model": model,
        "category": category,
        "condition": condition,
        "color": color,
        "market_price": market_price,
        "sell_price": sell_price,
        "price_estimated": (best_len == 0),  # 字典没有命中时标记估算
    }


def _restore_model_name(key: str) -> str:
    """把归一化的英文 key 还原成标准显示名"""
    known = {
        # Apple
        "iphone15promax": "iPhone 15 Pro Max", "iphone15pro": "iPhone 15 Pro",
        "iphone15": "iPhone 15", "iphone14promax": "iPhone 14 Pro Max",
        "iphone14pro": "iPhone 14 Pro", "iphone14": "iPhone 14",
        "iphone13": "iPhone 13", "iphone16promax": "iPhone 16 Pro Max",
        "macbookpro14": "MacBook Pro 14", "macbookpro16": "MacBook Pro 16",
        "macbookair13": "MacBook Air 13", "macbookair15": "MacBook Air 15",
        "ipadpro12.9": "iPad Pro 12.9", "ipadpro11": "iPad Pro 11",
        "ipadair11": "iPad Air 11", "ipad10": "iPad 10",
        # Xiaomi
        "xiaomi15": "小米15", "xiaomi14ultra": "小米14 Ultra",
        "xiaomi14pro": "小米14 Pro", "xiaomi14": "小米14",
        "xiaomi13pro": "小米13 Pro", "xiaomi13": "小米13",
        # Redmi
        "redmik70pro": "Redmi K70 Pro", "redmik70": "Redmi K70",
        "redminote13": "Redmi Note 13",
        # Samsung
        "galaxys25ultra": "Galaxy S25 Ultra", "galaxys25": "Galaxy S25",
        "galaxyzfold6": "Galaxy Z Fold6", "galaxyzflip6": "Galaxy Z Flip6",
        # Huawei
        "mate70pro": "Mate 70 Pro", "mate60": "Mate 60",
        "p70pro": "P70 Pro", "p70": "P70",
        # Honor
        "honormagic6pro": "荣耀Magic 6 Pro", "honormagic6": "荣耀Magic 6",
        # vivo
        "x200pro": "X200 Pro", "x200": "X200",
        "x100pro": "X100 Pro", "x100": "X100",
        # iQOO
        "iqoo13": "iQOO 13", "iqooneo10": "iQOO Neo 10",
        # OnePlus
        "oneplus12": "OnePlus 12", "oneplusace4": "OnePlus Ace 4",
        # OPPO
        "findx8pro": "Find X8 Pro", "findx8": "Find X8",
        "reno13": "Reno 13", "reno12": "Reno 12",
        # realme
        "realmegt5": "realme GT5", "realmepro": "realme 13 Pro",
        "realme13pro": "realme 13 Pro",
        # Sony
        "xperia1vi": "Xperia 1 VI", "xperia5v": "Xperia 5 V",
        # Nubia
        "nubiaz60ultra": "Nubia Z60 Ultra",
        # ZTE
        "axon60": "Axon 60",
        # Motorola
        "motoedge50": "moto edge 50", "motox50": "moto X50",
        # ThinkPad
        "thinkpadx1carbon": "ThinkPad X1 Carbon", "thinkpadt14": "ThinkPad T14",
        # Xiaomi Pad
        "xiaomipad7pro": "小米平板7 Pro", "xiaomipad7": "小米平板7",
    }
    return known.get(key, key)


def auto_fill(raw: str) -> dict:
    return parse(raw)


def describe_product(info: dict) -> str:
    price_note = " ⚠️估算" if info.get("price_estimated") else ""
    return (
        f"品类: {info['category']} | 品牌: {info['brand']} | 型号: {info['model']}{price_note} | "
        f"成色: {info['condition']} | 颜色: {info['color']} | 定价: {info['sell_price']}"
    )
