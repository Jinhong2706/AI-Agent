import os
import sys
import json
import base64
from PIL import Image

from modules.config import load_config, get_api_key
from modules.constants import STYLE_MAPPING


def _gemini_generate_image(
    prompt,
    output_image_path,
    reference_image_path=None,
    api_key=None,
    model=None,
    size=None,
):
    """调用 Gemini API 生成图像"""
    print(f"[*] Generating image with Gemini...")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "Error: google-genai not installed. Run: pip install google-genai",
            file=sys.stderr,
        )
        return False

    try:
        client = genai.Client(api_key=api_key)

        if reference_image_path and os.path.exists(reference_image_path):
            with open(reference_image_path, "rb") as f:
                image_data = f.read()

            import imghdr

            img_type = imghdr.what(reference_image_path)
            mime_type = f"image/{img_type}" if img_type else "image/jpeg"

            contents = [
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt,
            ]
        else:
            contents = prompt

        image_config = None
        if size and "*" in size:
            w, h = map(int, size.split("*"))
            if w > h:
                image_config = types.ImageConfig(aspect_ratio="16:9")
            elif h > w:
                image_config = types.ImageConfig(aspect_ratio="9:16")
            else:
                image_config = types.ImageConfig(aspect_ratio="1:1")

        config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        if image_config:
            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"], image_config=image_config
            )

        response = client.models.generate_content(
            model=model or "gemini-2.5-flash-image",
            contents=contents,
            config=config,
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_image_path, "wb") as f:
                    f.write(image_data)
                print(f"[✓] Image saved: {output_image_path}")
                return True

        print("Error: No image in response", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return False


def _qwen_wanx_generate(
    prompt, output_image_path, model=None, api_base_url=None, api_key=None, size=None
):
    """wanx 系列模型的图像生成（使用 ImageSynthesis API）"""
    import dashscope
    import json
    import requests

    if api_key:
        dashscope.api_key = api_key
    if api_base_url:
        dashscope.base_url = api_base_url

    normalized_model = (model or "wan2.6-t2i").strip().lower()

    try:
        if normalized_model.startswith("wan2."):
            from dashscope.aigc.image_generation import ImageGeneration
            from dashscope.api_entities.dashscope_response import Message

            message = Message(role="user", content=[{"text": prompt}])
            response = ImageGeneration.call(
                model=model or "wan2.6-t2i",
                api_key=api_key,
                messages=[message],
                negative_prompt="",
                prompt_extend=True,
                watermark=False,
                n=1,
                size=size or "1024*1024",
            )

            if response.status_code == 200:
                resp_dict = json.loads(str(response))
                content = (
                    resp_dict.get("output", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", [])
                )
                for item in content:
                    image_url = item.get("image")
                    if image_url:
                        img_response = requests.get(image_url)
                        if img_response.status_code == 200:
                            with open(output_image_path, "wb") as f:
                                f.write(img_response.content)
                            print(f"[✓] Image saved: {output_image_path}")
                            return True
        else:
            from dashscope import ImageSynthesis

            response = ImageSynthesis.call(
                model=model or "wan2.6-t2i",
                prompt=prompt,
                n=1,
                size=size or "1024*1024",
            )

            if response.status_code == 200 and response.output and response.output.results:
                image_url = response.output.results[0].url
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    with open(output_image_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"[✓] Image saved: {output_image_path}")
                    return True
        print(f"Error from Qwen API: {response.message}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        return False


def _qwen_image_generate(
    prompt,
    output_image_path,
    model=None,
    api_base_url=None,
    reference_image_path=None,
    api_key=None,
    size=None,
):
    """qwen-image 系列模型的图像生成（使用 MultiModalConversation API）"""
    import dashscope
    from dashscope import MultiModalConversation

    if api_key:
        dashscope.api_key = api_key
    if api_base_url:
        dashscope.base_http_api_url = api_base_url
    else:
        dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

    try:
        content = [{"text": prompt}]

        if reference_image_path and os.path.exists(reference_image_path):
            with open(reference_image_path, "rb") as f:
                image_data = f.read()
            import imghdr

            img_type = imghdr.what(reference_image_path) or "png"
            content.insert(
                0,
                {
                    "image": f"data:image/{img_type};base64,{base64.b64encode(image_data).decode('utf-8')}"
                },
            )

        messages = [{"role": "user", "content": content}]

        response = MultiModalConversation.call(
            model=model or "qwen-image-2.0-pro",
            messages=messages,
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt="透明格子背景，伪透明背景，噪点，杂质，杂色，颗粒感，地面阴影，投影，光影伪造，边框，网格线，白色边框，黑色边框，分割线，画框，低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有 AI 感，构图混乱，文字模糊，扭曲，背景污染，渐变背景，花纹背景，阴影效果，发光效果",
            size=size or "1024*1024",
        )

        if response.status_code == 200:
            resp_dict = json.loads(str(response))
            if (
                resp_dict.get("output")
                and resp_dict["output"].get("choices")
                and resp_dict["output"]["choices"][0].get("message")
            ):
                message = resp_dict["output"]["choices"][0]["message"]
                if message.get("content"):
                    for item in message["content"]:
                        if item.get("image"):
                            image_url = item["image"]
                            import requests

                            img_response = requests.get(image_url)
                            if img_response.status_code == 200:
                                with open(output_image_path, "wb") as f:
                                    f.write(img_response.content)
                                print(f"[✓] Image saved: {output_image_path}")
                                return True
                            else:
                                print(
                                    f"Error downloading image: {img_response.status_code}",
                                    file=sys.stderr,
                                )
                                return False
            print("Error: No image in response", file=sys.stderr)
            return False
        else:
            print(
                f"Error from Qwen API: HTTP {response.status_code} - {response.message}",
                file=sys.stderr,
            )
            return False
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return False


def _qwen_generate_image(
    prompt,
    output_image_path,
    reference_image_path=None,
    api_key=None,
    model=None,
    api_base_url=None,
    size=None,
):
    """调用千问 API 生成图像"""
    print(f"[*] Generating image with Qwen (model: {model})...")

    try:
        import dashscope
    except ImportError:
        print(
            "Error: dashscope not installed. Run: pip install dashscope",
            file=sys.stderr,
        )
        return False

    dashscope.api_key = api_key
    normalized_model = (model or "").strip().lower()
    is_wanx_model = normalized_model.startswith("wan")

    if is_wanx_model:
        return _qwen_wanx_generate(
            prompt, output_image_path, model, api_base_url, api_key, size
        )
    else:
        return _qwen_image_generate(
            prompt,
            output_image_path,
            model,
            api_base_url,
            reference_image_path,
            api_key,
            size,
        )


def generate_image(
    prompt, output_image_path, reference_image_path=None, provider=None, size=None
):
    """调用图片生成 API 生成图像，支持 Gemini 和 千问（直接传入 prompt 字符串）"""
    config = load_config()

    if not provider:
        provider = config.get("default_provider", "gemini")

    provider_config = config["providers"].get(provider, {})
    api_key = provider_config.get("api_key")

    if not api_key:
        if provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
        elif provider == "qwen":
            api_key = os.environ.get("DASHSCOPE_API_KEY")

        if not api_key:
            api_key, provider = get_api_key()
            if not api_key:
                return False

    print(f"=== Image Generation ({provider.upper()}) ===")
    print(f"[*] Output path: {output_image_path}")
    if reference_image_path:
        print(f"[*] Reference image: {reference_image_path}")

    model = provider_config.get("model")
    if not model:
        model = (
            "gemini-3.1-flash-image-preview"
            if provider == "gemini"
            else "qwen-image-2.0-pro"
        )
    api_base_url = provider_config.get("api_base_url", "")

    print(f"[*] Using model: {model}")
    if size:
        print(f"[*] Image size: {size}")

    if provider == "qwen":
        return _qwen_generate_image(
            prompt,
            output_image_path,
            reference_image_path,
            api_key,
            model,
            api_base_url,
            size,
        )
    else:
        return _gemini_generate_image(
            prompt, output_image_path, reference_image_path, api_key, model, size
        )


def remote_draw_trigger(
    prompt_path, output_image_path, reference_image_path=None, provider=None, size=None
):
    """调用图片生成 API 生成图像（从文件读取 prompt）"""
    print(f"[*] Reading prompt: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return generate_image(
        prompt, output_image_path, reference_image_path, provider, size
    )


def _process_reference_image(image_data, output_path, target_size=512):
    """后处理 reference image：缩放到标准尺寸（512x512）"""
    try:
        from io import BytesIO

        img = Image.open(BytesIO(image_data))

        if img.mode != "RGB":
            img = img.convert("RGB")

        width, height = img.size
        print(f"[*] Generated image size: {width}x{height}")

        if width != height:
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            upper = (height - min_dim) // 2
            right = left + min_dim
            lower = upper + min_dim
            img = img.crop((left, upper, right, lower))
            print(f"[*] Cropped to square: {min_dim}x{min_dim}")

        if img.size != (target_size, target_size):
            img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

        img.save(output_path, "PNG")
        print(f"[✓] Reference image saved: {target_size}x{target_size}")
        return True

    except Exception as e:
        print(f"[!] Reference image post-processing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def transform_photo_to_chibi(photo_path, prompt, output_path, provider=None):
    """将真人照片转换为角色定妆图"""
    print(f"=== Transforming Photo to Sticker Character ===")
    print(f"[*] Input photo: {photo_path}")
    print(f"[*] Output: {output_path}")

    if not os.path.exists(photo_path):
        print(f"Error: Photo not found: {photo_path}", file=sys.stderr)
        return False

    config = load_config()

    if not provider:
        provider = config.get("default_provider", "gemini")

    provider_config = config["providers"].get(provider, {})
    api_key = provider_config.get("api_key")

    if not api_key:
        if provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY")
        elif provider == "qwen":
            api_key = os.environ.get("DASHSCOPE_API_KEY")

        if not api_key:
            api_key, provider = get_api_key()
            if not api_key:
                return False

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "Error: google-genai not installed. Run: pip install google-genai",
            file=sys.stderr,
        )
        return False

    with open(photo_path, "rb") as f:
        photo_data = f.read()

    import imghdr

    img_type = imghdr.what(photo_path)
    mime_type = f"image/{img_type}" if img_type else "image/jpeg"

    print(f"[*] Transforming with gemini-3.1-flash-image-preview...")
    print(f"[*] Letting Gemini identify and transform the main person...")

    try:
        client = genai.Client(api_key=api_key)

        contents = [types.Part.from_bytes(data=photo_data, mime_type=mime_type), prompt]

        response = client.models.generate_content(
            model=model or "gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data

                processed = _process_reference_image(image_data, output_path)
                if processed:
                    return True
                else:
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"[✓] Character reference saved: {output_path}")
                    return True

        print("Error: No image in response", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error transforming photo: {e}", file=sys.stderr)
        return False


def draw_character_reference(prompt, output_path, provider=None):
    """生成角色定妆参考图（不带动作，纯外观展示）"""
    print(f"=== Generating Character Reference Image ===")
    return generate_image(prompt, output_path, provider=provider)
