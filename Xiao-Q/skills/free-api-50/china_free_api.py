# -*- coding: utf-8 -*-
"""
Clawhub 免费中国API Skill V6.0
完全免费 | 无密钥 | 无次数限制 | 国内接口
"""
import requests
import urllib.parse
import random
import string
from clawhub import Skill, skill_command

class ChinaFreeAPISkill(Skill):
    def __init__(self):
        super().__init__(
            name="china_free_api",
            description="中国免费API大全：天气、快递、股票、油价、日历、IP、二维码、去水印、百科、汇率、OCR、周公解梦、高校、拼音、表情包、热量等",
            version="6.0.0",
            author="Clawhub Developer"
        )

    # ====================== 1. 天气 ======================
    @skill_command("weather")
    def get_weather(self, city: str):
        try:
            url = f"http://wttr.in/{city}?format=j1"
            res = requests.get(url, timeout=10).json()
            w = res['current_condition'][0]
            return (
                f"🌤 {city}天气\n"
                f"温度：{w['temp_C']}℃\n"
                f"天气：{w['weatherDesc'][0]['value']}\n"
                f"湿度：{w['humidity']}%\n"
                f"风速：{w['windspeedKmph']}km/h"
            )
        except:
            return "❌ 天气查询失败"

    # ====================== 2. 手机号归属地 ======================
    @skill_command("phone")
    def get_phone_info(self, phone: str):
        if len(phone) != 11 or not phone.isdigit():
            return "❌ 请输入11位手机号"
        try:
            url = f"https://api.muxiaoguo.cn/api/mobile?phone={phone}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"📱 手机号：{phone}\n"
                    f"归属地：{d['province']}{d['city']}\n"
                    f"运营商：{d['corp']}"
                )
        except:
            pass
        return "❌ 查询失败"

    # ====================== 3. 快递 ======================
    @skill_command("express")
    def get_express(self, no: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/kuaidi?no={no}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                data = res["data"]
                ret = f"🚚 快递：{no}\n状态：{data['state']}\n"
                for item in data["list"][:5]:
                    ret += f"{item['time']}\n{item['context']}\n"
                return ret
        except:
            pass
        return "❌ 快递查询失败"

    # ====================== 4. 新闻 ======================
    @skill_command("news")
    def get_news(self, t="top"):
        try:
            url = f"https://api.muxiaoguo.cn/api/toutiao?type={t}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                ret = "📰 热点新闻\n"
                for i, n in enumerate(res["data"][:5], 1):
                    ret += f"{i}. {n['title']}\n"
                return ret
        except:
            pass
        return "❌ 获取新闻失败"

    # ====================== 5. 垃圾分类 ======================
    @skill_command("rubbish")
    def rubbish(self, name: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/lajifenlei?word={name}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return f"♻️ {d['name']} → {d['type']}\n{d['explain']}"
        except:
            pass
        return "❌ 未找到分类"

    # ====================== 6. A股股票 ======================
    @skill_command("stock")
    def stock(self, code: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/a_stock?msg={code}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"📈 {d['name']}({d['code']})\n"
                    f"现价：{d['price']} 元\n"
                    f"涨跌：{d['change']} {d['change_percent']}\n"
                    f"开：{d['open']} 高：{d['high']} 低：{d['low']}"
                )
        except:
            pass
        return "❌ 股票查询失败"

    # ====================== 7. 油价 ======================
    @skill_command("oil")
    def oil(self):
        try:
            url = "https://api.muxiaoguo.cn/api/youjia"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"⛽ 今日油价\n"
                    f"92号：{d['p92']} 元/升\n"
                    f"95号：{d['p95']} 元/升\n"
                    f"98号：{d['p98']} 元/升\n"
                    f"柴油：{d['p0']} 元/升"
                )
        except:
            pass
        return "❌ 油价查询失败"

    # ====================== 8. 日历 ======================
    @skill_command("calendar")
    def calendar(self):
        try:
            url = "https://api.muxiaoguo.cn/api/calendar"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"📅 今日日历\n"
                    f"公历：{d['date']} {d['week']}\n"
                    f"农历：{d['nongli']}\n"
                    f"宜：{d['yi']}\n"
                    f"忌：{d['ji']}"
                )
        except:
            pass
        return "❌ 日历查询失败"

    # ====================== 9. 成语 ======================
    @skill_command("idiom")
    def idiom(self, word: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/chengyu?word={word}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"📖 成语：{d['name']}\n"
                    f"拼音：{d['pinyin']}\n"
                    f"解释：{d['explain']}\n"
                    f"出处：{d['source']}"
                )
        except:
            pass
        return "❌ 成语查询失败"

    # ====================== 10. 歌词 ======================
    @skill_command("lyric")
    def lyric(self, song: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/geci?msg={song}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200 and res["data"]["lyric"]:
                d = res["data"]
                return f"🎵 {d['song']} - {d['singer']}\n\n{d['lyric'][:800]}..."
        except:
            pass
        return "❌ 未找到歌词"

    # ====================== 11. 随机壁纸 ======================
    @skill_command("wallpaper")
    def wallpaper(self, tp="fengjing"):
        try:
            url = f"https://api.muxiaoguo.cn/api/bizhi?type={tp}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🖼️ 随机壁纸：{res['data']['url']}"
        except:
            pass
        return "❌ 获取壁纸失败"

    # ====================== 12. IP查询 ======================
    @skill_command("ip")
    def ip_info(self, ip: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/ip?ip={ip}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🌐 IP信息：{ip}\n"
                    f"位置：{d['position']}\n"
                    f"运营商：{d['isp']}"
                )
        except:
            pass
        return "❌ IP查询失败"

    # ====================== 13. 二维码生成 ======================
    @skill_command("qrcode")
    def qrcode(self, text: str):
        try:
            enc = urllib.parse.quote(text)
            url = f"https://api.muxiaoguo.cn/api/qr?text={enc}"
            return f"📱 二维码：{url}"
        except:
            return "❌ 生成失败"

    # ====================== 14. 抖音去水印 ======================
    @skill_command("dy")
    def douyin(self, url: str):
        try:
            api = f"https://api.muxiaoguo.cn/api/dy?url={url}"
            res = requests.get(api, timeout=15).json()
            if res["code"] == 200:
                return (
                    f"🎬 去水印成功\n"
                    f"标题：{res['data']['title']}\n"
                    f"无水印视频：{res['data']['video_url']}"
                )
        except:
            pass
        return "❌ 解析失败（仅支持抖音）"

    # ====================== 15. 短链接 ======================
    @skill_command("short")
    def short_url(self, long_url: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/short?url={long_url}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                return f"🔗 短链接：{res['data']['url']}"
        except:
            pass
        return "❌ 生成短链接失败"

    # ====================== 16. 手机号吉凶 ======================
    @skill_command("phoneluck")
    def phone_luck(self, phone: str):
        if len(phone) != 11:
            return "❌ 请输入11位手机号"
        try:
            url = f"https://api.muxiaoguo.cn/api/phonejl?phone={phone}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🔮 手机号分析：{phone}\n"
                    f"评分：{d['score']}\n"
                    f"结果：{d['result']}\n"
                    f"分析：{d['analysis']}"
                )
        except:
            pass
        return "❌ 查询失败"

    # ====================== 17. 百科查询 ======================
    @skill_command("wiki")
    def wiki(self, keyword: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/baike?msg={keyword}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                d = res["data"]
                content = d['content'].replace('<br>', '\n')[:600]
                return f"📚 {d['title']}\n\n{content}..."
        except:
            pass
        return "❌ 百科查询失败"

    # ====================== 18. 随机一言 ======================
    @skill_command("word")
    def random_word(self):
        try:
            url = "https://api.muxiaoguo.cn/api/yiyan"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"✍️ {res['data']['content']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 19. 汇率查询 ======================
    @skill_command("exchange")
    def exchange(self, money="100"):
        try:
            url = f"https://api.muxiaoguo.cn/api/huilv?money={money}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"💱 人民币汇率 ({money}元)\n"
                    f"美元：{d['usd']}\n"
                    f"欧元：{d['eur']}\n"
                    f"港币：{d['hkd']}\n"
                    f"日元：{d['jpy']}"
                )
        except:
            pass
        return "❌ 汇率查询失败"

    # ====================== 20. 随机笑话 ======================
    @skill_command("joke")
    def joke(self):
        try:
            url = "https://api.muxiaoguo.cn/api/joke"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"😂 {res['data']['content']}"
        except:
            pass
        return "❌ 获取笑话失败"

    # ====================== 21. 古诗词查询 ======================
    @skill_command("poem")
    def poem(self, keyword: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/gushi?msg={keyword}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"📜 {d['title']} - {d['author']}\n"
                    f"{d['content']}\n"
                    f"注释：{d['note']}"
                )
        except:
            pass
        return "❌ 未找到古诗词"

    # ====================== 22. 星座运势 ======================
    @skill_command("star")
    def star(self, sign: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/star?msg={sign}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"✨ {d['name']}今日运势\n"
                    f"综合：{d['comprehensive']}\n"
                    f"爱情：{d['love']}\n"
                    f"事业：{d['career']}\n"
                    f"财运：{d['money']}"
                )
        except:
            pass
        return "❌ 星座查询失败（输入：白羊/金牛/双子/巨蟹/狮子/处女/天秤/天蝎/射手/摩羯/水瓶/双鱼）"

    # ====================== 23. 车牌归属地 ======================
    @skill_command("plate")
    def plate(self, plate: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/car?msg={plate}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🚗 车牌{plate}归属地：{res['data']['area']}"
        except:
            pass
        return "❌ 车牌查询失败"

    # ====================== 24. 翻译（中英） ======================
    @skill_command("translate")
    def translate(self, text: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/translate?msg={text}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                return f"🔤 翻译结果：{res['data']['result']}"
        except:
            pass
        return "❌ 翻译失败"

    # ====================== 25. 成语接龙 ======================
    @skill_command("idiomlink")
    def idiom_link(self, word: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/chengyujl?msg={word}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🔗 成语接龙：{res['data']['result']}"
        except:
            pass
        return "❌ 接龙失败"

    # ====================== 26. 倒计时/纪念日 ======================
    @skill_command("countdown")
    def countdown(self, date: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/countdown?date={date}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"⏰ 距离{date}还有{res['data']['days']}天"
        except:
            pass
        return "❌ 倒计时失败（格式：2026-05-01）"

    # ====================== 27. 历史上的今天 ======================
    @skill_command("history")
    def history(self):
        try:
            url = "https://api.muxiaoguo.cn/api/history"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                ret = "📜 历史上的今天\n"
                for i, h in enumerate(res["data"][:5], 1):
                    ret += f"{i}. {h['year']}年：{h['content']}\n"
                return ret
        except:
            pass
        return "❌ 获取历史事件失败"

    # ====================== 28. IP精准定位 ======================
    @skill_command("ipprecise")
    def ip_precise(self, ip: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/ip2?ip={ip}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🌍 IP精准定位：{ip}\n"
                    f"国家：{d['country']}\n"
                    f"省份：{d['province']}\n"
                    f"城市：{d['city']}\n"
                    f"运营商：{d['isp']}\n"
                    f"经纬度：{d['lat']},{d['lon']}"
                )
        except:
            pass
        return "❌ 精准定位失败"

    # ====================== 29. 随机头像 ======================
    @skill_command("avatar")
    def avatar(self, type="anime"):
        try:
            url = f"https://api.muxiaoguo.cn/api/avatar?type={type}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"👤 随机头像：{res['data']['url']}"
        except:
            pass
        return "❌ 获取头像失败"

    # ====================== 30. 二维码解码 ======================
    @skill_command("qrcodedecode")
    def qrcode_decode(self, url: str):
        try:
            api = f"https://api.muxiaoguo.cn/api/qrdecode?url={url}"
            res = requests.get(api, timeout=10).json()
            if res["code"] == 200:
                return f"🔍 解码结果：{res['data']['result']}"
        except:
            pass
        return "❌ 解码失败"

    # ====================== 31. 4K壁纸 ======================
    @skill_command("wallpaper4k")
    def wallpaper4k(self, type="4k"):
        try:
            url = f"https://api.muxiaoguo.cn/api/bizhi4k?type={type}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🖼️ 4K壁纸：{res['data']['url']}"
        except:
            pass
        return "❌ 获取壁纸失败"

    # ====================== 32. 7天天气预报 ======================
    @skill_command("weather7")
    def weather7(self, city: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/tianqi7?city={city}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                ret = f"🌦️ {city} 未来7天天气预报\n"
                for item in res["data"]:
                    ret += f"{item['date']} {item['week']} {item['weather']} {item['temp']}\n"
                return ret
        except:
            pass
        return "❌ 7天天气预报失败"

    # ====================== 33. 24小时预报 ======================
    @skill_command("weather24")
    def weather24(self, city: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/tianqi24?city={city}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                ret = f"⏱️ {city} 24小时预报\n"
                for item in res["data"][:8]:
                    ret += f"{item['time']} {item['weather']} {item['temp']}℃\n"
                return ret
        except:
            pass
        return "❌ 24小时预报失败"

    # ====================== 34. 随机密码生成 ======================
    @skill_command("password")
    def password(self, length: int = 12):
        try:
            chars = string.ascii_letters + string.digits + "!@#$%^&*()"
            pwd = ''.join(random.choice(chars) for _ in range(length))
            return f"🔐 随机密码：{pwd}"
        except:
            return "❌ 生成失败"

    # ====================== 35. 随机姓名生成 ======================
    @skill_command("name")
    def name(self, gender: str = "男"):
        try:
            url = f"https://api.muxiaoguo.cn/api/name?sex={gender}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"📛 随机{gender}姓名：{res['data']['name']}"
        except:
            pass
        return "❌ 姓名生成失败"

    # ====================== 36. 土味情话 ======================
    @skill_command("love")
    def love(self):
        try:
            url = "https://api.muxiaoguo.cn/api/qinghua"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"💘 {res['data']['content']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 37. 随机美女图片 ======================
    @skill_command("girl")
    def girl(self):
        try:
            url = "https://api.muxiaoguo.cn/api/girl"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"👩 美女图片：{res['data']['pic']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 38. 随机动漫图片 ======================
    @skill_command("anime")
    def anime(self):
        try:
            url = "https://api.muxiaoguo.cn/api/anime"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🎨 动漫图片：{res['data']['pic']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 39. 随机狗狗图片 ======================
    @skill_command("dog")
    def dog(self):
        try:
            url = "https://api.muxiaoguo.cn/api/dog"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🐶 狗狗图片：{res['data']['pic']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 40. 随机猫咪图片 ======================
    @skill_command("cat")
    def cat(self):
        try:
            url = "https://api.muxiaoguo.cn/api/cat"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🐱 猫咪图片：{res['data']['pic']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 41. 常用网址导航 ======================
    @skill_command("nav")
    def nav(self):
        try:
            url = "https://api.muxiaoguo.cn/api/nav"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                ret = "🔗 常用网址\n"
                for k, v in res["data"].items():
                    ret += f"{k}：{v}\n"
                return ret
        except:
            pass
        return "❌ 获取失败"

    # ====================== 42. 全国城市列表 ======================
    @skill_command("city")
    def city(self):
        try:
            url = "https://api.muxiaoguo.cn/api/city"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                return f"🏙️ 全国城市数量：{len(res['data'])} 个"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 43. 简繁体转换 ======================
    @skill_command("traditional")
    def traditional(self, text: str):
        try:
            enc = urllib.parse.quote(text)
            url = f"https://api.muxiaoguo.cn/api/jianfan?msg={enc}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                return f"📝 繁体：{res['data']['result']}"
        except:
            pass
        return "❌ 转换失败"

    # ====================== 44. 银行卡归属地查询 ======================
    @skill_command("bank")
    def bank(self, card: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/bank?card={card}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"💳 银行卡：{card}\n"
                    f"银行：{d['bank']}\n"
                    f"卡种：{d['type']}\n"
                    f"logo：{d['logo']}"
                )
        except:
            pass
        return "❌ 银行卡查询失败"

    # ====================== 【新增】45. 周公解梦 ======================
    @skill_command("dream")
    def dream(self, keyword: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/dream?msg={keyword}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return f"🌙 梦见{keyword}：{d['content']}"
        except:
            pass
        return "❌ 解梦失败"

    # ====================== 【新增】46. 新闻分类 ======================
    @skill_command("newstype")
    def newstype(self, type: str):
        try:
            # 支持：top, guonei, guoji, shehui, keji, yule, tiyu, caijing
            url = f"https://api.muxiaoguo.cn/api/toutiao?type={type}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                ret = f"📰 {type}新闻\n"
                for i, n in enumerate(res["data"][:5], 1):
                    ret += f"{i}. {n['title']}\n"
                return ret
        except:
            pass
        return "❌ 获取新闻失败"

    # ====================== 【新增】47. 随机表情包 ======================
    @skill_command("emote")
    def emote(self):
        try:
            url = "https://api.muxiaoguo.cn/api/emoji"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"😜 表情包：{res['data']['url']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 【新增】48. 车牌估值 ======================
    @skill_command("carprice")
    def carprice(self, plate: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/carprice?msg={plate}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🚙 车牌{plate} 估值：{res['data']['price']}"
        except:
            pass
        return "❌ 车牌估值失败"

    # ====================== 【新增】49. 歌曲搜索 ======================
    @skill_command("song")
    def song(self, name: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/music?msg={name}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🎵 {d['title']} - {d['singer']}\n"
                    f"链接：{d['url']}"
                )
        except:
            pass
        return "❌ 歌曲搜索失败"

    # ====================== 【新增】50. 图片OCR文字识别 ======================
    @skill_command("ocr")
    def ocr(self, pic_url: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/ocr?url={pic_url}"
            res = requests.get(url, timeout=15).json()
            if res["code"] == 200:
                return f"📝 识别结果：{res['data']['content']}"
        except:
            pass
        return "❌ OCR识别失败"

    # ====================== 【新增】51. 全国高校查询 ======================
    @skill_command("school")
    def school(self, name: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/school?msg={name}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🎓 {d['name']}\n"
                    f"省份：{d['province']}\n"
                    f"层次：{d['level']}\n"
                    f"类型：{d['type']}"
                )
        except:
            pass
        return "❌ 高校查询失败"

    # ====================== 【新增】52. 汉字转拼音 ======================
    @skill_command("pinyin")
    def pinyin(self, text: str):
        try:
            enc = urllib.parse.quote(text)
            url = f"https://api.muxiaoguo.cn/api/pinyin?msg={enc}"
            res = requests.get(url, timeout=10).json()
            if res["code"] == 200:
                return f"🔡 拼音：{res['data']['pinyin']}"
        except:
            pass
        return "❌ 拼音转换失败"

    # ====================== 【新增】53. 随机二次元壁纸 ======================
    @skill_command("acg")
    def acg(self):
        try:
            url = "https://api.muxiaoguo.cn/api/acg"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                return f"🌸 二次元壁纸：{res['data']['pic']}"
        except:
            pass
        return "❌ 获取失败"

    # ====================== 【新增】54. 食物热量查询 ======================
    @skill_command("food")
    def food(self, name: str):
        try:
            url = f"https://api.muxiaoguo.cn/api/food?msg={name}"
            res = requests.get(url, timeout=8).json()
            if res["code"] == 200:
                d = res["data"]
                return (
                    f"🥗 {d['name']}\n"
                    f"热量：{d['calorie']}\n"
                    f"蛋白质：{d['protein']}\n"
                    f"脂肪：{d['fat']}"
                )
        except:
            pass
        return "❌ 食物热量查询失败"

if __name__ == "__main__":
    skill = ChinaFreeAPISkill()
    skill.run()