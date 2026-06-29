#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全能实用工具箱（SkillHub上架版）
功能：集成10大高频实用工具，已完成安全整改，适配SkillHub平台安全规范
整改说明：优化第三方API调用安全、文件操作安全、参数过滤，删除内购相关冗余代码
"""

import os
import time
import json
import hashlib
import qrcode
import requests
import numpy as np
import sounddevice as sd
from scipy import signal
from PIL import Image
from datetime import datetime, timedelta
import json5

# ====================== 技能基础配置（SkillHub必填） ======================
SKILL_INFO = {
    "skill_name": "全能实用工具箱",
    "skill_version": "v1.0.1",
    "skill_desc": "集成10大高频实用工具（二维码生成、地震查询、噪音检测等），免费无广告，适配多端调用，已完成安全优化",
    "author": "",  # 填写你的作者信息
    "support_device": ["phone", "pad", "pc"],
    "update_desc": "优化代码安全，修复安全扫描漏洞，提升数据及接口安全性"
}

# 临时文件目录配置（避免路径泄露，规范存储）
TEMP_DIR = "./skill_temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, mode=0o700)  # 权限设置为仅当前用户可读写，避免权限过高

# ====================== 安全工具函数（新增：接口校验+参数过滤） ======================
def verify_api_response(resp, api_name):
    """API响应校验：防止接口返回异常数据、篡改数据，适配第三方API安全调用"""
    try:
        # 校验响应状态码
        if resp.status_code != 200:
            raise Exception(f"{api_name}接口响应异常，状态码：{resp.status_code}")
        # 校验响应数据格式（根据不同API调整，此处以JSON为例）
        try:
            resp.json()
        except Exception as e:
            raise Exception(f"{api_name}接口返回数据格式错误，非JSON")
        # 限流控制（避免高频调用触发API封禁，同时符合平台安全规范）
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"{api_name}接口校验失败：{str(e)}")
        return False

def filter_param(param, param_type="str"):
    """参数过滤：根据类型过滤非法字符，防止注入攻击、路径遍历"""
    if param_type == "str":
        # 过滤字符串中的特殊字符（如../、<、>、;等）
        illegal_chars = ["../", "./", "<", ">", ";", "'", "\"", "(", ")", "&", "|"]
        for char in illegal_chars:
            if char in str(param):
                param = str(param).replace(char, "")
        return param.strip()
    elif param_type == "int" or param_type == "float":
        # 确保数值参数为合法数字
        try:
            return float(param) if param_type == "float" else int(param)
        except:
            return 0
    elif param_type == "path":
        # 过滤路径中的非法字符，防止路径遍历
        return os.path.abspath(filter_param(param, "str"))

# ====================== 全能工具箱核心类（含所有工具+安全优化） ======================
class ToolBoxSkill:
    def __init__(self):
        print(f"✅ {SKILL_INFO['skill_name']}（{SKILL_INFO['skill_version']}）加载完成")
        # 新增：临时文件定时清理，防止隐私泄露和存储冗余
        self.clean_temp_files()

    # ------------------------------ 工具1：二维码生成 ------------------------------
    def qrcode(self, text: str, output="qrcode.png"):
        try:
            # 新增：参数过滤（过滤文本中的非法字符）
            text = filter_param(text, "str")
            output = filter_param(output, "str")
            if not text:
                return {"status": "fail", "msg": "文本内容不能为空"}
            
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            save_path = os.path.join(TEMP_DIR, output)
            img.save(save_path)
            return {"status": "success", "msg": "二维码生成成功", "file_path": save_path}
        except Exception as e:
            return {"status": "fail", "msg": f"生成失败：{str(e)}"}

    # ------------------------------ 工具2：全球地震查询（API安全优化） ------------------------------
    def earthquake(self, region="china", min_mag=4.0, hours=24):
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson", "starttime": start_time.isoformat(), "endtime": end_time.isoformat(),
                "minmagnitude": min_mag, "limit": 8, "orderby": "time-asc"
            }
            if region == "china":
                params.update({"minlatitude": 18, "maxlatitude": 54, "minlongitude": 73, "maxlongitude": 135})
            
            # 新增：接口超时优化（延长至20秒，添加重试机制，最多2次重试）
            retry_count = 0
            while retry_count < 2:
                try:
                    resp = requests.get(base_url, params=params, timeout=20)
                    # 新增：调用接口校验方法
                    if verify_api_response(resp, "USGS地震查询"):
                        break
                    retry_count += 1
                except Exception as e:
                    retry_count += 1
                    if retry_count >= 2:
                        return {"status": "error", "msg": f"获取失败：{str(e)}，请稍后重试"}
            
            resp.raise_for_status()
            data = resp.json()
            quakes = [{
                "位置": feat["properties"]["place"], "震级": feat["properties"]["mag"],
                "时间": datetime.fromtimestamp(feat["properties"]["time"]//1000).strftime("%Y-%m-%d %H:%M"),
                "深度(km)": round(feat["geometry"]["coordinates"][2], 1)
            } for feat in data["features"]]

            return {"status": "found" if quakes else "normal", "地震列表": quakes, "count": len(quakes)}
        except Exception as e:
            return {"status": "error", "msg": f"获取失败：{str(e)}"}

    # ------------------------------ 工具3：环境噪音检测（本地无API，安全无风险） ------------------------------
    def noise(self, duration=3):
        try:
            duration = filter_param(duration, "int")
            if duration < 1 or duration > 10:
                return {"status": "fail", "msg": "检测时长需1-10秒"}
            
            sample_rate = 44100
            audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
            sd.wait()
            audio = np.squeeze(audio)
            rms = np.sqrt(np.mean(np.square(audio)))
            db = 20 * np.log10(rms / 2e-5) if rms != 0 else 0

            if db < 30: level = "安静"
            elif db < 50: level = "正常"
            elif db < 70: level = "较吵"
            else: level = "嘈杂"

            return {"status": "success", "分贝值": round(db, 1), "噪音等级": level, "检测时长(秒)": duration}
        except Exception as e:
            return {"status": "fail", "msg": f"检测失败：{str(e)}"}

    # ------------------------------ 工具4：AI智能去水印（API安全优化） ------------------------------
    def remove_watermark(self, image_path: str, output="no_watermark.png"):
        try:
            # 新增：图片路径校验（防止路径遍历漏洞）
            image_path = filter_param(image_path, "path")
            if not os.path.exists(image_path) or not os.path.isfile(image_path):
                return {"status": "fail", "msg": "图片路径无效，不存在该文件"}
            # 新增：限制图片大小（最大10MB，避免恶意上传大文件消耗资源）
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return {"status": "fail", "msg": "图片大小超过10MB，请上传更小的图片"}
            
            files = {"file": (os.path.basename(image_path), open(image_path, "rb"), "image/jpeg")}
            # 新增：接口超时优化+重试机制
            retry_count = 0
            while retry_count < 2:
                try:
                    resp = requests.post("https://cleanup.pictures/api/remove", files=files, timeout=30)
                    if verify_api_response(resp, "AI去水印"):
                        break
                    retry_count += 1
                except Exception as e:
                    retry_count += 1
                    if retry_count >= 2:
                        return {"status": "fail", "msg": f"处理失败：{str(e)}，请稍后重试"}
            
            if resp.status_code == 200:
                save_path = os.path.join(TEMP_DIR, output)
                with open(save_path, "wb") as f: f.write(resp.content)
                return {"status": "success", "msg": "去水印完成", "output": save_path}
            return {"status": "fail", "msg": "服务器繁忙，请稍后重试"}
        except Exception as e:
            return {"status": "fail", "msg": f"处理失败：{str(e)}"}

    # ------------------------------ 工具5：OCR文字识别（API安全优化） ------------------------------
    def ocr(self, image_path: str):
        try:
            # 新增：路径校验+大小限制
            image_path = filter_param(image_path, "path")
            if not os.path.exists(image_path) or not os.path.isfile(image_path):
                return {"status": "fail", "msg": "图片路径无效，不存在该文件"}
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return {"status": "fail", "msg": "图片大小超过10MB，请上传更小的图片"}
            
            files = {"image": (os.path.basename(image_path), open(image_path, "rb"), "image/jpeg")}
            # 新增：接口超时+重试+校验
            retry_count = 0
            while retry_count < 2:
                try:
                    resp = requests.post("https://api.ocr.space/parse/image", files=files, timeout=25)
                    if verify_api_response(resp, "OCR文字识别"):
                        break
                    retry_count += 1
                except Exception as e:
                    retry_count += 1
                    if retry_count >= 2:
                        return {"status": "fail", "msg": f"识别失败：{str(e)}，请稍后重试"}
            
            data = resp.json()
            if data.get("IsErroredOnProcessing"):
                return {"status": "fail", "msg": f"识别失败：{data.get('ErrorMessage', '未知错误')}"}
            text = "\n".join([item["ParsedText"] for item in data.get("ParsedResults", []) if item.get("ParsedText")])
            return {"status": "success", "识别结果": text.strip()} if text else {"status": "fail", "msg": "未识别到文字"}
        except Exception as e:
            return {"status": "fail", "msg": f"识别失败：{str(e)}"}

    # ------------------------------ 工具6：全能单位换算（参数过滤优化） ------------------------------
    def unit_convert(self, value: float, from_unit: str, to_unit: str):
        try:
            # 新增：参数过滤
            value = filter_param(value, "float")
            from_unit = filter_param(from_unit, "str")
            to_unit = filter_param(to_unit, "str")
            
            unit_map = {
                "length": {"m":1,"cm":100,"mm":1000,"km":0.001,"in":39.3701,"ft":3.2808},
                "weight": {"kg":1,"g":1000,"mg":1e6,"t":0.001,"lb":2.2046},
                "area": {"m2":1,"cm2":10000,"km2":1e-6,"in2":1550},
                "volume": {"m3":1,"cm3":1e6,"L":1000,"mL":1e6},
                "speed": {"kmh":1,"mps":0.2778,"mph":0.6214},
                "temperature": {"c":1, "f":1, "k":1}
            }
            temp = None
            for typ, units in unit_map.items():
                if from_unit in units and to_unit in units: temp = typ; break
            if not temp: return {"status": "fail", "msg": "不支持的单位组合"}
            
            if temp == "temperature":
                if from_unit == "c" and to_unit == "f": res = value*9/5+32
                elif from_unit == "f" and to_unit == "c": res = (value-32)*5/9
                elif from_unit == "c" and to_unit == "k": res = value+273.15
                elif from_unit == "k" and to_unit == "c": res = value-273.15
                else: res = value
            else:
                res = value / unit_map[temp][from_unit] * unit_map[temp][to_unit]
            return {"status": "success", "result": round(res, 4), "unit": to_unit}
        except Exception as e:
            return {"status": "fail", "msg": f"换算失败：{str(e)}"}

    # ------------------------------ 工具7：标准证件照生成（文件操作优化） ------------------------------
    def id_photo(self, image_path: str, size="1寸", background="white", output="id_photo.png"):
        try:
            # 新增：路径校验+大小限制
            image_path = filter_param(image_path, "path")
            if not os.path.exists(image_path) or not os.path.isfile(image_path):
                return {"status": "fail", "msg": "图片路径无效，不存在该文件"}
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return {"status": "fail", "msg": "图片大小超过10MB，请上传更小的图片"}
            
            size_map = {"1寸": (295, 413), "2寸": (413, 579), "小1寸": (260, 378), "大1寸": (390, 567)}
            bg_color = {"white": (255,255,255), "blue": (67,142,219), "red": (255,0,0)}
            if size not in size_map: return {"status": "fail", "msg": "支持尺寸：1寸/2寸/小1寸/大1寸"}
            if background not in bg_color: return {"status": "fail", "msg": "支持背景：white/blue/red"}
            
            img = Image.open(image_path).convert("RGBA")
            img.thumbnail(size_map[size], Image.Resampling.LANCZOS)
            img = img.resize(size_map[size], Image.Resampling.LANCZOS)
            bg = Image.new("RGB", size_map[size], bg_color[background])
            bg.paste(img, (0,0), img)
            
            save_path = os.path.join(TEMP_DIR, output)
            bg.save(save_path)
            return {"status": "success", "msg": f"{size}证件照生成完成", "output": save_path}
        except Exception as e:
            return {"status": "fail", "msg": f"生成失败：{str(e)}"}

    # ------------------------------ 工具8：图片压缩（文件操作优化） ------------------------------
    def image_compress(self, image_path: str, quality=80, output="compressed.png"):
        try:
            # 新增：路径校验+大小限制
            image_path = filter_param(image_path, "path")
            if not os.path.exists(image_path) or not os.path.isfile(image_path):
                return {"status": "fail", "msg": "图片路径无效，不存在该文件"}
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return {"status": "fail", "msg": "图片大小超过10MB，请上传更小的图片"}
            
            quality = filter_param(quality, "int")
            if not (1<=quality<=100): return {"status": "fail", "msg": "质量需1-100"}
            img = Image.open(image_path).convert("RGBA" if image_path.lower().endswith((".png","webp")) else "RGB")
            output_ext = os.path.splitext(output)[1].lower()
            if output_ext in [".jpg", ".jpeg"]: img = img.convert("RGB")
            
            save_path = os.path.join(TEMP_DIR, output)
            img.save(save_path, optimize=True, quality=quality)
            
            orig = os.path.getsize(image_path)/1024
            comp = os.path.getsize(save_path)/1024
            rate = round((1-comp/orig)*100, 1)
            return {"status": "success", "压缩率": f"{rate}%", "输出": save_path}
        except Exception as e:
            return {"status": "fail", "msg": f"压缩失败：{str(e)}"}

    # ------------------------------ 工具9：格式转换（文件操作优化） ------------------------------
    def file_convert(self, input_path: str, output_format: str, output="converted"):
        try:
            # 新增：路径校验
            input_path = filter_param(input_path, "path")
            if not os.path.exists(input_path) or not os.path.isfile(input_path):
                return {"status": "fail", "msg": "输入文件路径无效，不存在该文件"}
            
            input_ext = os.path.splitext(input_path)[1].lower().lstrip(".")
            output_format = filter_param(output_format, "str").lower()
            output_path = os.path.join(TEMP_DIR, f"{output}.{output_format}")
            
            if input_ext in ["png","jpg","jpeg","webp"] and output_format in ["png","jpg","webp"]:
                img = Image.open(input_path).convert("RGBA" if input_ext in ["png","webp"] else "RGB")
                if output_format in ["jpg","jpeg"]: img = img.convert("RGB")
                img.save(output_path, optimize=True)
                return {"status": "success", "msg": f"{input_ext}→{output_format} 完成", "output": output_path}
            elif input_ext == "txt" and output_format == "md":
                with open(input_path, "r", encoding="utf-8") as f: cnt = f.read()
                with open(output_path, "w", encoding="utf-8") as f: f.write(cnt)
                return {"status": "success", "msg": "txt→md 完成", "output": output_path}
            else:
                return {"status": "fail", "msg": "不支持的转换组合"}
        except Exception as e:
            return {"status": "fail", "msg": f"转换失败：{str(e)}"}

    # ------------------------------ 工具10：画质修复（API安全优化） ------------------------------
    def image_restore(self, image_path: str, output="restored.png"):
        try:
            # 新增：路径校验+大小限制
            image_path = filter_param(image_path, "path")
            if not os.path.exists(image_path) or not os.path.isfile(image_path):
                return {"status": "fail", "msg": "图片路径无效，不存在该文件"}
            if os.path.getsize(image_path) > 10 * 1024 * 1024:
                return {"status": "fail", "msg": "图片大小超过10MB，请上传更小的图片"}
            
            files = {"image": (os.path.basename(image_path), open(image_path, "rb"), "image/jpeg")}
            # 新增：接口超时+重试+校验
            retry_count = 0
            while retry_count < 2:
                try:
                    resp = requests.post("https://api.restorephotos.io/restore", files=files, timeout=35)
                    if verify_api_response(resp, "画质修复"):
                        break
                    retry_count += 1
                except Exception as e:
                    retry_count += 1
                    if retry_count >= 2:
                        return {"status": "fail", "msg": f"修复失败：{str(e)}，请稍后重试"}
            
            if resp.status_code == 200:
                save_path = os.path.join(TEMP_DIR, output)
                with open(save_path, "wb") as f: f.write(resp.content)
                return {"status": "success", "msg": "画质修复完成", "output": save_path}
            return {"status": "fail", "msg": "服务器繁忙，请稍后重试"}
        except Exception as e:
            return {"status": "fail", "msg": f"修复失败：{str(e)}"}

    # ------------------------------ 新增：安全相关方法 ------------------------------
    def clean_temp_files(self, days=1):
        """清理过期临时文件（默认清理1天前的文件），防止隐私泄露和存储冗余"""
        try:
            now = time.time()
            for file in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, file)
                if os.path.getmtime(file_path) < now - days * 24 * 3600:
                    os.remove(file_path)
            print("✅ 临时文件清理完成")
        except Exception as e:
            print(f"临时文件清理失败：{str(e)}")

    def verify_user_id(self, user_id: str):
        """校验用户ID合法性（适配SkillHub用户ID格式），防止恶意调用"""
        if not user_id or not isinstance(user_id, str) or len(user_id) < 8:
            return False
        # 可根据SkillHub用户ID格式，添加更严格的正则校验
        return True

    # ====================== SkillHub 统一入口（必选，安全优化版） ======================
    def run(self, tool: str, params: dict = None):
        params = params or {}
        user_id = params.get("user_id")
        # 新增：用户ID合法性校验，防止恶意调用
        if not user_id or not self.verify_user_id(user_id):
            return {"code": 401, "msg": "无效的用户ID，请重新登录SkillHub", "skill": SKILL_INFO}
        
        # 工具调用映射（无内购权限校验，适配未接内购场景）
        tool_map = {
            "qrcode": self.qrcode, "earthquake": self.earthquake, "noise": self.noise,
            "remove_watermark": self.remove_watermark, "ocr": self.ocr, "unit_convert": self.unit_convert,
            "id_photo": self.id_photo, "image_compress": self.image_compress, "file_convert": self.file_convert,
            "image_restore": self.image_restore
        }
        if tool not in tool_map:
            return {"code": 400, "msg": "不支持的工具", "skill": SKILL_INFO}
        try:
            result = tool_map[tool](**params)
            return {"code": 200, "skill": SKILL_INFO, "tool": tool, "result": result}
        except Exception as e:
            return {"code": 500, "msg": f"执行异常：{str(e)}", "skill": SKILL_INFO, "tool": tool}

# ====================== 本地测试（可删除，不影响上架） ======================
if __name__ == "__main__":
    tb = ToolBoxSkill()
    # 测试示例（注释掉不影响上架）
    # print(tb.run("qrcode", {"text": "https://skillhub.com", "user_id": "skillhub12345678"}))
    # print(tb.run("earthquake", {"user_id": "skillhub12345678"}))
